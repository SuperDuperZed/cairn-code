// xprotect-linux — rootkit detection signatures
// Covers: LD_PRELOAD rootkits, kernel module (LKM) rootkits, hidden files/process,
// shared object hijacking, and /etc/ld.so.preload manipulation.

rule XPL_LD_PRELOAD_Rootkit {
    meta:
        description = "LD_PRELOAD shared object rootkit"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1574.006"
    strings:
        $s1 = "dlopen" ascii
        $s2 = "__attribute__((constructor" ascii
        $s3 = "readdir" ascii
        $s4 = "getdents" ascii
        $s5 = "stat" ascii
        $s6 = "open" ascii
        $s7 = "fopen" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        $s1 and $s2 and 2 of ($s3*, $s4*, $s5*, $s6*, $s7*)
}

rule XPL_LD_Preload_Hook_Hidden_Proc {
    meta:
        description = "LD_PRELOAD rootkit hooking readdir to hide processes"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "__attribute__((constructor" ascii
        $s2 = "readdir" ascii
        $s3 = "strstr" ascii
        $s4 = "strcmp" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        all of them
}

rule XPL_LKM_Rootkit_Generic {
    meta:
        description = "Linux kernel module rootkit — .ko ELF with suspicious sys_call_table access"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1014"
    strings:
        $s1 = "sys_call_table" ascii
        $s2 = "module_init" ascii
        $s3 = "module_exit" ascii
        $s4 = "THIS_MODULE" ascii
        $s5 = "sys_open" ascii
        $s6 = "sys_read" ascii
        $s7 = "sys_getdents" ascii
        $s8 = "proc_ops" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        ( $s1 and 2 of ($s5*, $s6*, $s7*) ) or
        ( $s2 and $s3 and $s4 and 1 of ($s1*, $s8*) )
}

rule XPL_LKM_Hide_Process {
    meta:
        description = "Kernel rootkit that hooks task_struct to hide processes"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "task_struct" ascii
        $s2 = "next_task" ascii
        $s3 = "PIDTYPE_PID" ascii
        $s4 = "find_task_by_vpid" ascii
        $s5 = "init_pid_ns" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and ( $s3 or $s4 or $s5 )
}

rule XPL_LKM_Keylogger {
    meta:
        description = "Kernel keylogger module — hooks keyboard notifier chain"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "keyboard_notifier" ascii
        $s2 = "register_keyboard_notifier" ascii
        $s3 = "notifier_block" ascii
        $s4 = "task_struct" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        2 of ($s1*, $s2*, $s3*) and $s4
}

rule XPL_LKM_Network_Backdoor {
    meta:
        description = "Kernel module that opens a hidden network backdoor"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "sock_create" ascii
        $s2 = "kernel_accept" ascii
        $s3 = "kernel_recvmsg" ascii
        $s4 = "call_usermodehelper" ascii
        $s5 = "THIS_MODULE" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s5 and 2 of ($s1*, $s2*, $s3*, $s4*)
}

rule XPL_AntiForensics_Tool {
    meta:
        description = "Binary that securely deletes files to hide evidence"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "shred" ascii
        $s2 = "secure_delete" ascii
        $s3 = "O_DIRECT" ascii
        $s4 = "fallocate" ascii
        $s5 = "BLKDISCARD" ascii
        $s6 = "FALLOC_FL_PUNCH_HOLE" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        1 of ($s1*, $s2*) or
        ( $s6 and 1 of ($s4*, $s5*) )
}

rule XPL_Proc_Hide_Shared_Lib {
    meta:
        description = "Shared library that hides entries from /proc"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "/proc/" ascii
        $s2 = "readdir" ascii
        $s3 = "getdents64" ascii
        $s4 = "d_ino" ascii
        $s5 = "__attribute__((constructor" ascii
    condition:
        uint16(0) == 0x457f and filesize < 1MB and
        $s1 and $s3 and $s5
}
