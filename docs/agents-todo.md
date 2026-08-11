# Agents TODO - what's left

Actionable breakdown of the open work for the control-room **agent layer**, grouped
by the component-matrix categories in [`agentic-app-prep-workflow.md`](agentic-app-prep-workflow.md).
`STATUS.md` stays the checkbox rollup for the dashboard; this file expands each open
box into tasks with acceptance criteria. Full rationale: [`agents-plan.md`](agents-plan.md).

Legend: **[verified done]** already in code, **[open]** to do, **[gap]** not in the
STATUS template but called for by the LangChain component model.

> Last updated: 2026-08-11

---

## 1. Infra & databases
- [open] **Deploy target beyond local CLI.** Wire the Tracker to run unattended from
  `.github/workflows/daily-dashboard.yml`.
  - Acceptance: a scheduled Action run produces the tracker summary and commits/updates
    the dashboard narrative without a human present; secrets read from repo Actions secrets.

## 2. Agents
- [verified done] Supervisor + Planner/Tracker/Reviewer/Historian; recursion + step caps.
- [open] **Empty/ambiguous request handling.** Supervisor should return a clarifying
  question instead of routing to `END` silently or looping.
  - Acceptance: `python -m agents ""` and a nonsense request both yield a single clear
    "what do you want to do?" reply; no recursion past `max_supervisor_steps`.

## 3. Tools
- [open] **Register `build_dashboard` + `sync_status` as tools** (plan lists them; only
  `read_status` / `read_history` wrappers exist today).
  - Acceptance: both callable as `@tool`s, assigned to the Tracker subset, covered by a test.
- [open] **Make the three scripts importable (`main()` callable)** without changing CLI
  behavior, so tools can import instead of `subprocess`-shelling where practical.
  - Acceptance: `from scripts.build_dashboard import main` works; existing `python scripts/...` unchanged.
- [open] **`fetch_pr_reviews` auth + timeouts hardening.** Confirm `gh` auth path via
  `PORTFOLIO_TOKEN`; already degrades on missing token/timeout - add a test for each path.
  - Acceptance: unit tests cover no-token, timeout, and malformed-JSON without raising.

## 4. Memory
- [verified done] Short-term checkpointer + durable `ConversationStore` + `recall_history`.
- [open] **History window / summarization strategy** for long sessions.
  - Acceptance: sessions past N turns are summarized or windowed before the model call;
    documented in `agents-plan.md`; behavior covered by a test.
- [gap] **Long-term semantic recall** (deferred by design). Keep as N/A until a use case
  needs vector recall over the transcript.

## 5. Prompts
- [open] **Fix stray leading `{` in every prompt string** in `agents/prompts.py`
  (`"""{` opens each prompt - looks unintentional and leaks into the system prompt).
  - Acceptance: prompts start at the first real sentence; router still returns a bare worker name.
- [open] **Document each prompt's placeholders** (`{like_this}`) in a short header per role.

## 6. Frontend components
- [verified done] CLI surface with `--session` / `--list-sessions` / `--history` / `--model`;
  CLI streams graph events via `graph.stream()`.
- [open] **Error + empty-state UX in the CLI** (friendly message on missing key, no history,
  `gh` unauthenticated).
- [open] **(Optional) Streamlit chat surface** - defer until routing is proven.

## 7. Tracing / observability / eval
- [verified done] LangSmith per-node + per-tool spans (`agents/tracing.py`).
- [open] **Run/session correlation id + token/latency/cost metrics** surfaced per run.
  - Acceptance: each run logs a correlation id and token counts; visible in LangSmith and local logs.
- [open] **Eval harness / LLM-judge** over a golden request set (routing correctness +
  output shape).
  - Acceptance: `pytest`-runnable eval asserts the router picks the expected worker for a
    labeled set; an LLM-judge scores output shape; report printed.

## Cross-cutting
- [open] **Enable the Claude PR code-review workflow on THIS repo**
  (`templates/claude-review.yml` is only pushed to project repos today).
  - Acceptance: a PR here triggers the review; `scripts/deploy_review_workflows.sh` includes self.
- [open] **End-to-end smoke test** with a real key (plan -> STATUS skeleton; stalled-projects query).
- [open] **Verify coverage vs the portfolio >80% bar** (`pytest --cov`).
- [open] **Add this repo as a track in `projects.json`** so its STATUS.md rolls up to the board.

---

## LangChain-model gaps (not in the STATUS template - candidates for both this repo and the template)

These come from the LangChain component list and are not named in the current
`agentic-ai-demo/STATUS.md` matrix. Decide build vs N/A per project.

- [gap] **Middleware.** No before/after-model middleware layer (LangChain v1 first-class
  concept: summarization, guardrails, logging as middleware). Decision: evaluate a
  logging/summarization middleware for the worker calls.
- [gap] **Guardrails.** No input/output validation or content-safety layer. Decision:
  add an output guard on tool inputs (the agents are read-mostly - assert no write/push).
- [gap] **Human-in-the-loop.** `interrupt_before` / `interrupt_after` are wired empty in
  `graph.py`. Decision: add an approval interrupt before the Planner writes any file into
  a target repo.
- [gap] **Structured output.** Workers return free text. Decision: define a Pydantic
  response schema per worker and use structured output so the supervisor composes reliably.
- [gap] **MCP (Model Context Protocol).** Tools are local `@tool`s only. Decision: N/A for
  v1; revisit if a worker needs an external MCP server (e.g. GitHub MCP for the Reviewer).
- [gap] **Dev/eval tooling.** LangSmith **Studio** graph-debugging and **Agent Chat UI**
  not used. Decision: optional; Studio is useful for debugging the routing graph.
