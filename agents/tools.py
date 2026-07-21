"""Tool registry for the control-room agents.

Each worker gets a subset of tools (see docs/agentic-app-prep-workflow.md matrix row 3).
Tools are wrapped as @tool callables so LangGraph can invoke them with structured inputs.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from langchain.tools import tool

from .config import settings
from .memory import ConversationStore


@tool
def new_agentic_project(
    project_name: str, framework: str = "LangGraph"
) -> str:
    """Generate a component-coverage matrix plan + STATUS.md skeleton for a new agentic app.

    Args:
        project_name: The project's display name (e.g., "Invoice Parser Agent")
        framework: One of "LangGraph", "FastAPI+Anthropic", "MS Agent Framework"

    Returns:
        A filled plan template with every component category answered.
    """
    result = subprocess.run(
        [
            "python3",
            str(settings.scripts_dir / "new_agentic_project.py"),
            project_name,
            "--framework", framework,
        ],
        capture_output=True,
        text=True,
        cwd=settings.root,
    )
    if result.returncode != 0:
        return f"Error: {result.stderr}"
    return result.stdout


@tool
def read_status() -> str:
    """Read all project todos and summarize completion.

    Returns:
        A JSON summary of {project_key: {done, total, path}}.
    """
    if not settings.projects_json.exists():
        return "projects.json not found"

    reg = json.loads(settings.projects_json.read_text())
    summary = {}
    for t in reg.get("tracks", []):
        todo_file = settings.todos_dir / t["todo"]
        if not todo_file.exists():
            continue
        text = todo_file.read_text()
        done = text.count("[x]")
        total = text.count("- [")
        summary[t["key"]] = {"label": t["label"], "done": done, "total": total}
    return json.dumps(summary, indent=2)


@tool
def read_history() -> str:
    """Read the 30-day progress history (trend data).

    Returns:
        A JSON summary of daily snapshots from data/history.json.
    """
    if not settings.history_json.exists():
        return "No history recorded yet"
    hist = json.loads(settings.history_json.read_text()).get("snapshots", [])
    # Return the last 30 days
    return json.dumps(hist[-30:], indent=2)


@tool
def fetch_pr_reviews(repo: str | None = None) -> str:
    """Fetch recent PR review comments from repos to identify patterns.

    Analyzes PR comments from the last 30 days and clusters recurring issues.
    Args:
        repo: Specific repo (e.g., "multimodal_rag_application"), or None for all

    Returns:
        A summary of common quality issues found in recent PRs.
    """
    if not settings.github_token:
        return "GitHub token not configured (set PORTFOLIO_TOKEN). Skipping PR review analysis."

    try:
        reg = json.loads(settings.projects_json.read_text())
        owner = reg["owner"]
        repos_to_check = []

        if repo:
            repos_to_check = [repo]
        else:
            repos_to_check = [t["repo"] for t in reg.get("tracks", []) if t.get("repo")]

        if not repos_to_check:
            return "No repos configured in projects.json"

        issues = {}
        checked = 0
        for r in repos_to_check[:5]:  # Limit to first 5 to avoid timeout
            try:
                result = subprocess.run(
                    ["gh", "pr", "list", "-R", f"{owner}/{r}", "--state", "closed",
                     "--limit", "10", "--json", "number,title,comments"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode != 0:
                    continue
                checked += 1
                prs = json.loads(result.stdout)
                for pr in prs:
                    if pr.get("comments"):
                        key = pr["title"][:40]
                        issues[key] = issues.get(key, 0) + 1
            except (subprocess.TimeoutExpired, json.JSONDecodeError):
                continue

        if not issues:
            return f"No recent PR data found (checked {checked} repos)"

        sorted_issues = sorted(issues.items(), key=lambda x: x[1], reverse=True)
        result = f"Common issues in recent PRs ({checked} repos checked):\n"
        for issue, count in sorted_issues[:5]:
            result += f"  - {issue}: {count} mentions\n"
        return result

    except Exception as e:
        return f"Error fetching PR reviews: {e} (continuing without review data)"


@tool
def recall_history(query: str = "", session_id: str = "") -> str:
    """Query the durable conversation store.

    Args:
        query: A search keyword (e.g., "invoice parser"), or empty to list sessions
        session_id: A specific session to retrieve, or empty to list

    Returns:
        Session list, transcript, or search results.
    """
    store = ConversationStore()
    try:
        if session_id:
            msgs = store.get_messages(session_id)
            if not msgs:
                return f"No messages in session {session_id}"
            result = f"Session {session_id}:\n"
            for m in msgs:
                result += f"  {m.role}: {m.content[:100]}...\n"
            return result
        elif query:
            results = store.search(query)
            if not results:
                return f"No messages matching '{query}'"
            result = f"Found {len(results)} messages matching '{query}':\n"
            for m in results[:10]:
                result += f"  {m.session_id} | {m.role}: {m.content[:80]}...\n"
            return result
        else:
            sessions = store.list_sessions()
            if not sessions:
                return "No conversation history yet."
            result = "Recent sessions:\n"
            for s in sessions:
                result += f"  {s['session_id']} | {s['title']} | {s['n_messages']} messages\n"
            return result
    finally:
        store.close()


# Tool subsets per worker
PLANNER_TOOLS = [new_agentic_project]
TRACKER_TOOLS = [read_status, read_history]
REVIEWER_TOOLS = [fetch_pr_reviews]
HISTORIAN_TOOLS = [recall_history]
SUPERVISOR_TOOLS = []  # Supervisor routes, doesn't call tools directly
