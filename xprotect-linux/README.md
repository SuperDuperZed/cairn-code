# xprotect-linux

Local-first anti-malware daemon for Ubuntu. Intercepts `execve(2)` and `LD_PRELOAD` at the kernel level via `fanotify`, scans binaries and shared libraries against YARA signatures, and blocks malicious execution before page-load — no cloud, no telemetry, no dependencies beyond libc and libyara.

## How It Works

```
execve("/tmp/payload")        LD_PRELOAD=/evil.so ./app
    │                              │
    ▼                              ▼
┌──────────────────────┐   ┌──────────────────────┐
│  Linux Kernel        │   │  Linux Kernel        │
│  fanotify            │   │  fanotify            │
│  FAN_CLASS_PRE_CONTENT│   │  FAN_ACCESS_PERM     │
│  FAN_OPEN_EXEC_PERM  │   │  (.so interception)  │
└────────┬─────────────┘   └────────┬─────────────┘
         │ blocks thread              │ blocks dlopen
         ▼                            ▼
┌────────────────────────────────────────────────────┐
│  xprotect-linux v2                                   │
│  1. Behavioral: rapid exec burst? → DENY + SIGKILL  │
│  2. Trust model: strict/permissive/whitelist-only    │
│  3. SHA256 allowlist (strict/whitelist modes)        │
│  4. ELF validation (prevent malformed binary crash)  │
│  5. YARA scan against 200+ signatures               │
│  6. Match? → FAN_DENY + SIGKILL                      │
│     No match → FAN_ALLOW                             │
│                                                      │
│  Parallel: inotify watchers on /tmp, /dev/shm       │
│            flag rapid file creation patterns          │
└────────────────────────────────────────────────────┘
```

**Six layers of defence (v2):**

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| Behavioral | Sliding-window exec rate tracking | Detects rapid fork/exec bursts (shellcode runners, droppers) |
| Trust Model | Configurable strict/permissive/whitelist-only | Controls which paths get blanket trust |
| Hash Allowlist | SHA256 pre-computed allowlist | Deny-by-default for non-OS binaries in strict/whitelist mode |
| ELF Validation | Pre-scan header sanity checks | Prevents malformed ELF from crashing libyara (anti-denial-of-service) |
| Interception | `FAN_OPEN_EXEC_PERM` + `FAN_ACCESS_PERM` | Blocks exec + shared library loads before page-load |
| Evaluation | `libyara` compiled rule matrices | Pattern matching against 200+ signatures |

## Build

### Prerequisites

- **Go 1.23+** with CGO enabled
- **libyara-dev** (`libyara4` on Ubuntu 24.04)
- **GCC** (CGO requirement)
- **Root** or `CAP_SYS_ADMIN` (fanotify permission class requirement)

```bash
sudo apt install -y libyara-dev build-essential golang-go
git clone git@github.com:Cairn/xprotect-linux.git
cd xprotect-linux
CGO_ENABLED=1 go build -ldflags="-s -w" -o xprotect-linux .
```

## Install

```bash
sudo cp xprotect-linux /usr/local/bin/
sudo chmod 755 /usr/local/bin/xprotect-linux

# Deploy rules
sudo mkdir -p /etc/xprotect-linux/rules
sudo cp rules/*.yar /etc/xprotect-linux/rules/

# Set up allowlist (strict mode requires this)
# Populate with SHA256 hashes of trusted binaries:
#   sha256sum /usr/bin/python3 /opt/myapp/bin/worker >> /etc/xprotect-linux/allowlist.json
sudo cp allowlist.json /etc/xprotect-linux/allowlist.json

# Install systemd service
sudo cp xprotect-linux.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now xprotect-linux

sudo systemctl status xprotect-linux
sudo journalctl -u xprotect-linux -f
```

## Rules

200+ YARA signatures across 14 rule files in `/etc/xprotect-linux/rules/`. Hot-reload with `SIGHUP`.

