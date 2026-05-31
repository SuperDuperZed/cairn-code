// xprotect-linux — local-first anti-malware daemon for Ubuntu
// Supply-chain hardened: fanotify pre-exec interception + libyara scanning
// Zero cloud dependencies. Zero external telemetry. Pure UNIX composition.
package main

import (
        "context"
        "encoding/binary"
        "errors"
        "flag"
        "fmt"
        "io"
        "log"
        "os"
        "os/signal"
        "path/filepath"
        "strings"
        "sync"
        "syscall"
        "time"
        "unsafe"

        "github.com/hillu/go-yara/v4"
        "golang.org/x/sys/unix"
)

// ── constants ──────────────────────────────────────────────────────────────

const (
        appName        = "xprotect-linux"
        version        = "1.0.0"
        maxScanBytes   = 64 << 20 // 64 MiB — cap scan to prevent OOM on huge binaries
        eventBufSize   = 4096     // fanotify read buffer (holds multiple metadata structs)
        metadataSize   = 32        // sizeof(struct fanotify_event_metadata) on x86-64
        defaultPidFile = "/run/xprotect-linux/xprotect.pid"
        defaultRules   = "/etc/xprotect-linux/rules"
)

// ── fanotify kernel structures (mirrors <linux/fanotify.h>) ──────────────────

// fanotifyEventMetadata represents struct fanotify_event_metadata.
// Layout must match the kernel: event_len(4) vers(4) reserved(4) pad(4) mask(8) fd(4) pid(4) = 32 bytes.
type fanotifyEventMetadata struct {
        EventLen uint32
        Vers     uint32
        Reserved uint32
        Mask     uint64
        Fd       int32
        Pid      int32
}

// ── configuration ──────────────────────────────────────────────────────────

// Config holds all daemon tuning parameters.
type Config struct {
        RulesDir    string   // directory tree of .yar / .yara files
        WatchMounts []string // mount points to monitor (default ["/"])
        MaxScan     int64    // per-file byte ceiling (default 64 MiB)
        PidFile     string   // runtime PID file path
        Verbose     bool     // extra stderr logging
}

// ── daemon ────────────────────────────────────────────────────────────────

// Daemon is the core runtime: fanotify fd, compiled YARA rules, and event loop.
type Daemon struct {
        cfg     Config
        fanFd   int
        rules   *yara.Rules
        rulesMu sync.RWMutex // guards rule hot-reload
        running bool
}

// NewDaemon constructs a Daemon with sensible defaults applied to any zero-valued fields.
func NewDaemon(cfg Config) *Daemon {
        if cfg.MaxScan <= 0 {
                cfg.MaxScan = maxScanBytes
        }
        if len(cfg.WatchMounts) == 0 {
                cfg.WatchMounts = []string{"/"}
        }
        if cfg.PidFile == "" {
                cfg.PidFile = defaultPidFile
        }
        if cfg.RulesDir == "" {
                cfg.RulesDir = defaultRules
        }
        return &Daemon{cfg: cfg}
}

// ── YARA rule loading ─────────────────────────────────────────────────────

// LoadRules walks the configured rules directory, compiles every .yar/.yara file,
// and atomically swaps the compiled rule set into the daemon.
func (d *Daemon) LoadRules() error {
        compiler, err := yara.NewCompiler()
        if err != nil {
                return fmt.Errorf("yara: new compiler: %w", err)
        }
        defer compiler.Destroy()

        loaded := 0
        err = filepath.WalkDir(d.cfg.RulesDir, func(path string, de os.DirEntry, walkErr error) error {
                if walkErr != nil {
                        return nil // skip unreadable entries, don't abort
                }
                if de.IsDir() {
                        return nil
                }
                ext := strings.ToLower(filepath.Ext(path))
                if ext != ".yar" && ext != ".yara" {
                        return nil
                }
                if addErr := compiler.AddFile(path, ""); addErr != nil {
                        log.Printf("[WARN] skip %s: %v", path, addErr)
                        return nil
                }
                loaded++
                return nil
        })
        if err != nil {
                return fmt.Errorf("yara: walk %s: %w", d.cfg.RulesDir, err)
        }
        if loaded == 0 {
                return fmt.Errorf("yara: no .yar/.yara files found in %s", d.cfg.RulesDir)
        }

        rules, err := compiler.GetRules()
        if err != nil {
                return fmt.Errorf("yara: compile: %w", err)
        }

        ruleCount := len(rules.GetRules())
        d.rulesMu.Lock()
        d.rules = rules
        d.rulesMu.Unlock()

        log.Printf("[INFO] compiled %d rule file(s), %d active signatures", loaded, ruleCount)
        return nil
}

