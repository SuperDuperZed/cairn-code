// xprotect-linux — proprietary anti-evasion detection engine
// Detects binaries employing techniques specifically designed to evade YARA,
// static analysis, and behavioral scanners. These rules target the evasion
// mechanisms themselves, not specific malware families.

// ── String obfuscation ─────────────────────────────────────────────────────

rule AE_XOR_String_Decrypt {
    meta:
        description = "Binary with XOR-based string decryption loop at runtime"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "0x" ascii
        $s2 = "^ " ascii
        $s3 = "XOR" ascii nocase
        $s4 = "decrypt" ascii nocase
        $s5 = "decode" ascii nocase
        // XOR key constants commonly used in obfuscation
        $k1 = { 55 48 43 4F 44 } ascii  // "UXCOD" (simple key)
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        1 of ($s1*, $s2*) and 1 of ($s4*, $s5*) and filesize < 2MB
}

rule AE_Base64_Inline_Decode_Execute {
    meta:
        description = "Binary that base64-decodes embedded strings then executes them"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "base64" ascii nocase
        $s2 = "decode" ascii nocase
        $s3 = "system(" ascii
        $s4 = "popen(" ascii
        $s5 = "execve(" ascii
        $s6 = "eval(" ascii
        // Large base64 blob (>200 chars continuous)
        $b64 = /[A-Za-z0-9+\/]{300,}/ ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $b64 and 1 of ($s1*, $s2*) and 1 of ($s3*, $s4*, $s5*, $s6*)
}

rule AE_RC4_Decrypt_Payload {
    meta:
        description = "RC4 stream cipher used to decrypt payload at runtime"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "RC4" ascii
        $s2 = "rc4" ascii nocase
        $s3 = "arcfour" ascii nocase
        $s4 = "S-box" ascii
        $s5 = "swap" ascii
        $s6 = "cipher" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        ( 1 of ($s1*, $s2*, $s3*) ) and $s5 and filesize < 3MB
}

rule AE_AES_Decrypt_Runtime {
    meta:
        description = "Binary with AES decryption of embedded payload (uncommon for legitimate small binaries)"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "AES_" ascii
        $s2 = "EVP_DecryptInit" ascii
        $s3 = "EVP_DecryptUpdate" ascii
        $s4 = "PKCS5" ascii
        $s5 = "cipher" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        1 of ($s1*, $s2*, $s3*) and $s5
}

// ── Packing / binary protection ───────────────────────────────────────────

rule AE_UPX_Packed {
    meta:
        description = "UPX-packed binary (common evasion to hide embedded signatures)"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "UPX0" ascii
        $s2 = "UPX1" ascii
        $s3 = "UPX!" ascii
    condition:
        uint16(0) == 0x457f and
        any of them
}

rule AE_UPX_Packed_Modified_Header {
    meta:
        description = "UPX-packed with modified magic (anti-unpacking evasion)"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        // UPX section names present but UPX! magic corrupted/missing
        $s1 = "UPX0" ascii
        $s2 = "UPX1" ascii
    condition:
        uint16(0) == 0x457f and
        all of them and
        not any of ( "UPX!" at 0 .. 4096 )
}

rule AE_Generic_Packer_Indicators {
    meta:
        description = "Binary with packer-like characteristics (high entropy, small unpack stub)"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    condition:
        uint16(0) == 0x457f and
        filesize > 100KB and filesize < 10MB and
        // High entropy in .text section (> 7.5 bits per byte indicates encryption/compression)
        entropy( filesize * 0.5, filesize * 0.75 ) > 7.5
}

rule AE_Section_Name_Anomaly {
    meta:
        description = "ELF with suspicious section names (obfuscated packer sections)"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    condition:
        uint16(0) == 0x457f and
        for any section in elf_sections :
        (
            section.name matches /(\.)([a-z]{16,}|[0-9a-f]{16,}|[A-Z]{8,}|[a-z]{1,2}\d{4,})/ nocase and
            section.type == elf.SHT_PROGBITS
        )
}

// ── Anti-analysis / anti-debug ─────────────────────────────────────────────

rule AE_Ptrace_Anti_Debug {
    meta:
        description = "Anti-debugging via ptrace TRACEME (prevents debugger attachment)"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "ptrace(PTRACE_TRACEME" ascii
        $s2 = "PTRACE_TRACEME" ascii
        $s3 = "Cannot debug" ascii
        $s4 = "debugger detected" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        1 of them
}

