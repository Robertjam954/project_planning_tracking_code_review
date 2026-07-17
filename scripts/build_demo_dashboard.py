#!/usr/bin/env python3
"""Generate a DEMO copy of the portfolio dashboard from fake data.

Purpose: a shareable, portfolio-safe screenshot/URL of what the tracking
dashboard looks like — using invented projects and invented progress, with no
connection to any real work or real completion state.

It reuses the *exact* renderer in build_dashboard.py (so the demo looks
identical) by pointing that module's paths at a throwaway workspace filled with
fabricated projects.json / todos / history, running it, then relabeling the
output header as a demo. build_dashboard.py itself is never modified.

Usage:
    python scripts/build_demo_dashboard.py [output_index.html]
Default output: ../portfolio-dashboard-demo/index.html
"""
import sys
import tempfile
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_dashboard as bd  # noqa: E402

# --- fabricated, unrelated demo projects ---------------------------------
DEMO = [
    {"key": "recipe",   "label": "Recipe Recommender",   "note": "meal-planning agent",   "hue": "#0E9E8E", "visibility": "public",  "total": 18, "final": 16},
    {"key": "habit",    "label": "Habit Tracker Bot",    "note": "streaks + nudges",      "hue": "#3B6FE0", "visibility": "public",  "total": 14, "final": 11},
    {"key": "weather",  "label": "Weather Digest Agent", "note": "daily brief generator", "hue": "#8B54D6", "visibility": "private", "total": 12, "final": 12},
    {"key": "books",    "label": "Bookshelf API",        "note": "catalog + search",      "hue": "#2E9E4F", "visibility": "public",  "total": 20, "final": 9},
    {"key": "trivia",   "label": "Trivia Night",         "note": "quiz game service",     "hue": "#D9722B", "visibility": "public",  "total": 10, "final": 4},
    {"key": "expense",  "label": "Expense Splitter",     "note": "group-bill agent",      "hue": "#B8890E", "visibility": "private", "total": 16, "final": 13},
    {"key": "podcast",  "label": "Podcast Summarizer",   "note": "transcript to notes",   "hue": "#D45C86", "visibility": "public",  "total": 15, "final": 7},
]
DAYS = 30


def done_on_day(final: int, t: int) -> int:
    """Rising progress from ~15% to the final value over DAYS days."""
    frac = 0.15 + 0.85 * (t / (DAYS - 1))
    return min(final, round(final * frac))


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        HERE.parent.parent.parent / "portfolio-dashboard-demo" / "index.html"
    )
    ws = Path(tempfile.mkdtemp(prefix="dashboard-demo-"))
    (ws / "todos").mkdir()
    (ws / "data").mkdir()
    (ws / "docs").mkdir()

    # projects.json (owner deliberately generic; no real repos linked)
    registry = {"owner": "example", "tracks": [
        {"key": p["key"], "label": p["label"], "note": p["note"], "hue": p["hue"],
         "todo": f"{p['key']}.md", "repo": "", "visibility": p["visibility"], "url": ""}
        for p in DEMO
    ]}
    (ws / "projects.json").write_text(json.dumps(registry, indent=2))

    # todos/*.md sized so build_dashboard counts hit each project's final done/total
    for p in DEMO:
        lines = [f"# {p['label']}", "", f"> {p['note']}", ""]
        lines += [f"- [x] Task {i+1}" for i in range(p["final"])]
        lines += [f"- [ ] Task {i+1}" for i in range(p["final"], p["total"])]
        (ws / "todos" / f"{p['key']}.md").write_text("\n".join(lines) + "\n")

    # fabricated 30-day history so the sparklines show plausible upward trends
    snaps = []
    for t in range(DAYS):
        tracks = {p["key"]: {"done": done_on_day(p["final"], t), "total": p["total"]} for p in DEMO}
        od = sum(v["done"] for v in tracks.values())
        ot = sum(v["total"] for v in tracks.values())
        # dates are cosmetic here; build_dashboard replaces the final (today) row
        snaps.append({"date": f"2025-12-{t+1:02d}", "overall": {"done": od, "total": ot}, "tracks": tracks})
    (ws / "data" / "history.json").write_text(json.dumps({"snapshots": snaps}, indent=2))

    # Point the real renderer at the throwaway workspace and run it unchanged.
    bd.ROOT = ws
    bd.TODOS_DIR = ws / "todos"
    bd.HISTORY = ws / "data" / "history.json"
    bd.OUT = ws / "docs" / "index.html"
    bd.main()

    html = (ws / "docs" / "index.html").read_text()
    # Relabel the header so it reads unmistakably as a demo.
    html = html.replace(
        "<title>Portfolio Planning &amp; Tracking</title>",
        "<title>Portfolio Dashboard — Live Demo</title>")
    html = html.replace(
        "Project Planning &middot; Tracking &middot; Code Review",
        "Portfolio Dashboard &middot; Live Demo")
    html = html.replace(
        "Every project's todo list in one place, tracked daily.",
        "Sample data for demonstration only — invented projects, not real progress.")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(f"Demo dashboard -> {out} ({len(html)} bytes, {len(DEMO)} demo projects)")


if __name__ == "__main__":
    main()
