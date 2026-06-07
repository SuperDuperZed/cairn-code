// linux-protect — local-first anti-malware daemon for Ubuntu
// Supply-chain hardened: fanotify pre-exec interception + libyara scanning
// Zero cloud dependencies. Zero external telemetry. Pure UNIX composition.
//
// v4.0 — closes all red-team gaps: script argument scanning, memfd_create
// detection, config integrity hashing, inotify proactive scanning, temp-path
// allowlist enforcement, interpreter-aware exec interception, proc scanner.
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
	"io/fs"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"

	"github.com/BurntSushi/toml"
	"github.com/hillu/go-yara/v4"
	"golang.org/x/sys/unix"
)

// ── constants ──────────────────────────────────────────────────────────────

const (
	appName          = "linux-protect"
	version          = "4.0.0"
	maxScanBytes     = 64 << 20 // 64 MiB
	eventBufSize     = 8192
	metadataSize     = 32
	defaultPidFile   = "/run/linux-protect/linux-protect.pid"
	defaultRules     = "/etc/linux-protect/rules"
	defaultConfig    = "/etc/linux-protect/linux-protect.toml"
	defaultAllowlist = "/etc/linux-protect/allowlist.json"

	// behavioral thresholds
	maxExecPerSecond   = 8
	maxExecWindow      = 1
	execBurstCooldown  = 5
	tempFileCreateMax  = 20
	tempFileWindow     = 10
	maxChainDepth      = 4

	// memfd scanner
	memfdScanInterval = 3 * time.Second

	// inotify
	inotifyBufSize = 8192
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

// ── trust modes ────────────────────────────────────────────────────────────

type TrustMode int

const (
	TrustEnforce  TrustMode = iota
	TrustStrict
	TrustParanoid
	TrustAudit
)

func (m TrustMode) String() string {
	switch m {
	case TrustEnforce:
		return "enforce"
	case TrustStrict:
		return "strict"
	case TrustParanoid:
		return "paranoid"
	case TrustAudit:
		return "audit"
	default:
		return "unknown"
	}
}

// ── known interpreters (for script argument scanning) ────────────────────────

// interpreters is a set of binary basenames that execute scripts from arguments.
// When an exec of one of these is allowed (trusted path), we parse /proc/pid/cmdline
// to find the script file argument and scan it against YARA.
var interpreters = map[string]bool{
	"python": true, "python3": true, "python3.8": true, "python3.9": true,
	"python3.10": true, "python3.11": true, "python3.12": true,
	"perl": true, "ruby": true, "node": true, "nodejs": true,
	"php": true, "php8.2": true, "php8.3": true, "php8.4": true,
	"bash": true, "sh": true, "dash": true, "zsh": true,
	"awk": true, "gawk": true, "lua": true, "lua5.3": true, "lua5.4": true,
	"tclsh": true, "wish": true,
}

// ── TOML configuration ────────────────────────────────────────────────────

type ConfigFile struct {
	Trust        string   `toml:"trust_mode"`
	TrustedPaths []string `toml:"trusted_paths"`
	WatchDirs    []string `toml:"watch_dirs"`
	RulesDir     string   `toml:"rules_dir"`
	Allowlist    string   `toml:"allowlist"`
	PidFile      string   `toml:"pid_file"`
	MaxScanMB    int64    `toml:"max_scan_mb"`
	Verbose      bool     `toml:"verbose"`
	ExecRate     int      `toml:"exec_rate_limit"`
	TempFileRate int      `toml:"temp_file_rate"`
	WatchMounts  []string `toml:"watch_mounts"`
	// v4 additions
	ScanScripts     bool `toml:"scan_scripts"`      // scan interpreter arguments (default true)
	MemfdDetect     bool `toml:"memfd_detect"`      // scan /proc for memfd_create (default true)
	ProactiveInotify bool `toml:"proactive_inotify"`  // scan files created in temp dirs (default true)
}

func (cf *ConfigFile) MergeInto(cfg *Config) {
	if cf.Trust != "" {
		switch strings.ToLower(cf.Trust) {
		case "enforce":
			cfg.Trust = TrustEnforce
		case "strict":
			cfg.Trust = TrustStrict
		case "paranoid":
			cfg.Trust = TrustParanoid
		case "audit":
			cfg.Trust = TrustAudit
		}
	}
	if len(cf.TrustedPaths) > 0 {
		cfg.CustomTrustedPaths = cf.TrustedPaths
	}
	if len(cf.WatchDirs) > 0 {
		cfg.WatchDirs = cf.WatchDirs
	}
	if cf.RulesDir != "" {
		cfg.RulesDir = cf.RulesDir
	}
	if cf.Allowlist != "" {
		cfg.Allowlist = cf.Allowlist
	}
	if cf.PidFile != "" {
		cfg.PidFile = cf.PidFile
	}
	if cf.MaxScanMB > 0 {
		cfg.MaxScan = cf.MaxScanMB << 20
	}
	if cf.Verbose {
		cfg.Verbose = true
	}
	if cf.ExecRate > 0 {
		cfg.ExecRateLimit = cf.ExecRate
	}
	if cf.TempFileRate > 0 {
		cfg.TempFileRate = cf.TempFileRate
	}
	if len(cf.WatchMounts) > 0 {
		cfg.WatchMounts = cf.WatchMounts
	}
	if cf.ScanScripts {
		cfg.ScanScripts = true
	}
	if cf.MemfdDetect {
		cfg.MemfdDetect = true
	}
	if cf.ProactiveInotify {
		cfg.ProactiveInotify = true
	}
}

// ── runtime configuration ─────────────────────────────────────────────────

type Config struct {
	RulesDir           string
	Allowlist          string
	WatchMounts        []string
	MaxScan            int64
	PidFile            string
	Verbose            bool
	Trust              TrustMode
	CustomTrustedPaths []string
	WatchDirs          []string
	ExecRateLimit      int
	TempFileRate       int
	// v4
	ScanScripts      bool // scan interpreter script arguments
	MemfdDetect      bool // scan /proc for memfd_create
	ProactiveInotify bool // proactively scan temp-created files
}

// ── config integrity ────────────────────────────────────────────────────────

// ConfigIntegrity stores the hash and mtime of the config file to detect tampering.
type ConfigIntegrity struct {
	mu       sync.RWMutex
	fileHash string
	modTime  time.Time
}

func (ci *ConfigIntegrity) Record(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	info, err := os.Stat(path)
	if err != nil {
		return err
	}
	h := sha256.Sum256(data)
	ci.mu.Lock()
	defer ci.mu.Unlock()
	ci.fileHash = hex.EncodeToString(h[:])
	ci.modTime = info.ModTime()
	return nil
}

// Check verifies the config file hasn't been tampered with.
// Returns true if the file appears unchanged.
func (ci *ConfigIntegrity) Check(path string) bool {
	data, err := os.ReadFile(path)
	if err != nil {
		return false
	}
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	h := sha256.Sum256(data)
	ci.mu.RLock()
	defer ci.mu.RUnlock()
	return hex.EncodeToString(h[:]) == ci.fileHash
}

// verifyConfigPermissions ensures the config file has restrictive permissions.
func verifyConfigPermissions(path string) error {
	info, err := os.Stat(path)
	if err != nil {
		return err
	}
	perm := info.Mode().Perm()
	// Config should not be world-readable or writable by group
	if perm&0077 != 0 {
		return fmt.Errorf("config file %s has overly permissive permissions (%o), should be 0600 or more restrictive", path, perm)
	}
	return nil
}

// ── allowlist ──────────────────────────────────────────────────────────────

type Allowlist struct {
	mu    sync.RWMutex
	hash  map[[32]byte]bool
}

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

func (al *Allowlist) IsAllowed(content []byte) bool {
	h := sha256.Sum256(content)
	al.mu.RLock()
	defer al.mu.RUnlock()
	return al.hash[h]
}

// ── parent-child chain tracker ──────────────────────────────────────────────

type ChainTracker struct {
	mu    sync.Mutex
	chain map[int32]int32
	depth map[int32]int
}

func NewChainTracker() *ChainTracker {
	return &ChainTracker{
		chain: make(map[int32]int32),
		depth: make(map[int32]int),
	}
}

func (ct *ChainTracker) RecordExec(pid int32) bool {
	ct.mu.Lock()
	defer ct.mu.Unlock()

	ppid := int32(1)
	if raw, err := os.ReadFile(fmt.Sprintf("/proc/%d/stat", pid)); err == nil {
		closeParen := -1
		for i, c := range raw {
			if c == ')' {
				closeParen = i
				break
			}
		}
		if closeParen >= 0 {
			fields := strings.Fields(string(raw[closeParen+2:]))
			if len(fields) >= 1 {
				if v, err := strconv.Atoi(fields[0]); err == nil {
					ppid = int32(v)
				}
			}
		}
	}

	ct.chain[pid] = ppid
	d := 1
	if parentDepth, ok := ct.depth[ppid]; ok {
		d = parentDepth + 1
	}
	ct.depth[pid] = d

	if len(ct.chain) > 10000 {
		ct.chain = make(map[int32]int32, 5000)
		ct.depth = make(map[int32]int, 5000)
	}

	return d > maxChainDepth
}

// ── behavioral tracker ─────────────────────────────────────────────────────

type BehaviorTracker struct {
	mu           sync.Mutex
	execTimes    []time.Time
	blockedUntil time.Time
	tempCreates  []time.Time
	alertCount   int
	execRate     int
	tempRate     int
}

func NewBehaviorTracker(execRate, tempRate int) *BehaviorTracker {
	if execRate <= 0 {
		execRate = maxExecPerSecond
	}
	if tempRate <= 0 {
		tempRate = tempFileCreateMax
	}
	return &BehaviorTracker{
		execTimes:   make([]time.Time, 0, execRate*2),
		tempCreates: make([]time.Time, 0, tempRate*2),
		execRate:    execRate,
		tempRate:    tempRate,
	}
}

func (bt *BehaviorTracker) RecordExec() bool {
	bt.mu.Lock()
	defer bt.mu.Unlock()

	now := time.Now()
	if now.Before(bt.blockedUntil) {
		return true
	}

	cutoff := now.Add(-time.Duration(maxExecWindow) * time.Second)
	pruned := bt.execTimes[:0]
	for _, t := range bt.execTimes {
		if t.After(cutoff) {
			pruned = append(pruned, t)
		}
	}
	bt.execTimes = pruned

	if len(bt.execTimes) >= bt.execRate {
		bt.blockedUntil = now.Add(time.Duration(execBurstCooldown) * time.Second)
		bt.alertCount++
		return true
	}

	bt.execTimes = append(bt.execTimes, now)
	return false
}

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

	return len(bt.tempCreates) > bt.tempRate
}

