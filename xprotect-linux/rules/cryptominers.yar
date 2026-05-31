// xprotect-linux — cryptominer detection signatures
// Covers: XMRig, xmrig-proxy, CNRig, SRBMiner, TeamRedMiner, T-Rex, NBMiner,
// lolMiner, PhoenixMiner, crypto-looting tools, and pool configuration patterns.

rule XPL_XMRig_Miner_Full {
    meta:
        description = "XMRig Monero miner — stratum + config patterns"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1496"
        mitre = "Cryptocurrency Mining"
    strings:
        $s1 = "stratum+tcp://" ascii
        $s2 = "donate-level" ascii
        $s3 = "randomx" ascii nocase
        $s4 = "xmrig" ascii nocase
        $s5 = "pool.mineropt" ascii nocase
        $s6 = "cryptonight" ascii nocase
        $s7 = "moneroero" ascii nocase
        $s8 = "XMRig/" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        3 of ($s1*, $s2*, $s3*, $s4*, $s5*, $s6*, $s7*, $s8*)
}

rule XPL_XMRig_Proxy {
    meta:
        description = "XMRig-proxy — proxy layer for mining pool obfuscation"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "xmrig-proxy" ascii nocase
        $s2 = "stratum+tcp://" ascii
        $s3 = "bind" ascii
        $s4 = "keepalive" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2
}

rule XPL_CNRig {
    meta:
        description = "CNRig — CryptoNight (Monero/Bytecoin) miner"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "cnrig" ascii nocase
        $s2 = "CryptoNight" ascii
        $s3 = "stratum+tcp://" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        2 of them
}

rule XPL_SRBMiner {
    meta:
        description = "SRBMiner — multi-algo crypto miner"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "SRBMiner" ascii
        $s2 = "stratum+tcp://" ascii
        $s3 = "pool_use_tls" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        2 of them
}

rule XPL_TeamRedMiner {
    meta:
        description = "TeamRedMiner — AMD GPU crypto miner"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "TeamRedMiner" ascii
        $s2 = "stratum+tcp://" ascii
        $s3 = "OpenCL" ascii
    condition:
        uint16(0) == 0x457f and filesize < 30MB and
        $s1 and $s2
}

rule XPL_Trex_Miner {
    meta:
        description = "T-Rex NVIDIA crypto miner"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "T-Rex" ascii
        $s2 = "NVIDIA" ascii
        $s3 = "stratum+tcp://" ascii
        $s4 = "cuda" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 30MB and
        $s1 and $s3
}

rule XPL_NBMiner {
    meta:
        description = "NBMiner — multi-currency GPU miner"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "NBMiner" ascii
        $s2 = "stratum+tcp://" ascii
        $s3 = "nicehash" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 30MB and
        $s1 and $s2
}

rule XPL_LolMiner {
    meta:
        description = "lolMiner — multi-algo Equihash/Ethash miner"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "lolMiner" ascii
        $s2 = "stratum+tcp://" ascii
        $s3 = "worker" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        $s1 and $s2
}

rule XPL_PhoenixMiner {
    meta:
        description = "PhoenixMiner — Ethash/ProgPoW miner"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "Phoenix Miner" ascii
        $s2 = "PhoenixMiner" ascii
        $s3 = "ethash" ascii nocase
        $s4 = "stratum+tcp://" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        ( $s1 or $s2 ) and $s4
}

rule XPL_Hidden_Miner_Generic {
    meta:
        description = "Generic hidden miner — common pool strings in suspicious paths"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "stratum+tcp://" ascii
        $s2 = "stratum+ssl://" ascii
        $s3 = "pool." ascii
        $s4 = "worker" ascii
        $s5 = "wallet" ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        filename matches /^\/(tmp|dev\/shm|var\/tmp|\.hidden)\/.*/ and
        2 of ($s1*, $s2*) and 2 of ($s3*, $s4*, $s5*)
}

rule XPL_Crypto_Looter_Wallet_Steal {
    meta:
        description = "Cryptocurrency wallet stealer — targets wallet.dat, keystore files"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "wallet.dat" ascii
        $s2 = "keystore" ascii
        $s3 = "/.bitcoin/" ascii
        $s4 = "/.monero/" ascii
        $s5 = "/.ethereum/" ascii
        $s6 = "UTC--" ascii  // Ethereum keystore prefix
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        2 of ($s1*, $s2*, $s6*) and 1 of ($s3*, $s4*, $s5*)
}

rule XPL_Miner_Process_Spoof {
    meta:
        description = "Miner with process name spoofing to mask as legitimate service"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "prctl(PR_SET_NAME" ascii
        $s2 = "stratum+tcp://" ascii
        $s3 = "kworker" ascii  // common spoof target
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2
}
