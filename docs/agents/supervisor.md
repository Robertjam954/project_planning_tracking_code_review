# Supervisor Agent (Router)

## Purpose
Route an incoming natural-language request to the single best worker, or ask for
clarification when the request is unclear. Compose the final answer from the worker's
report-back.

## Responsibilities
- Classify the request into one of: planner, tracker, reviewer, historian.
- Return the bare worker name (no punctuation, no explanation) or `END` when unclear.
- After a worker reports back, compose the user-facing final message.
- Enforce loop safety: force finish past `max_supervisor_steps`.

## Inputs
- `MessagesState` (the conversation so far); the latest user request.

## Outputs
- A routing decision written to `state.worker` (`planner | tracker | reviewer | historian | END`).
- The composed final message once a worker has reported back.

## Tools
None. The supervisor routes; it does not call tools directly (`SUPERVISOR_TOOLS = []`).

## Prompt
`SUPERVISOR_ROUTER` in `agents/prompts.py`. Node: `supervisor_node` in `agents/nodes.py`.

## Decision rules
- "plan / create / start a new app" -> planner.
- "progress / stalled / how is the portfolio doing" -> tracker.
- "quality issues / review patterns / code quality report" -> reviewer.
- "what did we discuss / last session / history" -> historian.
- Ambiguous or empty -> return `END` with a clarifying question (see `docs/agents-todo.md`,
  open item under category 2). Never loop.

## Memory
Reads short-term `MessagesState` for multi-turn coherence; does not persist directly.

## Related ADRs
- [0002 - LangGraph supervisor topology](../adr/0002-langgraph-supervisor-topology.md)
