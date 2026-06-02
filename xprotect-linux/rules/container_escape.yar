// xprotect-linux — container escape and Docker/Kubernetes attack detection
// Covers: container breakout, K8s API abuse, pod privilege escalation,
// and suspicious binaries in container-like environments.

rule XPL_Docker_Socket_Abuse {
    meta:
        description = "Binary that communicates with Docker socket for container escape"
        severity = "critical"
        source = "xprotect-linux"
        reference = "ATT&CK T1611"
    strings:
        $s1 = "/var/run/docker.sock" ascii
        $s2 = "/run/docker.sock" ascii
        $s3 = "POST /containers" ascii
        $s4 = "HostConfig" ascii
        $s5 = "Privileged" ascii
        $s6 = "Binds" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        ( $s1 or $s2 ) and 1 of ($s3*, $s4*, $s5*, $s6*)
}

rule XPL_Cgroups_Release_Agent_Escape {
    meta:
        description = "Container escape via cgroups notify_on_release + release_agent"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "release_agent" ascii
        $s2 = "notify_on_release" ascii
        $s3 = "/sys/fs/cgroup" ascii
        $s4 = "cgroups" ascii
        $s5 = "nsenter" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s2 and ( $s3 or $s4 )
}

rule XPL_Kubernetes_API_Access {
    meta:
        description = "Binary accessing Kubernetes API server (pod/service account abuse)"
        severity = "high"
        source = "xprotect-linux"
        reference = "ATT&CK T1078.004"
    strings:
        $s1 = "kubernetes" ascii nocase
        $s2 = "/var/run/secrets/kubernetes.io" ascii
        $s3 = "/api/v1/" ascii
        $s4 = "Bearer " ascii
        $s5 = "serviceaccount" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        ( $s2 or $s5 ) and ( $s3 or $s4 )
}

rule XPL_Kubeconfig_Exfil {
    meta:
        description = "Binary that reads kubeconfig for cluster credential theft"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = ".kube/config" ascii
        $s2 = "certificate-authority-data" ascii
        $s3 = "client-certificate-data" ascii
        $s4 = "client-key-data" ascii
        $s5 = "cluster" ascii
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and 2 of ($s2*, $s3*, $s4*, $s5*)
}

rule XPL_Container_Mount_HostFS {
    meta:
        description = "Binary that mounts host filesystem from inside container"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "mount(" ascii
        $s2 = "/host" ascii
        $s3 = "/rootfs" ascii
        $s4 = "MS_BIND" ascii
        $s5 = "chroot" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and ( $s2 or $s3 ) and $s5
}

rule XPL_Cap_Dropped_Binary {
    meta:
        description = "Container breakout exploiting dropped capabilities"
        severity = "high"
        source = "xprotect-linux"
    strings:
        $s1 = "CAP_SYS_PTRACE" ascii
        $s2 = "CAP_SYS_ADMIN" ascii
        $s3 = "CAP_DAC_READ_SEARCH" ascii
        $s4 = "ptrace" ascii
        $s5 = "/proc/1/ns" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s4 and $s5
}

rule XPL_Etcd_Secret_Dump {
    meta:
        description = "Binary that dumps secrets from Kubernetes etcd"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "etcdctl" ascii nocase
        $s2 = "/secrets/" ascii
        $s3 = "get" ascii
        $s4 = " --prefix" ascii
    condition:
        uint16(0) == 0x457f and filesize < 15MB and
        $s1 and $s2
}

rule XPL_Cloud_Metadata_Request {
    meta:
        description = "Binary querying cloud instance metadata for credential theft"
        severity = "high"
        source = "xprotect-linux"
        strings:
        $s1 = "169.254.169.254" ascii
        $s2 = "metadata" ascii
        $s3 = "aws" ascii nocase
        $s4 = "gcp" ascii nocase
        $s5 = "azure" ascii nocase
    condition:
        uint16(0) == 0x457f and filesize < 10MB and
        $s1 and $s2
}

rule XPL_Namespace_Escape {
    meta:
        description = "Binary exploiting Linux namespaces for container escape"
        severity = "critical"
        source = "xprotect-linux"
    strings:
        $s1 = "unshare(" ascii
        $s2 = "CLONE_NEWNS" ascii
        $s3 = "CLONE_NEWUSER" ascii
        $s4 = "pivot_root" ascii
        $s5 = "nsenter" ascii
    condition:
        uint16(0) == 0x457f and filesize < 5MB and
        $s1 and $s4
}
