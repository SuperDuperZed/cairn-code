package ui

import (
        "context"
        "encoding/json"
        "fmt"
        "os/exec"
        "strings"
        "time"

        "github.com/charmbracelet/bubbletea"
        "github.com/charmbracelet/glamour"
        "github.com/charmbracelet/lipgloss"

        "github.com/cairn/cairn-code/internal/agent"
        "github.com/cairn/cairn-code/internal/cost"
        "github.com/cairn/cairn-code/internal/llm"
        "github.com/cairn/cairn-code/internal/session"
)

// State represents the REPL state.
type state int

const (
        stateIdle state = iota
        stateRunning
)

// OutputLine represents a line of output from the agent.
type OutputLine struct {
        Type     string // "text", "tool_use", "tool_result", "error", "system"
        Content  string
        ToolName string
        Duration time.Duration
}

// replModel is the bubbletea Model for the terminal REPL.
type replModel struct {
        agent      *agent.Agent
        state      state
        input      string
        cursor     int
        output     []OutputLine
        history    []string
        histIdx    int
        width      int
        height     int
        totalUsage llm.Usage
        err        error
        quit       bool
        renderer   *glamour.TermRenderer
        spinner    int
        sessionDir string
        sessionID  string // current session ID for auto-save
        model      string // track model name for cost calculation
        gitBranch  string // current git branch
        lastActive time.Time
}

var (
        // Styles
        promptStyle = lipgloss.NewStyle().
                        Bold(true).
                        Foreground(lipgloss.Color("63")) // cyan-ish

        userStyle = lipgloss.NewStyle().
                        Bold(true).
                        Foreground(lipgloss.Color("221")) // warm yellow

        toolNameStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("6")) // cyan

        toolInputStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("245")) // dim

        toolResultStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("245")) // dim

        toolSuccessStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("82")) // green

        toolErrorStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("196")) // red

        errorStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("196")) // red

        systemStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("245")) // dim

        usageStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("245")) // dim

        titleStyle = lipgloss.NewStyle().
                        Bold(true).
                        Foreground(lipgloss.Color("63"))

        costStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("214")) // orange

        statusBarStyle = lipgloss.NewStyle().
                        Foreground(lipgloss.Color("245"))

        statusAccentStyle = lipgloss.NewStyle().
                                Foreground(lipgloss.Color("6")) // cyan

        spinnerChars = []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}
        blinkerChars = []string{"●", "○"}
)

// NewREPL creates a new REPL model.
func NewREPL(a *agent.Agent, sessionDir string) replModel {
        renderer, err := glamour.NewTermRenderer(
                glamour.WithAutoStyle(),
                glamour.WithEmoji(),
        )
        if err != nil {
                renderer = nil
        }

        // Detect git branch
        branch := detectGitBranch()

        return replModel{
                agent:      a,
                state:      stateIdle,
                histIdx:    -1,
                renderer:   renderer,
                sessionDir: sessionDir,
                model:      a.Model(),
                gitBranch:  branch,
                lastActive: time.Now(),
        }
}

// detectGitBranch returns the current git branch name, or empty string if not in a git repo.
func detectGitBranch() string {
        cmd := exec.Command("git", "rev-parse", "--abbrev-ref", "HEAD")
        cmd.Stderr = nil // suppress errors
        out, err := cmd.Output()
        if err != nil {
                return ""
        }
        return strings.TrimSpace(string(out))
}

// Init initializes the model.
func (m replModel) Init() tea.Cmd {
        return tea.Batch(tickSpinner(), tickBlink())
}

