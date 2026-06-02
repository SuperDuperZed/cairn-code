// xprotect-linux — test detection signatures
// These rules exist solely for automated verification that the daemon
// correctly intercepts, scans, and blocks malicious execution.

rule XPL_Test_Detection {
	meta:
		description = "Test signature — verify detection pipeline end-to-end"
		severity    = "test"
		source      = "xprotect-linux-test"
	strings:
		$s1 = "XPROTECT_MALWARE_TEST_SIG_2024" ascii
		$s2 = "XPROTECT_MALWARE_TEST_SIG_2024" wide
	condition:
		any of them
}

rule XPL_Test_EICAR_Like {
	meta:
		description = "EICAR-variant test signature for scanner validation"
		severity    = "test"
		source      = "xprotect-linux-test"
	strings:
		$s1 = "XPROTECT_EICAR_TEST_FILE" ascii
	condition:
		$s1 at 0
}
