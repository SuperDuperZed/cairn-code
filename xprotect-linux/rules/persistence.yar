// xprotect-linux — persistence mechanism detection
// Covers: systemd service backdoors, cron job implants, SSH authorized_keys injection,
// init.d scripts, and profile/rc file tampering.

rule XPL_Systemd_Backdoor_Service {
    meta:
        description = "Binary that installs a malicious systemd service"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1543.002"
    strings:
        $s1 = "/etc/systemd/system/" ascii
        $s2 = "[Unit]" ascii
        $s3 = "[Service]" ascii
        $s4 = "ExecStart=" ascii
        $s5 = "WantedBy=multi-user" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and $s3 and $s4
}

rule XPL_Systemd_Timer_Backdoor {
    meta:
        description = "Binary that installs a systemd timer for periodic callback"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1053.003"
    strings:
        $s1 = ".timer" ascii
        $s2 = "[Timer]" ascii
        $s3 = "OnUnitActiveSec" ascii
        $s4 = "systemctl" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and $s3
}

rule XPL_Cron_Implant {
    meta:
        description = "Binary that installs a cron job for persistence"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1053.003"
    strings:
        $s1 = "/etc/cron.d/" ascii
        $s2 = "crontab" ascii
        $s3 = "*/" ascii
        $s4 = "* * * *" ascii
        $s5 = "crontab -e" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s2 and $s4
}

rule XPL_SSH_Authorized_Keys_Injection {
    meta:
        description = "Binary that injects SSH authorized_keys for backdoor access"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1098.004"
    strings:
        $s1 = "/.ssh/authorized_keys" ascii
        $s2 = "ssh-rsa" ascii
        $s3 = "ssh-ed25519" ascii
        $s4 = "fopen(" ascii
        $s5 = "fputs(" ascii
        $s6 = "fappend" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and $s4
}

rule XPL_SSH_Config_Hijack {
    meta:
        description = "Binary that modifies SSH client config for MITM/proxying"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "/.ssh/config" ascii
        $s2 = "ProxyCommand" ascii
        $s3 = "ProxyJump" ascii
        $s4 = "IdentityFile" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and ( $s2 or $s3 )
}

rule XPL_InitD_Backdoor {
    meta:
        description = "Binary that installs an init.d script for boot persistence"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1543.002"
    strings:
        $s1 = "/etc/init.d/" ascii
        $s2 = "chkconfig" ascii
        $s3 = "update-rc.d" ascii
        $s4 = "#!/bin/sh" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s4 and ( $s2 or $s3 )
}

rule XPL_Bash_Profile_Implant {
    meta:
        description = "Binary that injects commands into shell profile/rc files"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1546.004"
    strings:
        $s1 = "/.bashrc" ascii
        $s2 = "/.bash_profile" ascii
        $s3 = "/.profile" ascii
        $s4 = "/.zshrc" ascii
        $s5 = "export" ascii
        $s6 = "alias" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        1 of ($s1*, $s2*, $s3*, $s4*) and 1 of ($s5*, $s6*)
}

rule XPL_AT_Job_Schedule {
    meta:
        description = "Binary that schedules tasks via at(1) for evasion"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1053.002"
    strings:
        $s1 = "at " ascii
        $s2 = "AT_JOB" ascii
        $s3 = "/var/spool/at" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s3
}

rule XPL_Lock_File_Persistence {
    meta:
        description = "Binary using lockfile mechanism to ensure single-instance persistence"
        severity = "medium"
        source = "xprotect-linux"
    strings:
        $s1 = "flock(" ascii
        $s2 = "lockfile" ascii
        $s3 = "/var/lock/" ascii
        $s4 = "/var/run/" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        ( $s1 or $s2 ) and 1 of ($s3*, $s4*)
}

rule XPL_Autostart_Desktop {
    meta:
        description = "Binary that installs desktop autostart entry"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "/.config/autostart/" ascii
        $s2 = "[Desktop Entry]" ascii
        $s3 = "Exec=" ascii
        $s4 = "Type=Application" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and $s3
}
