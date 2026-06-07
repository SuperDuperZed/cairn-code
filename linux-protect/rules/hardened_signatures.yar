// xprotect-linux — hardened rules targeting compiled Go/Rust/static binaries,
// LD_PRELOAD abuse, shellcode byte arrays, and runtime download-execute patterns.
// These address specific evasion vectors identified during red-team assessment.

// ── Go-compiled binary heuristics ──────────────────────────────────────────

rule AE_Go_ReverseShell_Static {
    meta:
        description = "Go-compiled reverse shell — net.Dial + exec.Cmd pattern without libc strings"
        severity = "critical"
        source = "xprotect-linux"
        category = "compiled-go"
    strings:
        $s1 = "net.Dial(" ascii
        $s2 = "exec.Command(" ascii
        $s3 = "os/exec" ascii
        $s4 = "runtime.main" ascii
        $s5 = "go.buildid" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        $s4 and $s1 and $s2
}

rule AE_Go_Implant_With_Sleep {
    meta:
        description = "Go implant with beacon sleep timing (common in Go-based C2)"
        severity = "critical"
        source = "xprotect-linux"
        category = "compiled-go"
    strings:
        $s1 = "runtime.main" ascii
        $s2 = "go.buildid" ascii
        $s3 = "time.Sleep(" ascii
        $s4 = "crypto/tls" ascii
        $s5 = "net/http" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        $s1 and $s2 and $s3 and ( $s4 or $s5 )
}

rule AE_Go_Crypto_TLS_Custom {
    meta:
        description = "Go binary with custom TLS config (common in implants for cert pinning bypass)"
        severity = "high"
        source = "xprotect-linux"
        category = "compiled-go"
    strings:
        $s1 = "crypto/tls" ascii
        $s2 = "InsecureSkipVerify" ascii
        $s3 = "runtime.main" ascii
        $s4 = "go.buildid" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        all of them and filename matches /^\/(tmp|dev\/shm|var\/tmp)\/.*/
}

rule AE_Go_Static_Binary_No_Symbols {
    meta:
        description = "Stripped Go static binary with network capability in temp directory"
        severity = "high"
        source = "xprotect-linux"
        category = "compiled-go"
    condition:
        uint16(0) == 0x457f and
        filesize > 100KB and filesize < 20MB and
        filename matches /^\/(tmp|dev\/shm|var\/tmp)\/.*/ and
        // Go runtime marker even in stripped binaries (appears in .go.buildinfo or .gopclntab)
        any of ( "go.buildid" at 0..filesize, ".noptrdata" ascii at 0..4096, "main.main" ascii at 0..filesize )
}

rule AE_Go_Sliver_Implant_Specific {
    meta:
        description = "Sliver C2 Go implant — specific Go package paths"
        severity = "critical"
        source = "xprotect-linux"
        category = "compiled-go"
    strings:
        $s1 = "github.com/bishopfox/sliver" ascii
        $s2 = "implant" ascii
        $s3 = "beacon" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        $s1
}

rule AE_Go_DNS_Exfil_Pattern {
    meta:
        description = "Go binary performing DNS-based exfiltration"
        severity = "critical"
        source = "xprotect-linux"
        category = "compiled-go"
    strings:
        $s1 = "net.ResolveIPAddr" ascii
        $s2 = "encoding/base64" ascii
        $s3 = "runtime.main" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and $s2 and $s3
}

// ── Rust-compiled binary heuristics ────────────────────────────────────────

rule AE_Rust_Implant_Generic {
    meta:
        description = "Rust-compiled implant with Tokio async runtime and networking"
        severity = "high"
        source = "xprotect-linux"
        category = "compiled-rust"
    strings:
        $s1 = "tokio" ascii
        $s2 = "runtime" ascii
        $s3 = "std::" ascii
        $s4 = "core::" ascii
        $s5 = "hyper" ascii
        $s6 = "reqwest" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and $s3 and $s4 and filesize < 5MB
}

