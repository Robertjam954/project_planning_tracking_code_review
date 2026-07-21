# ADR-0002: LangGraph supervisor over Planner / Tracker / Reviewer workers

Date: 2026-07-19
Status: accepted

## Context

The repo already does three distinct jobs as separate scripts and workflows:
planning (`scripts/new_agentic_project.py` + the component-matrix prep workflow),
tracking (`scripts/build_dashboard.py` + `scripts/sync_status.py` over `todos/*.md`
and `data/history.json`), and code review (`templates/claude-review.yml` per PR).
We want to drive all three from one natural-language request without rewriting the
scripts, and to match the multi-agent pattern already used by the sibling
`agentic_research_team` repo. Constraints: the only "state" is a handful of
git-tracked JSON/markdown files; the users are the repo owner (local CLI) and a
scheduled GitHub Action; cost must stay low (`claude-sonnet-5`, a hard step cap).

## Decision

Build a **LangGraph `StateGraph` supervisor** (`agents/graph.py`, `agents/nodes.py`)
that routes a request to one of three worker nodes - `planner`, `tracker`,
`reviewer` - each of which reports a structured result back to the supervisor for
final composition. Design decisions as planned in `docs/agents-plan.md`:

- **Tools are thin wrappers, not rewrites** (`agents/tools.py`): `new_agentic_project`,
  `build_dashboard`, `sync_status` shell out to / import the existing scripts, which
  remain the source of truth; plus `read_status`, `read_history`, and
  `fetch_pr_reviews` (`gh api`). Each worker is given only its tool subset.
- **State = the repo's own files.** No new database and no vector store; `projects.json`,
  `data/history.json`, and `todos/*.md` are the durable state (matrix rows 1 and 4 mark
  DB-beyond-files and long-term/retrieval memory as N/A).
- **Short-term memory** via LangGraph `MessagesState` + a checkpointer (in-memory in dev,
  SQLite for the CLI), keyed by session id.
- **Prompts** are one-per-role in `agents/prompts.py`; **tracing** is LangSmith per-node +
  per-tool spans (`agents/tracing.py`, `LANGCHAIN_TRACING_V2`).
- **Surface** is a CLI (`python -m agents "<request>"`); the rendered `docs/index.html`
  dashboard is reused as the read surface. Agents are read-mostly - they never push to
  project repos or edit `projects.json`.

## Consequences

- Easier: one entrypoint for all three jobs; adding a worker is a node + a prompt + a
  tool subset; behavior stays testable because the underlying scripts are unchanged.
- Harder / trade-offs: a router prompt to tune and a recursion cap to enforce so a bad
  route cannot loop; `gh` auth becomes a runtime dependency for the Reviewer (it must
  degrade, not crash, when unauthenticated).
- Rejected alternatives: (a) a standalone DB for agent state - unnecessary, the JSON/markdown
  is already versioned state; (b) a full FastAPI + React app - overkill for a CLI + scheduled
  job; (c) one monolithic agent - loses the per-job routing and report-back that is the point.

## References

- `docs/agents-plan.md` - full plan + component-coverage matrix
- `STATUS.md` - build checklist (rolls up to the dashboard)
- `agents/graph.py`, `agents/nodes.py`, `agents/tools.py`, `agents/prompts.py`, `agents/tracing.py` (to be built)
- Sibling pattern: `agentic_research_team` LangGraph supervisor
- Supersedes nothing; extends ADR-0001
