// xprotect-linux — credential harvesting tool detection
// Covers: password dumpers, SSH key stealers, browser credential extractors,
// and tooling for hash harvesting from memory.

rule XPL_Mimipy_Linux {
    meta:
        description = "Mimipy — Linux memory-based password dumper"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1003.001"
    strings:
        $s1 = "mimipy" ascii nocase
        $s2 = "/proc/" ascii
        $s3 = "maps" ascii
        $s4 = "grep password" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2
}

rule XPL_Lazagne_Linux {
    meta:
        description = "LaZagne — local credential harvester for Linux"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "LaZagne" ascii
        $s2 = "lazagne" ascii nocase
        $s3 = "credential" ascii
        $s4 = "password" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        ( $s1 or $s2 ) and $s3
}

rule XPL_SSH_Key_Scraper {
    meta:
        description = "Binary that harvests SSH private keys from user directories"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1552.004"
    strings:
        $s1 = "/.ssh/id_rsa" ascii
        $s2 = "/.ssh/id_ed25519" ascii
        $s3 = "/.ssh/id_ecdsa" ascii
        $s4 = "-----BEGIN" ascii
        $s5 = "OPENSSH" ascii
        $s6 = "PRIVATE KEY" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        2 of ($s1*, $s2*, $s3*) and ( $s4 or $s5 )
}

rule XPL_Known_Hosts_Stealer {
    meta:
        description = "Binary that reads SSH known_hosts for pivot targets"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "/.ssh/known_hosts" ascii
        $s2 = "ssh-rsa" ascii
        $s3 = "ssh-ed25519" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and 1 of ($s2*, $s3*)
}

rule XPL_Browser_Credential_Extract {
    meta:
        description = "Browser credential/cookie extractor (Chrome, Firefox)"
        severity = "high"
        source = "xprotect-linux"
    reference = "ATT&CK T1555.003"
    strings:
        $s1 = "/.config/google-chrome" ascii
        $s2 = "/.mozilla/firefox" ascii
        $s3 = "Login Data" ascii
        $s4 = "key4.db" ascii
        $s5 = "cookies" ascii
        $s6 = "logins.json" ascii
        $s7 = "decrypt" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        1 of ($s1*, $s2*) and 2 of ($s3*, $s4*, $s5*, $s6*, $s7*)
}

rule XPL_GPG_Key_Extract {
    meta:
        description = "Binary that extracts GPG private keys"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "/.gnupg" ascii
        $s2 = "secring" ascii
        $s3 = "private-keys" ascii
        $s4 = "gpg --export-secret" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and 1 of ($s2*, $s3*, $s4*)
}

rule XPL_AWS_Credential_Stealer {
    meta:
        description = "AWS credential harvester — reads ~/.aws/credentials and env vars"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "/.aws/credentials" ascii
        $s2 = "aws_access_key_id" ascii
        $s3 = "aws_secret_access_key" ascii
        $s4 = "AWS_SESSION_TOKEN" ascii
        $s5 = "AWS_ACCESS_KEY" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        1 of ($s1*) or ( 1 of ($s2*, $s3*) and 1 of ($s4*, $s5*) )
}

rule XPL_GCP_Service_Account_Stealer {
    meta:
        description = "GCP service account key harvester"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "application_default_credentials.json" ascii
        $s2 = "service_account" ascii
        $s3 = "private_key" ascii
        $s4 = "client_email" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s2 and $s3
}

rule XPL_Memory_Hash_Dump {
    meta:
        description = "Binary that dumps process memory for hash extraction"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "/proc/" ascii
        $s2 = "/mem" ascii
        $s3 = "ptrace" ascii
        $s4 = "PTRACE_ATTACH" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and $s3
}

rule XPL_Kerberos_Ticket_Extract {
    meta:
        description = "Kerberos ticket extractor (kirbi/ccache harvesting)"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "/tmp/krb5cc_" ascii
        $s2 = "/tmp/krb5ccache" ascii
        $s3 = "krb5" ascii
        $s4 = "ccache" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s3 and 1 of ($s1*, $s2*, $s4*)
}
