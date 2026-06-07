# linux-protect

Local-first anti-malware daemon for Ubuntu. Intercepts `execve(2)` and `LD_PRELOAD` at the kernel level via `fanotify`, scans binaries and shared libraries against YARA signatures, and blocks malicious execution before page-load — no cloud, no telemetry, no dependencies beyond libc and libyara.

## How It Works

```
execve("/tmp/payload")        python3 /tmp/evil.py        LD_PRELOAD=/evil.so ./app
    │                              │                            │
    ▼                              ▼                            ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  fanotify        │   │  fanotify        │   │  fanotify        │
│  FAN_OPEN_EXEC   │   │  FAN_OPEN_EXEC   │   │  FAN_ACCESS_PERM │
│  (trusted path)  │   │  (trusted interp)│   │  (.so intercept) │
└────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
         │    │                  │                       │
         │    │                  ▼                       ▼
         │    │          ┌────────────────┐     ┌──────────────────┐
         │    │          │ v4: parse      │     │ scan .so content │
         │    │          │ /proc/pid/     │     │ against YARA     │
         │    │          │ cmdline → find │     └────────┬─────────┘
         │    │          │ script arg     │              │
         │    │          │ → scan script  │              │
         │    │          └────────────────┘              │
         ▼    ▼                                        ▼
┌──────────────────────────────────────────────────────┐
│  linux-protect v4                                    │
│                                                       │
│  1. Audit check (log-only mode?)                     │
│  2. .so scan (FAN_ACCESS_PERM)                       │
│  3. Behavioral: exec burst? → DENY + SIGKILL        │
│  4. Behavioral: chain depth? → DENY + SIGKILL       │
│  5. Trust: path trusted?                             │
│     ├─ YES + interpreter? → v4: scan script args    │
│     └─ NO → continue                                │
│  6. v4 FIX: temp path + strict/paranoid? → allowlist │
│  7. Non-temp + strict/paranoid? → allowlist          │
│  8. YARA scan against 200+ signatures                │
│  9. Match? → FAN_DENY + SIGKILL                      │
│                                                       │
│  Background goroutines:                              │
│  • inotify: proactive scan temp-created files        │
│  • memfd scanner: /proc/*/exe for anonymous exec     │
│  • Config integrity: hash + permission verification  │
└──────────────────────────────────────────────────────┘
```

## Trust Modes

Four tiers of enforcement, cumulative by design:

| Mode | Flag | Behavior | Use Case |
|------|------|----------|----------|
| **enforce** | `--trust enforce` | Scan all non-OS paths, deny on YARA match. Script args scanned. | Default for production servers |
| **strict** | `--trust strict` | Enforce + deny-by-default: ALL binaries need allowlist (including temp dirs). | CI runners, HPC clusters |
| **paranoid** | `--trust paranoid` | Strict + behavioral heuristics + memfd detection + proactive temp scanning | High-value targets, air-gapped |
| **audit** | `--trust audit` | Log all scan results but never deny. | Baselining, compliance evidence |

Mode inheritance: `paranoid ⊃ strict ⊃ enforce`. `audit` is independent.

## v4 New Defences

| Defence | What It Catches | Active In |
|---------|----------------|-----------|
| **Script argument scanning** | `python3 /tmp/evil.py` — parses `/proc/<pid>/cmdline`, scans the script file | All modes |
| **memfd_create detection** | Anonymous memory-backed execution (frida, reptile, fileless loaders) | paranoid (kills), enforce (logs) |
| **Proactive inotify** | Immediately scans files created in temp dirs against YARA, deletes malware | All modes |
| **Temp-path allowlist** | v3 allowed temp files to bypass hash allowlist — v4 enforces allowlist in temp dirs too | strict, paranoid |
| **Config integrity** | SHA256 hash of TOML config + permission verification (warns if world-readable) | All modes |
| **Config reload safety** | SIGHUP reload checks if config was tampered with, logs alert on changes | All modes |

### dlopen() Runtime Limitation

`FAN_ACCESS_PERM` intercepts `LD_PRELOAD` and initial `.so` loads, but **not** `dlopen()` calls made mid-execution by a running process. An implant that starts clean and later calls `dlopen("/tmp/evil.so")` may bypass interception depending on kernel version. This is a fundamental fanotify limitation — full coverage requires LSM (eBPF/BPF) hooks.

## Build

```bash
sudo apt install -y libyara-dev build-essential golang-go
git clone git@github.com:Cairn/linux-protect.git
cd linux-protect
CGO_ENABLED=1 go build -ldflags="-s -w" -o linux-protect .
```

## Install