// ReloadRules is a safe facade for SIGHUP recompilation.
func (d *Daemon) ReloadRules() {
        log.Print("[INFO] SIGHUP received — reloading rules")
        if err := d.LoadRules(); err != nil {
                log.Printf("[ERROR] reload failed: %v (keeping previous rules)", err)
        }
}

// ── fanotify lifecycle ───────────────────────────────────────────────────

// InitFanotify creates the fanotify monitoring fd with pre-content permission class.
func (d *Daemon) InitFanotify() error {
        // FAN_CLASS_PRE_CONTENT: enables permission events (FAN_OPEN_EXEC_PERM) before page-load.
        // FAN_CLOEXEC: fd does not leak into child processes across execve(2).
        fd, err := unix.FanotifyInit(unix.FAN_CLASS_PRE_CONTENT|unix.FAN_CLOEXEC, unix.O_RDONLY|unix.O_LARGEFILE)
        if err != nil {
                return fmt.Errorf("fanotify_init: %w", err)
        }
        d.fanFd = fd
        return nil
}

// AddWatchMarks registers FAN_OPEN_EXEC_PERM on every configured mount point.
func (d *Daemon) AddWatchMarks() error {
        mask := uint64(unix.FAN_OPEN_EXEC_PERM)
        for _, mnt := range d.cfg.WatchMounts {
                if err := unix.FanotifyMark(d.fanFd,
                        unix.FAN_MARK_ADD|unix.FAN_MARK_MOUNT,
                        mask, unix.AT_FDCWD, mnt,
                ); err != nil {
                        return fmt.Errorf("fanotify_mark %s: %w", mnt, err)
                }
                log.Printf("[INFO] monitoring mount: %s (FAN_OPEN_EXEC_PERM)", mnt)
        }
        return nil
}

// ── fanotify response ──────────────────────────────────────────────────────

// respond writes a struct fanotify_response into the fanotify fd.
// The kernel unblocks the waiting process according to allow/deny.
func (d *Daemon) respond(eventFd int32, allow bool) {
        var buf [8]byte
        binary.LittleEndian.PutUint32(buf[0:4], uint32(eventFd))
        resp := uint32(unix.FAN_ALLOW)
        if !allow {
                resp = uint32(unix.FAN_DENY)
        }
        binary.LittleEndian.PutUint32(buf[4:8], resp)

        if _, err := unix.Write(d.fanFd, buf[:]); err != nil {
                log.Printf("[ERROR] fanotify response write failed (fd=%d): %v", eventFd, err)
        }
}

// ── path resolution ─────────────────────────────────────────────────────────

// resolveFdPath reads /proc/self/fd/<n> symlink to obtain the absolute file path.
func resolveFdPath(fd int) string {
        link, err := os.Readlink(fmt.Sprintf("/proc/self/fd/%d", fd))
        if err != nil {
                return "<unreadable>"
        }
        return link
}

// ── exemption logic ────────────────────────────────────────────────────────

// trustedPrefixes are paths that are implicitly allowed to avoid false positives
// on core OS binaries. This list should be audited before production deployment.
var trustedPrefixes = []string{
        "/usr/bin/", "/usr/sbin/", "/usr/lib/", "/usr/libexec/",
        "/bin/", "/sbin/", "/lib/", "/lib64/",
        "/snap/", "/snapd/", "/nix/store/",
        "/opt/", // many third-party tools install here
}

// isExempt returns true for files in trusted system directories.
func isExempt(fdPath string) bool {
        for _, prefix := range trustedPrefixes {
                if strings.HasPrefix(fdPath, prefix) {
                        return true
                }
        }
        return false
}

// ── content scanning ──────────────────────────────────────────────────────

// readFdContent reads up to max bytes from the fanotify event fd.
// The fd position is at offset 0 (fanotify opens fresh for each event).
func readFdContent(fd int, max int64) ([]byte, error) {
        var stat unix.Stat_t
        if err := unix.Fstat(fd, &stat); err != nil {
                return nil, fmt.Errorf("fstat: %w", err)
        }

        readSize := stat.Size
        if readSize > max {
                readSize = max
        }
        if readSize <= 0 {
                return nil, nil
        }

        buf := make([]byte, readSize)
        n, err := unix.Read(fd, buf)
        if err != nil && err != io.EOF {
                return nil, fmt.Errorf("read: %w", err)
        }
        if n == 0 {
                return nil, nil
        }
        return buf[:n], nil
}