// Update handles messages.
func (m replModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
        switch msg := msg.(type) {
        case tea.WindowSizeMsg:
                m.width = msg.Width
                m.height = msg.Height
                return m, nil

        case tea.KeyMsg:
                switch msg.String() {
                case "ctrl+c":
                        if m.state == stateRunning {
                                m.quit = true
                                return m, tea.Quit
                        }
                        m.quit = true
                        return m, tea.Quit

                case "enter":
                        if m.state == stateRunning {
                                return m, nil
                        }

                        input := strings.TrimSpace(m.input)
                        m.input = ""
                        m.cursor = 0

                        // Handle commands
                        if strings.HasPrefix(input, "/") {
                                return m.handleCommand(input)
                        }

                        if input == "" {
                                return m, nil
                        }

                        // Add to history
                        m.history = append(m.history, input)
                        m.histIdx = len(m.history)

                        // Add user message to output
                        m.output = append(m.output, OutputLine{
                                Type:    "user",
                                Content: input,
                        })

                        // Run agent
                        m.state = stateRunning
                        m.lastActive = time.Now()
                        return m, m.runAgent(input)

                case "up":
                        if m.histIdx > 0 {
                                m.histIdx--
                                m.input = m.history[m.histIdx]
                                m.cursor = len(m.input)
                        } else if m.histIdx == 0 {
                                m.input = m.history[0]
                                m.cursor = len(m.input)
                        }

                case "down":
                        if m.histIdx < len(m.history)-1 {
                                m.histIdx++
                                m.input = m.history[m.histIdx]
                                m.cursor = len(m.input)
                        } else {
                                m.histIdx = len(m.history)
                                m.input = ""
                                m.cursor = 0
                        }

                case "backspace":
                        if m.cursor > 0 && m.cursor <= len(m.input) {
                                m.input = m.input[:m.cursor-1] + m.input[m.cursor:]
                                m.cursor--
                        }

                case "ctrl+w": // delete word
                        if m.cursor > 0 {
                                i := m.cursor - 1
                                for i > 0 && m.input[i-1] != ' ' {
                                        i--
                                }
                                m.input = m.input[:i] + m.input[m.cursor:]
                                m.cursor = i
                        }

                case "home":
                        m.cursor = 0

                case "end":
                        m.cursor = len(m.input)

                case "left":
                        if m.cursor > 0 {
                                m.cursor--
                        }

                case "right":
                        if m.cursor < len(m.input) {
                                m.cursor++
                        }

                default:
                        // Insert character at cursor position
                        if len(msg.String()) == 1 {
                                if m.cursor < len(m.input) {
                                        m.input = m.input[:m.cursor] + msg.String() + m.input[m.cursor:]
                                } else {
                                        m.input += msg.String()
                                }
                                m.cursor++
                        }
                }

        case agentCompleteMsg:
                m.state = stateIdle
                m.output = append(m.output, msg.output...)
                m.totalUsage.InputTokens += msg.usage.InputTokens
                m.totalUsage.OutputTokens += msg.usage.OutputTokens
                m.totalUsage.CacheRead += msg.usage.CacheRead
                m.totalUsage.CacheCreate += msg.usage.CacheCreate
                if msg.err != nil {
                        m.err = msg.err
                }
                // Auto-save session after each agent run
                if len(m.agent.History()) > 0 {
                        m.autoSaveSession()
                }

        case agentResultMsg:
                m.state = stateIdle
                if msg.err != nil {
                        m.output = append(m.output, OutputLine{
                                Type:    "error",
                                Content: msg.err.Error(),
                        })
                        m.err = msg.err
                }

        case agentTextMsg:
                m.output = append(m.output, OutputLine{
                        Type:    "text",
                        Content: msg.text,
                })

        case agentToolUseMsg:
                m.output = append(m.output, OutputLine{
                        Type:     "tool_use",
                        ToolName: msg.name,
                        Content:  formatToolInput(msg.input),
                })

        case agentToolResultMsg:
                m.output = append(m.output, OutputLine{
                        Type:     "tool_result",
                        ToolName: msg.name,
                        Content:  msg.output,
                        Duration: msg.duration,
                })

        case agentTurnEndMsg:
                m.totalUsage.InputTokens += msg.usage.InputTokens
                m.totalUsage.OutputTokens += msg.usage.OutputTokens
                m.totalUsage.CacheRead += msg.usage.CacheRead
                m.totalUsage.CacheCreate += msg.usage.CacheCreate

        case spinnerTickMsg:
                m.spinner = (m.spinner + 1) % len(spinnerChars)
                if m.state == stateRunning {
                        return m, tickSpinner()
                }
                return m, nil

        case blinkTickMsg:
                if m.state == stateRunning {
                        return m, tickBlink()
                }
                return m, nil
        }

        return m, nil
}

