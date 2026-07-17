# Agentic-App Prep Workflow

The prep workflow for **any agentic AI app**, whatever the framework. Its one job:
make sure no component gets silently dropped. Every agentic app is planned against
the same fixed **component matrix** below - and each category is either **built**,
**reused**, or explicitly marked **N/A with a reason**. Never omitted by accident.

This complements the portfolio's `context-engineering-workflow.md` (curate context
-> plan -> implement). This doc is the agentic-specific layer: *what* to plan for.

- Plan template: [`../templates/agentic-app-plan-template.md`](../templates/agentic-app-plan-template.md)
- Status ledger template: [`../templates/agentic-app-STATUS.md`](../templates/agentic-app-STATUS.md)
- Generate a starter ledger: `python scripts/new_agentic_project.py "<Project Name>"`
- Reference implementation: the [`agentic-ai-app-template`](https://github.com/Robertjam954/agentic-ai-app-template) repo has a part for every category below.

---

## The three phases

1. **Curate context** - write `PRODUCT.md` (what & why), `ARCHITECTURE.md` (what each
   folder holds), `CONTRIBUTING.md`. Decide the framework (see below).
2. **Plan** - copy the plan template, fill the **component coverage matrix** (one row
   per category, decision = build / reuse / N/A+why), expand each built row into tasks.
3. **Implement** - work the tasks; keep `STATUS.md` current (it rolls up to the
   portfolio dashboard). Every PR gets the Claude code-quality review.

> **Framework is a choice, not a skip.** The categories are framework-neutral. Two
> reference mappings are given per category: the **FastAPI + Anthropic template**
> (single/multi-agent, self-hosted) and **multi-agent frameworks** (LangGraph
> supervisor/graph, or Microsoft Agent Framework: `AgentSession`, `ContextProvider`,
> workflows). Pick one; the category still has to be answered.

---

## The component matrix

For each category: what it is, where it lives in the template, how it maps to a
multi-agent framework, the decision cue, and the todos it generates.

### 1. Infra & databases
- **What:** the runtime and persistence — app server, database, container/orchestration, config, secrets.
- **Template:** FastAPI + Postgres (SQLModel + Alembic migrations), Docker `compose*.yml` + Traefik, `backend/app/core/config.py`, `.env`.
- **Multi-agent:** same host options; add a vector store if doing retrieval (pgvector / Chroma / Azure AI Search). Hosting can be Azure Functions (MS Agent Framework `host_your_agent`) or a container.
- **Decision cue:** Does it need persistence beyond a request? A DB? A vector store? Where does it deploy?
- **Todos:** provision DB + migrations · config/env schema · secrets management · container/deploy target · (vector store if retrieval).

### 2. Agents
- **What:** the reasoning unit(s). One agent, or a **supervisor/router + specialized workers** (multi-agent).
- **Template:** `backend/app/agents/service.py` (single tool-using loop) and `backend/app/agents/orchestrator.py` (supervisor routing to workers).
- **Multi-agent:** LangGraph `StateGraph` with a supervisor node routing to worker nodes that "report back" (see the reference `agents.py`); or MS Agent Framework agents composed in a workflow graph.
- **Decision cue:** Is this one agent or several with distinct roles? Who routes? What is the stop condition / recursion limit?
- **Todos:** define agent roster + responsibilities · routing/supervisor logic · per-agent config (model, temperature) · step/recursion caps · report-back contract.

### 3. Tools
- **What:** the functions agents can call (DB queries, external APIs, computation, retrieval).
- **Template:** `backend/app/agents/tools.py` — a registry mapping a JSON schema to a handler; agents can be given tool **subsets**.
- **Multi-agent:** `@tool`-decorated functions (LangChain / MS Agent Framework); each worker gets only the tools it needs.
- **Decision cue:** What real actions must the agent take? Which tools are safe/scoped to which agent? Rate limits, auth, cost?
- **Todos:** enumerate tools + input schemas · per-agent tool assignment · auth/secrets for external APIs · error/timeout handling · tests per tool.

### 4. Memory
- **What:** **short-term** (multi-turn conversation history within a session) and **long-term** (facts/context carried across sessions, often retrieval).
- **Template:** `backend/app/agents/memory.py` + `Conversation`/`Message` tables; `service.run_agent(conversation_id=...)` loads prior turns and saves new ones. In-memory fallback when no DB.
- **Multi-agent:** LangGraph `AgentState.messages` / checkpointer; MS Agent Framework `AgentSession` (multi-turn) + `ContextProvider` (memory).
- **Decision cue:** Multi-turn? Does it need to remember across sessions/users? Retrieval-augmented?
- **Todos:** session/conversation store · history load/save wiring · long-term memory / retrieval (if any) · summarization/window strategy · privacy/retention.

### 5. Prompts
- **What:** the system/role instructions, kept versioned and separate from code — one per agent role.
- **Template:** `backend/app/agents/prompts.py` — a named prompt registry; `config.py` keeps a default that references it.
- **Multi-agent:** one prompt template per node/role (see the reference `prompts.py` with search/analyzer/researcher/generator prompts).
- **Decision cue:** How many distinct roles/prompts? Where do they live? How are they versioned/reviewed?
- **Todos:** prompt registry · one prompt per agent role · variables/placeholders documented · prompt versioning · (eval prompts if judged).

### 6. Frontend components
- **What:** the user surface — usually a chat/agent UI, plus any dashboards or forms — wired to the agent API.
- **Template:** `frontend/src/components/Agent/AgentChat.tsx` + `frontend/src/routes/_layout/agent.tsx` calling `/api/v1/agents/chat`; generated OpenAPI client in `frontend/src/client/`.
- **Multi-agent:** Streamlit chat (see the reference `app.py`: `st.chat`, pills, per-agent callbacks) or any SPA hitting the agent endpoint.
- **Decision cue:** Who uses it and how? Chat, form, dashboard, or headless API only?
- **Todos:** chat/agent surface · streaming/partial output · session UI (new/continue) · error + empty states · auth on the surface.

### 7. Tracing / observability / eval
- **What:** visibility into agent turns and tool calls — traces, logs, metrics — plus evaluation of quality.
- **Template:** `backend/app/agents/tracing.py` wraps turns/tool-calls; emits **Sentry spans** when `SENTRY_DSN` is set (Sentry is already initialized in `main.py`), structured `logging` always, and optional LangSmith/OTel via `TRACING_ENABLED` / `LANGCHAIN_TRACING_V2`.
- **Multi-agent:** LangSmith (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_PROJECT` — see the reference `app.py`) or OpenTelemetry spans per node.
- **Decision cue:** How will you debug a bad run? What's traced? Any offline eval / LLM-judge?
- **Todos:** per-turn + per-tool tracing · run/session correlation id · token/latency/cost metrics · eval harness / LLM-judge (if measuring quality).

### Cross-cutting (also answered in every plan)
- **Auth & secrets** — who can call the agent; where keys live (never committed).
- **Deployment / hosting** — container vs. serverless; env promotion.
- **Testing** — unit tests per tool, agent-loop test, an end-to-end smoke.
- **Code review** — the centrally-managed `claude-review.yml` runs on every PR (deploy via `scripts/deploy_review_workflows.sh`).

---

## How this feeds the dashboard

The generated `STATUS.md` uses the exact checkbox format the portfolio dashboard
counts (`- [ ]` / `- [x]`). Drop it in a project repo, and `sync_status.py` +
`build_dashboard.py` roll its completion up automatically — so "which components are
still open" is visible per project on the board.
