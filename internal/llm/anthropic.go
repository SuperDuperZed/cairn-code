package llm

import (
        "bufio"
        "bytes"
        "context"
        "encoding/json"
        "fmt"
        "io"
        "net/http"
        "strings"
        "time"

        "github.com/cairn/cairn-code/internal/config"
)

// AnthropicProvider implements the Provider interface for Anthropic's API.
type AnthropicProvider struct {
        apiKey  string
        baseURL string
        client  *http.Client
}

// NewAnthropicProvider creates a new Anthropic provider.
func NewAnthropicProvider(cfg *config.Config) *AnthropicProvider {
        return &AnthropicProvider{
                apiKey:  cfg.GetAnthropicAPIKey(),
                baseURL: cfg.GetAnthropicBaseURL(),
                client:  &http.Client{Timeout: 120 * time.Second},
        }
}

// Name returns the provider name.
func (p *AnthropicProvider) Name() string {
        return "anthropic"
}

// AvailableModels returns the list of available Anthropic models.
func (p *AnthropicProvider) AvailableModels() []ModelInfo {
        return []ModelInfo{
                {ID: "claude-sonnet-4-20250514", Name: "Claude Sonnet 4", MaxCtx: 200000},
                {ID: "claude-3-5-sonnet-20241022", Name: "Claude 3.5 Sonnet", MaxCtx: 200000},
                {ID: "claude-3-5-haiku-20241022", Name: "Claude 3.5 Haiku", MaxCtx: 200000},
                {ID: "claude-3-opus-20240229", Name: "Claude 3 Opus", MaxCtx: 200000},
        }
}

// anthropicRequest is the request format for Anthropic's API.
type anthropicRequest struct {
        Model     string              `json:"model"`
        MaxTokens int                 `json:"max_tokens"`
        System    string              `json:"system,omitempty"`
        Messages  []anthropicMessage  `json:"messages"`
        Tools     []anthropicTool     `json:"tools,omitempty"`
}

type anthropicMessage struct {
        Role    string `json:"role"`
        Content any    `json:"content"`
}

type anthropicTool struct {
        Name        string         `json:"name"`
        Description string         `json:"description"`
        InputSchema map[string]any `json:"input_schema"`
}

// anthropicResponse is the response format from Anthropic's API.
type anthropicResponse struct {
        ID           string              `json:"id"`
        Type         string              `json:"type"`
        Role         string              `json:"role"`
        Content      []anthropicContent   `json:"content"`
        Model        string              `json:"model"`
        StopReason   string              `json:"stop_reason"`
        Usage        anthropicUsage      `json:"usage"`
}

type anthropicContent struct {
        Type    string         `json:"type"`
        Text    string         `json:"text,omitempty"`
        ID      string         `json:"id,omitempty"`
        Name    string         `json:"name,omitempty"`
        Input   json.RawMessage `json:"input,omitempty"`
        Content string         `json:"content,omitempty"`
        IsError bool           `json:"is_error,omitempty"`
}

type anthropicUsage struct {
        InputTokens              int `json:"input_tokens"`
        OutputTokens             int `json:"output_tokens"`
        CacheReadInputTokens     int `json:"cache_read_input_tokens"`
        CacheCreationInputTokens int `json:"cache_creation_input_tokens"`
}

// SendMessage sends a message to the Anthropic API.
func (p *AnthropicProvider) SendMessage(ctx context.Context, messages []Message, tools []ToolDefinition, system string, model string) (*Response, error) {
        if model == "" {
                model = "claude-sonnet-4-20250514"
        }

        // Convert messages to Anthropic format
        anthMessages := make([]anthropicMessage, 0, len(messages))
        for _, msg := range messages {
                if msg.Role == RoleSystem {
                        // Anthropic handles system separately
                        continue
                }
                anthMsg := anthropicMessage{
                        Role:    string(msg.Role),
                        Content: convertContentToAnthropic(msg.Content),
                }
                anthMessages = append(anthMessages, anthMsg)
        }

        // Build request
        reqBody := anthropicRequest{
                Model:     model,
                MaxTokens: 8192,
                System:    system,
                Messages:  anthMessages,
        }

        // Convert tools
        if len(tools) > 0 {
                anthTools := make([]anthropicTool, 0, len(tools))
                for _, t := range tools {
                        anthTools = append(anthTools, anthropicTool{
                                Name:        t.Name,
                                Description: t.Description,
                                InputSchema: t.InputSchema,
                        })
                }
                reqBody.Tools = anthTools
        }

        jsonBody, err := json.Marshal(reqBody)
        if err != nil {
                return nil, fmt.Errorf("marshaling request: %w", err)
        }

        // Create HTTP request
        url := p.baseURL + "/v1/messages"
        req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(jsonBody))
        if err != nil {
                return nil, fmt.Errorf("creating request: %w", err)
        }

        req.Header.Set("x-api-key", p.apiKey)
        req.Header.Set("anthropic-version", "2023-06-01")
        req.Header.Set("content-type", "application/json")

        // Send request
        resp, err := p.client.Do(req)
        if err != nil {
                return nil, fmt.Errorf("sending request: %w", err)
        }
        defer resp.Body.Close()

        body, err := io.ReadAll(resp.Body)
        if err != nil {
                return nil, fmt.Errorf("reading response: %w", err)
        }

        if resp.StatusCode != http.StatusOK {
                return nil, fmt.Errorf("anthropic API error (status %d): %s", resp.StatusCode, string(body))
        }

        // Parse response
        var anthResp anthropicResponse
        if err := json.Unmarshal(body, &anthResp); err != nil {
                return nil, fmt.Errorf("parsing response: %w", err)
        }

        // Convert to our format
        return p.convertResponse(&anthResp), nil
}

