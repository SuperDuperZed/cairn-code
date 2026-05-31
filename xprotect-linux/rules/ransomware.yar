// xprotect-linux — Linux ransomware detection
// Covers: file encryption patterns, ransom notes, encryption APIs in suspicious
// binaries, and known Linux ransomware families.

rule XPL_Ransomware_Generic_Encrypt {
    meta:
        description = "Binary that recursively encrypts files (AES+RSA pattern)"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1486"
    strings:
        $s1 = "EVP_EncryptInit" ascii
        $s2 = "EVP_EncryptUpdate" ascii
        $s3 = "EVP_EncryptFinal" ascii
        $s4 = "AES" ascii
        $s5 = "RSA" ascii
        $s6 = ".encrypted" ascii
        $s7 = "RECOVER" ascii
        $s8 = "DECRYPT" ascii
        $s9 = ".README" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        2 of ($s1*, $s2*, $s3*) and
        1 of ($s4*, $s5*) and
        1 of ($s6*, $s7*, $s8*, $s9*)
}

rule XPL_Ransomware_File_Walk {
    meta:
        description = "Binary that walks filesystem recursively and writes encrypted output"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "opendir" ascii
        $s2 = "readdir" ascii
        $s3 = "fopen(" ascii
        $s4 = "fwrite(" ascii
        $s5 = ".encrypted" ascii
        $s6 = ".locked" ascii
        $s7 = ".cry" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2 and $s3 and $s4 and 1 of ($s5*, $s6*, $s7*)
}

rule XPL_Ransomware_Ransom_Note {
    meta:
        description = "Binary that drops ransom payment instructions"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "Your files have been encrypted" ascii
        $s2 = "pay the ransom" ascii nocase
        $s3 = "bitcoin" ascii nocase
        $s4 = "RECOVER-FILES" ascii nocase
        $s5 = "decrypt" ascii nocase
        $s6 = "restore" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and ( $s2 or $s3 ) and 1 of ($s4*, $s5*, $s6*)
}

rule XPL_Ransomware_Chacha20_Encrypt {
    meta:
        description = "Binary using ChaCha20 for file encryption (common in Linux ransomware)"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "chacha" ascii nocase
        $s2 = "encrypt" ascii nocase
        $s3 = "fread(" ascii
        $s4 = "fwrite(" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2 and $s3 and $s4
}

rule XPL_Ransomware_Setsid_Detach {
    meta:
        description = "Ransomware that daemonizes via setsid/fork to run in background"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "setsid" ascii
        $s2 = "fork" ascii
        $s3 = "chdir(" ascii
        $s4 = "close(" ascii
        $s5 = "encrypt" ascii nocase
        $s6 = ".encrypted" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2 and $s5 and $s6
}

rule XPL_Ransomware_Target_Database {
    meta:
        description = "Ransomware specifically targeting database files"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = ".sql" ascii
        $s2 = ".db" ascii
        $s3 = ".mdb" ascii
        $s4 = "encrypt" ascii nocase
        $s5 = "truncate" ascii
        $s6 = "EVP_" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        2 of ($s1*, $s2*, $s3*) and ( $s4 or $s6 )
}

rule XPL_Ransomware_Backup_Wipe {
    meta:
        description = "Binary that deletes backups before encryption"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "unlink(" ascii
        $s2 = "remove(" ascii
        $s3 = ".bak" ascii
        $s4 = ".backup" ascii
        $s5 = ".tar.gz" ascii
        $s6 = ".snapshot" ascii
        $s7 = "encrypt" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s7 and 1 of ($s3*, $s4*, $s5*, $s6*)
}
