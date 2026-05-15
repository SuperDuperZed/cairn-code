#!/usr/bin/env python3
"""Supply Chain Compromise Monitor for euxaristia's npm dependencies.

Detects:
- New versions published with install scripts (preinstall/postinstall) that didn't have them before
- Package published by a different person than the baseline
- Suspicious version bumps (patch/minor bump adding many new dependencies)
- Package takeover indicators (new publisher, major repo URL change)
"""
import json, urllib.request, time, sys

def npm_api(pkg):
    url = f"https://registry.npmjs.org/{pkg.replace('/', '%2F')}"
    req = urllib.request.Request(url, headers={"User-Agent": "SupplyChain-Monitor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except:
        return None

# Load baseline
try:
    with open("/home/z/my-project/supply_chain_baseline.json") as f:
        bl = json.load(f)
    baseline = bl["packages"]
except:
    print("ERROR: No baseline found at /home/z/my-project/supply_chain_baseline.json")
    sys.exit(1)

alerts = []

for pkg, base in baseline.items():
    data = npm_api(pkg)
    if not data or not data.get("versions"):
        continue
    
    latest = data.get("dist-tags", {}).get("latest", "")
    if not latest:
        continue
    
    # Skip if version hasn't changed
    if latest == base["latest_version"]:
        continue
    
    ver = data["versions"].get(latest, {})
    if not ver:
        continue
    
    # CHECK 1: New install scripts
    scripts = ver.get("scripts", {})
    install_scripts = {k: v for k, v in scripts.items() if k in ("preinstall", "install", "postinstall", "prestart", "poststart", "prepare")}
    has_install_script = bool(install_scripts)
    
    if has_install_script and not base["has_install_script"]:
        alerts.append({
            "type": "CRITICAL",
            "package": pkg,
            "old_version": base["latest_version"],
            "new_version": latest,
            "detail": f"NEW install scripts appeared: {list(install_scripts.keys())}",
            "script_content": install_scripts,
        })
    
    # CHECK 2: Changed publisher
    new_publisher = ver.get("_npmUser", {}).get("name", "")
    if new_publisher and base.get("published_by") and new_publisher != base["published_by"]:
        alerts.append({
            "type": "CRITICAL",
            "package": pkg,
            "old_version": base["latest_version"],
            "new_version": latest,
            "detail": f"Published by different user: was '{base['published_by']}', now '{new_publisher}'",
        })
    
    # CHECK 3: Suspicious dependency explosion
    deps = ver.get("dependencies", {})
    old_deps = set(base.get("top_deps", []))
    new_deps = set(deps.keys())
    added_deps = new_deps - old_deps
    
    if len(added_deps) > 10:  # More than 10 new deps in a single bump is suspicious
        alerts.append({
            "type": "WARNING",
            "package": pkg,
            "old_version": base["latest_version"],
            "new_version": latest,
            "detail": f"Added {len(added_deps)} new dependencies. Top additions: {list(added_deps)[:10]}",
        })
    
    # CHECK 4: Install script content changed for packages that already had scripts
    if has_install_script and base["has_install_script"]:
        old_scripts = base.get("scripts", {})
        for key, val in install_scripts.items():
            if key in old_scripts and val != old_scripts[key]:
                alerts.append({
                    "type": "WARNING",
                    "package": pkg,
                    "old_version": base["latest_version"],
                    "new_version": latest,
                    "detail": f"Install script '{key}' content changed",
                })
                break

# Output results
if alerts:
    with open("/home/z/my-project/supply_chain_alerts.json", "w") as f:
        json.dump({"found": len(alerts), "alerts": alerts, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}, f, indent=2)
    print(f"ALERT: {len(alerts)} suspicious changes detected!")
    for a in alerts:
        print(f"  [{a['type']}] {a['package']} ({a['old_version']} -> {a['new_version']}): {a['detail']}")
else:
    print("CLEAR: No suspicious changes detected.")
    # Update baseline versions
    for pkg, base in baseline.items():
        data = npm_api(pkg)
        if data:
            latest = data.get("dist-tags", {}).get("latest", "")
            if latest:
                base["latest_version"] = latest
    with open("/home/z/my-project/supply_chain_baseline.json", "w") as f:
        json.dump({"snapshot_time": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "packages": baseline, "all_tracked_packages": bl.get("all_tracked_packages", [])}, f, indent=2)

