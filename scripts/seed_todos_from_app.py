#!/usr/bin/env python3
"""One-time seeder: turn a todo-app export into per-project markdown lists.

The Portfolio Ops todo app stores every task as "[tag] text". This reads a JSON
export (list of {name, completed}) plus projects.json, groups tasks by their tag
onto the matching track, and writes todos/<slug>.md - one file per project.

Usage:
    python scripts/seed_todos_from_app.py path/to/todos.json

After the first seed, the markdown files are the source of truth: edit them by
hand (check a box with [x]) and the daily dashboard picks up the change.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODOS_DIR = ROOT / "todos"

TAG_RE = re.compile(r"^\s*\[([^\]]+)\]\s*(.*)$")


def main() -> None:
    export = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    registry = json.loads((ROOT / "projects.json").read_text())
    tracks = {t["key"]: t for t in registry["tracks"]}

    # Bucket every exported task under its tag; untagged -> "inbox".
    buckets: dict[str, list[dict]] = {k: [] for k in tracks}
    buckets["inbox"] = []
    if export and export.exists():
        for item in json.loads(export.read_text()):
            m = TAG_RE.match(item.get("name", ""))
            key = (m.group(1).strip().lower() if m else "inbox")
            text = (m.group(2).strip() if m else item.get("name", "").strip())
            if key not in buckets:
                key = "inbox"
            buckets[key].append({"text": text, "done": bool(item.get("completed"))})

    TODOS_DIR.mkdir(exist_ok=True)
    for key, track in tracks.items():
        rows = sorted(buckets.get(key, []), key=lambda r: (r["done"], r["text"].lower()))
        lines = [f"# {track['label']}", ""]
        meta = track["note"]
        if track.get("repo"):
            meta += f" · [{track['repo']}](https://github.com/{registry['owner']}/{track['repo']})"
        lines += [f"> {meta}", ""]
        if rows:
            for r in rows:
                box = "x" if r["done"] else " "
                lines.append(f"- [{box}] {r['text']}")
        else:
            lines.append("- [ ] Define the next milestone for this project")
        (TODOS_DIR / track["todo"]).write_text("\n".join(lines) + "\n")
        print(f"  {track['todo']:32s} {len(rows):3d} tasks")

    # Inbox only if there is anything untagged.
    if buckets["inbox"]:
        lines = ["# Inbox", "", "> untagged tasks", ""]
        for r in sorted(buckets["inbox"], key=lambda r: r["done"]):
            box = "x" if r["done"] else " "
            lines.append(f"- [{box}] {r['text']}")
        (TODOS_DIR / "inbox.md").write_text("\n".join(lines) + "\n")
        print(f"  inbox.md {len(buckets['inbox'])} tasks")


if __name__ == "__main__":
    main()