// View renders the model.
func (m replModel) View() string {
        if m.quit && m.err == nil {
                return ""
        }

        var b strings.Builder
        availHeight := m.height
        if availHeight <= 0 {
                availHeight = 40
        }

        // Reserve lines for: title (1) + gap (1) + status bar (1) + gap (1) + prompt (1) = 5
        reserved := 5
        outputBudget := availHeight - reserved
        if outputBudget < 5 {
                outputBudget = 5
        }

        // Title
        title := titleStyle.Render("⚡ Cairn Code")
        if m.agent != nil {
                title += systemStyle.Render(fmt.Sprintf("  [%s / %s]", m.agent.ProviderName(), m.agent.Model()))
        }
        if m.sessionID != "" {
                title += systemStyle.Render(fmt.Sprintf("  session: %s", m.sessionID[:8]))
        }
        b.WriteString(title)
        b.WriteString("\n\n")

        // Calculate output lines
        renderedLines := m.renderOutput()

        // Check if we have a spinner or tool loader to show at the bottom
        hasActiveIndicator := m.state == stateRunning
        if hasActiveIndicator {
                if outputBudget > 2 {
                        outputBudget--
                }
        }

        // Show only the last N lines that fit
        totalLines := len(renderedLines)
        startIdx := 0
        if totalLines > outputBudget {
                startIdx = totalLines - outputBudget
        }
        // Count newline-delimited lines for proper slicing
        visibleLines := trimToLines(renderedLines, startIdx, outputBudget)
        b.WriteString(visibleLines)

        // Active indicator (spinner or tool loader)
        if m.state == stateRunning {
                if lastLine, ok := m.lastOutputLineInfo(); ok && lastLine.Type == "tool_use" {
                        // Show blinking loader next to the last tool_use
                        blinkIdx := int(time.Now().UnixNano()/300000000) % len(blinkerChars)
                        b.WriteString(fmt.Sprintf(" %s\n", blinkerChars[blinkIdx]))
                } else {
                        b.WriteString(fmt.Sprintf("\n%s Thinking...\n", spinnerChars[m.spinner]))
                }
        }

        // Status bar
        b.WriteString("\n")
        b.WriteString(m.renderStatusBar())
        b.WriteString("\n")

        // Input prompt
        if !m.quit {
                // Render input with cursor
                if m.cursor >= len(m.input) {
                        b.WriteString(promptStyle.Render("⟩ ") + m.input)
                } else {
                        b.WriteString(promptStyle.Render("⟩ ") + m.input[:m.cursor] + m.input[m.cursor:])
                }
                b.WriteString("\n")
        }

        return b.String()
}

// lastOutputLineInfo returns info about the last output line.
func (m *replModel) lastOutputLineInfo() (OutputLine, bool) {
        if len(m.output) == 0 {
                return OutputLine{}, false
        }
        return m.output[len(m.output)-1], true
}

// trimToLines takes the full rendered output string, splits into lines,
// and returns only the last `maxLines` lines starting from `skipFirst`.
func trimToLines(rendered string, skipFirst, maxLines int) string {
        lines := strings.Split(rendered, "\n")
        total := len(lines)
        start := skipFirst
        if start >= total {
                start = 0
        }
        end := start + maxLines
        if end > total {
                end = total
        }
        return strings.Join(lines[start:end], "\n")
}

// renderStatusBar renders the bottom status bar with cost, tokens, git branch, and provider info.
func (m *replModel) renderStatusBar() string {
        if m.width <= 0 {
                m.width = 80
        }

        var parts []string

        // Left side: provider / model
        if m.agent != nil {
                providerModel := fmt.Sprintf("%s/%s", m.agent.ProviderName(), m.agent.Model())
                parts = append(parts, statusAccentStyle.Render(providerModel))
        }

        // Git branch
        if m.gitBranch != "" {
                parts = append(parts, statusBarStyle.Render("⎇ "+m.gitBranch))
        }

        // Session ID
        if m.sessionID != "" {
                parts = append(parts, statusBarStyle.Render(m.sessionID[:8]))
        }

        // Cost
        if m.totalUsage.InputTokens > 0 {
                modelName := m.model
                if m.agent != nil {
                        modelName = m.agent.Model()
                }
                estimatedCost := cost.EstimateCost(modelName,
                        m.totalUsage.InputTokens, m.totalUsage.OutputTokens,
                        m.totalUsage.CacheRead, m.totalUsage.CacheCreate)
                parts = append(parts, costStyle.Render(cost.FormatCostShort(estimatedCost)))
        }

        // Tokens
        if m.totalUsage.InputTokens > 0 {
                tokenStr := fmt.Sprintf("%d↓ %d↑", m.totalUsage.InputTokens, m.totalUsage.OutputTokens)
                if m.totalUsage.CacheRead > 0 {
                        tokenStr += fmt.Sprintf(" cache:%d", m.totalUsage.CacheRead)
                }
                parts = append(parts, usageStyle.Render(tokenStr))
        }

        if len(parts) == 0 {
                return ""
        }

        // Build status bar with separator dots
        separator := usageStyle.Render(" · ")
        line := strings.Join(parts, separator)

        // Truncate to terminal width
        if m.width > 0 && len(line) > m.width {
                line = line[:m.width-3] + "..."
        }

        return line
}