rule AE_ProcSelfStatus_Debug_Check {
    meta:
        description = "Checks /proc/self/status TracerPid to detect debugger attachment"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "TracerPid" ascii
        $s2 = "/proc/self/status" ascii
        $s3 = "strace" ascii nocase
        $s4 = "ltrace" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2
}

rule AE_Syscall_Straight_Execve {
    meta:
        description = "Direct syscall execve bypassing libc (evades LD_PRELOAD and libc hooks)"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "syscall(" ascii
        $s2 = "SYS_execve" ascii
        $s3 = "__NR_execve" ascii
        $s4 = "/bin/sh" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        ( $s2 or $s3 ) and $s4
}

rule AE_Syscall_Straight_Socket {
    meta:
        description = "Direct syscall for networking bypassing libc hooks"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "__NR_socket" ascii
        $s2 = "__NR_connect" ascii
        $s3 = "SYS_socket" ascii
        $s4 = "SYS_connect" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        ( $s1 and $s2 ) or ( $s3 and $s4 )
}

rule AE_Syscall_Table_Hook_Bypass {
    meta:
        description = "Binary reads /proc/kallsyms to locate syscall table (hook detection bypass)"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "kallsyms" ascii
        $s2 = "sys_call_table" ascii
        $s3 = "/proc/" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2
}

// ── Anti-sandbox / anti-VM ─────────────────────────────────────────────────

rule AE_Sandbox_Timing_Check {
    meta:
        description = "Time-based sandbox detection (sleep + rdtsc to detect acceleration)"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "clock_gettime" ascii
        $s2 = "rdtsc" ascii
        $s3 = "sleep(" ascii
        $s4 = "nanosleep" ascii
        $s5 = "gettimeofday" ascii
        $s6 = "sandbox" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        ( $s2 or 1 of ($s1*, $s5*) ) and 1 of ($s3*, $s4*) and filesize < 3MB
}

rule AE_VM_Hardware_Detection {
    meta:
        description = "VM detection via CPUID, hypervisor MSR, or DMI tables"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "vmware" ascii nocase
        $s2 = "vbox" ascii nocase
        $s3 = "qemu" ascii nocase
        $s4 = "xen" ascii nocase
        $s5 = "hypervisor" ascii nocase
        $s6 = "KVM" ascii
        $s7 = "Microsoft Corporation" ascii
        $s8 = "cpuid" ascii nocase
        $s9 = "hypervisor present" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        1 of ($s1*, $s2*, $s3*, $s4*, $s5*, $s6*, $s7*, $s9*) and
        filesize < 3MB
}

rule AE_Sandbox_Username_Check {
    meta:
        description = "Checks username/environment for sandbox indicators"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "sandbox" ascii nocase
        $s2 = "malware" ascii nocase
        $s3 = "virus" ascii nocase
        $s4 = "getenv(" ascii
        $s5 = "getlogin" ascii
        $s6 = "cwd" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        1 of ($s1*, $s2*, $s3*) and 1 of ($s4*, $s5*) and filesize < 2MB
}

rule AE_Sandbox_Mouse_Activity {
    meta:
        description = "Checks for user interaction (mouse movement) to detect headless sandbox"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "/dev/input/mouse" ascii
        $s2 = "/dev/input/event" ascii
        $s3 = "GetMouseMovePos" ascii
        $s4 = "XOpenDisplay" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        1 of ($s1*, $s2*, $s3*, $s4*) and filesize < 2MB
}

rule AE_Sandbox_Memory_Check {
    meta:
        description = "Checks RAM size or CPU count to detect sandbox VMs"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "MemTotal" ascii
        $s2 = "/proc/meminfo" ascii
        $s3 = "nproc" ascii
        $s4 = "/proc/cpuinfo" ascii
        $s5 = "sysconf(_SC_NPROCESSORS" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        ( $s1 and $s2 ) or ( $s5 and filesize < 2MB )
}

// ── Fileless execution evasion ──────────────────────────────────────────────

rule AE_Memfd_Create_Fileless {
    meta:
        description = "Uses memfd_create to execute entirely in memory (evades disk-based scanning)"
        severity = "critical"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "memfd_create" ascii
        $s2 = "fexecve" ascii
        $s3 = "MFD_CLOEXEC" ascii
        $s4 = "seal" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and ( $s2 or $s3 )
}

rule AE_Pipe_Inject_Execute {
    meta:
        description = "Injects payload into pipe then exec (fileless execution)"
        severity = "critical"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "pipe(" ascii
        $s2 = "fork(" ascii
        $s3 = "dup2(" ascii
        $s4 = "execl(" ascii
        $s5 = "/bin/sh" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        all of them
}

