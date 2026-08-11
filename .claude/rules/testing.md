---
paths:
  - "agents/**/*.py"
  - "scripts/**/*.py"
  - "tests/**/*.py"
---

# Testing rules

- Framework: `pytest`. Run `pytest tests/` before committing; keep CI green.
- Coverage: new code >80% line coverage; modified code must not decrease coverage.
- One unit test per tool. Mock `subprocess` and `gh` calls - never hit the network or shell out in tests.
- Cover the degrade paths, not just the happy path: no `ANTHROPIC_API_KEY`, no `PORTFOLIO_TOKEN`,
  `gh` unauthenticated, tool timeout, malformed JSON. The agent degrades, it does not crash.
- One agent-loop routing test: assert the supervisor picks the expected worker for representative requests.
- One end-to-end smoke test (real key) for the two headline flows: plan a new app; report stalled projects.
- Test names describe behavior, e.g. `test_supervisor_routes_stalled_query_to_tracker`.
