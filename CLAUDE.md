# Project Planning, Tracking & Code Review

The control room for the whole AI-engineering portfolio. Aggregates status, tracks todos, seeds new projects, and runs review workflows across the other portfolio repos.

## Quick Facts
- **Type**: Automation / process repo (Python scripts + agents), not a deployed app
- **Deps**: `agents-requirements.txt` (runtime), `test-requirements.txt` (tests)
- **State**: `projects.json` (portfolio registry), `STATUS.md` (rolled-up board)
- **Todos**: markdown files under `todos/` - the canonical location for portfolio project todos

## Commands
- Install: `pip install -r agents-requirements.txt` (+ `-r test-requirements.txt` for tests)
- Build dashboard: `python scripts/build_dashboard.py`
- Sync status: `python scripts/sync_status.py`
- New project: `python scripts/new_agentic_project.py`
- Tests: `pytest tests/`

## Key Directories
- `agents/` - portfolio automation agents
- `scripts/` - dashboard build, status sync, project seeding
- `templates/` - project/document templates
- `todos/` - per-project todo markdown (source of truth for tracking)
- `data/`, `docs/` - supporting data and docs

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
- **Single source of truth**: `projects.json` + `todos/` drive dashboards; update those, not derived artifacts.
- **Prose**: single hyphen (-), never em dashes.
- **Models**: agent/LLM work uses `claude-sonnet-5`.
- A `settings.json` hook blocks edits on `main`/`master` - branch first.