```bash
sudo cp linux-protect /usr/local/bin/
sudo chmod 755 /usr/local/bin/linux-protect

sudo mkdir -p /etc/linux-protect/rules
sudo cp rules/*.yar /etc/linux-protect/rules/

# Config — set restrictive permissions (daemon verifies this)
sudo cp linux-protect.toml /etc/linux-protect/linux-protect.toml
sudo chmod 600 /etc/linux-protect/linux-protect.toml

# Allowlist (strict/paranoid modes require this)
sudo cp allowlist.json /etc/linux-protect/allowlist.json

sudo cp linux-protect.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now linux-protect

sudo systemctl status linux-protect
sudo journalctl -u linux-protect -f
```

## Configuration

### CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-config` | `/etc/linux-protect/linux-protect.toml` | TOML configuration file |
| `-rules` | `/etc/linux-protect/rules` | YARA rules directory |
| `-allowlist` | `/etc/linux-protect/allowlist.json` | SHA256 allowlist JSON file |
| `-pid` | `/run/linux-protect/linux-protect.pid` | PID file path |
| `-max-scan` | `67108864` (64 MiB) | Max bytes scanned per file |
| `-v` | `false` | Verbose per-event logging |
| `-trust` | `enforce` | Trust mode: enforce, strict, paranoid, audit |
| `-version` | — | Print version and exit |

### TOML Config

```toml
trust_mode = "enforce"           # enforce | strict | paranoid | audit
trusted_paths = []               # additional trusted path prefixes
watch_dirs = ["/tmp", "/dev/shm", "/var/tmp"]
rules_dir = "/etc/linux-protect/rules"
allowlist = "/etc/linux-protect/allowlist.json"
max_scan_mb = 64
verbose = false
exec_rate_limit = 8
temp_file_rate = 20
scan_scripts = true               # v4: scan interpreter script arguments
memfd_detect = true               # v4: detect memfd_create anonymous execution
proactive_inotify = true          # v4: immediately scan temp-created files
```

### Security Notes

- **Config file must be `0600`** — daemon warns if permissions are too open
- **Config integrity hash** — daemon stores SHA256 of TOML on load; on SIGHUP reload, alerts if changed
- **Allowlist in ALL modes** — strict/paranoid enforce allowlist even in `/tmp`, `/dev/shm`
- **Script scanning** — catches `python3 evil.py`, `bash evil.sh`, `perl evil.pl` even when interpreters are in trusted paths
- **memfd detection** — background `/proc/*/exe` scan every 3s catches `memfd_create()` based fileless execution

## Rules

200+ YARA signatures across 15 rule files. Hot-reload with `SIGHUP`.

| File | Rules | Targets |
|------|-------|---------|
| `reverse_shell.yar` | 15 | netcat, socat, PHP, Ruby, Go, Dart, Perl, awk, telnet, pwsh, mkfifo, C implant |
| `cryptominers.yar` | 11 | XMRig, xmrig-proxy, CNRig, SRBMiner, T-Rex, NBMiner, lolMiner, PhoenixMiner |
| `implant_c2.yar` | 14 | Metasploit, Sliver, Havoc, Covenant, Empire, PoshC2, Cobalt Strike, Brute Ratel |
| `rootkits.yar` | 9 | LD_PRELOAD hooks, LKM rootkits, process hiding, kernel keyloggers |
| `privilege_escalation.yar` | 14 | LinPEAS, sudo abuse, SUID shell, kernel exploits, PwnKit, Docker socket |
| `credential_stealers.yar` | 11 | Mimipy, LaZagne, SSH key scrapers, browser creds, GPG, AWS/GCP tokens |
| `ransomware.yar` | 7 | AES/RSA file encryptors, ransom notes, ChaCha20, DB targeting |
| `network_tools.yar` | 12 | chisel, ligolo, gost tunnels, DNS/ICMP exfil, SSH reverse tunnels |
| `container_escape.yar` | 9 | Docker socket abuse, cgroups escape, K8s API, kubeconfig theft |
| `persistence.yar` | 10 | systemd backdoors, cron implants, SSH key injection, init.d |
| `supply_chain.yar` | 10 | npm/pip trojans, GPG strip, deb/rpm repackage, apt modification |
| `linux_malware.yar` | 12 | memfd fileless exec, ELF hollowing, anti-debug/VM, Mirai, Mozi, Kinsing |
| `anti_evasion.yar` | 37 | XOR/RC4/AES decrypt, UPX, anti-debug, anti-VM, anti-sandbox |
| `hardened_signatures.yar` | 25 | Go/Rust implants, LD_PRELOAD abuse, shellcode stubs, ptrace injection |
| `test_detection.yar` | — | Test signature for verification |

