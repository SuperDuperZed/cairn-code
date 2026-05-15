import json, urllib.request, time, sys

def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "PR-Monitor/1.0", "Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)}

prs = [
    ("euxaristia/videre", 4),
    ("euxaristia/pcc", 8),
    ("euxaristia/colt", 6),
    ("euxaristia/gemini-cli", 4),
    ("euxaristia/gemini-cli", 3),
    ("euxaristia/gitee-cli", 2),
    ("euxaristia/adapt", 1),
    ("euxaristia/colt", 5),
    ("euxaristia/colt", 4),
    ("google-gemini/gemini-cli", 26498),
    ("anomalyco/opencode", 25355),
    ("euxaristia/VoxelPopuli", 4),
    ("euxaristia/colt", 3),
    ("charmbracelet/glow", 937),
    ("euxaristia/VoxelPopuli", 2),
    ("euxaristia/colt", 1),
    ("euxaristia/tree-sitter", 1),
    ("euxaristia/dotfiles", 1),
    ("clockworklabs/SpacetimeDB", 4773),
    ("QwenLM/qwen-code", 2838),
    ("microsoft/node-pty", 901),
]

results = []
for repo, num in prs:
    key = f"{repo}#{num}"
    detail = api(f"https://api.github.com/repos/{repo}/pulls/{num}")
    if "_error" in detail:
        print(f"ERROR {key}: {detail['_error']}", file=sys.stderr)
        time.sleep(2)
        continue
    
    sha = detail.get("head", {}).get("sha", "")
    reviews = api(f"https://api.github.com/repos/{repo}/pulls/{num}/reviews")
    comments = api(f"https://api.github.com/repos/{repo}/issues/{num}/comments")
    commits = api(f"https://api.github.com/repos/{repo}/pulls/{num}/commits")
    rev_comments = api(f"https://api.github.com/repos/{repo}/pulls/{num}/comments")
    status = api(f"https://api.github.com/repos/{repo}/commits/{sha}/status") if sha else {}
    
    pr_data = {
        "key": key, "repo": repo, "number": num,
        "title": detail.get("title", ""),
        "url": detail.get("html_url", ""),
        "state": detail.get("state", ""),
        "draft": detail.get("draft", False),
        "created_at": detail.get("created_at", ""),
        "updated_at": detail.get("updated_at", ""),
        "mergeable": detail.get("mergeable"),
        "additions": detail.get("additions", 0),
        "deletions": detail.get("deletions", 0),
        "changed_files": detail.get("changed_files", 0),
        "labels": [l["name"] for l in detail.get("labels", [])],
        "head_sha": sha,
        "ci_status": status.get("state", "unknown") if not "_error" in status else "unknown",
        "ci_total": status.get("total_count", 0) if not "_error" in status else 0,
        "reviews": reviews if isinstance(reviews, list) else [],
        "issue_comments": comments if isinstance(comments, list) else [],
        "commits": commits if isinstance(commits, list) else [],
        "review_comments": rev_comments if isinstance(rev_comments, list) else [],
    }
    results.append(pr_data)
    print(f"Fetched {key} (+{pr_data['additions']}/-{pr_data['deletions']}, {len(pr_data['reviews'])} rev, {len(pr_data['issue_comments'])} ic)", file=sys.stderr)
    time.sleep(1.5)

with open("/home/z/my-project/pr_data.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nDone. {len(results)} PRs saved.", file=sys.stderr)
