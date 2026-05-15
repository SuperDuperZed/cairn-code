#!/usr/bin/env python3
"""NPM Dependency Vulnerability Monitor for euxaristia"""
import json, urllib.request, time, sys

def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Vuln-Monitor/1.0", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except:
        return None

# Load dependency list
with open("/home/z/my-project/dep_data.json") as f:
    dep_data = json.load(f)
all_pkgs = dep_data["all_packages"]

# Load baseline
try:
    with open("/home/z/my-project/vuln_baseline.json") as f:
        baseline_data = json.load(f)
    known = set(baseline_data["known_advisories"].keys())
except:
    known = set()

# Priority packages to check (most commonly exploited)
priority = [
    "axios", "node-pty", "@lydell/node-pty", "express", "ws", "marked", "turndown",
    "semver", "lodash-es", "execa", "cross-spawn", "undici", "xss", "yaml",
    "chalk", "glob", "yargs", "commander", "zod", "sharp", "esbuild",
    "react", "react-dom", "@anthropic-ai/sdk", "@modelcontextprotocol/sdk",
    "nan", "minimatch", "https-proxy-agent", "simple-git", "duck-duck-scrape",
    "sst", "ink", "qrcode", "shell-quote", "fflate", "proper-lockfile",
    "@mendable/firecrawl-js", "@growthbook/growthbook", "@grpc/grpc-js",
    "domexception", "google-auth-library", "@aws-sdk/client-s3", "node-gyp",
    "msw", "node-fetch-native", "react-compiler-runtime",
]
# Add any package with high-risk keywords
for pkg in all_pkgs:
    for kw in ["auth", "crypto", "ssh", "tls", "token", "session", "cookie", "password", "serialize", "eval", "exec", "spawn", "child_process", "fetch", "http", "request"]:
        if kw in pkg.lower() and pkg not in priority:
            priority.append(pkg)
            break

priority = list(set(priority))

# Check advisories
new_vulns = []
for pkg in priority:
    query = pkg.replace("/", "%2F")
    url = f"https://api.github.com/advisories?ecosystem=npm&affects={query}&per_page=5"
    result = api(url)
    if isinstance(result, list):
        for adv in result:
            ghsa_id = adv.get("ghsa_id", "")
            severity = adv.get("severity", "")
            if severity in ("critical", "high") and ghsa_id not in known:
                new_vulns.append({
                    "package": pkg,
                    "ghsa_id": ghsa_id,
                    "cve_id": adv.get("cve_id", ""),
                    "severity": severity,
                    "summary": adv.get("summary", ""),
                    "published_at": adv.get("published_at", ""),
                    "url": adv.get("html_url", ""),
                })
    time.sleep(0.3)

if new_vulns:
    new_vulns.sort(key=lambda x: (0 if x["severity"]=="critical" else 1, x["published_at"]), reverse=True)
    with open("/home/z/my-project/vuln_new_alert.json", "w") as f:
        json.dump({"found": len(new_vulns), "vulnerabilities": new_vulns}, f, indent=2)
    print(f"ALERT: {len(new_vulns)} new critical/high vulnerabilities found!")
    for v in new_vulns:
        print(f"  [{v['severity'].upper()}] {v['package']}: {v['summary'][:100]} ({v['cve_id'] or v['ghsa_id']})")
else:
    # Update baseline timestamp
    with open("/home/z/my-project/vuln_baseline.json", "w") as f:
        json.dump({
            "last_checked": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "known_advisories": {k: v for k, v in zip(known, [time.strftime("%Y-%m-%dT%H:%M:%SZ")]*len(known))} if known else {},
        }, f, indent=2)
    print("No new vulnerabilities found.")