// renderOutput renders all output lines into a single string.
func (m *replModel) renderOutput() string {
        var b strings.Builder
        for _, line := range m.output {
                b.WriteString(m.renderOutputLine(line))
        }
        return b.String()
}

// renderOutputLine renders a single output line.
func (m *replModel) renderOutputLine(line OutputLine) string {
        switch line.Type {
        case "user":
                return userStyle.Render("⟩ " + line.Content) + "\n\n"

        case "text":
                rendered := line.Content
                if m.renderer != nil {
                        md, err := m.renderer.Render(line.Content)
                        if err == nil {
                                rendered = md
                        }
                }
                return rendered + "\n"

        case "tool_use":
                var b strings.Builder
                b.WriteString(toolNameStyle.Render(fmt.Sprintf("▸ %s", line.ToolName)))
                if line.Content != "" {
                        b.WriteString("\n")
                        // Truncate long tool inputs for display
                        content := line.Content
                        if len(content) > 500 {
                                content = content[:500] + "\n  ... [truncated]"
                        }
                        b.WriteString(toolInputStyle.Render(indent(content, "  ")))
                }
                b.WriteString("\n")
                return b.String()

        case "tool_result":
                var b strings.Builder
                // Check if it's an error result
                isError := strings.Contains(line.Content, "Error:")
                if isError {
                        b.WriteString(toolErrorStyle.Render(fmt.Sprintf("  ✗ %s", line.ToolName)))
                } else {
                        b.WriteString(toolSuccessStyle.Render(fmt.Sprintf("  ✓ %s", line.ToolName)))
                }
                if line.Duration > 0 {
                        b.WriteString(usageStyle.Render(fmt.Sprintf(" (%.1fs)", line.Duration.Seconds())))
                }
                b.WriteString("\n")
                // Truncate long tool results for display
                content := strings.TrimSpace(line.Content)
                if len(content) > 2000 {
                        content = content[:2000] + "\n  ... [output truncated]"
                }
                if content != "" {
                        b.WriteString(toolResultStyle.Render(indent(content, "    ")))
                        b.WriteString("\n")
                }
                return b.String()

        case "error":
                return errorStyle.Render("✗ " + line.Content) + "\n\n"

        case "system":
                return systemStyle.Render(line.Content) + "\n"

        default:
                return line.Content + "\n"
        }
}

