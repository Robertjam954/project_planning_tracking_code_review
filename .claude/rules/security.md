# Security rules

- Secrets live in `.env` only (gitignored). Never commit `ANTHROPIC_API_KEY`, `PORTFOLIO_TOKEN`,
  `GH_TOKEN`, or `LANGCHAIN_API_KEY`. `.env.example` documents names with no values.
- **Read-mostly by design.** Agents must not push commits to project repos, must not edit
  `projects.json`, and must not modify another repo's state. They write only plan / STATUS
  artifacts and the dashboard narrative, and only when explicitly asked.
- The runtime SQLite DBs (`data/agent_memory.db`, `data/agent_checkpoints.db`) are per-user
  state and stay gitignored - they are not portfolio records.
- External calls (`gh`) get a timeout and degrade gracefully on auth failure; never leak token
  values into logs, traces, or error messages.
- GitHub token scope: `repo` only when private repos must be read; prefer the least scope that works.
- Do not send repo contents or transcripts to any external service beyond the configured
  Anthropic and (optional) LangSmith endpoints.
