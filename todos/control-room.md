# Status

Live checklist of what is left to complete for the control-room **agent layer**,
one section per component category (see [`docs/agentic-app-prep-workflow.md`](docs/agentic-app-prep-workflow.md)).
Check a box (`[ ]` -> `[x]`) as you finish. Same checkbox format the portfolio
dashboard reads, so this rolls up automatically once this repo is added as a track
in `projects.json`. If a whole category does not apply, keep the heading and add a
single `- [x] N/A - <reason>` so the decision stays visible. Full rationale lives in
[`docs/agents-plan.md`](docs/agents-plan.md).

> Project: **Control-room agent layer** · Framework: **LangGraph** · Stage: **scoping**

## 1. Infra & databases
- [ ] Config + env schema defined (`core/config.py` + `.env.example`: `ANTHROPIC_API_KEY`, `PORTFOLIO_TOKEN`, `LANGSMITH_*`)
- [ ] Secrets management (no keys in git; `.env` gitignored)
- [ ] State source confirmed: existing git-tracked `projects.json` / `data/history.json` / `todos/*.md` (no new DB)
- [ ] Deploy target: local CLI now; Tracker runnable from `daily-dashboard.yml`
- [x] Vector store - N/A - no retrieval; state is small structured files

## 2. Agents
- [ ] Agent roster + responsibilities defined (supervisor + planner + tracker + reviewer + historian)
- [ ] Supervisor/router `StateGraph` implemented (`agents/graph.py`, `agents/nodes.py`)
- [ ] Report-back contract: workers return a structured result to the supervisor
- [ ] Model + params per agent (`claude-sonnet-5`); step/recursion cap enforced
- [ ] Historian worker answers "what did we discuss" from durable conversation memory

## 3. Tools
- [ ] Tools enumerated with input schemas (`new_agentic_project`, `build_dashboard`, `sync_status`, `read_status`, `read_history`, `fetch_pr_reviews`, `recall_history`)
- [ ] Existing scripts made importable (`main()` callable) without changing CLI behavior
- [ ] Registered in `agents/tools.py`; per-agent tool subsets assigned
- [ ] `gh api` auth for `fetch_pr_reviews`; timeouts + error handling (degrade, don't crash)
- [ ] Unit test per tool (mock `subprocess` / `gh`)

## 4. Memory
- [ ] Short-term: `MessagesState` wired; multi-turn within a session
- [ ] Checkpointer (SQLite `SqliteSaver`, `data/agent_checkpoints.db`) keyed by session/thread id
- [ ] Durable conversation store (`agents/memory.py` `ConversationStore`, SQLite `data/agent_memory.db`): every turn persisted across sessions
- [ ] Queryable recall: `recall_history` tool (list sessions, read a session transcript, keyword search) surfaced via the historian worker
- [ ] History window / summarization strategy (only if sessions grow long)

## 5. Prompts
- [ ] Prompt registry `agents/prompts.py` (separate from code)
- [ ] One system prompt per role: supervisor router, planner, tracker, reviewer, historian
- [ ] Variables/placeholders documented; versioned in git

## 6. Frontend components
- [ ] CLI surface: `python -m agents "<request>"` wired to the graph
- [ ] Reuse rendered `docs/index.html` dashboard as the read surface
- [ ] Error & empty/ambiguous-request states (supervisor clarifies, does not loop)
- [ ] (Optional) Streamlit chat surface
- [x] Auth on the surface - N/A - local CLI

## 7. Tracing / observability / eval
- [ ] Per-node + per-tool LangSmith spans (`agents/tracing.py`, `LANGCHAIN_TRACING_V2`)
- [ ] Run/session correlation id; token / latency metrics
- [ ] Eval harness / LLM-judge over a golden request set (routing correctness + output shape) - build-lite; else `- [x] N/A`

## Cross-cutting
- [ ] Auth & secrets (`.env` only)
- [ ] Deployment / hosting configured (CLI + scheduled Tracker via existing Action)
- [ ] Tests: agent-loop routing test + end-to-end smoke
- [ ] Claude PR code-review workflow enabled on THIS repo (`templates/claude-review.yml`)
- [ ] README + `docs/agents-plan.md` updated to final state

> Last doc sync: 2026-07-19