// handleCommand processes slash commands.
func (m replModel) handleCommand(cmd string) (tea.Model, tea.Cmd) {
        parts := strings.Fields(cmd)
        if len(parts) == 0 {
                return m, nil
        }

        switch parts[0] {
        case "/help", "/?":
                helpText := `Available commands:
  /help              Show this help message
  /clear             Clear conversation history
  /model [name]      Show or change the current model
  /compact           Summarize and compact the conversation using the LLM
  /cost              Show token usage and estimated cost
  /provider          Show current provider
  /save              Save current session to disk
  /resume [id]       Resume a saved session (latest if no ID given)
  /sessions          List all saved sessions
  /tools             List available tools
  /quit, /exit       Exit the application

Keyboard shortcuts:
  Ctrl+C             Quit
  Ctrl+W             Delete word
  Up/Down            Navigate command history
  Home/End           Move cursor to start/end
`
                m.output = append(m.output, OutputLine{
                        Type:    "system",
                        Content: helpText,
                })
                return m, nil

        case "/clear":
                m.agent.Reset()
                m.totalUsage = llm.Usage{}
                m.sessionID = ""
                m.output = append(m.output, OutputLine{
                        Type:    "system",
                        Content: "Conversation cleared.",
                })
                return m, nil

        case "/compact":
                m.state = stateRunning
                return m, m.runCompact()

        case "/model":
                if len(parts) > 1 {
                        newModel := strings.Join(parts[1:], " ")
                        m.agent.SetModel(newModel)
                        m.model = newModel
                        m.output = append(m.output, OutputLine{
                                Type:    "system",
                                Content: fmt.Sprintf("Model set to: %s", newModel),
                        })
                } else {
                        modelName := m.agent.Model()
                        provider := m.agent.ProviderName()
                        pricing := cost.GetModelPricing(modelName)
                        m.output = append(m.output, OutputLine{
                                Type: "system",
                                Content: fmt.Sprintf("Current model: %s (provider: %s)\n  Pricing: $%.2f/M in, $%.2f/M out",
                                        modelName, provider, pricing.InputCostPerM, pricing.OutputCostPerM),
                        })
                }
                return m, nil

        case "/cost":
                modelName := m.model
                if m.agent != nil {
                        modelName = m.agent.Model()
                }
                estimatedCost := cost.EstimateCost(modelName,
                        m.totalUsage.InputTokens, m.totalUsage.OutputTokens,
                        m.totalUsage.CacheRead, m.totalUsage.CacheCreate)
                costText := fmt.Sprintf(`Session Cost Estimate (%s):
  Input tokens:    %s
  Output tokens:   %s
  Cache read:      %s
  Cache creation:  %s
  Estimated cost:  %s`,
                        modelName,
                        formatTokenCount(m.totalUsage.InputTokens),
                        formatTokenCount(m.totalUsage.OutputTokens),
                        formatTokenCount(m.totalUsage.CacheRead),
                        formatTokenCount(m.totalUsage.CacheCreate),
                        cost.FormatCost(estimatedCost),
                )
                m.output = append(m.output, OutputLine{
                        Type:    "system",
                        Content: costText,
                })
                return m, nil

        case "/provider":
                m.output = append(m.output, OutputLine{
                        Type:    "system",
                        Content: fmt.Sprintf("Provider: %s", m.agent.ProviderName()),
                })
                return m, nil

        case "/save":
                return m, m.saveCurrentSession()

        case "/resume":
                resumeID := ""
                if len(parts) > 1 {
                        resumeID = parts[1]
                }
                m.state = stateRunning
                return m, m.resumeSession(resumeID)

        case "/sessions":
                m.state = stateRunning
                return m, m.listSessions()

        case "/tools":
                m.output = append(m.output, OutputLine{
                        Type:    "system",
                        Content: "Available tools: file_read, file_write, file_edit, bash, glob, grep, todo_write, web_search, web_fetch",
                })
                return m, nil

        case "/quit", "/exit", "/q":
                m.quit = true
                return m, tea.Quit

        default:
                m.output = append(m.output, OutputLine{
                        Type:    "error",
                        Content: fmt.Sprintf("Unknown command: %s (type /help for available commands)", parts[0]),
                })
                return m, nil
        }
}

// formatTokenCount formats a token count with comma separators.
func formatTokenCount(count int) string {
        if count == 0 {
                return "0"
        }
        s := fmt.Sprintf("%d", count)
        if len(s) <= 3 {
                return s
        }
        var result []byte
        for i, c := range s {
                if i > 0 && (len(s)-i)%3 == 0 {
                        result = append(result, ',')
                }
                result = append(result, byte(c))
        }
        return string(result)
}

