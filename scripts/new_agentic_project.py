#!/usr/bin/env python3
"""Generate a component-complete STATUS.md skeleton for a new agentic app.

Every component category is pre-listed as unchecked todos, so a new project
starts already accounting for infra/db, agents, tools, memory, prompts, frontend,
and tracing — nothing is silently dropped. Drop the output into a new project
repo as STATUS.md; the portfolio dashboard picks it up via sync_status.py.

Read-only w.r.t. this repo: it never edits todos/ or projects.json.

Usage:
    python scripts/new_agentic_project.py "Recipe Recommender"
    python scripts/new_agentic_project.py "Recipe Recommender" --framework LangGraph -o /path/STATUS.md
"""
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "templates" / "agentic-app-STATUS.md"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("name", help="Project display name")
    ap.add_argument("--framework", default="FastAPI+Anthropic",
                    help="FastAPI+Anthropic | LangGraph | MS Agent Framework")
    ap.add_argument("--stage", default="scoping")
    ap.add_argument("-o", "--output", help="Write here instead of stdout")
    args = ap.parse_args()

    text = TEMPLATE.read_text()
    # Fill the front-matter line's placeholders.
    text = text.replace("**<name>**", f"**{args.name}**")
    text = text.replace(
        "**<FastAPI+Anthropic | LangGraph | MS Agent Framework>**",
        f"**{args.framework}**")
    text = text.replace("**<scoping | build | integrate | deploy>**",
                        f"**{args.stage}**")

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print(f"Wrote STATUS skeleton for {args.name!r} -> {out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
