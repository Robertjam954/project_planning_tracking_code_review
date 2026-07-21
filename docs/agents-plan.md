---
title: Control-room agent layer (Planner / Tracker / Reviewer on a LangGraph supervisor)
version: 0.1
date_created: 2026-07-19
last_updated: 2026-07-19
owner: robertjames
framework: LangGraph
---

# Implementation Plan: control-room agent layer

Today this repo is the portfolio "control room" as **plain scripts + GitHub
Actions**: `build_dashboard.py` counts todos and renders `docs/index.html`,
`sync_status.py` pulls each project's `STATUS.md` into `todos/<slug>.md`, and
`templates/claude-review.yml` runs a per-PR Claude review in every project repo.
This plan adds a thin **agent layer** on top of those existing scripts so the
three jobs the repo already does - planning, tracking, code review - can be driven
from one natural-language request instead of remembered command invocations.

The roster is a **LangGraph `StateGraph` supervisor** routing to four workers:
**Planner** (turns a project idea into a component-matrix plan + a `STATUS.md`
skeleton), **Tracker** (reads status across repos, summarizes progress, flags
stalled projects, drafts the dashboard narrative), **Reviewer** (aggregates
the per-repo PR-review findings into one cross-portfolio quality summary), and
**Historian** (answers "what did we discuss / plan last time" from durable
conversation memory). Workers report back to the supervisor, which composes the
final answer.

Success criteria: a single command - `python -m agents "plan a new invoice-parser
app"` or `... "which projects are stalled?"` - produces the same artifact the
manual script would, with every LangGraph node + tool call traced in LangSmith,
and no existing script or workflow broken.

## Requirements

**Functional**
- Route an NL request to the correct worker (or a short sequence) and return a composed result.
- Planner: given a project name + one-line idea, emit a filled `agentic-app-plan-template.md` and a `STATUS.md` skeleton (reuse `scripts/new_agentic_project.py`), covering every component-matrix row.
- Tracker: read `todos/*.md` + `data/history.json` (+ live `STATUS.md` via `sync_status.py`), report per-project completion, name projects with no progress over a threshold, and draft the dashboard summary text.
- Reviewer: pull the `claude-review.yml` PR-review comments across the repos in `projects.json` (via `gh`), cluster recurring issues, and return a portfolio-level quality summary.
- Multi-turn: a follow-up ("now do the same for the tracker output") reuses prior context in the session.

**Non-functional**
- Cost ceiling: default model `claude-sonnet-5` (per user memory - the retired `claude-sonnet-4-20250514` pin must not be used); a hard step/recursion cap so a bad route cannot loop.
- Deployment: local CLI first; the Tracker is also runnable unattended from the existing daily GitHub Action.
- Secrets: `ANTHROPIC_API_KEY`, a GitHub token (`PORTFOLIO_TOKEN` for private repos), optional `LANGSMITH_API_KEY` - never committed.
- Read-mostly: agents must not push to project repos or edit `projects.json`; they write only plan/STATUS artifacts and dashboard narrative, and only when asked.

## Component coverage matrix

**Every row must be answered.** Decision is one of **Build** / **Reuse** / **N/A**.
See [`agentic-app-prep-workflow.md`](agentic-app-prep-workflow.md) for what each
category means and how it maps to LangGraph.

| # | Component | Decision | Notes / where it lives / N/A reason |
|---|-----------|----------|--------------------------------------|
| 1 | Infra & databases (DB, migrations, container, config, secrets) | Build (light) | State is the repo's own git-tracked files: `projects.json`, `data/history.json`, `todos/*.md`. No new DB. `core/config.py` reads `.env` (`ANTHROPIC_API_KEY`, `PORTFOLIO_TOKEN`, `LANGSMITH_*`). Vector store **N/A** - no retrieval, state is small and structured. |
| 2 | Agents (single vs. supervisor + workers; routing) | Build | LangGraph `StateGraph`: `supervisor` node routes to `planner` / `tracker` / `reviewer` worker nodes; workers report back. `agents/graph.py`, `agents/nodes.py`. |
| 3 | Tools (registry; per-agent subsets; external APIs) | Build (mostly wrappers) | `agents/tools.py` wraps existing scripts as `@tool`s: `new_agentic_project`, `build_dashboard`, `sync_status`, plus `read_status`, `read_history`, `fetch_pr_reviews` (`gh api`). Each worker gets only its subset. |
| 4 | Memory (multi-turn history; long-term / retrieval) | Build | Short-term: LangGraph `MessagesState` + a `SqliteSaver` checkpointer keyed by thread id. **Durable + queryable:** `agents/memory.py` `ConversationStore` (SQLite `data/agent_memory.db`) persists every turn across sessions; a `recall_history` tool (list sessions / read a transcript / keyword search) lets the user ask for past conversation history, answered by the `historian` worker. Vector/semantic recall deferred - keyword + structured recall first. |
| 5 | Prompts (per-role registry; versioning) | Build | `agents/prompts.py` - one system prompt per role (supervisor router + planner + tracker + reviewer), versioned in git. |
| 6 | Frontend components (chat/agent surface) | Build (CLI) / Reuse (dashboard) | Primary surface is a CLI (`python -m agents "<request>"`). Optional Streamlit chat later. The rendered `docs/index.html` dashboard is the read surface and is reused as-is. |
| 7 | Tracing / observability / eval | Build | LangSmith per-node + per-tool spans via `LANGCHAIN_TRACING_V2` / `LANGCHAIN_PROJECT` (`agents/tracing.py`). Eval: a small LLM-judge over a golden set of requests (routing correctness + output shape) - **build-lite**, can start N/A. |
| - | Auth & secrets | Build | `.env` only; `ANTHROPIC_API_KEY`, GitHub token, LangSmith key. CLI is local (no surface auth needed). |
| - | Deployment / hosting | Build (light) | Local CLI now; Tracker invocable from the existing `daily-dashboard.yml` GitHub Action on schedule. No new container required. |
| - | Testing | Build | Unit test per tool (mock `subprocess` / `gh`), one agent-loop routing test, one end-to-end smoke with a fake request. |
| - | Code review (claude-review.yml) | Reuse | Deploy `templates/claude-review.yml` to **this** repo too (it is currently only pushed to project repos). |

