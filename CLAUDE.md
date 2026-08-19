# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Project Planning, Tracking & Code Review

The control room for the whole AI-engineering portfolio. Aggregates status, tracks todos, seeds new projects, and runs review workflows across the other portfolio repos.

## Quick Facts
- **Type**: Automation / process repo (Python agents + scripts, TS chat frontend), not a deployed app
- **Deps**: `agents-requirements.txt` (runtime), `test-requirements.txt` (tests), `frontend/package.json` (chat UI, separate Node project)
- **State**: `projects.json` (portfolio registry), `todos/*.md` (per-project source of truth), `data/history.json` (daily snapshots), `docs/index.html` (generated dashboard). `data/agent_memory.db` / `data/agent_checkpoints.db` are gitignored per-user agent state, not portfolio records.
- **Models**: agent/LLM work uses `claude-sonnet-5` (`agents/config.py:DEFAULT_MODEL`)

## Commands
- Install: `pip install -r agents-requirements.txt` (+ `-r test-requirements.txt` for tests)
- Build dashboard: `python scripts/build_dashboard.py` (counts todos, snapshots `data/history.json`, renders `docs/index.html`)
- Preview dashboard with fake data: `python scripts/build_demo_dashboard.py`
- Sync status from project repos: `python scripts/sync_status.py`
- New project ledger: `python scripts/new_agentic_project.py "My Agent App" --framework LangGraph -o STATUS.md`
- Deploy review workflow to every portfolio repo: `./scripts/deploy_review_workflows.sh` (sets `ANTHROPIC_API_KEY` secret too; `--no-secret` to skip)
- Tests: `pytest tests/` - single test: `pytest tests/test_graph.py::test_graph_import -v`
- Coverage: `pytest tests/ --cov=agents --cov-report=term-missing`
- Agent CLI: `python -m agents "which projects are stalled"` (flags: `--session <id>`, `--list-sessions`, `--history <id>`, `--model`)
- LangGraph dev server (backs the chat frontend): `langgraph dev --port 2024` (needs `pip install "langgraph-cli[inmem]"`)
- Frontend dev, from `frontend/`: `npm install && npm run dev` (port 4100; proxies `/api/langgraph` to the graph server, no CORS needed)

## Architecture

### Two halves that share state, not code paths
1. **Scripts** (`scripts/*.py`) hold the real logic: read `todos/*.md` + `projects.json`, write `docs/index.html` + `data/history.json`. They run standalone (no LLM) from `.github/workflows/daily-dashboard.yml`.
2. **Agent layer** (`agents/`) is a LangGraph supervisor graph that wraps those scripts as tools and adds a conversational interface. Workers call the same scripts (via `subprocess`) or read the same files directly - scripts stay canonical, agents never reimplement or bypass them.

### Agent graph (`agents/graph.py`)
Topology: `START -> supervisor -> {planner | tracker | reviewer | historian} -> supervisor -> end -> END` (see `docs/adr/0002-langgraph-supervisor-topology.md`). The supervisor is a plain LLM call that reads the latest message and returns a worker name (or "end"); workers report back to the supervisor rather than terminating directly, so multi-turn requests stay coherent. `settings.recursion_limit` guards against routing loops.

- `agents/state.py` - `ControlRoomState(MessagesState)` adds `worker` and `context`.
- `agents/nodes.py` - one `create_agent(...)` per worker role (LangChain agent template), sharing a single lazily-built chat model that rebuilds itself if `settings.model`/`temperature` change (e.g. via CLI `--model`).
- `agents/tools.py` - one tool list per role: `PLANNER_TOOLS` (shells out to `new_agentic_project.py`), `TRACKER_TOOLS` (reads `projects.json`/`todos/`/`data/history.json` directly), `REVIEWER_TOOLS` (shells out to `gh pr list`, degrades gracefully without `PORTFOLIO_TOKEN`/`gh`), `HISTORIAN_TOOLS` (queries `ConversationStore`).
- `agents/memory.py` - SQLite `ConversationStore` (`data/agent_memory.db`) for durable, queryable transcripts - distinct from the LangGraph checkpointer (`data/agent_checkpoints.db`, `get_checkpointer()`) used for in-flight graph state.
- `agents/config.py` - `Settings.load()` reads `.env`. Must stay import-safe (no LLM SDK imports at module scope) so `python -m agents --help` works before dependencies are installed.
- `agents/prompts.py` - per-role system prompts via `get_prompt(role)`.
- `langgraph.json` exposes the compiled graph (`agents/graph.py:get_graph`) as the `control_room` graph for `langgraph dev` and the frontend.

