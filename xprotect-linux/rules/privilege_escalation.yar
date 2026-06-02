// xprotect-linux — privilege escalation tool detection
// Covers: LinPEAS, LinEnum, unix-privesc-check, Linux Exploit Suggester,
// and common GTFObins binary abuse patterns.

rule XPL_LinPEAS {
    meta:
        description = "LinPEAS (Linux Privilege Escalation Awesome Script) compiled or embedded"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1059.004"
    strings:
        $s1 = "linpeas" ascii nocase
        $s2 = "LINPEAS" ascii
        $s3 = "linuxprivchecker" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        any of them
}

rule XPL_LinEnum {
    meta:
        description = "LinEnum — Linux local enumeration script compiled binary"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "LinEnum" ascii
        $s2 = "Local Linux Enumeration" ascii
        $s3 = "/etc/passwd" ascii
        $s4 = "/etc/shadow" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and 2 of ($s2*, $s3*, $s4*)
}

rule XPL_Unix_Privesc_Check {
    meta:
        description = "unix-privesc-check — privilege auditing tool"
        severity = "medium"
        source = "xprotect-linux"
    strings:
        $s1 = "unix-privesc-check" ascii
        $s2 = "check_write_perms" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        any of them
}

rule XPL_Linux_Exploit_Suggester {
    meta:
        description = "Linux Exploit Suggester — recommends kernel exploits for privesc"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "Linux Exploit Suggester" ascii
        $s2 = "kernel version" ascii nocase
        $s3 = "exploit" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s3
}

rule XPL_Sudo_Abuse {
    meta:
        description = "Binary that exploits sudo misconfigurations (GTFObins pattern)"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1548.003"
    strings:
        $s1 = "sudo" ascii
        $s2 = "/etc/sudoers" ascii
        $s3 = "sudo -l" ascii
        $s4 = "NOPASSWD" ascii
        $s5 = "root" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s4 and ( $s2 or $s3 )
}

rule XPL_SUID_Binary_Shell {
    meta:
        description = "SUID binary that spawns a root shell"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1548.001"
    strings:
        $s1 = "setuid(" ascii
        $s2 = "seteuid(" ascii
        $s3 = "/bin/sh" ascii
        $s4 = "execve(" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        $s1 and $s3 and $s4
}

rule XPL_Sudoedit_Hijack {
    meta:
        description = "Binary leveraging sudoedit symlink race condition"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "sudoedit" ascii
        $s2 = "symlink" ascii
        $s3 = "race" ascii
        $s4 = "tmpfile" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        $s1 and $s2
}

rule XPL_Capability_Abuse {
    meta:
        description = "Binary that exploits Linux capabilities for privesc"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1548.002"
    strings:
        $s1 = "capset" ascii
        $s2 = "CAP_SYS_ADMIN" ascii
        $s3 = "CAP_SETUID" ascii
        $s4 = "CAP_SETGID" ascii
        $s5 = "CAP_NET_RAW" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and 1 of ($s3*, $s4*)
}

rule XPL_Kernel_Exploit_Generic {
    meta:
        description = "Linux kernel exploit binary (Dirty COW, PwnKit, etc.)"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1068"
    strings:
        $s1 = "/proc/self/mem" ascii
        $s2 = "mprotect" ascii
        $s3 = "/etc/passwd" ascii
        $s4 = "CVE-" ascii
        $s5 = "dirty" ascii nocase
        $s6 = "cow" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        ( $s1 and $s2 ) or
        ( $s4 and $s5 and $s6 )
}

rule XPL_Polkit_Pwn {
    meta:
        description = "PolicyKit (polkit) privilege escalation exploit"
        severity = "critical"
        source = "xprotect-linux"
        reference = "CVE-2021-4034 PwnKit"
    strings:
        $s1 = "pkexec" ascii
        $s2 = "GCONV_PATH" ascii
        $s3 = "spawn_helper" ascii
        $s4 = "ptrace" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        $s1 and $s2
}

rule XPL_Docker_Privesc {
    meta:
        description = "Binary that exploits Docker socket for container escape / host privesc"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1611"
    strings:
        $s1 = "/var/run/docker.sock" ascii
        $s2 = "docker" ascii
        $s3 = "mount(" ascii
        $s4 = "/host" ascii
        $s5 = "volumes" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2 and 1 of ($s3*, $s4*)
}

rule XPL_Shadow_File_Reader {
    meta:
        description = "Binary that reads /etc/shadow for offline cracking"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "/etc/shadow" ascii
        $s2 = "fopen(" ascii
        $s3 = "fgets(" ascii
        $s4 = "$6$" ascii   // SHA-512 hash prefix
        $s5 = "$y$" ascii   // yescrypt prefix
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        $s1 and $s2 and 1 of ($s4*, $s5*)
}

rule XPL_Passwd_Writer {
    meta:
        description = "Binary that writes to /etc/passwd to add backdoor accounts"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "/etc/passwd" ascii
        $s2 = "fopen(" ascii
        $s3 = "fprintf(" ascii
        $s4 = ":0:0:" ascii  // UID 0 (root)
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        $s1 and $s2 and $s3 and $s4
}
