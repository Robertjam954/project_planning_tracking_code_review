# Product agent role-specs

Formal specifications for the runtime agents in the control-room LangGraph app
(`agents/`). These document the roster the portfolio standard requires (purpose,
I/O contract, tools, prompt, decision rules per agent). They describe the **product**
agents, not the Claude Code dev subagents in [`.claude/agents/`](../../.claude/agents/).

Topology (see [`../adr/0002-langgraph-supervisor-topology.md`](../adr/0002-langgraph-supervisor-topology.md)):

```
                 supervisor (router)
        ┌────────────┬──────────┬───────────┐
     planner      tracker    reviewer    historian
        └────────────┴──────────┴───────────┘
              workers report back to supervisor
```

| Agent | Spec | Node | Prompt | Tools |
|-------|------|------|--------|-------|
| Supervisor | [supervisor.md](supervisor.md) | `supervisor_node` | `SUPERVISOR_ROUTER` | none (routes) |
| Planner | [planner.md](planner.md) | `planner_node` | `PLANNER_ROLE` | `new_agentic_project` |
| Tracker | [tracker.md](tracker.md) | `tracker_node` | `TRACKER_ROLE` | `read_status`, `read_history` |
| Reviewer | [reviewer.md](reviewer.md) | `reviewer_node` | `REVIEWER_ROLE` | `fetch_pr_reviews` |
| Historian | [historian.md](historian.md) | `historian_node` | `HISTORIAN_ROLE` | `recall_history` |

Model: `claude-sonnet-5`, temperature 0.0. Loop safety: `max_supervisor_steps=8`,
`max_tool_steps=6`, `recursion_limit=40` (`agents/config.py`). Full rationale in
[`../agents-plan.md`](../agents-plan.md).