## Architecture and design

- **Data flow:** CLI/entrypoint -> `supervisor` node (router prompt) -> selected worker node -> worker calls its tool subset (which shell out to the existing scripts or `gh`) -> worker returns a structured report -> supervisor composes the final message. All state in `MessagesState`; checkpointer keys on a session id.
- **New code paths:** an `agents/` package - `graph.py` (StateGraph + edges + recursion cap), `nodes.py` (node fns), `tools.py` (tool registry), `prompts.py`, `state.py`, `tracing.py`, `core/config.py`, and `__main__.py` (CLI). No changes to the existing `scripts/` beyond making three of them importable (a `main(...)` callable, not just `__main__`).
- **Reuse over rewrite:** tools are thin wrappers around `new_agentic_project.py`, `build_dashboard.py`, `sync_status.py` - the scripts stay the source of truth for behavior; the agents only orchestrate them.
- **Rejected trade-offs:** (a) a standalone DB for agent state - rejected, the repo's JSON/markdown already is the state and is git-versioned; (b) FastAPI + React full app - rejected for v1, the users are the repo owner and a scheduled job, so a CLI + the existing dashboard suffice; (c) one monolithic agent - rejected, distinct routing/report-back per job is the whole point and matches the sibling `agentic_research_team` supervisor pattern.

## Tasks

> These mirror the **Build** rows above. Kept in `- [ ]` form; the checklist of
> record is [`../STATUS.md`](../STATUS.md), which rolls up to the dashboard.

- [ ] Scaffold the `agents/` package + `core/config.py` reading `.env` - acceptance: `python -m agents --help` runs, missing `ANTHROPIC_API_KEY` fails with a clear message
- [ ] Make `new_agentic_project.py` / `build_dashboard.py` / `sync_status.py` importable (`main()` callable) without changing CLI behavior
- [ ] Build `agents/tools.py` with the 6 tools + input schemas; per-agent subsets
- [ ] Build the LangGraph supervisor + 3 worker nodes with a recursion/step cap - acceptance: a bad route cannot exceed the cap
- [ ] Write one system prompt per role in `agents/prompts.py`
- [ ] Wire short-term memory (MessagesState + SQLite checkpointer) keyed by session id
- [ ] Add LangSmith tracing (`agents/tracing.py`); every node + tool appears as a span
- [ ] CLI entrypoint `python -m agents "<request>"`
- [ ] Deploy `claude-review.yml` onto this repo; add an agent-run smoke step to CI
- [ ] Tests: per-tool unit tests, routing test, e2e smoke
- [ ] Update README.md with the agent layer; add `.env.example`
- [ ] (Optional) Streamlit chat surface; (optional) LLM-judge eval over a golden request set

## Test plan

- Local: `python -m agents "plan a new X app"` produces a plan + STATUS skeleton; `python -m agents "which projects are stalled?"` returns a progress summary from `data/history.json`.
- Per-tool unit tests mock `subprocess`/`gh`; agent-loop test asserts the router picks the right worker for representative requests; e2e smoke with a real key set.
- Edge cases: no `ANTHROPIC_API_KEY` (graceful exit), empty/ambiguous request (supervisor asks to clarify, does not loop), `gh` unauthenticated (Reviewer degrades to "no PR data" rather than crashing), tool timeout.

## Open questions

1. Reviewer scope: read PR-review comments live via `gh api` per request, or have the Tracker cache them into `data/` on the daily run and read the cache?
2. Should the Planner be allowed to write the plan/STATUS files directly into a target repo, or only emit them to stdout / this repo's `docs/` for the user to place?
3. Streamlit surface now or defer until the CLI has proven the routing?

## Out of scope

- Vector store / long-term retrieval memory (matrix row 4 N/A - state is small structured files).
- A full FastAPI + React web app (CLI + existing dashboard suffice for v1).
- Agents writing to `projects.json` or pushing commits to project repos (read-mostly by design).
