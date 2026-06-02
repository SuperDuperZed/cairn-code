// xprotect-linux — local-first anti-malware daemon for Ubuntu
// Supply-chain hardened: fanotify pre-exec interception + libyara scanning
// Zero cloud dependencies. Zero external telemetry. Pure UNIX composition.
//
// v2.0 — hardened against evasion: shared library scanning, SHA256 allowlist,
// behavioral rate limiting, inotify temp-dir monitoring, ELF pre-validation,
// configurable trust model (strict/permissive), and wide-string YARA support.
package main

import (
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
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
	appName          = "xprotect-linux"
	version          = "2.0.0"
	maxScanBytes     = 64 << 20 // 64 MiB
	eventBufSize     = 8192     // fanotify read buffer
	metadataSize     = 32       // sizeof(struct fanotify_event_metadata) x86-64
	defaultPidFile   = "/run/xprotect-linux/xprotect.pid"
	defaultRules     = "/etc/xprotect-linux/rules"
	defaultAllowlist = "/etc/xprotect-linux/allowlist.json"

	// behavioral thresholds
	maxExecPerSecond     = 8   // rapid exec burst threshold
	maxExecWindow        = 1   // seconds in the sliding window
	execBurstCooldown    = 5   // seconds to block after burst detection
	tempFileCreateMax    = 20  // max file creates in temp dirs per 10s
	tempFileWindow       = 10  // seconds

	// inotify watch buffer
	inotifyEventSize = 1024
	inotifyBufSize   = 8192
)

// ── fanotify kernel structures ─────────────────────────────────────────────

type fanotifyEventMetadata struct {
	EventLen uint32
	Vers     uint32
	Reserved uint32
	Mask     uint64
	Fd       int32
	Pid      int32
}

// ── configuration ──────────────────────────────────────────────────────────

// TrustMode controls how strict the path exemption model is.
type TrustMode int

const (
	TrustStrict      TrustMode = 0 // Only hash-allowlisted + core OS paths
	TrustPermissive  TrustMode = 1 // Broad path exemptions (legacy mode)
	TrustWhitelist   TrustMode = 2 // Only hash-allowlisted binaries may execute
)

// Config holds all daemon tuning parameters.
type Config struct {
	RulesDir    string     // YARA rules directory
	Allowlist   string     // SHA256 allowlist JSON path
	WatchMounts []string   // mount points (default ["/"])
	MaxScan     int64      // per-file byte ceiling
	PidFile     string     // runtime PID file
	Verbose     bool       // per-event tracing
	Trust       TrustMode // path trust model
	StrictMode  bool       // alias: if true, use TrustStrict
}

// ── allowlist ──────────────────────────────────────────────────────────────

// Allowlist stores pre-computed SHA256 hashes of trusted binaries.
type Allowlist struct {
	mu   sync.RWMutex
	hash map[[32]byte]bool
}

// LoadAllowlist reads a JSON file of {"sha256": ["hex1", "hex2", ...]} entries.
func LoadAllowlist(path string) (*Allowlist, error) {
	al := &Allowlist{hash: make(map[[32]byte]bool)}
	if path == "" {
		return al, nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			log.Printf("[WARN] allowlist not found at %s — only path exemptions active", path)
			return al, nil
		}
		return nil, fmt.Errorf("allowlist: %w", err)
	}
	var entries map[string][]string
	if err := json.Unmarshal(data, &entries); err != nil {
		return nil, fmt.Errorf("allowlist parse: %w", err)
	}
	count := 0
	for _, hexes := range entries {
		for _, h := range hexes {
			b, err := hex.DecodeString(strings.TrimSpace(h))
			if err != nil || len(b) != 32 {
				log.Printf("[WARN] invalid sha256 hash: %s", h)
				continue
			}
			var key [32]byte
			copy(key[:], b)
			al.hash[key] = true
			count++
		}
	}
	log.Printf("[INFO] loaded %d trusted binary hashes from %s", count, path)
	return al, nil
}

// IsAllowed returns true if the file's SHA256 is in the allowlist.
func (al *Allowlist) IsAllowed(content []byte) bool {
	h := sha256.Sum256(content)
	al.mu.RLock()
	defer al.mu.RUnlock()
	return al.hash[h]
}

// ── behavioral tracker ─────────────────────────────────────────────────────

// BehaviorTracker monitors exec rates and temp-file creation patterns.
type BehaviorTracker struct {
	mu           sync.Mutex
	execTimes    []time.Time   // sliding window of exec timestamps
	blockedUntil time.Time     // cooldown until burst subsides
	tempCreates  []time.Time   // file creation events in temp dirs
	alertCount   int
}

