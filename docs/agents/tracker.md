# Tracker Agent

## Purpose
Monitor portfolio progress across all projects and surface trends and risks - the
narrative behind the dashboard.

## Responsibilities
- Read all project todos and completion; read the 30-day progress trend.
- Summarize overall completion %, per-project done/total, stalled (zero-progress) projects,
  and trend direction (improving / flat / declining).
- Return a concise executive summary with actionable insights, citing exact numbers and dates.

## Inputs
- A request for portfolio status; reads `todos/*.md` + `data/history.json`.

## Outputs
- An executive summary: overall %, per-project breakdown, at-risk list, trend.

## Tools
- `read_status`, `read_history` (`TRACKER_TOOLS`).
- Planned additions: `build_dashboard`, `sync_status` as tools (see `docs/agents-todo.md`, category 3).

## Prompt
`TRACKER_ROLE` in `agents/prompts.py`. Node: `tracker_node` in `agents/nodes.py`.

## Decision rules
- Be factual and specific; cite exact numbers and dates; do not speculate.
- "Stalled" = zero progress over the past week.
- Deployment target: also runnable unattended from `daily-dashboard.yml` (open item).

## Memory
Reads structured state files (source of truth); turn persisted to `ConversationStore`.

## Related ADRs
- [0002 - LangGraph supervisor topology](../adr/0002-langgraph-supervisor-topology.md)
