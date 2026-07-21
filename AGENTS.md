# Control Room Agent Layer

Add these to your `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
PORTFOLIO_TOKEN=ghp_...  # GitHub token with `repo` scope (optional, for private repos)
LANGCHAIN_API_KEY=ls_...  # LangSmith key (optional, for tracing)
LANGCHAIN_PROJECT=control-room-agents
```

## Install

```bash
pip install -r agents-requirements.txt
```

## Use

```bash
# Plan a new agentic app
python -m agents "plan an invoice parser agent"

# Check portfolio progress
python -m agents "which projects are stalled"

# Code quality review
python -m agents "show me common code quality issues"

# Recall history
python -m agents --list-sessions
python -m agents --history <session_id>
python -m agents "what did we plan last time" --session <session_id>
```

## How It Works

The `agents/` package is a LangGraph supervisor graph:

1. **supervisor** node routes your request to the best worker (planner / tracker / reviewer / historian)
2. **planner** calls `new_agentic_project` to generate a component-coverage plan
3. **tracker** reads `todos/*.md` + `data/history.json` to summarize portfolio progress
4. **reviewer** fetches PR-review comments and clusters recurring issues
5. **historian** recalls past sessions from `data/agent_memory.db` (durable, queryable transcript)

Every conversation is persisted to SQLite (`data/agent_memory.db`), so you can ask "what did we discuss" and recall old sessions.

See `docs/agents-plan.md` for the full spec and `docs/adr/` for the architecture decisions.
