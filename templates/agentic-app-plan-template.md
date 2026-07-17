---
title: [Short title]
version: 0.1
date_created: YYYY-MM-DD
last_updated: YYYY-MM-DD
owner: [author]
framework: [FastAPI+Anthropic template | LangGraph | MS Agent Framework | other]
---

# Implementation Plan: <agentic app / feature>

[1-3 paragraphs: what this agent does, who asked, and the success criteria.]

## Requirements
- Functional requirements (what the agent must do, for whom).
- Non-functional constraints (latency, cost ceiling, deployment target, rate limits, privacy).

## Component coverage matrix

**Every row must be answered.** Decision is one of **Build** / **Reuse** / **N/A**.
An N/A requires a one-line reason — this is how we guarantee nothing is dropped by
accident. See [`../docs/agentic-app-prep-workflow.md`](../docs/agentic-app-prep-workflow.md)
for what each category means and how it maps to your framework.

| # | Component | Decision | Notes / where it lives / N/A reason |
|---|-----------|----------|--------------------------------------|
| 1 | Infra & databases (DB, migrations, container, config, secrets) | Build/Reuse/N/A | |
| 2 | Agents (single vs. supervisor + workers; routing) | Build/Reuse/N/A | |
| 3 | Tools (registry; per-agent subsets; external APIs) | Build/Reuse/N/A | |
| 4 | Memory (multi-turn history; long-term / retrieval) | Build/Reuse/N/A | |
| 5 | Prompts (per-role registry; versioning) | Build/Reuse/N/A | |
| 6 | Frontend components (chat/agent surface) | Build/Reuse/N/A | |
| 7 | Tracing / observability / eval | Build/Reuse/N/A | |
| — | Auth & secrets | Build/Reuse/N/A | |
| — | Deployment / hosting | Build/Reuse/N/A | |
| — | Testing | Build/Reuse/N/A | |
| — | Code review (claude-review.yml) | Build/Reuse/N/A | |

## Architecture and design
- Where this fits in [ARCHITECTURE.md](./ARCHITECTURE.md): agent roster, routing, data flow.
- New code paths, models/tables, env vars, deploy artifacts.
- Trade-offs considered and rejected.

## Tasks
> Expand every **Build** row above into concrete tasks with acceptance criteria.
> Keep them in `- [ ]` form so `STATUS.md` (and the portfolio dashboard) can track them.

- [ ] Task 1 — acceptance criterion
- [ ] Task 2
- [ ] Update PRODUCT.md / ARCHITECTURE.md if scope shifted
- [ ] Update .env.example if config changed
- [ ] Update Dockerfile / deploy config if deployment changed

## Test plan
- Local: boot the app + a representative multi-turn conversation.
- Per-tool unit tests; agent-loop test; end-to-end smoke with a key set.
- Edge cases: no API key (graceful 503), empty input, tool failure/timeout.

## Open questions
1. ...
2. ...

## Out of scope
- Items intentionally deferred and why (mirror the N/A rows above).