rule AE_ProcSelfMem_Write {
    meta:
        description = "Writes to /proc/self/mem for code injection without file on disk"
        severity = "critical"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "/proc/self/mem" ascii
        $s2 = "mmap(" ascii
        $s3 = "PROT_WRITE" ascii
        $s4 = "PROT_EXEC" ascii
        $s5 = "ptrace" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s3 and $s4
}

// ── Dynamic import / API hiding ───────────────────────────────────────────

rule AE_Dlopen_Runtime_Resolve {
    meta:
        description = "Uses dlopen/dlsym for runtime API resolution (evades static import analysis)"
        severity = "medium"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "dlopen" ascii
        $s2 = "dlsym" ascii
        $s3 = "RTLD_LAZY" ascii
        $s4 = "RTLD_NOW" ascii
        $s5 = "libc.so" ascii
        $s6 = "libpthread.so" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and 1 of ($s5*, $s6*)
}

rule AE_GOT_PLM_Hook_Install {
    meta:
        description = "PLT/GOT hooking to intercept and redirect library calls"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "PLT" ascii
        $s2 = ".got" ascii
        $s3 = "mprotect(" ascii
        $s4 = "hook" ascii nocase
        $s5 = "intercept" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s3 and ( $s4 or $s5 )
}

rule AE_VDSO_Abuse {
    meta:
        description = "Uses vDSO for direct syscalls to bypass seccomp/ptrace"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    condition:
        uint16(0) == 0x457f and
        for any section in elf_sections :
        (
            section.name == ".vdso" or
            section.name == "__vdso_"
        ) and
        filesize < 5MB
}

// ── Hollowing / injection ───────────────────────────────────────────────────

rule AE_Process_Hollow {
    meta:
        description = "Process hollowing — unmaps legitimate code, injects malicious payload"
        severity = "critical"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "munmap(" ascii
        $s2 = "mmap(" ascii
        $s3 = "ptrace(" ascii
        $s4 = "PTRACE_ATTACH" ascii
        $s5 = "PTRACE_DETACH" ascii
        $s6 = "PROT_WRITE" ascii
        $s7 = "PROT_EXEC" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s4 and $s5 and $s6 and $s7
}

rule AE_Inotify_Modified_Self {
    meta:
        description = "Monitors own binary via inotify and rewrites on disk to evade scanner"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "inotify_init" ascii
        $s2 = "inotify_add_watch" ascii
        $s3 = "/proc/self/exe" ascii
        $s4 = "truncate(" ascii
        $s5 = "rewrite" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s3
}

// ── Environment / context evasion ─────────────────────────────────────────

rule AE_Check_Security_Tools {
    meta:
        description = "Checks for running security tools (AV, EDR, sandbox) before payload activation"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "clamav" ascii nocase
        $s2 = "chkrootkit" ascii nocase
        $s3 = "rkhunter" ascii nocase
        $s4 = "ossec" ascii nocase
        $s5 = "crowdstrike" ascii nocase
        $s6 = "falcon" ascii nocase
        $s7 = "sentinel" ascii nocase
        $s8 = "defender" ascii nocase
        $s9 = "/proc/" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        1 of ($s1*, $s2*, $s3*, $s4*, $s5*, $s6*, $s7*, $s8*) and
        $s9
}

rule AE_Disable_Security_Mechanisms {
    meta:
        description = "Attempts to disable SELinux, AppArmor, or other security controls"
        severity = "critical"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "setenforce 0" ascii
        $s2 = "SELinux" ascii
        $s3 = "AppArmor" ascii
        $s4 = "aa-disable" ascii
        $s5 = "sestatus" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        ( $s1 or $s4 )
}

rule AE_Clear_Evidence {
    meta:
        description = "Clears bash history, logs, or other forensic artifacts"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = ".bash_history" ascii
        $s2 = "/var/log/" ascii
        $s3 = "> /dev/null" ascii
        $s4 = "unset HISTFILE" ascii
        $s5 = "history -c" ascii
        $s6 = "shred" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        ( $s4 or $s5 ) or ( $s1 and $s3 )
}

rule AE_Remove_Temp_After_Exec {
    meta:
        description = "Binary that deletes itself after execution (zero-footprint)"
        severity = "high"
        source = "xprotect-linux"
        category = "anti-evasion"
    strings:
        $s1 = "unlink(" ascii
        $s2 = "remove(" ascii
        $s3 = "/proc/self/exe" ascii
        $s4 = "/proc/self/fd/" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        ( $s1 or $s2 ) and ( $s3 or $s4 )
}
