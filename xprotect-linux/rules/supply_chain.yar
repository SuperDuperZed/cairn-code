// xprotect-linux — supply chain compromise and trojanized package detection
// Covers: typosquat indicators, common compromised npm/pip/go binary paths,
// and binary repackaging/redirection patterns.

rule XPL_Npm_Malicious_Binary {
    meta:
        description = "Suspicious binary in node_modules or npm cache with network capability"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1195.002"
    strings:
        $s1 = "node_modules" ascii
        $s2 = "child_process" ascii
        $s3 = "require(" ascii
        $s4 = "http.request" ascii
        $s5 = "os.hostname" ascii
        $s6 = "os.userInfo" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        filename matches /.*node_modules\/.*/ and
        $s2 and 1 of ($s4*, $s5*, $s6*)
}

rule XPL_Pip_Install_Trojan {
    meta:
        description = "Compiled Python binary with post-install data exfiltration"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "setup.py" ascii
        $s2 = "install_requires" ascii
        $s3 = "requests" ascii
        $s4 = "urllib" ascii
        $s5 = "b64decode" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and 1 of ($s3*, $s4*) and 1 of ($s3*, $s4*, $s5*)
}

rule XPL_Go_Mod_Proxy_Hijack {
    meta:
        description = "Go binary with suspicious proxy/mod replacement patterns"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "GOPROXY" ascii
        $s2 = "gomod" ascii
        $s3 = "replace" ascii
        $s4 = "=> " ascii
    condition:
        uint16(0) == 0x457f and filesize < 20MB and
        $s1 and $s3
}

rule XPL_GPG_Signature_Strip {
    meta:
        description = "Binary that strips GPG signatures from packages"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "gpg" ascii
        $s2 = "--delete-signature" ascii
        $s3 = "--detach-sign" ascii
        $s4 = "debsig" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and 1 of ($s2*, $s3*, $s4*)
}

rule XPL_Deb_Rpm_Repack {
    meta:
        description = "Binary that repackages .deb/.rpm with malicious payload"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "ar " ascii
        $s2 = "control.tar" ascii
        $s3 = "data.tar" ascii
        $s4 = "debian-binary" ascii
        $s5 = "postinst" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s2 and $s3 and $s5
}

rule XPL_Python_Pip_Modified_Install {
    meta:
        description = "Modified pip that injects code during package installation"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "pip" ascii
        $s2 = "install" ascii
        $s3 = "setup.py" ascii
        $s4 = "os.system" ascii
        $s5 = "post-install" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and $s3 and $s4
}

rule XPL_Apt_Get_Modified {
    meta:
        description = "Modified apt-get/apt that injects code during package management"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "apt-get" ascii
        $s2 = "DPkg::Pre-Install-Pkgs" ascii
        $s3 = "DPkg::Post-Invoke" ascii
        $s4 = "APT::Update::Pre-Invoke" ascii
        $s5 = "Exec" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and 1 of ($s2*, $s3*, $s4*)
}

rule XPL_Compromised_Source_DL {
    meta:
        description = "Binary that downloads and executes code from suspicious sources"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "wget " ascii
        $s2 = "curl " ascii
        $s3 = "chmod +x" ascii
        $s4 = "/tmp/" ascii
        $s5 = "| sh" ascii
        $s6 = "| bash" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        ( $s1 or $s2 ) and $s3 and $s4 and ( $s5 or $s6 )
}

rule XPL_Supply_Chain_Typosquat {
    meta:
        description = "Binary installed from typosquatted package name path"
        severity = "medium"
        source = "xprotect-linux"
    strings:
        // Common typosquat targets
        $s1 = "npmm" ascii
        $s2 = "pypp" ascii
        $s3 = "golang" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        filename matches /.*(npmm|pypp|golang-org).*/ nocase
}
