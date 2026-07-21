# ADR-0001: Record architecture decisions

Date: 2026-07-19
Status: accepted

## Context

This repo is growing from a set of dashboard/sync scripts into an agentic app (a
LangGraph supervisor over Planner / Tracker / Reviewer workers). Architectural
choices - agent topology, tools, memory, prompts, tracing, deploy target - are made
continuously, often by the coding agent, and the reasoning is lost if it lives only
in commit messages or chat history. Reviewers and future maintainers need a durable
record of *why* the structure is the way it is. Every sibling project in the
portfolio already keeps ADRs; this one did not, so the convention is being adopted
here to match.

## Decision

Record every significant architectural decision as an Architecture Decision Record
(ADR) in `docs/adr/`, one file per decision, numbered sequentially
(`NNNN-short-title.md`) in the format at `.claude/adr-template.md`.

The managed self-documenting agent (`.claude/agents/self-documenter.md`, run on a
schedule and after substantive changes) writes ADRs automatically when it detects a
significant architectural change in the diff, inferring the decision and trade-offs
from the code itself. Minor fixes, refactors, and doc/test-only changes get no ADR.

An ADR is immutable once accepted. To change a decision, add a new ADR that supersedes
it and update the older record's status.

## Consequences

- The reasoning behind the architecture is durable, reviewable, and lives next to the code.
- Decisions are captured as they happen - the agent writes them from the diff, not from memory.
- Small overhead: significant changes now ship with a short written record.
- ADR numbers are append-only; superseded records stay for history.
- This repo now carries a `.claude/` directory it previously lacked (template + agent).

## References

- `.claude/adr-template.md` - the record format
- `.claude/agents/self-documenter.md` - the agent that maintains these
- `docs/adr/README.md` - the index of records
- Michael Nygard, "Documenting Architecture Decisions" (2011)
