# xprotect-linux

Local-first anti-malware daemon for Ubuntu. Intercepts `execve(2)` at the kernel level via `fanotify`, scans binaries against YARA signatures, and blocks malicious execution before page-load — no cloud, no telemetry, no dependencies beyond libc and libyara.

## How It Works

```
execve("/tmp/payload")
    │
    ▼
┌──────────────────────┐
│  Linux Kernel        │
│  fanotify            │
│  FAN_CLASS_PRE_CONTENT│
│  FAN_OPEN_EXEC_PERM  │
└────────┬─────────────┘
         │ blocks thread
         ▼
┌──────────────────────┐
│  xprotect-linux       │
│  1. Read binary via fd│
│  2. Scan with libyara │
│  3. Match?            │
│     ├─ YES → FAN_DENY │
│     │        + SIGKILL │
│     └─ NO  → FAN_ALLOW│
└──────────────────────┘
```

**Three layers of defence:**

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| Interception | `fanotify` with `FAN_OPEN_EXEC_PERM` | Synchronously block execution before binary pages load |
| Evaluation | `libyara` compiled rule matrices | Pattern matching against known malware signatures |
| Remediation | `FAN_DENY` + `SIGKILL` | Kernel denies execution, daemon terminates the offending PID |

## Build

### Prerequisites

- **Go 1.23+** with CGO enabled
- **libyara-dev** (`libyara4` on Ubuntu 24.04)
- **GCC** (CGO requirement)
- **Root** or `CAP_SYS_ADMIN` (fanotify permission class requirement)

```bash
# Ubuntu/Debian
sudo apt install -y libyara-dev build-essential golang-go

# Clone
git clone git@github.com:Cairn/xprotect-linux.git
cd xprotect-linux

# Build (CGO required for libyara bindings)
CGO_ENABLED=1 go build -ldflags="-s -w" -o xprotect-linux .
```

## Install

```bash
# Copy binary
sudo cp xprotect-linux /usr/local/bin/
sudo chmod 755 /usr/local/bin/xprotect-linux

# Deploy rules
sudo mkdir -p /etc/xprotect-linux/rules
sudo cp rules/*.yar /etc/xprotect-linux/rules/

# Install systemd service
sudo cp xprotect-linux.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now xprotect-linux

# Check status
sudo systemctl status xprotect-linux
sudo journalctl -u xprotect-linux -f
```

## Rules

YARA rule files go in `/etc/xprotect-linux/rules/`. Any `.yar` or `.yara` file is loaded recursively on startup.

Included signatures:

| Rule | Target |
|------|--------|
| `XPL_Bash_ReverseShell` | `/dev/tcp/` bash reverse shells |
| `XPL_Python_ReverseShell` | Python `socket.connect` + `os.dup2` |
| `XPL_Perl_ReverseShell` | Perl `SOCK_STREAM` backdoors |
| `XPL_XMRig_Miner` | XMRig/monero cryptominer |
| `XPL_Generic_Backdoor` | `ptmx` + `SOCK_STREAM` implants |
| `XPL_Ephemeral_Drop` | ELF binaries executed from `/tmp`, `/dev/shm` |
| `XPL_Modified_Loader` | `LD_PRELOAD` + `dlopen` injection |

**Hot-reload rules without restart:**
```bash
sudo systemctl reload xprotect-linux
# or
sudo kill -HUP $(cat /run/xprotect-linux/xprotect.pid)
```

## Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `-rules` | `/etc/xprotect-linux/rules` | YARA rules directory |
| `-pid` | `/run/xprotect-linux/xprotect.pid` | PID file path |
| `-max-scan` | `67108864` (64 MiB) | Max bytes scanned per file |
| `-v` | `false` | Verbose per-event logging |
| `-version` | — | Print version and exit |

## Security Hardening

The daemon is designed with strict error containment:

- **Unhandled exceptions default to `FAN_ALLOW`** — a scanning failure never locks out the system
- **Trusted path exemptions** — `/usr/bin`, `/bin`, `/usr/lib`, `/snap`, `/nix/store` bypass scanning
- **No network stack** — the systemd unit denies all socket families except `AF_UNIX`/`AF_NETLINK`
- **Capability bounding** — only `CAP_SYS_ADMIN` (fanotify) and `CAP_KILL` (SIGKILL) are retained
- **No cloud, no telemetry** — all detection and logging is local via stderr/journald

## Test

The automated test suite compiles a clean and a malicious binary, starts the daemon, and verifies:

1. Clean binary executes successfully
2. Malicious binary (containing embedded test signature) is blocked with SIGKILL

```bash
# Must run as root
sudo ./test/detection_test.sh
```

## Project Structure

```
xprotect-linux/
├── main.go              # Daemon: fanotify loop, libyara scanning, remediation
├── go.mod               # Go module (CGO + go-yara/v4 + x/sys)
├── xprotect-linux.service  # Hardened systemd unit
├── rules/
│   ├── linux_malware.yar    # Production detection signatures
│   └── test_detection.yar   # Test-only signatures for verification
└── test/
    └── detection_test.sh    # Automated end-to-end detection test
```

## License

Proprietary — Cairn