// scanContent runs the compiled YARA rule set against an in-memory buffer.
// Returns matched rule identifiers or an empty slice on clean content.
func (d *Daemon) scanContent(buf []byte) ([]string, error) {
        if len(buf) == 0 {
                return nil, nil
        }

        d.rulesMu.RLock()
        defer d.rulesMu.RUnlock()

        var matches yara.MatchRules
        if err := d.rules.ScanMem(buf, 0, 0, &matches); err != nil {
                return nil, fmt.Errorf("yara scan: %w", err)
        }

        if len(matches) == 0 {
                return nil, nil
        }

        ids := make([]string, 0, len(matches))
        for _, m := range matches {
                ids = append(ids, m.Rule)
        }
        return ids, nil
}

// ── event processing ──────────────────────────────────────────────────────

// processEvent handles a single fanotify permission event.
//
// Error containment contract:
//  1. Every code path MUST close the event fd (defer guarantees this).
//  2. On panic or unhandled error, the fd is closed which yields an implicit
//     FAN_ALLOW from the kernel — the system never locks up.
//  3. FAN_DENY is sent ONLY on confirmed signature match.
func (d *Daemon) processEvent(meta fanotifyEventMetadata) {
        eventFd := int(meta.Fd)
        if eventFd < 0 {
                return
        }

        // Non-permission events: close fd, move on.
        if meta.Mask&unix.FAN_OPEN_EXEC_PERM == 0 {
                unix.Close(eventFd)
                return
        }

        pid := meta.Pid

        // ── Safety net: close fd on any panic (implicit ALLOW) ────────────
        defer unix.Close(eventFd)

        responded := false
        defer func() {
                if r := recover(); r != nil {
                        log.Printf("[PANIC] recovered in event handler (pid=%d): %v", pid, r)
                }
                if !responded {
                        // Unhandled path — allow to prevent system deadlock.
                        d.respond(meta.Fd, true)
                }
        }()

        // ── Resolve paths for logging ─────────────────────────────────────
        fdPath := resolveFdPath(eventFd)
        exePath := "<unknown>"
        if link, err := os.Readlink(fmt.Sprintf("/proc/%d/exe", pid)); err == nil {
                exePath = link
        }

        if d.cfg.Verbose {
                log.Printf("[TRACE] exec intercept pid=%d exe=%s target=%s", pid, exePath, fdPath)
        }

        // ── Exemption: trusted system paths → ALLOW ────────────────────────
        if isExempt(fdPath) {
                d.respond(meta.Fd, true)
                responded = true
                return
        }

        // ── Read file content through the fanotify fd ─────────────────────
        content, err := readFdContent(eventFd, d.cfg.MaxScan)
        if err != nil {
                log.Printf("[WARN] read %s (pid=%d): %v → ALLOW", fdPath, pid, err)
                return // defer sends ALLOW
        }

        // ── YARA scan ────────────────────────────────────────────────────
        matched, err := d.scanContent(content)
        if err != nil {
                log.Printf("[ERROR] scan %s (pid=%d): %v → ALLOW", fdPath, pid, err)
                return // defer sends ALLOW
        }

        if len(matched) == 0 {
                // Clean binary — allow execution.
                d.respond(meta.Fd, true)
                responded = true
                return
        }

        // ── SIGNATURE MATCH → DENY + TERMINATE ────────────────────────────
        ruleStr := strings.Join(matched, ",")
        log.Printf("[ALERT] MALWARE DETECTED — pid=%d exe=%s path=%s rules=[%s]",
                pid, exePath, fdPath, ruleStr)

        d.respond(meta.Fd, false) // explicit DENY
        responded = true

        // Send SIGKILL to the offending process.
        if err := syscall.Kill(pid, syscall.SIGKILL); err != nil {
                log.Printf("[ERROR] kill pid=%d: %v", pid, err)
        } else {
                log.Printf("[BLOCK] terminated pid=%d — matched: [%s]", pid, ruleStr)
        }
}

// ── event loop ─────────────────────────────────────────────────────────────

// eventLoop reads packed fanotify events from the kernel and dispatches each
// one to processEvent. Runs until the context is cancelled.
func (d *Daemon) eventLoop(ctx context.Context) {
        buf := make([]byte, eventBufSize)

        for d.running {
                select {
                case <-ctx.Done():
                        return
                default:
                }

                n, err := unix.Read(d.fanFd, buf)
                if err != nil {
                        if errors.Is(err, unix.EINTR) || errors.Is(err, context.Canceled) {
                                continue
                        }
                        log.Printf("[ERROR] fanotify read: %v", err)
                        // Brief sleep to avoid tight loop on persistent error.
                        time.Sleep(100 * time.Millisecond)
                        continue
                }

                if n < metadataSize {
                        continue // partial read, discard
                }

                // Walk packed event metadata structs.
                offset := 0
                for offset < n {
                        if n-offset < metadataSize {
                                break
                        }
                        meta := *(*fanotifyEventMetadata)(unsafe.Pointer(&buf[offset]))
                        if meta.EventLen == 0 {
                                break // corrupt event, stop processing this batch
                        }
                        d.processEvent(meta)
                        offset += int(meta.EventLen)
                }
        }
}

