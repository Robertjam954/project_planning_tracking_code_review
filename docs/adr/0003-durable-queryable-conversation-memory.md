# ADR-0003: Durable, queryable conversation memory

Date: 2026-07-19
Status: accepted

## Context

ADR-0002 gave the agent layer only short-term memory (LangGraph `MessagesState` +
a checkpointer scoped to one thread). A requirement was added: the user must be able
to **ask for the conversation history** - "what did we plan last time", "show my last
session" - which a per-thread checkpointer cannot answer, because its state is opaque
graph-internal channel data keyed by thread id, not a queryable transcript, and it is
not designed to be read back across sessions. We need memory that survives across
sessions and can be listed, read, and searched, while keeping the "state is small
structured files, no server DB" constraint from ADR-0002.

## Decision

Add two complementary layers in `agents/memory.py`:

- **Short-term (unchanged from ADR-0002):** a LangGraph `SqliteSaver` checkpointer at
  `data/agent_checkpoints.db`, keyed by thread/session id, for multi-turn continuity
  within a run.
- **Durable + queryable:** a `ConversationStore` backed by a local SQLite database
  (`data/agent_memory.db`) with `sessions(session_id, created_at, title)` and
  `messages(session_id, ts, role, content)` tables. Every user turn and final assistant
  turn is written through on each request. It exposes `list_sessions()`,
  `get_messages(session_id)`, and `search(query)` (SQL `LIKE` keyword match for now).

A `recall_history` tool wraps `ConversationStore`, and a dedicated **historian** worker
node holds that tool, so "ask for the conversation history" is a routable request like
planning or tracking. Both SQLite files live under `data/` and are gitignored (they are
per-user runtime state, not portfolio records).

Semantic/vector recall is explicitly deferred: keyword + structured recall is enough for
a single-user control room, and it avoids standing up an embedding pipeline the rest of
the app does not need.

## Consequences

- The user can query past conversations across sessions; the historian answers from a
  real transcript, not opaque checkpoint state.
- Two SQLite files instead of one: the checkpointer (graph continuity) and the
  conversation store (durable transcript) have different shapes and lifetimes, so they
  stay separate rather than overloading one.
- Write-through on every turn adds a tiny, local write; no network dependency.
- Deferring vector recall means paraphrase queries ("did we ever talk about caching?")
  rely on keyword match for now; a follow-up ADR would add embeddings if that proves
  insufficient.
- `data/*.db` must be gitignored so runtime memory never lands in version control.

## References

- `agents/memory.py` - `ConversationStore` + `get_checkpointer()`
- `agents/tools.py` - `recall_history`
- `agents/nodes.py` - the `historian` worker
- `docs/agents-plan.md` - component matrix row 4
- Supersedes the "long-term memory N/A" line in ADR-0002's matrix; extends, does not replace, ADR-0002
