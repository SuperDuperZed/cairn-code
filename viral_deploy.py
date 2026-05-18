#!/usr/bin/env python3
"""Deploy a single HTML project to GitHub Pages via the GitHub API."""
import sys, os, json, base64, time, subprocess

GITHUB_USER = "SuperDuperZed"
TOKEN_FILE = "/home/z/my-project/.github_creds.json"

def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f).get("token", "")
    env_token = os.environ.get("GITHUB_TOKEN", "")
    if env_token:
        return env_token
    return ""

def api(method, path, body=None, token=""):
    import urllib.request, urllib.error
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "viral-engine")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        if resp.status in (200, 201, 204):
            if resp.status == 204:
                return {}
            return json.loads(resp.read())
        return {"status": resp.status}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.fp else ""
        return {"status": e.code, "error": err_body}

def deploy(repo_slug, html_dir, description, token):
    repo_name = repo_slug.strip().lower()
    print(f"[deploy] Creating repo: {GITHUB_USER}/{repo_name}")
    
    r = api("POST", f"/user/repos", {
        "name": repo_name,
        "description": description,
        "homepage": f"https://{GITHUB_USER.lower()}.github.io/{repo_name}/",
        "auto_init": False,
        "private": False
    }, token)
    
    if "id" not in r and "status" in r:
        # might already exist
        print(f"[deploy] Repo creation returned: {r.get('status')} {r.get('message','')}")
        r = api("GET", f"/repos/{GITHUB_USER}/{repo_name}", token=token)
        if "id" not in r:
            return False, f"Cannot create/access repo: {r}"
    
    print(f"[deploy] Repo ready: {r.get('html_url','?')}")
    
    # Read index.html
    html_path = os.path.join(html_dir, "index.html")
    if not os.path.exists(html_path):
        return False, f"No index.html at {html_path}"
    with open(html_path, "rb") as f:
        html_content = base64.b64encode(f.read()).decode()
    
    # Try to commit via API
    import urllib.request
    # Get default branch
    repo_info = api("GET", f"/repos/{GITHUB_USER}/{repo_name}", token=token)
    branch = repo_info.get("default_branch", "main")
    
    # Check if there's an existing file to get SHA
    existing = api("GET", f"/repos/{GITHUB_USER}/{repo_name}/contents/index.html?ref={branch}", token=token)
    sha = existing.get("sha") if "sha" in existing else None
    
    r = api("PUT", f"/repos/{GITHUB_USER}/{repo_name}/contents/index.html", {
        "message": "deploy viral experiment",
        "content": html_content,
        "branch": branch,
        "sha": sha
    }, token)
    
    if "commit" not in r:
        # Try with git
        print("[deploy] API commit failed, trying git...")
        return deploy_git(repo_name, html_dir, description, token)
    
    print(f"[deploy] File committed via API")
    
    # Enable GitHub Pages
    pages = api("POST", f"/repos/{GITHUB_USER}/{repo_name}/pages", {
        "source": {"branch": branch, "path": "/"},
        "build_type": "legacy"
    }, token)
    
    live_url = f"https://{GITHUB_USER.lower()}.github.io/{repo_name}/"
    print(f"[deploy] Pages enabled: {live_url}")
    
    return True, live_url

def deploy_git(repo_name, html_dir, description, token):
    """Fallback: clone, commit, push via git."""
    tmp = f"/tmp/viral-{repo_name}-{int(time.time())}"
    repo_url = f"https://{token}@github.com/{GITHUB_USER}/{repo_name}.git"
    
    os.makedirs(tmp, exist_ok=True)
    try:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, tmp], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        subprocess.run(["git", "clone", repo_url, tmp], capture_output=True, check=False)
    
    # Copy index.html
    import shutil
    shutil.copy2(os.path.join(html_dir, "index.html"), os.path.join(tmp, "index.html"))
    
    subprocess.run(["git", "-C", tmp, "add", "index.html"], capture_output=True)
    subprocess.run(["git", "-C", tmp, "commit", "-m", "deploy viral experiment"], capture_output=True)
    subprocess.run(["git", "-C", tmp, "push", "origin", "HEAD"], capture_output=True)
    
    # Enable pages via API
    import urllib.request
    repo_info = api("GET", f"/repos/{GITHUB_USER}/{repo_name}", token=token)
    branch = repo_info.get("default_branch", "main")
    api("POST", f"/repos/{GITHUB_USER}/{repo_name}/pages", {
        "source": {"branch": branch, "path": "/"},
        "build_type": "legacy"
    }, token)
    
    shutil.rmtree(tmp, ignore_errors=True)
    
    live_url = f"https://{GITHUB_USER.lower()}.github.io/{repo_name}/"
    return True, live_url

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: viral_deploy.py <repo-slug> <html-dir> [--desc <description>]")
        sys.exit(1)
    
    repo_slug = sys.argv[1]
    html_dir = sys.argv[2]
    desc = ""
    for i, arg in enumerate(sys.argv):
        if arg == "--desc" and i+1 < len(sys.argv):
            desc = sys.argv[i+1]
    
    token = get_token()
    if not token:
        print("[deploy] ERROR: No GitHub token found. Set GITHUB_TOKEN env or add .github_creds.json")
        sys.exit(1)
    
    ok, result = deploy(repo_slug, html_dir, desc, token)
    if ok:
        print(f"SUCCESS: {result}")
    else:
        print(f"FAILED: {result}")
        sys.exit(1)
