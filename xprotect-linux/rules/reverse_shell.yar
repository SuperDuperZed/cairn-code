// xprotect-linux — reverse shell signatures
// Covers: netcat, socat, Python, PHP, Ruby, Perl, PowerShell, Dart, Rust shells
// and common C implant patterns.

rule XPL_Netcat_ReverseShell {
    meta:
        description = "Netcat reverse shell with -e flag for exec"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1059.004"
    strings:
        $s1 = "nc -e /bin" ascii
        $s2 = "ncat -e /bin" ascii
        $s3 = "netcat -e" ascii
        $s4 = "ncat --sh-exec" ascii
        $s5 = "/bin/sh -c" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        2 of ($s1*, $s2*, $s3*, $s4*) and $s5
}

rule XPL_Socat_ReverseShell {
    meta:
        description = "Socat reverse shell with exec and TCP relay"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1059.004"
    strings:
        $s1 = "socat exec:" ascii
        $s2 = "socat TCP:" ascii
        $s3 = "socat -d -d" ascii
        $s4 = "openssl s_client" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        any of ($s1*, $s2*) and 1 of ($s3*, $s4*)
}

rule XPL_PHP_ReverseShell {
    meta:
        description = "Compiled PHP payload with socket and shell execution"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "php" ascii
        $s2 = "fsockopen" ascii
        $s3 = "shell_exec" ascii
        $s4 = "proc_open" ascii
        $s5 = "/bin/sh" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        3 of ($s1*, $s2*, $s3*, $s4*, $s5*)
}

rule XPL_Ruby_ReverseShell {
    meta:
        description = "Compiled Ruby payload with TCPSocket shell"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "TCPSocket.open" ascii wide
        $s2 = "ruby" ascii
        $s3 = "IO.popen" ascii
        $s4 = "/bin/sh -i" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        2 of ($s1*, $s2*, $s3*) and $s4
}

rule XPL_Awk_Gawk_ReverseShell {
    meta:
        description = "AWK/gawk reverse shell via /inet/tcp"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "/inet/tcp" ascii
        $s2 = "gawk" ascii
        $s3 = "2>&1|&" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and 1 of ($s2*, $s3*)
}

rule XPL_Telnet_ReverseShell {
    meta:
        description = "Telnet-based reverse shell (legacy)"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "telnet" ascii
        $s2 = "/bin/sh" ascii
        $s3 = "pipe(0)" ascii
        $s4 = "inetd" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and 1 of ($s3*, $s4*)
}

rule XPL_PowerShell_Core_Linux {
    meta:
        description = "PowerShell Core (pwsh) execution with suspicious network patterns"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1059.001"
    strings:
        $s1 = "System.Management.Automation" ascii wide
        $s2 = "DownloadString" ascii wide
        $s3 = "Invoke-Expression" ascii wide
        $s4 = "Start-BitsTransfer" ascii wide
        $s5 = "IEX " ascii wide
    condition:
        uint16(0) == 0x457f and filesize < 50MB and
        $s1 and 2 of ($s2*, $s3*, $s4*, $s5*)
}

rule XPL_C_Implant_ReverseShell {
    meta:
        description = "C/C++ compiled reverse shell with socket, dup2, execve pattern"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "/bin/sh" ascii
        $s2 = "socket(AF_INET" ascii
        $s3 = "connect(" ascii
        $s4 = "dup2(" ascii
        $s5 = "execve(" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        all of ($s1*, $s2*, $s3*, $s4*, $s5*)
}

rule XPL_Golang_ReverseShell {
    meta:
        description = "Go-compiled reverse shell with net.Dial and exec.Command"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "net.Dial(" ascii
        $s2 = "exec.Command(" ascii
        $s3 = "/bin/sh" ascii
        $s4 = "os/exec" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        $s1 and $s2 and $s3
}

rule XPL_Dart_Flutter_Implant {
    meta:
        description = "Dart/Flutter compiled implant with Socket.connect"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "dart:io" ascii
        $s2 = "Socket.connect" ascii
        $s3 = "Process.start" ascii
    condition:
        uint16(0) == 0x457f and filesize < 30MB and
        all of them
}

rule XPL_Nodemailer_ReverseShell {
    meta:
        description = "Node.js compiled binary with child_process.exec for shell"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "child_process" ascii
        $s2 = ".exec(" ascii
        $s3 = "net.connect" ascii
        $s4 = "node" ascii
    condition:
        uint16(0) == 0x457f and filesize < 40MB and
        $s1 and $s2 and 1 of ($s3*, $s4*)
}

rule XPL_Mkfifo_PipeShell {
    meta:
        description = "Named pipe (FIFO) reverse shell via mkfifo"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "mkfifo" ascii
        $s2 = "/bin/sh" ascii
        $s3 = "S_ISFIFO" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2
}

rule XPL_FIFO_Based_Backdoor {
    meta:
        description = "FIFO-based backdoor with persistent listener"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "mknod" ascii
        $s2 = "p" ascii  // FIFO type flag
        $s3 = "open(" ascii
        $s4 = "dup2(" ascii
        $s5 = "execl(" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        $s1 and $s4 and $s5
}
