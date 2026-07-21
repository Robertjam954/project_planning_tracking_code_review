# Architecture Decision Records

Significant architectural decisions for this project, one file per decision. Each
record is immutable once accepted; a decision is changed by adding a new ADR that
supersedes it.

- Format: [`.claude/adr-template.md`](../../.claude/adr-template.md)
- Numbering: `NNNN-short-title.md`, sequential
- Maintained by: the [`self-documenter`](../../.claude/agents/self-documenter.md) agent,
  which writes an ADR when it detects a significant architectural change in the diff.

## Records

- [ADR-0001](0001-record-architecture-decisions.md) - Record architecture decisions
- [ADR-0002](0002-langgraph-supervisor-topology.md) - LangGraph supervisor over Planner / Tracker / Reviewer workers
- [ADR-0003](0003-durable-queryable-conversation-memory.md) - Durable, queryable conversation memory