// ── daemon ────────────────────────────────────────────────────────────────

type Daemon struct {
	cfg          Config
	fanFd        int
	inotifyFd    int
	rules        *yara.Rules
	rulesMu      sync.RWMutex
	allowlist    *Allowlist
	behavior     *BehaviorTracker
	chains       *ChainTracker
	configHash   *ConfigIntegrity
	configPath   string
	running      bool
}

func NewDaemon(cfg Config, configPath string) *Daemon {
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
	if len(cfg.WatchDirs) == 0 {
		cfg.WatchDirs = defaultTempDirs()
	}
	return &Daemon{
		cfg:        cfg,
		configPath: configPath,
		behavior:   NewBehaviorTracker(cfg.ExecRateLimit, cfg.TempFileRate),
		chains:     NewChainTracker(),
		allowlist:  &Allowlist{hash: make(map[[32]byte]bool)},
		configHash: &ConfigIntegrity{},
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
	log.Print("[INFO] SIGHUP received — reloading rules + allowlist + config")

	// Check config integrity before reload
	if d.configPath != "" {
		if d.configHash.Check(d.configPath) {
			log.Print("[INFO] config file unchanged, skipping reload")
		} else {
			log.Print("[WARN] config file has been modified — reloading with new values")
			// Verify permissions
			if err := verifyConfigPermissions(d.configPath); err != nil {
				log.Printf("[ALERT] CONFIG INTEGRITY — %s", err)
			}
			var cf ConfigFile
			if _, err := toml.DecodeFile(d.configPath, &cf); err != nil {
				log.Printf("[ERROR] config reload parse error: %v", err)
			} else {
				cf.MergeInto(&d.cfg)
				d.behavior = NewBehaviorTracker(d.cfg.ExecRateLimit, d.cfg.TempFileRate)
			}
			d.configHash.Record(d.configPath)
		}
	}

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

func (d *Daemon) AddWatchMarks() error {
	execMask := uint64(unix.FAN_OPEN_EXEC_PERM)
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

func defaultTempDirs() []string {
	return []string{"/tmp", "/dev/shm", "/var/tmp"}
}

func (d *Daemon) InitInotify() error {
	fd, err := unix.InotifyInit1(unix.IN_CLOEXEC)
	if err != nil {
		return fmt.Errorf("inotify_init: %w", err)
	}
	d.inotifyFd = fd

	watchMask := uint32(unix.IN_CREATE | unix.IN_MOVED_TO | unix.IN_OPEN |
		unix.IN_CLOSE_WRITE | unix.IN_ATTRIB)

	for _, dir := range d.cfg.WatchDirs {
		wd, err := unix.InotifyAddWatch(fd, dir, watchMask)
		if err != nil {
			log.Printf("[WARN] inotify watch %s: %v (skipping)", dir, err)
			continue
		}
		log.Printf("[INFO] inotify watching: %s (wd=%d)", dir, wd)
	}
	return nil
}

// inotifyLoop reads inotify events. In proactive mode, newly created files
// are scanned against YARA immediately (not just rate-tracked).
func (d *Daemon) inotifyLoop(ctx context.Context) {
	buf := make([]byte, inotifyBufSize)
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
			_ = *(*int32)(unsafe.Pointer(&buf[offset])) // wd
			mask := *(*uint32)(unsafe.Pointer(&buf[offset+4]))
			nameLen := *(*int32)(unsafe.Pointer(&buf[offset+12]))
			totalSize := int(eventHeaderSize) + int(nameLen)
			if totalSize%eventHeaderSize != 0 {
				totalSize += eventHeaderSize - (totalSize%eventHeaderSize)
			}

			if mask&(unix.IN_CREATE|unix.IN_MOVED_TO) != 0 && nameLen > 0 {
				name := string(buf[offset+eventHeaderSize : offset+eventHeaderSize+int(nameLen)])
				suspiciousExt := strings.HasSuffix(name, ".so") || strings.HasSuffix(name, ".bin") ||
					strings.HasSuffix(name, ".sh") || strings.HasSuffix(name, ".py") ||
					strings.HasSuffix(name, ".elf") || !strings.Contains(name, ".")
				suspicious := d.behavior.RecordTempFileCreate()

				if suspicious {
					log.Printf("[ALERT] BEHAVIORAL — rapid file creation in temp dir (file=%s)", name)
				}
				if d.cfg.Verbose {
					log.Printf("[TRACE] temp file: event=CREATE name=%s", name)
				}

				// v4: proactive scanning — scan created files immediately
				if d.cfg.ProactiveInotify && suspiciousExt {
					for _, dir := range d.cfg.WatchDirs {
						fullPath := dir + "/" + name
						if _, statErr := os.Stat(fullPath); statErr == nil {
							d.proactiveScanFile(fullPath, name)
						}
					}
				}
			}

			offset += totalSize
		}
	}
}

// proactiveScanFile reads and scans a file created in a temp directory.
func (d *Daemon) proactiveScanFile(fullPath, name string) {
	f, err := os.Open(fullPath)
	if err != nil {
		return
	}
	defer f.Close()

	info, err := f.Stat()
	if err != nil || info.Size() <= 0 || info.Size() > d.cfg.MaxScan {
		return
	}

	buf := make([]byte, info.Size())
	n, err := f.Read(buf)
	if err != nil || n == 0 {
		return
	}

	// Validate ELF
	if err := validateELF(buf[:n]); err != nil {
		log.Printf("[ALERT] PROACTIVE — suspicious ELF in temp: %s (%v)", fullPath, err)
		return
	}

	matched, err := d.scanContent(buf[:n])
	if err != nil {
		return
	}

	if len(matched) > 0 {
		log.Printf("[ALERT] PROACTIVE — malware detected in temp file: %s rules=[%s]",
			fullPath, strings.Join(matched, ","))
		// Try to remove the malicious file
		os.Remove(fullPath)
	}
}

// ── memfd_create detection ─────────────────────────────────────────────────

// memfdScanner periodically scans /proc/*/exe for anonymous memory-backed
// executions (memfd_create). These bypass fanotify entirely since there's
// no filesystem path. In paranoid mode, processes using memfd are terminated.
func (d *Daemon) memfdScanner(ctx context.Context) {
	ticker := time.NewTicker(memfdScanInterval)
	defer ticker.Stop()

	for d.running {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			d.scanForMemfd()
		}
	}
}