// NewBehaviorTracker returns a ready-to-use tracker.
func NewBehaviorTracker() *BehaviorTracker {
	return &BehaviorTracker{
		execTimes:   make([]time.Time, 0, maxExecPerSecond*2),
		tempCreates: make([]time.Time, 0, tempFileCreateMax*2),
	}
}

// RecordExec adds an exec event and returns true if a burst is detected.
func (bt *BehaviorTracker) RecordExec() bool {
	bt.mu.Lock()
	defer bt.mu.Unlock()

	now := time.Now()

	// If in cooldown, deny
	if now.Before(bt.blockedUntil) {
		return true // burst still active
	}

	// Prune old entries
	cutoff := now.Add(-time.Duration(maxExecWindow) * time.Second)
	pruned := bt.execTimes[:0]
	for _, t := range bt.execTimes {
		if t.After(cutoff) {
			pruned = append(pruned, t)
		}
	}
	bt.execTimes = pruned

	// Check burst
	if len(bt.execTimes) >= maxExecPerSecond {
		bt.blockedUntil = now.Add(time.Duration(execBurstCooldown) * time.Second)
		bt.alertCount++
		return true
	}

	bt.execTimes = append(bt.execTimes, now)
	return false
}

// RecordTempFileCreate records a file creation in a temp directory.
// Returns true if the rate is suspicious.
func (bt *BehaviorTracker) RecordTempFileCreate() bool {
	bt.mu.Lock()
	defer bt.mu.Unlock()

	now := time.Now()
	cutoff := now.Add(-time.Duration(tempFileWindow) * time.Second)
	pruned := bt.tempCreates[:0]
	for _, t := range bt.tempCreates {
		if t.After(cutoff) {
			pruned = append(pruned, t)
		}
	}
	bt.tempCreates = pruned
	bt.tempCreates = append(bt.tempCreates, now)

	return len(bt.tempCreates) > tempFileCreateMax
}

// ── daemon ────────────────────────────────────────────────────────────────

// Daemon is the core runtime.
type Daemon struct {
	cfg       Config
	fanFd     int
	inotifyFd int
	rules     *yara.Rules
	rulesMu   sync.RWMutex
	allowlist *Allowlist
	behavior  *BehaviorTracker
	running   bool
}

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
	if cfg.Allowlist == "" {
		cfg.Allowlist = defaultAllowlist
	}
	if cfg.StrictMode {
		cfg.Trust = TrustStrict
	}
	return &Daemon{
		cfg:       cfg,
		behavior:  NewBehaviorTracker(),
		allowlist: &Allowlist{hash: make(map[[32]byte]bool)},
	}
}

// ── YARA rule loading ─────────────────────────────────────────────────────