// runAgent runs the agent in a goroutine and returns commands to the tea runtime.
func (m replModel) runAgent(input string) tea.Cmd {
        return func() tea.Msg {
                // Collect output via callbacks
                var collectedOutput []OutputLine
                var totalUsage llm.Usage
                var agentErr error

                cb := agent.Callbacks{
                        OnText: func(text string) {
                                collectedOutput = append(collectedOutput, OutputLine{
                                        Type:    "text",
                                        Content: text,
                                })
                        },
                        OnToolUse: func(name string, input any) {
                                collectedOutput = append(collectedOutput, OutputLine{
                                        Type:     "tool_use",
                                        ToolName: name,
                                        Content:  formatToolInput(input),
                                })
                        },
                        OnToolResult: func(name string, output string, duration time.Duration) {
                                collectedOutput = append(collectedOutput, OutputLine{
                                        Type:     "tool_result",
                                        ToolName: name,
                                        Content:  output,
                                        Duration: duration,
                                })
                        },
                        OnTurnEnd: func(turn int, usage llm.Usage) {
                                totalUsage.InputTokens += usage.InputTokens
                                totalUsage.OutputTokens += usage.OutputTokens
                                totalUsage.CacheRead += usage.CacheRead
                                totalUsage.CacheCreate += usage.CacheCreate
                        },
                        OnError: func(err error) {
                                collectedOutput = append(collectedOutput, OutputLine{
                                        Type:    "error",
                                        Content: err.Error(),
                                })
                        },
                        OnPermission: func(tool string, input any) bool {
                                return true
                        },
                }

                a := m.agent
                a.SetCallbacks(cb)
                agentErr = a.Run(context.Background(), input)

                return agentCompleteMsg{
                        output: collectedOutput,
                        usage:  totalUsage,
                        err:    agentErr,
                }
        }
}

// runCompact runs the compaction command.
func (m replModel) runCompact() tea.Cmd {
        return func() tea.Msg {
                a := m.agent
                a.SetCallbacks(agent.Callbacks{
                        OnError: func(err error) {
                                // noop — handled below
                        },
                })

                err := a.Compact(context.Background())
                if err != nil {
                        return agentCompleteMsg{
                                output: []OutputLine{
                                        {Type: "error", Content: fmt.Sprintf("Compaction failed: %v", err)},
                                },
                                usage: llm.Usage{},
                                err:   err,
                        }
                }

                return agentCompleteMsg{
                        output: []OutputLine{
                                {Type: "system", Content: "Conversation compacted successfully."},
                        },
                        usage: llm.Usage{},
                }
        }
}

// saveCurrentSession saves the current conversation as a session.
func (m replModel) saveCurrentSession() tea.Cmd {
        return func() tea.Msg {
                history := m.agent.History()
                if len(history) == 0 {
                        return agentCompleteMsg{
                                output: []OutputLine{
                                        {Type: "system", Content: "Nothing to save — conversation is empty."},
                                },
                        }
                }

                id := session.NewSessionID()
                sess := session.FromMessages(id, history, m.agent.Model(), m.agent.ProviderName(),
                        m.totalUsage.InputTokens, m.totalUsage.OutputTokens)

                if err := session.SaveSession(m.sessionDir, sess); err != nil {
                        return agentCompleteMsg{
                                output: []OutputLine{
                                        {Type: "error", Content: fmt.Sprintf("Failed to save session: %v", err)},
                                },
                        }
                }

                m.sessionID = id
                return agentCompleteMsg{
                        output: []OutputLine{
                                {Type: "system", Content: fmt.Sprintf("Session saved: %s", id)},
                        },
                }
        }
}

// resumeSession loads and resumes a saved session.
func (m replModel) resumeSession(id string) tea.Cmd {
        return func() tea.Msg {
                sessDir := m.sessionDir
                if id == "" {
                        // Load the most recent session
                        sessions, err := session.ListSessions(sessDir)
                        if err != nil {
                                return agentCompleteMsg{
                                        output: []OutputLine{
                                                {Type: "error", Content: fmt.Sprintf("Failed to list sessions: %v", err)},
                                        },
                                }
                        }
                        if len(sessions) == 0 {
                                return agentCompleteMsg{
                                        output: []OutputLine{
                                                {Type: "system", Content: "No saved sessions found."},
                                        },
                                }
                        }
                        id = sessions[0].ID
                }

                sess, err := session.LoadSession(sessDir, id)
                if err != nil {
                        return agentCompleteMsg{
                                output: []OutputLine{
                                        {Type: "error", Content: fmt.Sprintf("Failed to load session %s: %v", id, err)},
                                },
                        }
                }

                // Restore state
                if sess.Model != "" {
                        m.agent.SetModel(sess.Model)
                        m.model = sess.Model
                }
                m.agent.SetMessages(sess.ToMessages())
                m.totalUsage = llm.Usage{
                        InputTokens:  sess.TokensIn,
                        OutputTokens: sess.TokensOut,
                }
                m.sessionID = sess.ID

                return agentCompleteMsg{
                        output: []OutputLine{
                                {Type: "system", Content: fmt.Sprintf("Resumed session %s (model: %s, messages: %d)", sess.ID, sess.Model, len(sess.Messages))},
                        },
                }
        }
}

