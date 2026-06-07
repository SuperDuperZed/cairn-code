// xprotect-linux — suspicious network/reconnaissance tool detection
// Covers: port scanners, packet sniffers, proxy tools, tunneling binaries,
// and network exfiltration utilities found in temp/unexpected paths.

rule XPL_Nmap_Unauthorized {
    meta:
        description = "Nmap binary in suspicious location (unauthorized recon)"
        severity = "medium"
        source = "xprotect-linux"
        reference = "ATT&CK T1046"
    strings:
        $s1 = "nmap" ascii nocase
        $s2 = "NSE" ascii
        $s3 = "SYN scan" ascii
    condition:
        uint16(0) == 0x457f and filesize < 30MB and
        filename matches /^\/(tmp|dev\/shm|var\/tmp|home\/.+\/\.local)\/.*/ and
        $s1 and ( $s2 or $s3 )
}

rule XPL_Tcpdump_Unauthorized {
    meta:
        description = "Tcpdump in suspicious location (packet capture for exfil)"
        severity = "medium"
        source = "xprotect-linux"
        reference = "ATT&CK T1040"
    strings:
        $s1 = "tcpdump" ascii nocase
        $s2 = "pcap" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        filename matches /^\/(tmp|dev\/shm|var\/tmp)\/.*/ and
        $s1 and $s2
}

rule XPL_Python_Network_Tools {
    meta:
        description = "Compiled Python binary with network scanning libraries"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "scapy" ascii
        $s2 = "socket" ascii
        $s3 = "python" ascii nocase
        $s4 = "IP (" ascii
        $s5 = "TCP (" ascii
    condition:
        uint16(0) == 0x457f and filesize < 30MB and
        $s1 and $s4
}

rule XPL_SSHTunnel_Reverse {
    meta:
        description = "SSH reverse tunnel binary for lateral movement"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1572"
    strings:
        $s1 = "-R " ascii
        $s2 = "ssh" ascii
        $s3 = "-N" ascii
        $s4 = "tunnel" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2 and ( $s3 or $s4 )
}

rule XPL_Proxychains_Binary {
    meta:
        description = "Proxychains or similar proxy chaining tool in suspicious path"
        severity = "medium"
        source = "xprotect-linux"
    strings:
        $s1 = "proxychains" ascii nocase
        $s2 = "SOCKS" ascii
        $s3 = "dynamic_chain" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2
}

rule XPL_Chisel_Tunnel {
    meta:
        description = "Chisel HTTP tunnel for bypassing firewalls"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1572"
    strings:
        $s1 = "chisel" ascii nocase
        $s2 = "reverse" ascii
        $s3 = "socks" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and 1 of ($s2*, $s3*)
}

rule XPL_Ligolo_NG_Tunnel {
    meta:
        description = "Ligolo-NG tunnel/proxy tool"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "ligolo" ascii nocase
        $s2 = "tunnel" ascii
        $s3 = "agent" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and $s3
}

rule XPL_Gost_Tunnel {
    meta:
        description = "Gost Go Simple Tunnel — HTTP/SOCKS5 proxy tunnel"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "gost" ascii nocase
        $s2 = "SOCKS5" ascii
        $s3 = "relay" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and $s2
}

rule XPL_Ncat_Listener_Backdoor {
    meta:
        description = "Ncat listener acting as persistent backdoor (eeprom exec)"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "ncat" ascii
        $s2 = "--sh-exec" ascii
        $s3 = "--keep-open" ascii
        $s4 = "-e " ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and ( $s2 or $s4 )
}

rule XPL_DNS_Exfiltration {
    meta:
        description = "Binary performing DNS-based data exfiltration"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1048.003"
    strings:
        $s1 = "dns" ascii nocase
        $s2 = "exfil" ascii nocase
        $s3 = "base64" ascii nocase
        $s4 = "subdomain" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s2 and $s3
}

rule XPL_ICMP_Exfiltration {
    meta:
        description = "Binary using ICMP tunnel for covert data exfiltration"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1048"
    strings:
        $s1 = "ICMP" ascii
        $s2 = "SOCK_RAW" ascii
        $s3 = "IPPROTO_ICMP" ascii
        $s4 = "tunnel" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and $s3
}

rule XPL_Base64_Encoded_Payload {
    meta:
        description = "Binary with large embedded base64 payload for decode-execute"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $b64 = /[A-Za-z0-9+\/]{200,}/ ascii
        $s1 = "base64" ascii nocase
        $s2 = "decode" ascii nocase
        $s3 = "system(" ascii
        $s4 = "popen(" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $b64 and 1 of ($s1*, $s2*) and 1 of ($s3*, $s4*)
}
