# Historian Agent

## Purpose
Help the user recall past conversations and planning sessions from durable memory -
answers "what did we discuss / plan last time".

## Responsibilities
- Query the durable conversation store: list sessions, read a transcript, or keyword search.
- Format results readably: session list (date, title, count), transcript (role: content),
  or search results with context.
- Retrieve and format a full transcript when a specific session is named.

## Inputs
- A recall request, optionally a `session_id` or a search `query`.

## Outputs
- Session list, a formatted transcript, or search matches.

## Tools
- `recall_history` (`HISTORIAN_TOOLS`) - reads `ConversationStore` (SQLite `data/agent_memory.db`).

## Prompt
`HISTORIAN_ROLE` in `agents/prompts.py`. Node: `historian_node` in `agents/nodes.py`.

## Decision rules
- Empty query -> list sessions. `session_id` -> transcript. Non-empty query -> keyword search.
- If no history is found, suggest starting a new session.
- Recall is keyword + structured today; semantic/vector recall is deferred (see `docs/agents-todo.md`).

## Memory
This agent **is** the read interface to long-term memory: the durable, queryable
`ConversationStore` that persists every turn across sessions.

## Related ADRs
- [0002 - LangGraph supervisor topology](../adr/0002-langgraph-supervisor-topology.md)
- [0003 - Durable, queryable conversation memory](../adr/0003-durable-queryable-conversation-memory.md)
