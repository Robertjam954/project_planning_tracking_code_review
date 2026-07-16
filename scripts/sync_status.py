#!/usr/bin/env python3
"""Pull each project's own STATUS.md into this repo's todos/ folder.

Going-forward convention: every project repo carries a STATUS.md (dashboard-
readable checkbox list of what's left). This fetches each repo's STATUS.md via
the GitHub CLI and writes it to todos/<slug>.md, so build_dashboard.py counts
the project's live status without changing anything downstream.

Repos without a STATUS.md yet are left as-is (their existing todos/<slug>.md
stays the source of truth). Run locally or in CI where `gh` is authenticated:

    python scripts/sync_status.py           # sync all repos that have STATUS.md
    python scripts/sync_status.py --dry-run  # show what would change
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODOS = ROOT / "todos"


def gh_file(owner: str, repo: str, path: str) -> str | None:
    """Return the raw text of a file in a repo, or None if it doesn't exist."""
    for branch in ("main", "master"):
        r = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/contents/{path}?ref={branch}",
             "--jq", ".content"],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and r.stdout.strip():
            import base64
            return base64.b64decode(r.stdout.strip()).decode("utf-8", "replace")
    return None


def main() -> None:
    dry = "--dry-run" in sys.argv
    reg = json.loads((ROOT / "projects.json").read_text())
    owner = reg["owner"]
    synced = skipped = 0
    for t in reg["tracks"]:
        repo = t.get("repo")
        if not repo:
            skipped += 1
            continue
        text = gh_file(owner, repo, "STATUS.md")
        if text is None:
            print(f"  - {repo:40s} no STATUS.md (keeping todos/{t['todo']})")
            skipped += 1
            continue
        dest = TODOS / t["todo"]
        if dry:
            print(f"  ~ would update todos/{t['todo']} from {repo}/STATUS.md")
        else:
            dest.write_text(text)
            print(f"  + todos/{t['todo']:32s} <- {repo}/STATUS.md")
        synced += 1
    print(f"Synced {synced}, skipped {skipped}.")


if __name__ == "__main__":
    main()