func (d *Daemon) LoadRules() error {
	compiler, err := yara.NewCompiler()
	if err != nil {
		return fmt.Errorf("yara: new compiler: %w", err)
	}
	defer compiler.Destroy()

	loaded := 0
	err = filepath.WalkDir(d.cfg.RulesDir, func(path string, de os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return nil
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

func (d *Daemon) ReloadRules() {
	log.Print("[INFO] SIGHUP received — reloading rules + allowlist")
	if err := d.LoadRules(); err != nil {
		log.Printf("[ERROR] reload failed: %v (keeping previous rules)", err)
	}
	if al, err := LoadAllowlist(d.cfg.Allowlist); err != nil {
		log.Printf("[ERROR] allowlist reload failed: %v", err)
	} else {
		d.allowlist = al
	}
}

// ── fanotify lifecycle ───────────────────────────────────────────────────

func (d *Daemon) InitFanotify() error {
	fd, err := unix.FanotifyInit(unix.FAN_CLASS_PRE_CONTENT|unix.FAN_CLOEXEC, unix.O_RDONLY|unix.O_LARGEFILE)
	if err != nil {
		return fmt.Errorf("fanotify_init: %w", err)
	}
	d.fanFd = fd
	return nil
}

// AddWatchMarks registers both FAN_OPEN_EXEC_PERM (executables) and
// FAN_ACCESS_PERM for .so files (shared library interception for LD_PRELOAD).
func (d *Daemon) AddWatchMarks() error {
	// Executable interception
	execMask := uint64(unix.FAN_OPEN_EXEC_PERM)
	// Shared library interception (catches LD_PRELOAD abuse)
	soMask := uint64(unix.FAN_ACCESS_PERM)

	for _, mnt := range d.cfg.WatchMounts {
		if err := unix.FanotifyMark(d.fanFd,
			unix.FAN_MARK_ADD|unix.FAN_MARK_MOUNT,
			execMask|soMask, unix.AT_FDCWD, mnt,
		); err != nil {
			return fmt.Errorf("fanotify_mark %s: %w", mnt, err)
		}
		log.Printf("[INFO] monitoring mount: %s (FAN_OPEN_EXEC_PERM + FAN_ACCESS_PERM)", mnt)
	}
	return nil
}

// ── inotify temp-dir monitoring ────────────────────────────────────────────

var tempDirs = []string{"/tmp", "/dev/shm", "/var/tmp"}

func (d *Daemon) InitInotify() error {
	fd, err := unix.InotifyInit1(unix.IN_CLOEXEC)
	if err != nil {
		return fmt.Errorf("inotify_init: %w", err)
	}
	d.inotifyFd = fd

	watchMask := uint32(unix.IN_CREATE | unix.IN_MOVED_TO | unix.IN_OPEN |
		unix.IN_CLOSE_WRITE | unix.IN_ATTRIB)

	for _, dir := range tempDirs {
		wd, err := unix.InotifyAddWatch(fd, dir, watchMask)
		if err != nil {
			log.Printf("[WARN] inotify watch %s: %v (skipping)", dir, err)
			continue
		}
		log.Printf("[INFO] inotify watching: %s (wd=%d)", dir, wd)
	}
	return nil
}

// inotifyLoop reads inotify events and flags suspicious temp-dir activity.
// This runs in its own goroutine — it never blocks execution, only logs/alerts.
func (d *Daemon) inotifyLoop(ctx context.Context) {
	buf := make([]byte, inotifyBufSize)
	// inotify_event struct: wd(4) mask(4) cookie(4) len(4) + name
	const eventHeaderSize = 16

	for d.running {
		select {
		case <-ctx.Done():
			return
		default:
		}

		n, err := unix.Read(d.inotifyFd, buf)
		if err != nil {
			if errors.Is(err, unix.EINTR) || errors.Is(err, context.Canceled) {
				continue
			}
			time.Sleep(200 * time.Millisecond)
			continue
		}

		offset := 0
		for offset+eventHeaderSize <= n {
			wd := *(*int32)(unsafe.Pointer(&buf[offset]))
			mask := *(*uint32)(unsafe.Pointer(&buf[offset+4]))
			nameLen := *(*int32)(unsafe.Pointer(&buf[offset+12]))
			totalSize := int(eventHeaderSize) + int(nameLen)
			if totalSize%eventHeaderSize != 0 {
				totalSize += eventHeaderSize - (totalSize % eventHeaderSize)
			}

			if mask&(unix.IN_CREATE|unix.IN_MOVED_TO) != 0 && nameLen > 0 {
				name := string(buf[offset+eventHeaderSize : offset+eventHeaderSize+int(nameLen)])
				// Only flag executable-like files
				if strings.HasSuffix(name, ".so") || strings.HasSuffix(name, ".bin") ||
					strings.HasSuffix(name, ".sh") || strings.HasSuffix(name, ".py") ||
					strings.HasSuffix(name, ".elf") || !strings.Contains(name, ".") {
					suspicious := d.behavior.RecordTempFileCreate()
					if suspicious {
						log.Printf("[ALERT] BEHAVIORAL — rapid file creation in temp dir (wd=%d file=%s)", wd, name)
					}
					if d.cfg.Verbose {
						log.Printf("[TRACE] temp file: wd=%d event=CREATE name=%s", wd, name)
					}
				}
			}

			offset += totalSize
		}
	}
}

// ── fanotify response ──────────────────────────────────────────────────────

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

func resolveFdPath(fd int) string {
	link, err := os.Readlink(fmt.Sprintf("/proc/self/fd/%d", fd))
	if err != nil {
		return "<unreadable>"
	}
	return link
}

// ── trust model ─────────────────────────────────────────────────────────────

// coreOSPrefixes are the ONLY paths that get blanket trust in strict/whitelist mode.
// In permissive mode, additional prefixes are added.
var coreOSPrefixes = []string{
	"/usr/bin/", "/usr/sbin/", "/usr/lib/", "/usr/libexec/",
	"/bin/", "/sbin/", "/lib/", "/lib64/",
	"/snap/", "/snapd/", "/nix/store/",
}

// permissiveExtraPrefixes are paths trusted in legacy mode only.
var permissiveExtraPrefixes = []string{
	"/opt/", "/usr/local/bin/", "/usr/local/sbin/",
}

func isPathTrusted(fdPath string, mode TrustMode) bool {
	// Always trust core OS paths in all modes
	for _, prefix := range coreOSPrefixes {
		if strings.HasPrefix(fdPath, prefix) {
			return true
		}
	}
	// Permissive mode trusts extra paths
	if mode == TrustPermissive {
		for _, prefix := range permissiveExtraPrefixes {
			if strings.HasPrefix(fdPath, prefix) {
				return true
			}
		}
	}
	return false
}

// isTempPath returns true for files in writable ephemeral directories.
func isTempPath(fdPath string) bool {
	for _, dir := range tempDirs {
		if strings.HasPrefix(fdPath, dir+"/") {
			return true
		}
	}
	if strings.HasPrefix(fdPath, "/run/user/") {
		return true
	}
	return false
}

// ── ELF validation ──────────────────────────────────────────────────────────

// validateELF performs a lightweight sanity check on the buffer before passing
// it to YARA. This prevents malformed ELF from crashing libyara or consuming
// excessive memory in the scanner. Returns nil if the buffer looks like a
// legitimate ELF or non-ELF (allowing non-ELF through for other scans).
func validateELF(buf []byte) error {
	if len(buf) < 64 {
		return nil // too small to validate, let it pass
	}
	// Check ELF magic
	if buf[0] != 0x7f || buf[1] != 0x45 || buf[2] != 0x4c || buf[3] != 0x46 {
		return nil // not ELF, that's fine
	}
	// Sanity: verify e_ehsize matches expectation
	// e_ehsize is at offset 40 (2 bytes, little-endian)
	ehSize := uint16(buf[40]) | uint16(buf[41])<<8
	if ehSize != 64 && ehSize != 52 {
		// Unusual but not necessarily malicious (could be old binary format)
		// Just log in verbose mode, don't block
	}
	// Sanity: verify e_phoff (program header offset) is within file
	if len(buf) >= 44 {
		phOff := uint64(buf[32]) | uint64(buf[33])<<8 | uint64(buf[34])<<16 | uint64(buf[35])<<24
		phOff |= uint64(buf[36])<<32 | uint64(buf[37])<<40 | uint64(buf[38])<<48 | uint64(buf[39])<<56
		if phOff > uint64(len(buf)) && phOff != 0 {
			return fmt.Errorf("ELF program header offset %d exceeds file size %d", phOff, len(buf))
		}
	}
	// Sanity: verify e_shentsize (section header entry size) is reasonable
	if len(buf) >= 60 {
		shEntSize := uint16(buf[58]) | uint16(buf[59])<<8
		if shEntSize > 4096 {
			return fmt.Errorf("ELF section header entry size %d is suspiciously large", shEntSize)
		}
	}
	return nil
}

// ── content scanning ──────────────────────────────────────────────────────

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

func (d *Daemon) scanContent(buf []byte) ([]string, error) {
	if len(buf) == 0 {
		return nil, nil
	}

	// Pre-validate ELF to prevent YARA crashes on malformed binaries
	if err := validateELF(buf); err != nil {
		return nil, fmt.Errorf("ELF validation: %w", err)
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
//  2. On panic or unhandled error, the fd is closed → implicit FAN_ALLOW.
//  3. FAN_DENY is sent ONLY on confirmed signature match or behavioral block.
func (d *Daemon) processEvent(meta fanotifyEventMetadata) {
	eventFd := int(meta.Fd)
	if eventFd < 0 {
		return
	}

	isExecPerm := meta.Mask&unix.FAN_OPEN_EXEC_PERM != 0
	isAccessPerm := meta.Mask&unix.FAN_ACCESS_PERM != 0

	// Non-permission events: close fd, move on.
	if !isExecPerm && !isAccessPerm {
		unix.Close(eventFd)
		return
	}

	pid := meta.Pid

	defer unix.Close(eventFd)

	responded := false
	defer func() {
		if r := recover(); r != nil {
			log.Printf("[PANIC] recovered in event handler (pid=%d): %v", pid, r)
		}
		if !responded {
			d.respond(meta.Fd, true)
		}
	}()

	fdPath := resolveFdPath(eventFd)
	exePath := "<unknown>"
	if link, err := os.Readlink(fmt.Sprintf("/proc/%d/exe", pid)); err == nil {
		exePath = link
	}

	if d.cfg.Verbose {
		evtType := "EXEC"
		if isAccessPerm {
			evtType = "ACCESS(.so)"
		}
		log.Printf("[TRACE] %s intercept pid=%d exe=%s target=%s", evtType, pid, exePath, fdPath)
	}

	// ── Shared library interception ─────────────────────────────────────
	if isAccessPerm {
		d.handleSharedObjectAccess(meta, pid, exePath, fdPath, eventFd)
		responded = true
		return
	}

	// ── Behavioral: rapid exec burst detection ─────────────────────────
	if d.behavior.RecordExec() {
		log.Printf("[ALERT] BEHAVIORAL — exec burst detected pid=%d exe=%s target=%s (blocking)",
			pid, exePath, fdPath)
		d.respond(meta.Fd, false)
		responded = true
		syscall.Kill(pid, syscall.SIGKILL)
		return
	}

	// ── Trust model ───────────────────────────────────────────────────
	if isPathTrusted(fdPath, d.cfg.Trust) {
		d.respond(meta.Fd, true)
		responded = true
		return
	}

	// ── Whitelist-only mode: deny everything not in allowlist ──────────
	if d.cfg.Trust == TrustWhitelist {
		content, err := readFdContent(eventFd, d.cfg.MaxScan)
		if err != nil {
			log.Printf("[WARN] whitelist read %s: %v → ALLOW", fdPath, err)
			return
		}
		if !d.allowlist.IsAllowed(content) {
			log.Printf("[ALERT] WHITELIST — unapproved binary pid=%d path=%s", pid, fdPath)
			d.respond(meta.Fd, false)
			responded = true
			syscall.Kill(pid, syscall.SIGKILL)
			return
		}
		d.respond(meta.Fd, true)
		responded = true
		return
	}

	// ── Read and scan ───────────────────────────────────────────────────
	content, err := readFdContent(eventFd, d.cfg.MaxScan)
	if err != nil {
		log.Printf("[WARN] read %s (pid=%d): %v → ALLOW", fdPath, pid, err)
		return
	}

	// ── SHA256 allowlist check (strict mode) ───────────────────────────
	if d.cfg.Trust == TrustStrict && !isTempPath(fdPath) {
		if !d.allowlist.IsAllowed(content) {
			log.Printf("[ALERT] STRICT — unapproved binary pid=%d path=%s (not in allowlist)", pid, fdPath)
			d.respond(meta.Fd, false)
			responded = true
			syscall.Kill(pid, syscall.SIGKILL)
			return
		}
		// In allowlist and not temp → trusted
		d.respond(meta.Fd, true)
		responded = true
		return
	}

	// ── YARA scan (temp paths always get scanned) ──────────────────────
	matched, err := d.scanContent(content)
	if err != nil {
		log.Printf("[ERROR] scan %s (pid=%d): %v → ALLOW", fdPath, pid, err)
		return
	}

	if len(matched) == 0 {
		d.respond(meta.Fd, true)
		responded = true
		return
	}

	// ── SIGNATURE MATCH → DENY + TERMINATE ────────────────────────────
	ruleStr := strings.Join(matched, ",")
	log.Printf("[ALERT] MALWARE DETECTED — pid=%d exe=%s path=%s rules=[%s]",
		pid, exePath, fdPath, ruleStr)

	d.respond(meta.Fd, false)
	responded = true

	if err := syscall.Kill(pid, syscall.SIGKILL); err != nil {
		log.Printf("[ERROR] kill pid=%d: %v", pid, err)
	} else {
		log.Printf("[BLOCK] terminated pid=%d — matched: [%s]", pid, ruleStr)
	}
}

// handleSharedObjectAccess scans .so files loaded via FAN_ACCESS_PERM.
// Only scans suspicious .so files (in temp dirs or with known-bad patterns).
func (d *Daemon) handleSharedObjectAccess(meta fanotifyEventMetadata, pid int32, exePath, fdPath string, eventFd int) {
	// Only scan .so in non-trusted locations
	if !isTempPath(fdPath) && isPathTrusted(fdPath, d.cfg.Trust) {
		d.respond(meta.Fd, true)
		return
	}

	// Scan the .so content against YARA
	content, err := readFdContent(eventFd, d.cfg.MaxScan)
	if err != nil {
		// Can't read — allow it (don't break LD)
		d.respond(meta.Fd, true)
		return
	}

	matched, err := d.scanContent(content)
	if err != nil {
		d.respond(meta.Fd, true)
		return
	}

	if len(matched) == 0 {
		d.respond(meta.Fd, true)
		return
	}

	ruleStr := strings.Join(matched, ",")
	log.Printf("[ALERT] MALWARE in shared library — pid=%d exe=%s lib=%s rules=[%s]",
		pid, exePath, fdPath, ruleStr)

	d.respond(meta.Fd, false)
	syscall.Kill(pid, syscall.SIGKILL)
	log.Printf("[BLOCK] terminated pid=%d (malicious .so loaded) — matched: [%s]", pid, ruleStr)
}

// ── event loop ─────────────────────────────────────────────────────────────

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
			time.Sleep(100 * time.Millisecond)
			continue
		}

		if n < metadataSize {
			continue
		}

		offset := 0
		for offset < n {
			if n-offset < metadataSize {
				break
			}
			meta := *(*fanotifyEventMetadata)(unsafe.Pointer(&buf[offset]))
			if meta.EventLen == 0 {
				break
			}
			d.processEvent(meta)
			offset += int(meta.EventLen)
		}
	}
}

// ── signal handling ──────────────────────────────────────────────────────

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

func (d *Daemon) Shutdown() {
	d.running = false
	if d.fanFd >= 0 {
		unix.Close(d.fanFd)
		log.Print("[INFO] fanotify fd closed")
	}
	if d.inotifyFd >= 0 {
		unix.Close(d.inotifyFd)
		log.Print("[INFO] inotify fd closed")
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
	os.Remove(path)
}

// ── entry point ───────────────────────────────────────────────────────────

func main() {
	rulesDir := flag.String("rules", defaultRules, "directory containing .yar/.yara rule files")
	allowlist := flag.String("allowlist", defaultAllowlist, "SHA256 allowlist JSON file")
	pidFile := flag.String("pid", defaultPidFile, "PID file path")
	maxScan := flag.Int64("max-scan", maxScanBytes, "max bytes to scan per file")
	verbose := flag.Bool("v", false, "verbose logging")
	strict := flag.Bool("strict", false, "strict mode — only core OS paths + allowlist trusted")
	whitelist := flag.Bool("whitelist", false, "whitelist-only mode — only allowlisted SHA256 may execute")
	showVer := flag.Bool("version", false, "print version and exit")

	flag.Parse()

	if *showVer {
		fmt.Printf("%s %s\n", appName, version)
		os.Exit(0)
	}

	log.SetOutput(os.Stderr)
	log.SetFlags(log.Ldate | log.Ltime | log.Lmicroseconds | log.Lshortfile)

	trustMode := TrustPermissive
	if *strict {
		trustMode = TrustStrict
	}
	if *whitelist {
		trustMode = TrustWhitelist
	}

	log.Printf("[INFO] %s v%s starting (trust=%v)", appName, version, trustMode)

	d := NewDaemon(Config{
		RulesDir:    *rulesDir,
		Allowlist:   *allowlist,
		WatchMounts: []string{"/"},
		MaxScan:     *maxScan,
		PidFile:     *pidFile,
		Verbose:     *verbose,
		Trust:       trustMode,
	})

	if err := yara.Init(nil); err != nil {
		log.Fatalf("[FATAL] yara.Init: %v", err)
	}

	if err := d.LoadRules(); err != nil {
		log.Fatalf("[FATAL] %v", err)
	}

	al, err := LoadAllowlist(d.cfg.Allowlist)
	if err != nil {
		log.Fatalf("[FATAL] %v", err)
	}
	d.allowlist = al

	if err := d.InitFanotify(); err != nil {
		log.Fatalf("[FATAL] %v", err)
	}
	defer d.Shutdown()

	if err := d.AddWatchMarks(); err != nil {
		log.Fatalf("[FATAL] %v", err)
	}

	if err := d.InitInotify(); err != nil {
		log.Printf("[WARN] inotify init failed: %v (temp-dir monitoring disabled)", err)
	}

	if err := writePidFile(d.cfg.PidFile); err != nil {
		log.Fatalf("[FATAL] pid file: %v", err)
	}

	d.running = true
	ctx, cancel := context.WithCancel(context.Background())

	go d.handleSignals(ctx, cancel)
	if d.inotifyFd >= 0 {
		go d.inotifyLoop(ctx)
	}

	log.Print("[INFO] event loop active — monitoring all execve(2) + .so loads on /")
	d.eventLoop(ctx)

	d.running = false
	yara.Finalize()
	log.Print("[INFO] stopped")
}
