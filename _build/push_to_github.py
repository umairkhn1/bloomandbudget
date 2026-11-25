#!/usr/bin/env python3
"""Push the built site to GitHub via the REST Git Data API.

The sandbox's git protocol is unreliable (verified earlier: push "succeeds"
but commits never reach real GitHub), so this creates blobs, a tree on top of
the current one, a commit, and updates the branch ref. Then it verifies.

Usage: GITHUB_ACCESS_TOKEN=... python3 push_to_github.py
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "umairkhn1"
REPO = "bloomandbudget"
BRANCH = "main"
SITE = Path(__file__).resolve().parent.parent
TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN", "")

if not TOKEN:
    sys.exit("GITHUB_ACCESS_TOKEN is not set")

API = f"https://api.github.com/repos/{OWNER}/{REPO}"

# Never push local junk or files we deliberately leave alone.
SKIP_DIRS = {".git", "docs", "node_modules", "__pycache__"}
SKIP_NAMES = {".DS_Store", "Thumbs.db"}


def call(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            body = res.read().decode()
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as err:
        detail = err.read().decode()[:600]
        raise SystemExit(f"{method} {url} -> {err.code}\n{detail}")


def collect():
    files = []
    for path in sorted(SITE.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(SITE)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name in SKIP_NAMES:
            continue
        files.append((rel.as_posix(), path))
    return files


def main():
    ref = call("GET", f"{API}/git/ref/heads/{BRANCH}")
    head_sha = ref["object"]["sha"]
    head = call("GET", f"{API}/git/commits/{head_sha}")
    base_tree = head["tree"]["sha"]
    print(f"head {head_sha[:10]}  tree {base_tree[:10]}")

    files = collect()
    print(f"uploading {len(files)} files")

    tree = []
    for rel, path in files:
        content = path.read_bytes()
        blob = call("POST", f"{API}/git/blobs", {
            "content": base64.b64encode(content).decode(),
            "encoding": "base64",
        })
        tree.append({"path": rel, "mode": "100644", "type": "blob",
                     "sha": blob["sha"]})

    new_tree = call("POST", f"{API}/git/trees", {
        "base_tree": base_tree,
        "tree": tree,
    })
    print(f"new tree {new_tree['sha'][:10]}  ({len(tree)} entries)")

    commit = call("POST", f"{API}/git/commits", {
        "message": "Add sunday-money-reset post",
        "tree": new_tree["sha"],
        "parents": [head_sha],
    })
    print(f"commit {commit['sha'][:10]}")

    # plural "refs" on PATCH; singular returns 404
    call("PATCH", f"{API}/git/refs/heads/{BRANCH}", {
        "sha": commit["sha"],
        "force": False,
    })
    print("branch updated")

    # verify against the real remote (GitHub's read can lag a second or two)
    import time
    for attempt in range(6):
        check = call("GET", f"{API}/git/ref/heads/{BRANCH}")
        if check["object"]["sha"] == commit["sha"]:
            print(f"verify: remote head is {check['object']['sha'][:10]} -> MATCH")
            return
        time.sleep(2)
    print(f"verify: remote head is {check['object']['sha'][:10]} -> MISMATCH")
    sys.exit(1)


if __name__ == "__main__":
    main()
