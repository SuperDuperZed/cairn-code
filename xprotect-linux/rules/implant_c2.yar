// xprotect-linux — C2 (command-and-control) framework implant detection
// Covers: Metasploit Meterpreter, Sliver, Havoc, Covenant, Mythic, Brute Ratel,
// Empire/PoshC2, Cobalt Strike (cross-platform), and generic beacon patterns.

rule XPL_Metasploit_Meterpreter {
    meta:
        description = "Metasploit Meterpreter — stager or stage payload"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1055.001"
    strings:
        $s1 = "-meterpreter-" ascii
        $s2 = "metsrv" ascii
        $s3 = "RECV" ascii
        $s4 = "/bin/sh -c" ascii
        $s5 = "reverse_tcp" ascii
        $s6 = "migrate" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        3 of ($s1*, $s2*, $s3*, $s5*, $s6*) and $s4
}

rule XPL_Sliver_Implant {
    meta:
        description = "Sliver C2 framework implant binary"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1059"
    strings:
        $s1 = "github.com/sliver" ascii
        $s2 = "sliver" ascii nocase
        $s3 = "beacon" ascii
        $s4 = "c2.RPC" ascii
        $s5 = "Connect" ascii
        $s6 = "gRPC" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        $s1 and 1 of ($s3*, $s4*, $s6*)
}

rule XPL_Havoc_Implant {
    meta:
        description = "Havoc C2 framework implant (Demon agent)"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "Havoc" ascii
        $s2 = "Demon" ascii
        $s3 = "CommandId" ascii
        $s4 = "TaskId" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        2 of ($s1*, $s2*, $s3*, $s4*)
}

rule XPL_Covenant_Implant {
    meta:
        description = "Covenant C2 framework implant (Grunt)"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "Covenant" ascii
        $s2 = "Grunt" ascii nocase
        $s3 = "Task" ascii
        $s4 = "startup" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2
}

rule XPL_Empire_Stager {
    meta:
        description = "PowerShell Empire stager/exec binary"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "powershell" ascii nocase
        $s2 = "IEX " ascii
        $s3 = "DownloadString" ascii
        $s4 = "New-Object" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and 2 of ($s2*, $s3*, $s4*)
}

rule XPL_PoshC2_Implant {
    meta:
        description = "PoshC2 (PowerShell C2) implant"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "PoshC2" ascii
        $s2 = "P0sHC2" ascii
        $s3 = "Get-Shell" ascii
        $s4 = "sharpteeth" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        1 of ($s1*, $s2*) or 1 of ($s3*, $s4*)
}

rule XPL_Shad0w_Implant {
    meta:
        description = "Shad0w C2 framework implant (post-exploitation)"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "shad0w" ascii nocase
        $s2 = "beacon" ascii
        $s3 = "agent" ascii
        $s4 = "callback" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and 2 of ($s2*, $s3*, $s4*)
}

rule XPL_Cobalt_Strike_Beacon {
    meta:
        description = "Cobalt Strike Beacon (Linux cross-platform variant)"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "beacon" ascii nocase
        $s2 = "sleep(" ascii
        $s3 = "jitter" ascii
        $s4 = "kill date" ascii
        $s5 = "cobalt" ascii nocase
        $s6 = "puppet" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s3 and ( $s5 or $s6 )
}

rule XPL_Generic_Beacon_Sleep_Jitter {
    meta:
        description = "Generic implant with beacon sleep+jitter timing pattern"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "sleep(" ascii
        $s2 = "jitter" ascii nocase
        $s3 = "beacon" ascii nocase
        $s4 = "/bin/sh" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2 and $s4 and filesize < 2MB
}

rule XPL_Iterative_Socket_Reconnect {
    meta:
        description = "Implant with retry loop for C2 reconnection"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "sleep(" ascii
        $s2 = "connect(" ascii
        $s3 = "AF_INET" ascii
        $s4 = "SOCK_STREAM" ascii
    condition:
        uint16(0) == 0x457f and filesize < 2MB and
        all of them
}

rule XPL_Brute_Ratel_Implant {
    meta:
        description = "Brute Ratel C2 implant"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "Brute" ascii
        $s2 = "Ratel" ascii
        $s3 = "SRDI" ascii
        $s4 = "sleep_mask" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s2 and 1 of ($s1*, $s3*, $s4*)
}

rule XPL_Mythic_Agent {
    meta:
        description = "Mythic C2 framework agent binary"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "mythic" ascii nocase
        $s2 = "agent" ascii
        $s3 = "callbacks" ascii
        $s4 = "messages" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and $s2 and $s3
}

rule XPL_Fivem_Rev_Shell {
    meta:
        description = "FiveM mod menu with reverse shell capability"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "FiveM" ascii
        $s2 = "CFX" ascii
        $s3 = "reverse" ascii
        $s4 = "socket(" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        ( $s1 or $s2 ) and $s4
}
