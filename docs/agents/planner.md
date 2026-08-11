# Planner Agent

## Purpose
Turn a project idea into a detailed implementation plan that covers every component
category, plus a `STATUS.md` skeleton - so no component is silently dropped.

## Responsibilities
- Call `new_agentic_project` with the project name and framework (default: LangGraph).
- Return the filled plan template covering infra, agents, tools, memory, prompts, frontend, tracing.
- Ensure every matrix row is answered as Build / Reuse / N/A (with a reason) - no omissions.
- Ask for clarification before generating if the idea is underspecified.

## Inputs
- Project name and a one-line idea; optional framework choice.

## Outputs
- A filled `agentic-app-plan-template.md` and a `STATUS.md` skeleton (as text to the user).

## Tools
- `new_agentic_project` (`PLANNER_TOOLS`) - wraps `scripts/new_agentic_project.py`.

## Prompt
`PLANNER_ROLE` in `agents/prompts.py`. Node: `planner_node` in `agents/nodes.py`.

## Decision rules
- Default framework LangGraph unless the user names one.
- Do not invent details; ask before calling the tool when uncertain.
- Read-mostly: emit artifacts to stdout / this repo's `docs/`; do **not** write into a target
  repo unless explicitly asked (candidate for a human-in-the-loop approval interrupt - see
  `docs/agents-todo.md` LangChain-gap items).

## Memory
Turn persisted to the durable `ConversationStore`; no long-term retrieval memory.

## Related ADRs
- [0002 - LangGraph supervisor topology](../adr/0002-langgraph-supervisor-topology.md)