// convertContentToAnthropic converts message content to Anthropic format.
func convertContentToAnthropic(content any) any {
        switch c := content.(type) {
        case string:
                return c
        case []ContentBlock:
                blocks := make([]anthropicContent, 0, len(c))
                for _, b := range c {
                        ab := anthropicContent{
                                Type:    b.Type,
                                Text:    b.Text,
                                ID:      b.ID,
                                Name:    b.Name,
                                Content: b.Content,
                                IsError: b.IsError,
                        }
                        if b.Input != nil {
                                inputJSON, _ := json.Marshal(b.Input)
                                ab.Input = inputJSON
                        }
                        blocks = append(blocks, ab)
                }
                return blocks
        default:
                return c
        }
}

// Ensure AnthropicProvider satisfies StreamingProvider.
var _ StreamingProvider = (*AnthropicProvider)(nil)

// StreamMessage sends a streaming request to the Anthropic API.
func (p *AnthropicProvider) StreamMessage(ctx context.Context, messages []Message, tools []ToolDefinition, system string, model string, cb StreamingCallback) (*Response, error) {
        if model == "" {
                model = "claude-sonnet-4-20250514"
        }

        // Convert messages to Anthropic format
        anthMessages := make([]anthropicMessage, 0, len(messages))
        for _, msg := range messages {
                if msg.Role == RoleSystem {
                        continue
                }
                anthMsg := anthropicMessage{
                        Role:    string(msg.Role),
                        Content: convertContentToAnthropic(msg.Content),
                }
                anthMessages = append(anthMessages, anthMsg)
        }

        // Build streaming request
        type streamRequest struct {
                anthropicRequest
                Stream bool `json:"stream"`
        }
        reqBody := streamRequest{
                anthropicRequest: anthropicRequest{
                        Model:     model,
                        MaxTokens: 8192,
                        System:    system,
                        Messages:  anthMessages,
                },
                Stream: true,
        }

        // Convert tools
        if len(tools) > 0 {
                anthTools := make([]anthropicTool, 0, len(tools))
                for _, t := range tools {
                        anthTools = append(anthTools, anthropicTool{
                                Name:        t.Name,
                                Description: t.Description,
                                InputSchema: t.InputSchema,
                        })
                }
                reqBody.Tools = anthTools
        }

        jsonBody, err := json.Marshal(reqBody)
        if err != nil {
                return nil, fmt.Errorf("marshaling streaming request: %w", err)
        }

        // Create HTTP request (use longer timeout for streaming)
        client := &http.Client{Timeout: 300 * time.Second}
        url := p.baseURL + "/v1/messages"
        req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(jsonBody))
        if err != nil {
                return nil, fmt.Errorf("creating streaming request: %w", err)
        }

        req.Header.Set("x-api-key", p.apiKey)
        req.Header.Set("anthropic-version", "2023-06-01")
        req.Header.Set("content-type", "application/json")
        req.Header.Set("Accept", "text/event-stream")

        resp, err := client.Do(req)
        if err != nil {
                return nil, fmt.Errorf("sending streaming request: %w", err)
        }
        defer resp.Body.Close()

        if resp.StatusCode != http.StatusOK {
                body, _ := io.ReadAll(resp.Body)
                return nil, fmt.Errorf("anthropic streaming API error (status %d): %s", resp.StatusCode, string(body))
        }

        // Parse SSE stream
        var blocks []ContentBlock
        var currentTextBlock *ContentBlock
        var currentToolBlock *ContentBlock
        var toolInputBuilder *strings.Builder
        var stopReason string
        var responseModel string
        var usage anthropicUsage

        scanner := bufio.NewScanner(resp.Body)
        scanner.Buffer(make([]byte, 65536), 65536)

        var currentEvent string
        for scanner.Scan() {
                line := scanner.Text()

                // Track SSE event type
                if strings.HasPrefix(line, "event: ") {
                        currentEvent = strings.TrimPrefix(line, "event: ")
                        continue
                }

                if !strings.HasPrefix(line, "data: ") {
                        continue
                }

                data := strings.TrimPrefix(line, "data: ")
                if data == "" {
                        continue
                }

                switch currentEvent {
                case "message_start":
                        var msgEvent struct {
                                Message anthropicResponse `json:"message"`
                        }
                        if err := json.Unmarshal([]byte(data), &msgEvent); err == nil {
                                responseModel = msgEvent.Message.Model
                                usage = msgEvent.Message.Usage
                        }

                case "content_block_start":
                        var blockEvent struct {
                                Index  int `json:"index"`
                                Content struct {
                                        Type string `json:"type"`
                                        Text string `json:"text,omitempty"`
                                        ID   string `json:"id,omitempty"`
                                        Name string `json:"name,omitempty"`
                                } `json:"content_block"`
                        }
                        if err := json.Unmarshal([]byte(data), &blockEvent); err == nil {
                                switch blockEvent.Content.Type {
                                case "text":
                                        currentTextBlock = &ContentBlock{Type: "text", Text: ""}
                                case "tool_use":
                                        currentToolBlock = &ContentBlock{
                                                Type: "tool_use",
                                                ID:   blockEvent.Content.ID,
                                                Name: blockEvent.Content.Name,
                                        }
                                        toolInputBuilder = &strings.Builder{}
                                }
                        }

                case "content_block_delta":
                        var deltaEvent struct {
                                Delta struct {
                                        Type      string `json:"type"`
                                        Text      string `json:"text,omitempty"`
                                        PartialJS string `json:"partial_json,omitempty"`
                                } `json:"delta"`
                        }
                        if err := json.Unmarshal([]byte(data), &deltaEvent); err == nil {
                                switch deltaEvent.Delta.Type {
                                case "text_delta":
                                        if currentTextBlock != nil {
                                                currentTextBlock.Text += deltaEvent.Delta.Text
                                                if cb != nil {
                                                        cb(deltaEvent.Delta.Text, false)
                                                }
                                        }
                                case "input_json_delta":
                                        if toolInputBuilder != nil {
                                                toolInputBuilder.WriteString(deltaEvent.Delta.PartialJS)
                                        }
                                }
                        }

                case "content_block_stop":
                        if currentTextBlock != nil && currentTextBlock.Text != "" {
                                blocks = append(blocks, *currentTextBlock)
                                currentTextBlock = nil
                        }
                        if currentToolBlock != nil && toolInputBuilder != nil {
                                var input any
                                json.Unmarshal([]byte(toolInputBuilder.String()), &input)
                                currentToolBlock.Input = input
                                blocks = append(blocks, *currentToolBlock)
                                currentToolBlock = nil
                                toolInputBuilder = nil
                        }

                case "message_delta":
                        var msgDelta struct {
                                Delta struct {
                                        StopReason string `json:"stop_reason"`
                                } `json:"delta"`
                                Usage struct {
                                        OutputTokens int `json:"output_tokens"`
                                } `json:"usage"`
                        }
                        if err := json.Unmarshal([]byte(data), &msgDelta); err == nil {
                                if msgDelta.Delta.StopReason != "" {
                                        stopReason = msgDelta.Delta.StopReason
                                }
                                usage.OutputTokens = msgDelta.Usage.OutputTokens
                        }
                }
        }

        // Signal done
        if cb != nil {
                cb("", true)
        }

        if len(blocks) == 0 {
                blocks = append(blocks, ContentBlock{Type: "text", Text: ""})
        }

        return &Response{
                Content:    blocks,
                StopReason: stopReason,
                Model:      responseModel,
                Usage: Usage{
                        InputTokens:  usage.InputTokens,
                        OutputTokens: usage.OutputTokens,
                        CacheRead:    usage.CacheReadInputTokens,
                        CacheCreate:  usage.CacheCreationInputTokens,
                },
        }, nil
}

// convertResponse converts an Anthropic response to our format.
func (p *AnthropicProvider) convertResponse(anthResp *anthropicResponse) *Response {
        blocks := make([]ContentBlock, 0, len(anthResp.Content))
        for _, c := range anthResp.Content {
                block := ContentBlock{
                        Type:    c.Type,
                        Text:    c.Text,
                        ID:      c.ID,
                        Name:    c.Name,
                        Content: c.Content,
                        IsError: c.IsError,
                }
                if c.Input != nil {
                        var input any
                        json.Unmarshal(c.Input, &input)
                        block.Input = input
                }
                blocks = append(blocks, block)
        }

        return &Response{
                Content:    blocks,
                StopReason: anthResp.StopReason,
                Model:      anthResp.Model,
                Usage: Usage{
                        InputTokens:  anthResp.Usage.InputTokens,
                        OutputTokens: anthResp.Usage.OutputTokens,
                        CacheRead:    anthResp.Usage.CacheReadInputTokens,
                        CacheCreate:  anthResp.Usage.CacheCreationInputTokens,
                },
        }
}