rule AE_Rust_Static_Socket_Implant {
    meta:
        description = "Rust static binary with raw socket usage in suspicious path"
        severity = "high"
        source = "xprotect-linux"
        category = "compiled-rust"
    strings:
        $s1 = "rustc" ascii
        $s2 = "cargo" ascii
        $s3 = "socket2" ascii
        $s4 = "std::sys::" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        filename matches /^\/(tmp|dev\/shm|var\/tmp)\/.*/ and
        $s4
}

// ── LD_PRELOAD abuse detection ─────────────────────────────────────────────

rule AE_LD_Preload_Hijack_Exec {
    meta:
        description = "Shared library designed to hijack execution via LD_PRELOAD"
        severity = "critical"
        source = "xprotect-linux"
        category = "so-hijack"
    strings:
        $s1 = "__attribute__((constructor" ascii
        $s2 = "getenv(" ascii
        $s3 = "LD_PRELOAD" ascii
        $s4 = "dlopen" ascii
        $s5 = "execve" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        $s1 and $s3
}

rule AE_LD_Preload_Credential_Steal {
    meta:
        description = "LD_PRELOAD library that hooks libc functions to steal credentials"
        severity = "critical"
        source = "xprotect-linux"
        category = "so-hijack"
    strings:
        $s1 = "__attribute__((constructor" ascii
        $s2 = "fopen" ascii
        $s3 = "/etc/shadow" ascii
        $s4 = "fwrite" ascii
    condition:
        uint16(0) == 0x457f and filesize < 1MB and
        $s1 and $s3 and $s4
}

rule AE_LD_Preload_Hide_Proc {
    meta:
        description = "LD_PRELOAD library that hooks readdir to hide processes/files"
        severity = "critical"
        source = "xprotect-linux"
        category = "so-hijack"
    strings:
        $s1 = "__attribute__((constructor" ascii
        $s2 = "readdir" ascii
        $s3 = "strstr" ascii
        $s4 = "hidden" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 1MB and
        all of them
}

rule AE_SO_In_Temp_Directory {
    meta:
        description = "Shared object loaded from writable temp directory (never legitimate)"
        severity = "critical"
        source = "xprotect-linux"
        category = "so-hijack"
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        filename matches /^\/(tmp|dev\/shm|var\/tmp)\/.*\.so/
}

// ── Shellcode / encoded payload detection ──────────────────────────────────

rule AE_Shellcode_X86_Jmp_Call {
    meta:
        description = "Binary containing position-independent x86 shellcode stubs"
        severity = "critical"
        source = "xprotect-linux"
        category = "shellcode"
    strings:
        // Common shellcode prologues
        $sc1 = { E8 00 00 00 00 }           // call +5 (get EIP)
        $sc2 = { 31 C0 50 68 ?? ?? ?? ?? }  // xor eax,eax; push eax; push addr (null-terminated string)
        $sc3 = { FF D0 }                     // call eax
        $sc4 = { 31 C9 F7 E1 }              // xor ecx,ecx; mul ecx (zero eax, edx, ebx)
    condition:
       	uint16(0) == 0x457f and filesize < 2MB and
       	2 of ($sc1*, $sc2*, $sc3*, $sc4*)
}

rule AE_Shellcode_Linux_SysExecve {
    meta:
        description = "Linux syscall shellcode for execve(/bin/sh)"
        severity = "critical"
        source = "xprotect-linux"
        category = "shellcode"
    strings:
        // int 0x80 or syscall instruction with eax=0xb (execve)
        $sc1 = { B0 0B CD 80 }         // mov al,0xb; int 0x80
        $sc2 = { 31 C0 B0 0B CD 80 }   // xor eax,eax; mov al,0xb; int 0x80
        $sc3 = { 48 31 C0 48 C7 C0 }   // xor rax,rax; mov rax (x86-64)
        $sc4 = { 0F 05 }                // syscall (x86-64)
        $binsh = "/bin/sh" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        ( 1 of ($sc1*, $sc2*, $sc3*, $sc4*) ) and $binsh
}