| File | Rules | Targets |
|------|-------|---------|
| `reverse_shell.yar` | 15 | netcat, socat, PHP, Ruby, Go, Dart, Perl, awk, telnet, pwsh, mkfifo, C implant |
| `cryptominers.yar` | 11 | XMRig, xmrig-proxy, CNRig, SRBMiner, T-Rex, NBMiner, lolMiner, PhoenixMiner, wallet stealer |
| `implant_c2.yar` | 14 | Metasploit, Sliver, Havoc, Covenant, Empire, PoshC2, Shad0w, Cobalt Strike, Brute Ratel, Mythic |
| `rootkits.yar` | 9 | LD_PRELOAD hooks, LKM rootkits, process hiding, kernel keyloggers, anti-forensics |
| `privilege_escalation.yar` | 14 | LinPEAS, LinEnum, sudo abuse, SUID shell, kernel exploits, PwnKit, Docker socket privesc |
| `credential_stealers.yar` | 11 | Mimipy, LaZagne, SSH key scrapers, browser creds, GPG, AWS/GCP tokens, Kerberos tickets |
| `ransomware.yar` | 7 | AES/RSA file encryptors, ransom notes, ChaCha20, DB targeting, backup wipe |
| `network_tools.yar` | 12 | chisel, ligolo, gost tunnels, DNS/ICMP exfil, SSH reverse tunnels, base64 payloads |
| `container_escape.yar` | 9 | Docker socket abuse, cgroups escape, K8s API, kubeconfig theft, etcd dump, cloud metadata |
| `persistence.yar` | 10 | systemd backdoors, cron implants, SSH key injection, init.d, bash profile, autostart |
| `supply_chain.yar` | 10 | npm/pip trojans, GPG strip, deb/rpm repackage, apt modification, curl-pipe-sh downloads |
| `linux_malware.yar` | 12 | memfd fileless exec, ELF hollowing, anti-debug/VM, Mirai, Mozi, Kinsing, D-Bus privesc |
| `anti_evasion.yar` | 37 | XOR/RC4/AES decrypt, UPX, anti-debug, anti-VM, anti-sandbox, fileless exec, process hollowing, evidence clearing |
| `hardened_signatures.yar` | 25 | Go/Rust static binary implants, LD_PRELOAD .so abuse, shellcode stubs, download-execute, ptrace injection, temp-dir persistence |

## Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `-rules` | `/etc/xprotect-linux/rules` | YARA rules directory |
| `-allowlist` | `/etc/xprotect-linux/allowlist.json` | SHA256 allowlist JSON file |
| `-pid` | `/run/xprotect-linux/xprotect.pid` | PID file path |
| `-max-scan` | `67108864` (64 MiB) | Max bytes scanned per file |
| `-v` | `false` | Verbose per-event logging |
| `-strict` | `false` | Strict mode: only core OS paths + allowlist trusted |
| `-whitelist` | `false` | Whitelist-only: ONLY allowlisted SHA256 may execute |
| `-version` | — | Print version and exit |

### Trust Modes

| Mode | Flag | Behavior |
|------|------|----------|
| **Permissive** | (default) | Core OS paths + `/opt/` + `/usr/local/` trusted, everything else scanned |
| **Strict** | `-strict` | Only core OS paths trusted. Non-OS binaries require SHA256 allowlist entry. Temp dirs always scanned. |
| **Whitelist** | `-whitelist` | Deny-by-default. ONLY binaries in the SHA256 allowlist may execute anywhere. Maximum security. |

## Security Hardening

- **Unhandled exceptions default to `FAN_ALLOW`** — scanning failure never locks the system
- **ELF pre-validation** — malformed binaries are rejected before reaching libyara (prevents DoS via crafted ELF)
- **`/opt/` no longer exempt** — removed from default trust (was a major evasion vector)
- **Shared library scanning** — `FAN_ACCESS_PERM` catches `LD_PRELOAD` .so loads
- **Behavioral rate limiting** — rapid fork/exec bursts trigger automatic DENY + SIGKILL
- **inotify temp monitoring** — flags suspicious file creation patterns in `/tmp`, `/dev/shm`, `/var/tmp`
- **SHA256 allowlist** — hash-based positive enforcement in strict/whitelist modes
- **No network stack** — systemd unit denies all socket families except `AF_UNIX`/`AF_NETLINK`
- **Capability bounding** — `CAP_SYS_ADMIN` + `CAP_KILL` only
- **No cloud, no telemetry** — all detection and logging is local via stderr/journald

## Test

```bash
sudo ./test/detection_test.sh
```

## Project Structure

```
xprotect-linux/
├── main.go                    # Daemon: fanotify + inotify, libyara, behavioral engine, allowlist
├── go.mod                     # Go module (CGO + go-yara/v4 + x/sys)
├── allowlist.json             # SHA256 hash allowlist (populate with trusted binaries)
├── xprotect-linux.service     # Hardened systemd unit
├── rules/
│   ├── anti_evasion.yar       # Anti-evasion detection (37 rules)
│   ├── hardened_signatures.yar # Go/Rust/so/shellcode hardened rules (25 rules)
│   ├── reverse_shell.yar      # Reverse shell detection (15 rules)
│   ├── cryptominers.yar       # Cryptominer detection (11 rules)
│   ├── implant_c2.yar          # C2 framework implants (14 rules)
│   ├── rootkits.yar           # Rootkit detection (9 rules)
│   ├── privilege_escalation.yar # Privesc tool detection (14 rules)
│   ├── credential_stealers.yar  # Credential harvesting (11 rules)
│   ├── ransomware.yar         # Ransomware patterns (7 rules)
│   ├── network_tools.yar      # Recon/tunnel/exfil tools (12 rules)
│   ├── container_escape.yar    # Docker/K8s escape (9 rules)
│   ├── persistence.yar         # Persistence mechanisms (10 rules)
│   ├── supply_chain.yar        # Supply chain compromise (10 rules)
│   ├── linux_malware.yar       # Linux-specific malware (12 rules)
│   └── test_detection.yar      # Test signatures
└── test/
    └── detection_test.sh       # End-to-end verification
```

## License

Proprietary — Cairn