## Defence Layers (v4)

| Layer | Mechanism | Active In |
|-------|-----------|-----------|
| **Script Scanning** | Parse `/proc/<pid>/cmdline` for interpreter args, scan script | All modes |
| **memfd Detection** | Background `/proc/*/exe` scan for anonymous memory execution | All modes (paranoid kills) |
| **Trust Model** | Configurable enforce/strict/paranoid/audit with TOML | All modes |
| **Hash Allowlist** | SHA256 allowlist, deny-by-default in strict/paranoid | strict, paranoid |
| **Temp Allowlist** | v4: enforce allowlist even in temp directories | strict, paranoid |
| **.so Scanning** | `FAN_ACCESS_PERM` intercepts shared library loads | All modes |
| **Behavioral: Exec Rate** | Sliding-window fork/exec burst detection | paranoid |
| **Behavioral: Chain Depth** | Parent-child exec chain tracking | paranoid |
| **Proactive Inotify** | Immediate YARA scan of temp-created files, auto-delete | All modes |
| **Config Integrity** | SHA256 hash + permission verification on TOML config | All modes |
| **ELF Validation** | Pre-scan header sanity checks prevent malformed binary DoS | All modes |
| **Interception** | `FAN_OPEN_EXEC_PERM` + `FAN_CLASS_PRE_CONTENT` | All modes |
| **Evaluation** | `libyara` 200+ ATT&CK-tagged signatures | All modes |

## Security Hardening

- **Unhandled exceptions default to `FAN_ALLOW`** — scanning failure never locks the system
- **ELF pre-validation** — malformed binaries rejected before libyara (anti-DoS)
- **No hardcoded `/opt/` trust** — paths configurable via TOML only
- **Shared library scanning** — `FAN_ACCESS_PERM` catches `LD_PRELOAD`
- **Script argument scanning** — interpreters don't get a free pass anymore
- **memfd_create detection** — fileless execution caught via `/proc` scanning
- **Proactive inotify** — temp files scanned on creation, not just rate-tracked
- **Temp-path allowlist enforcement** — strict/paranoid block unknown files even in `/tmp`
- **Config integrity** — hash + permission checks detect and alert on tampering
- **No network stack** — systemd unit denies all socket families except `AF_UNIX`/`AF_NETLINK`
- **No cloud, no telemetry** — all detection and logging is local via stderr/journald

## Known Limitations

- **`dlopen()` at runtime**: `FAN_ACCESS_PERM` intercepts initial `.so` loads but not `dlopen()` calls made after a process is already running. Full coverage requires eBPF LSM hooks.
- **Core OS path trust**: `/usr/bin/`, `/usr/lib/` are trusted in all modes. If an attacker replaces a core binary (requiring root), it bypasses all scanning. Mitigate with `dpkg --verify` or IMA/EVM.
- **Race window on script scanning**: There's a brief window between `FAN_ALLOW` for the interpreter and the script scan completing. The interpreter starts but the script hasn't been fully parsed yet.
- **memfd scanner interval**: The `/proc` scan runs every 3 seconds. A fast memfd_create + exec + exit cycle could complete between scans.

## Test

```bash
sudo ./test/detection_test.sh
```

## Project Structure

```
linux-protect/
├── main.go                    # Daemon: fanotify + inotify, libyara, behavioral, memfd, config integrity
├── go.mod                     # Go module (CGO + go-yara/v4 + x/sys + toml)
├── linux-protect.toml         # TOML config template (must be 0600)
├── allowlist.json             # SHA256 hash allowlist
├── linux-protect.service      # Hardened systemd unit
├── rules/
│   ├── anti_evasion.yar       # (37 rules)
│   ├── hardened_signatures.yar # (25 rules)
│   ├── reverse_shell.yar      # (15 rules)
│   ├── cryptominers.yar       # (11 rules)
│   ├── implant_c2.yar         # (14 rules)
│   ├── rootkits.yar           # (9 rules)
│   ├── privilege_escalation.yar # (14 rules)
│   ├── credential_stealers.yar  # (11 rules)
│   ├── ransomware.yar         # (7 rules)
│   ├── network_tools.yar      # (12 rules)
│   ├── container_escape.yar   # (9 rules)
│   ├── persistence.yar        # (10 rules)
│   ├── supply_chain.yar       # (10 rules)
│   ├── linux_malware.yar      # (12 rules)
│   └── test_detection.yar     # Test signatures
└── test/
    └── detection_test.sh       # End-to-end verification
```

## License

Proprietary — Cairn