### Frontend (`frontend/`)
Standalone React + TypeScript + Vite chat UI that streams from the *same* Python graph over the LangGraph SDK - it is a client, not a second implementation, and requires `langgraph dev` running separately. Don't duplicate agent/routing logic in TypeScript; if behavior needs to change, change `agents/`. See `frontend/README.md` for the two-process dev setup.

### Dashboard data flow
`todos/<slug>.md` (checkbox markdown) + `projects.json` (registry mapping slug -> repo/color/URL) -> `scripts/build_dashboard.py` -> `docs/index.html` (GitHub Pages) + `data/history.json` (append-only daily snapshot, one row per day). In CI, `scripts/sync_status.py` runs first and pulls each project repo's own `STATUS.md` into `todos/<slug>.md` - so most files under `todos/` are generated copies. Edit a project's `STATUS.md` in *that project's* repo, not the synced copy here, unless the repo has no `STATUS.md` of its own.

### Code review workflow (two distinct layers)
- `templates/claude-review.yml`, deployed to every portfolio repo by `scripts/deploy_review_workflows.sh` (reading the repo list from `projects.json`), runs Claude review on PRs in *other* project repos.
- `.github/workflows/claude-review.yml` is this repo's own copy of that review, scoped to PRs against this repo only.

## New-project planning workflow (RAG-grounded, middleware-driven)

When seeding a new agentic project, the Planner grounds the plan in current LangChain docs
before writing anything, then generates the ADR and todos. This is implemented as a
**middleware stack** on the Planner `create_agent(...)`, not as subagents. LangChain docs
come from the official **docs MCP servers** - `docs-langchain` (https://docs.langchain.com/mcp)
and `reference-langchain` (https://reference.langchain.com/mcp), added via
`claude mcp add --transport http`. No local vector DB or ingestion needed; the MCP tools are
loaded into the agent with `langchain-mcp-adapters` (`MultiServerMCPClient`).

`create_agent(model, tools=[create_adr, write_todos, write_status], middleware=[...])` with,
in order:

1. **`LangChainDocsRetrievalMiddleware`** (custom, `before_agent` / `@dynamic_prompt`) -
   **retrieve first**: call the `docs-langchain` / `reference-langchain` MCP tools for the
   project idea and each matrix category, inject the retrieved component docs into the system
   prompt as grounding context.
2. **`AnthropicPromptCachingMiddleware(ttl="5m")`** - cache the injected docs + tool defs so
   repeated planning turns are cheap.
3. **`HumanInTheLoopMiddleware(interrupt_on={"create_adr": True, "write_todos": True, "write_status": True})`**
   - pause for approval before any ADR / todos / `STATUS.md` is written into the target project.
4. **`LoggingMiddleware`** (`before_model` / `after_model`) - trace each planning turn.

The agent then produces, grounded in and citing the retrieved docs: the framework/tooling
ADR(s) from `.claude/adr-template.md` (via the `create_adr` tool), and the component-coverage
todos (each Build row citing the LangChain doc it follows).

Where it lives: the Planner worker in `agents/`; outputs go to the new project's `docs/adr/`,
`todos/`, and `STATUS.md`. Reference implementation of each piece:
`agentic-ai-demo/backend/app/agents_lc/` (`mcp.py` LangChain docs MCP client, `middleware.py`
the stack above, `skills.py` create_adr).

## Working Rules
- **Single source of truth**: `projects.json` + `todos/` drive dashboards; update those, not derived artifacts (`docs/index.html`, `data/history.json` are generated, never hand-edited).
- **Agents are read-mostly** (`.claude/rules/security.md`): must not push commits to project repos, edit `projects.json`, or modify another repo's state - they write only plan/STATUS artifacts and dashboard narrative, and only when explicitly asked.
- **Secrets**: live in `.env` only (gitignored) - `ANTHROPIC_API_KEY`, `PORTFOLIO_TOKEN`, `GH_TOKEN`, `LANGCHAIN_API_KEY`. `.env.example` documents names with no values.
- **Prose**: single hyphen (-), never em dashes. No emojis.
- **Python style** (`.claude/rules/code-style.md`): type hints on every signature, `from __future__ import annotations` at the top, `ruff format` (auto-run by a PostToolUse hook on save), snake_case files/functions, PascalCase classes, UPPER_SNAKE_CASE constants. Keep agent tools as thin `@tool` wrappers over the existing scripts.
- **Testing** (`.claude/rules/testing.md`): mock `subprocess`/`gh` - never hit the network or shell out for real in tests. Cover degrade paths (missing `ANTHROPIC_API_KEY`/`PORTFOLIO_TOKEN`, unauthenticated `gh`, tool timeout, malformed JSON), not just the happy path.
- A `settings.json` hook blocks edits on `main`/`master` - branch first.

## Behavioral Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with the project-specific instructions above as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