func (d *Daemon) scanForMemfd() {
	entries, err := os.ReadDir("/proc")
	if err != nil {
		return
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		pid, err := strconv.Atoi(entry.Name())
		if err != nil {
			continue
		}

		// Read /proc/<pid>/exe symlink
		exePath, err := os.Readlink(fmt.Sprintf("/proc/%d/exe", pid))
		if err != nil {
			continue
		}

		// memfd_create files appear as /memfd:<name> (deleted)
		if strings.HasPrefix(exePath, "/memfd:") || strings.HasPrefix(exePath, "/memfd:") {
			// Skip our own process
			if pid == os.Getpid() {
				continue
			}

			// Get comm for logging
			comm := "<unknown>"
			if raw, err := os.ReadFile(fmt.Sprintf("/proc/%d/comm", pid)); err == nil {
				comm = strings.TrimSpace(string(raw))
			}

			if d.cfg.Trust >= TrustParanoid {
				log.Printf("[ALERT] MEMFD — anonymous memory execution detected pid=%d comm=%s exe=%s (terminating)",
					pid, comm, exePath)
				syscall.Kill(pid, syscall.SIGKILL)
			} else {
				log.Printf("[WARN] MEMFD — anonymous memory execution detected pid=%d comm=%s exe=%s",
					pid, comm, exePath)
			}
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

var coreOSPrefixes = []string{
	"/usr/bin/", "/usr/sbin/", "/usr/lib/", "/usr/libexec/",
	"/bin/", "/sbin/", "/lib/", "/lib64/",
	"/snap/", "/snapd/", "/nix/store/",
}

func isPathTrusted(fdPath string, mode TrustMode, customPaths []string) bool {
	for _, prefix := range coreOSPrefixes {
		if strings.HasPrefix(fdPath, prefix) {
			return true
		}
	}
	for _, prefix := range customPaths {
		if strings.HasPrefix(fdPath, prefix) {
			return true
		}
	}
	return false
}

func isTempPath(fdPath string, watchDirs []string) bool {
	for _, dir := range watchDirs {
		if strings.HasPrefix(fdPath, dir+"/") {
			return true
		}
	}
	if strings.HasPrefix(fdPath, "/run/user/") {
		return true
	}
	return false
}

func isInterpreter(fdPath string) bool {
	basename := filepath.Base(fdPath)
	return interpreters[basename]
}

// ── script argument scanning ────────────────────────────────────────────────

// scanScriptArguments reads /proc/<pid>/cmdline to find the script file
// being executed by an interpreter, then scans it against YARA.
// Returns matched rule names if malware found.
func (d *Daemon) scanScriptArguments(pid int32, fdPath string) []string {
	cmdlinePath := fmt.Sprintf("/proc/%d/cmdline", pid)
	data, err := os.ReadFile(cmdlinePath)
	if err != nil {
		return nil
	}

	// /proc/pid/cmdline is null-separated
	args := strings.Split(string(data), "\x00")
	if len(args) < 2 {
		return nil
	}

	// The script is typically the first non-flag argument after the interpreter
	for _, arg := range args[1:] {
		if len(arg) == 0 || strings.HasPrefix(arg, "-") {
			continue
		}
		// Check if it looks like a file path (not a module name or expression)
		if strings.Contains(arg, "/") || strings.Contains(arg, ".") {
			if _, err := os.Stat(arg); err == nil {
				return d.scanFileOnDisk(arg)
			}
		}
	}
	return nil
}

// scanFileOnDisk reads and scans a file at a given path.
func (d *Daemon) scanFileOnDisk(path string) []string {
	f, err := os.Open(path)
	if err != nil {
		return nil
	}
	defer f.Close()

	info, err := f.Stat()
	if err != nil || info.Size() <= 0 || info.Size() > d.cfg.MaxScan {
		return nil
	}

	buf := make([]byte, info.Size())
	n, err := f.Read(buf)
	if err != nil || n == 0 {
		return nil
	}

	matched, err := d.scanContent(buf[:n])
	if err != nil {
		return nil
	}
	return matched
}

// ── ELF validation ──────────────────────────────────────────────────────────

func validateELF(buf []byte) error {
	if len(buf) < 64 {
		return nil
	}
	if buf[0] != 0x7f || buf[1] != 0x45 || buf[2] != 0x4c || buf[3] != 0x46 {
		return nil
	}
	phOff := uint64(buf[32]) | uint64(buf[33])<<8 | uint64(buf[34])<<16 | uint64(buf[35])<<24
	phOff |= uint64(buf[36])<<32 | uint64(buf[37])<<40 | uint64(buf[38])<<48 | uint64(buf[39])<<56
	if phOff > uint64(len(buf)) && phOff != 0 {
		return fmt.Errorf("ELF program header offset %d exceeds file size %d", phOff, len(buf))
	}
	if len(buf) >= 60 {
		shEntSize := uint16(buf[58]) | uint16(buf[59])<<8
		if shEntSize > 4096 {
			return fmt.Errorf("ELF section header entry size %d is suspiciously large", shEntSize)
		}
	}
	if len(buf) >= 46 {
		phNum := uint16(buf[44]) | uint16(buf[45])<<8
		if phNum > 65535/4 {
			return fmt.Errorf("ELF program header count %d is suspiciously large", phNum)
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

	evtType := "EXEC"
	if isAccessPerm {
		evtType = "ACCESS(.so)"
	}
	if d.cfg.Verbose {
		log.Printf("[TRACE] %s intercept pid=%d exe=%s target=%s", evtType, pid, exePath, fdPath)
	}

	// Audit mode: log everything, never deny
	if d.cfg.Trust == TrustAudit {
		content, _ := readFdContent(eventFd, d.cfg.MaxScan)
		if content != nil {
			matched, _ := d.scanContent(content)
			if len(matched) > 0 {
				log.Printf("[AUDIT] would-block %s pid=%d exe=%s path=%s rules=[%s]",
					evtType, pid, exePath, fdPath, strings.Join(matched, ","))
			} else {
				log.Printf("[AUDIT] allow %s pid=%d exe=%s path=%s", evtType, pid, exePath, fdPath)
			}
		}
		d.respond(meta.Fd, true)
		responded = true
		return
	}

	// ── Shared library interception ─────────────────────────────────────
	if isAccessPerm {
		d.handleSharedObjectAccess(meta, pid, exePath, fdPath, eventFd)
		responded = true
		return
	}

	// ── Behavioral: rapid exec burst detection (paranoid mode) ──────────
	if d.cfg.Trust >= TrustParanoid && d.behavior.RecordExec() {
		log.Printf("[ALERT] BEHAVIORAL — exec burst detected pid=%d exe=%s target=%s (blocking)",
			pid, exePath, fdPath)
		d.respond(meta.Fd, false)
		responded = true
		syscall.Kill(pid, syscall.SIGKILL)
		return
	}

	// ── Parent-child chain detection (paranoid mode) ───────────────────
	if d.cfg.Trust >= TrustParanoid && d.chains.RecordExec(pid) {
		log.Printf("[ALERT] BEHAVIORAL — suspicious exec chain depth pid=%d exe=%s target=%s",
			pid, exePath, fdPath)
		d.respond(meta.Fd, false)
		responded = true
		syscall.Kill(pid, syscall.SIGKILL)
		return
	}

	// ── Trust model ───────────────────────────────────────────────────
	pathTrusted := isPathTrusted(fdPath, d.cfg.Trust, d.cfg.CustomTrustedPaths)

	if pathTrusted {
		// v4: scan script arguments for trusted interpreters
		if d.cfg.ScanScripts && isInterpreter(fdPath) {
			matched := d.scanScriptArguments(pid, fdPath)
			if len(matched) > 0 {
				ruleStr := strings.Join(matched, ",")
				log.Printf("[ALERT] MALWARE in script — pid=%d exe=%s target=%s rules=[%s]",
					pid, exePath, fdPath, ruleStr)
				d.respond(meta.Fd, false)
				responded = true
				syscall.Kill(pid, syscall.SIGKILL)
				return
			}
		}
		d.respond(meta.Fd, true)
		responded = true
		return
	}

	// ── Read file content ──────────────────────────────────────────────
	content, err := readFdContent(eventFd, d.cfg.MaxScan)
	if err != nil {
		log.Printf("[WARN] read %s (pid=%d): %v → ALLOW", fdPath, pid, err)
		return
	}

	// ── v4 FIX: Temp-path allowlist enforcement ──────────────────────
	// In strict/paranoid, temp files ALSO require allowlist entry.
	// Previously temp files skipped allowlist and went to YARA-only scan.
	if d.cfg.Trust >= TrustStrict && isTempPath(fdPath, d.cfg.WatchDirs) {
		// Even in temp dirs, check allowlist first in strict/paranoid
		if !d.allowlist.IsAllowed(content) {
			log.Printf("[ALERT] %s — unapproved binary in temp dir pid=%d path=%s (not in allowlist)",
				d.cfg.Trust.String(), pid, fdPath)
			d.respond(meta.Fd, false)
			responded = true
			syscall.Kill(pid, syscall.SIGKILL)
			return
		}
		// In allowlist — trusted even in temp
		d.respond(meta.Fd, true)
		responded = true
		return
	}

	// ── Strict/Paranoid: hash allowlist for non-temp paths ────────────
	if d.cfg.Trust >= TrustStrict {
		if !d.allowlist.IsAllowed(content) {
			log.Printf("[ALERT] %s — unapproved binary pid=%d path=%s (not in allowlist)",
				d.cfg.Trust.String(), pid, fdPath)
			d.respond(meta.Fd, false)
			responded = true
			syscall.Kill(pid, syscall.SIGKILL)
			return
		}
		d.respond(meta.Fd, true)
		responded = true
		return
	}

	// ── YARA scan (enforce mode fallback) ──────────────────────────────
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
func (d *Daemon) handleSharedObjectAccess(meta fanotifyEventMetadata, pid int32, exePath, fdPath string, eventFd int) {
	if !isTempPath(fdPath, d.cfg.WatchDirs) && isPathTrusted(fdPath, d.cfg.Trust, d.cfg.CustomTrustedPaths) {
		d.respond(meta.Fd, true)
		return
	}

	content, err := readFdContent(eventFd, d.cfg.MaxScan)
	if err != nil {
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

// ── shutdown ───────────────────────────────────────────────────────────

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
	if err := os.MkdirAll(filepath.Dir(path), fs.FileMode(0755)); err != nil {
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
	configPath := flag.String("config", defaultConfig, "TOML configuration file")
	pidFile := flag.String("pid", defaultPidFile, "PID file path")
	maxScan := flag.Int64("max-scan", maxScanBytes, "max bytes to scan per file")
	verbose := flag.Bool("v", false, "verbose logging")
	trustMode := flag.String("trust", "enforce", "trust mode: enforce, strict, paranoid, audit")
	showVer := flag.Bool("version", false, "print version and exit")

	flag.Parse()

	if *showVer {
		fmt.Printf("%s %s\n", appName, version)
		os.Exit(0)
	}

	log.SetOutput(os.Stderr)
	log.SetFlags(log.Ldate | log.Ltime | log.Lmicroseconds | log.Lshortfile)

	var trust TrustMode
	switch strings.ToLower(*trustMode) {
	case "enforce":
		trust = TrustEnforce
	case "strict":
		trust = TrustStrict
	case "paranoid":
		trust = TrustParanoid
	case "audit":
		trust = TrustAudit
	default:
		log.Fatalf("[FATAL] unknown trust mode: %s (use: enforce, strict, paranoid, audit)", *trustMode)
	}

	cfg := Config{
		RulesDir:   *rulesDir,
		Allowlist:  *allowlist,
		WatchMounts: []string{"/"},
		MaxScan:    *maxScan,
		PidFile:    *pidFile,
		Verbose:    *verbose,
		Trust:      trust,
		// v4 defaults: these features are ON by default
		ScanScripts:      true,
		MemfdDetect:      true,
		ProactiveInotify: true,
	}

	// Load TOML config
	if _, err := os.Stat(*configPath); err == nil {
		// v4: verify config file permissions before loading
		if permErr := verifyConfigPermissions(*configPath); permErr != nil {
			log.Printf("[ALERT] CONFIG INTEGRITY — %s", permErr)
		}

		var cf ConfigFile
		if _, err := toml.DecodeFile(*configPath, &cf); err != nil {
			log.Printf("[WARN] failed to parse config %s: %v (using defaults)", *configPath, err)
		} else {
			cf.MergeInto(&cfg)
			log.Printf("[INFO] loaded config from %s (trust=%s)", *configPath, cfg.Trust)
		}
	}

	log.Printf("[INFO] %s v%s starting (trust=%s, scripts=%v, memfd=%v, proactive=%v)",
		appName, version, cfg.Trust, cfg.ScanScripts, cfg.MemfdDetect, cfg.ProactiveInotify)

	d := NewDaemon(cfg, *configPath)

	// v4: record initial config integrity hash
	if _, err := os.Stat(*configPath); err == nil {
		d.configHash.Record(*configPath)
	}

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
	// v4: memfd_create detection scanner
	if d.cfg.MemfdDetect {
		go d.memfdScanner(ctx)
	}

	log.Print("[INFO] event loop active — monitoring all execve(2) + .so loads + memfd on /")
	d.eventLoop(ctx)

	d.running = false
	yara.Finalize()
	log.Print("[INFO] stopped")
}