// listSessions lists all saved sessions.
func (m replModel) listSessions() tea.Cmd {
        return func() tea.Msg {
                sessions, err := session.ListSessions(m.sessionDir)
                if err != nil {
                        return agentCompleteMsg{
                                output: []OutputLine{
                                        {Type: "error", Content: fmt.Sprintf("Failed to list sessions: %v", err)},
                                },
                        }
                }

                if len(sessions) == 0 {
                        return agentCompleteMsg{
                                output: []OutputLine{
                                        {Type: "system", Content: "No saved sessions found."},
                                },
                        }
                }

                var buf strings.Builder
                buf.WriteString(fmt.Sprintf("Saved sessions (%d):\n\n", len(sessions)))
                for i, s := range sessions {
                        summary := s.Summary
                        if summary == "" {
                                summary = "(no summary)"
                        }
                        buf.WriteString(fmt.Sprintf("  %d. %s  model=%s  msgs=%d  updated=%s\n", i+1, s.ID[:8], s.Model, len(s.Messages), s.UpdatedAt.Format("2006-01-02 15:04")))
                        if len(summary) > 60 {
                                summary = summary[:60] + "..."
                        }
                        buf.WriteString(fmt.Sprintf("     %s\n", summary))
                }

                return agentCompleteMsg{
                        output: []OutputLine{
                                {Type: "system", Content: buf.String()},
                        },
                }
        }
}

// autoSaveSession saves the current session if there is one.
func (m *replModel) autoSaveSession() {
        history := m.agent.History()
        if len(history) == 0 {
                return
        }

        id := m.sessionID
        if id == "" {
                id = session.NewSessionID()
                m.sessionID = id
        }

        sess := session.FromMessages(id, history, m.agent.Model(), m.agent.ProviderName(),
                m.totalUsage.InputTokens, m.totalUsage.OutputTokens)
        // Preserve created-at from existing session
        if prev, err := session.LoadSession(m.sessionDir, id); err == nil {
                sess.CreatedAt = prev.CreatedAt
        }

        _ = session.SaveSession(m.sessionDir, sess)
}

// Message types for tea.Cmd communication.
type agentResultMsg struct {
        err error
}

type agentTextMsg struct {
        text string
}

type agentToolUseMsg struct {
        name  string
        input any
}

type agentToolResultMsg struct {
        name     string
        output   string
        duration time.Duration
}

type agentTurnEndMsg struct {
        usage llm.Usage
}

type spinnerTickMsg time.Time

type blinkTickMsg time.Time

type agentCompleteMsg struct {
        output []OutputLine
        usage  llm.Usage
        err    error
}

// tickSpinner returns a command that ticks the spinner.
func tickSpinner() tea.Cmd {
        return tea.Tick(time.Millisecond*80, func(t time.Time) tea.Msg {
                return spinnerTickMsg(t)
        })
}

// tickBlink returns a command that ticks the tool loader blink.
func tickBlink() tea.Cmd {
        return tea.Tick(time.Millisecond*300, func(t time.Time) tea.Msg {
                return blinkTickMsg(t)
        })
}

// formatToolInput formats a tool's input for display.
func formatToolInput(input any) string {
        if input == nil {
                return ""
        }
        data, err := json.Marshal(input)
        if err != nil {
                return fmt.Sprintf("%v", input)
        }
        // Pretty-print the JSON
        var pretty map[string]any
        if err := json.Unmarshal(data, &pretty); err == nil {
                data, err = json.MarshalIndent(pretty, "", "  ")
                if err == nil {
                        return string(data)
                }
        }
        return string(data)
}

// indent indents each line of text with the given prefix.
func indent(text, prefix string) string {
        lines := strings.Split(text, "\n")
        for i, line := range lines {
                lines[i] = prefix + line
        }
        return strings.Join(lines, "\n")
}
