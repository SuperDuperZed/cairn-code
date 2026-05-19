#!/usr/bin/env python3
"""Fetch detailed PR data for euxaristia's open PRs."""
import json, time, sys, urllib.request, urllib.error

PR_LIST = [
    ("euxaristia/pcc", 10),
    ("euxaristia/adapt", 4),
    ("euxaristia/adapt", 1),
    ("euxaristia/gemini-cli", 4),
    ("euxaristia/gemini-cli", 3),
    ("euxaristia/VoxelPopuli", 2),
    ("euxaristia/tree-sitter", 1),
    ("google-gemini/gemini-cli", 26498),
    ("anomalyco/opencode", 25355),
    ("charmbracelet/glow", 937),
    ("clockworklabs/SpacetimeDB", 4773),
    ("QwenLM/qwen-code", 2838),
    ("microsoft/node-pty", 901),
]

HEADERS = {"User-Agent": "PR-Monitor-Bot/1.0", "Accept": "application/vnd.github.v3+json"}

def api_get(url, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt < retries:
                time.sleep(2)
            else:
                print(f"  HTTP {e.code} for {url}", file=sys.stderr)
                return []
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
            else:
                print(f"  Error: {e} for {url}", file=sys.stderr)
                return []

results = []
for repo, num in PR_LIST:
    key = f"{repo}#{num}"
    print(f"Fetching {key}...", flush=True)

    # PR details
    pr = api_get(f"https://api.github.com/repos/{repo}/pulls/{num}")
    if not pr or not isinstance(pr, dict):
        print(f"  SKIP (not found or rate limited)", file=sys.stderr)
        time.sleep(1)
        continue

    entry = {
        "key": key,
        "repo": repo,
        "number": num,
        "title": pr.get("title", ""),
        "url": pr.get("html_url", ""),
        "state": pr.get("state", "open"),
        "draft": pr.get("draft", False),
        "created_at": pr.get("created_at", ""),
        "updated_at": pr.get("updated_at", ""),
        "mergeable": pr.get("mergeable"),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "changed_files": pr.get("changed_files", 0),
        "labels": [l["name"] for l in pr.get("labels", [])],
        "head_sha": pr.get("head", {}).get("sha", ""),
        "author": pr.get("user", {}).get("login", ""),
        "body": (pr.get("body") or "")[:500],
        "ci_status": None,
        "ci_total": 0,
        "ci_success": 0,
        "ci_failure": 0,
        "ci_pending": 0,
        "reviews": [],
        "review_comments": [],
        "issue_comments": [],
        "commits": [],
    }

    # CI status
    sha = entry["head_sha"]
    if sha:
        status = api_get(f"https://api.github.com/repos/{repo}/commits/{sha}/status")
        if status and isinstance(status, dict):
            entry["ci_status"] = status.get("state")
            statuses = status.get("statuses", [])
            entry["ci_total"] = len(statuses)
            entry["ci_success"] = sum(1 for s in statuses if s.get("state") == "success")
            entry["ci_failure"] = sum(1 for s in statuses if s.get("state") == "failure")
            entry["ci_pending"] = sum(1 for s in statuses if s.get("state") == "pending")

    time.sleep(0.3)

    # Reviews
    reviews = api_get(f"https://api.github.com/repos/{repo}/pulls/{num}/reviews")
    if reviews and isinstance(reviews, list):
        entry["reviews"] = [{
            "id": r["id"],
            "user": r.get("user", {}).get("login", ""),
            "state": r.get("state", ""),
            "body": (r.get("body") or "")[:300],
            "submitted_at": r.get("submitted_at", ""),
        } for r in reviews]

    time.sleep(0.3)

    # Review comments
    rc = api_get(f"https://api.github.com/repos/{repo}/pulls/{num}/comments")
    if rc and isinstance(rc, list):
        entry["review_comments"] = [{
            "id": c["id"],
            "user": c.get("user", {}).get("login", ""),
            "body": (c.get("body") or "")[:200],
            "created_at": c.get("created_at", ""),
            "path": c.get("path", ""),
        } for c in rc]

    time.sleep(0.3)

    # Issue comments
    ic = api_get(f"https://api.github.com/repos/{repo}/issues/{num}/comments")
    if ic and isinstance(ic, list):
        entry["issue_comments"] = [{
            "id": c["id"],
            "user": c.get("user", {}).get("login", ""),
            "body": (c.get("body") or "")[:200],
            "created_at": c.get("created_at", ""),
        } for c in ic]

    time.sleep(0.3)

    # Commits
    commits = api_get(f"https://api.github.com/repos/{repo}/pulls/{num}/commits")
    if commits and isinstance(commits, list):
        entry["commits"] = [{
            "sha": c["sha"][:8],
            "message": (c.get("commit", {}).get("message") or "").split("\n")[0][:100],
            "date": c.get("commit", {}).get("author", {}).get("date", ""),
            "author": c.get("author", {}).get("login", "") if c.get("author") else "",
        } for c in commits]

    results.append(entry)
    print(f"  OK — {entry['labels']} | CI: {entry['ci_status']} | Reviews: {len(entry['reviews'])}", flush=True)
    time.sleep(0.5)

# Save
with open("/home/z/my-project/pr_data.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nDone. {len(results)} PRs saved to pr_data.json")