rule AE_Large_ByteArray_Encoded {
    meta:
        description = "Binary with suspicious large encoded byte arrays (shellcode/payload containers)"
        severity = "high"
        source = "xprotect-linux"
        category = "shellcode"
    strings:
        // Large base64 or hex-encoded blobs often used for shellcode containers
        $b64_1k = /[A-Za-z0-9+\/]{1000,}/ ascii
        $hex_1k = /[0-9a-fA-F]{1000,}/ ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        ( $b64_1k or $hex_1k ) and
        filename matches /^\/(tmp|dev\/shm|var\/tmp|home)\/.*/
}

// ── Runtime download-execute ──────────────────────────────────────────────

rule AE_Runtime_Download_Execute {
    meta:
        description = "Binary that downloads code and executes it at runtime"
        severity = "critical"
        source = "xprotect-linux"
        category = "download-execute"
    strings:
        $s1 = "http" ascii
        $s2 = "chmod(" ascii
        $s3 = "system(" ascii
        $s4 = "popen(" ascii
        $s5 = "curl " ascii
        $s6 = "wget " ascii
        $s7 = "| sh" ascii
        $s8 = "| bash" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        ( $s5 or $s6 ) and ( $s7 or $s8 )
}

rule AE_Wget_Curl_Pipe_Execute {
    meta:
        description = "Binary executing downloaded shell script via curl|sh or wget|bash"
        severity = "critical"
        source = "xprotect-linux"
        category = "download-execute"
    strings:
        $s1 = "GET /" ascii
        $s2 = "Content-Type" ascii
        $s3 = "system(" ascii
        $s4 = "popen(" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and ( $s3 or $s4 )
}

rule AE_Python_Eval_Remote {
    meta:
        description = "Binary calling python -c eval on remote content"
        severity = "critical"
        source = "xprotect-linux"
        category = "download-execute"
    strings:
        $s1 = "python" ascii nocase
        $s2 = "-c " ascii
        $s3 = "eval(" ascii
        $s4 = "urllib" ascii
        $s5 = "requests" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2 and $s3
}

// ── Process injection via ptrace ──────────────────────────────────────────

rule AE_Ptrace_Inject {
    meta:
        description = "Binary performing process injection via ptrace PTRACE_POKETEXT"
        severity = "critical"
        source = "xprotect-linux"
        category = "injection"
    strings:
        $s1 = "PTRACE_POKETEXT" ascii
        $s2 = "PTRACE_POKEdata" ascii
        $s3 = "PTRACE_CONT" ascii
        $s4 = "PTRACE_ATTACH" ascii
        $s5 = "ptrace(" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s5 and ( $s1 or $s2 )
}

// ── Cron/at persistence from temp ────────────────────────────────────────

rule AE_Cron_From_Temp {
    meta:
        description = "Binary installing cron jobs from temp directory (persistence from temp)"
        severity = "high"
        source = "xprotect-linux"
        category = "temp-persistence"
    strings:
        $s1 = "crontab" ascii
        $s2 = "/etc/cron" ascii
        $s3 = "echo " ascii
        $s4 = ">> " ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        filename matches /^\/(tmp|dev\/shm|var\/tmp)\/.*/ and
        $s1 and $s2
}

rule AE_Systemd_From_Temp {
    meta:
        description = "Binary installing systemd service from temp directory"
        severity = "high"
        source = "xprotect-linux"
        category = "temp-persistence"
    strings:
        $s1 = "/etc/systemd/system/" ascii
        $s2 = "[Unit]" ascii
        $s3 = "[Service]" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        filename matches /^\/(tmp|dev\/shm|var\/tmp)\/.*/ and
        $s1 and $s2
}
