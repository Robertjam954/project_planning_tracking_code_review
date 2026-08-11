# Reviewer Agent

## Purpose
Synthesize per-repo PR-review findings into one cross-portfolio code-quality picture.

## Responsibilities
- Pull the Claude PR-review comments from recent PRs across the repos in `projects.json`.
- Cluster findings by category (type checking, error handling, security, performance, ...).
- Identify recurring themes and top issue types.
- Return a short, actionable summary: most common issues (with example repos), quality trend,
  recommended focus areas.

## Inputs
- A request for code-quality insights; reads recent PRs via `gh`.

## Outputs
- A prioritized quality summary; patterns over detail.

## Tools
- `fetch_pr_reviews` (`REVIEWER_TOOLS`) - uses `gh pr list` across `projects.json` repos.

## Prompt
`REVIEWER_ROLE` in `agents/prompts.py`. Node: `reviewer_node` in `agents/nodes.py`.

## Decision rules
- Degrade gracefully: no `PORTFOLIO_TOKEN` / `gh` unauthenticated / timeout -> return
  "no PR data" rather than crashing.
- Limit repos checked per run (timeout guard) and never leak the token.
- Focus on patterns and priorities; do not overwhelm with detail.

## Memory
Stateless per request beyond the transcript; turn persisted to `ConversationStore`.

## Related ADRs
- [0002 - LangGraph supervisor topology](../adr/0002-langgraph-supervisor-topology.md)