// ── signal handling ──────────────────────────────────────────────────────

// handleSignals wires up SIGTERM/SIGINT for graceful shutdown and SIGHUP for
// live rule reloading.
func (d *Daemon) handleSignals(ctx context.Context, cancel context.CancelFunc) {
        sigCh := make(chan os.Signal, 1)
        signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT, syscall.SIGHUP)

        for {
                select {
                case <-ctx.Done():
                        return
                case sig := <-sigCh:
                        switch sig {
                        case syscall.SIGHUP:
                                d.ReloadRules()
                        default:
                                log.Printf("[INFO] received %v — shutting down", sig)
                                d.running = false
                                cancel()
                                return
                        }
                }
        }
}

// ── shutdown ───────────────────────────────────────────────────────────────

// Shutdown closes the fanotify fd and removes the PID file.
func (d *Daemon) Shutdown() {
        if d.fanFd >= 0 {
                unix.Close(d.fanFd)
                log.Print("[INFO] fanotify fd closed")
        }
        removePidFile(d.cfg.PidFile)
}

// ── PID file ───────────────────────────────────────────────────────────────

func writePidFile(path string) error {
        if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
                return fmt.Errorf("mkdir pid dir: %w", err)
        }
        if err := os.WriteFile(path, []byte(fmt.Sprintf("%d", os.Getpid())), 0644); err != nil {
                return fmt.Errorf("write pid: %w", err)
        }
        return nil
}

func removePidFile(path string) {
        os.Remove(path) // best-effort
}

// ── entry point ───────────────────────────────────────────────────────────

func main() {
        // ── CLI flags ──────────────────────────────────────────────────────
        rulesDir := flag.String("rules", defaultRules, "directory containing .yar/.yara rule files")
        pidFile := flag.String("pid", defaultPidFile, "PID file path")
        maxScan := flag.Int64("max-scan", maxScanBytes, "max bytes to scan per file")
        verbose := flag.Bool("v", false, "verbose logging (per-event tracing)")
        showVer := flag.Bool("version", false, "print version and exit")

        flag.Parse()

        if *showVer {
                fmt.Printf("%s %s\n", appName, version)
                os.Exit(0)
        }

        log.SetOutput(os.Stderr)
        log.SetFlags(log.Ldate | log.Ltime | log.Lmicroseconds | log.Lshortfile)

        log.Printf("[INFO] %s v%s starting", appName, version)

        // ── Daemon setup ──────────────────────────────────────────────────
        d := NewDaemon(Config{
                RulesDir:    *rulesDir,
                WatchMounts: []string{"/"},
                MaxScan:     *maxScan,
                PidFile:     *pidFile,
                Verbose:     *verbose,
        })

        // ── Initialize libyara ────────────────────────────────────────────
        if err := yara.Init(nil); err != nil {
                log.Fatalf("[FATAL] yara.Init: %v", err)
        }

        // ── Load rules ────────────────────────────────────────────────────
        if err := d.LoadRules(); err != nil {
                log.Fatalf("[FATAL] %v", err)
        }

        // ── Init fanotify ─────────────────────────────────────────────────
        if err := d.InitFanotify(); err != nil {
                log.Fatalf("[FATAL] %v", err)
        }
        defer d.Shutdown()

        if err := d.AddWatchMarks(); err != nil {
                log.Fatalf("[FATAL] %v", err)
        }

        // ── PID file ──────────────────────────────────────────────────────
        if err := writePidFile(d.cfg.PidFile); err != nil {
                log.Fatalf("[FATAL] pid file: %v", err)
        }

        // ── Start event loop ──────────────────────────────────────────────
        d.running = true
        ctx, cancel := context.WithCancel(context.Background())

        go d.handleSignals(ctx, cancel)

        log.Print("[INFO] event loop active — monitoring all execve(2) on /")
        d.eventLoop(ctx)

        // ── Cleanup ──────────────────────────────────────────────────────
        d.running = false
        yara.Finalize()
        log.Print("[INFO] stopped")
}
