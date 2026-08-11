---
title: Restructure plan docs to mirror the multimodal RAG tutor + absorb RAG components
version: 0.1
date_created: 2026-07-24
last_updated: 2026-07-24
owner: robertjames
status: design (awaiting review)
---

# Design: RAG-component plan restructure

## Problem

The portfolio's agentic-app planning system is built on a fixed **7-row component
coverage matrix** (Infra, Agents, Tools, Memory, Prompts, Frontend, Tracing/eval)
plus four cross-cutting rows (Auth, Deploy, Testing, Code review). That matrix
predates the portfolio's most substantial build - the **Multimodal RAG AI Tutor**
(`multimodal_rag_ai_tutor`, the real implementation of `~/loc/multimodal_rag_template`).

The tutor exercises a whole class of AI-engineering components the current matrix
buries as footnotes: retrieval/RAG (vector store, pluggable retriever, hybrid +
rerank), a data-ingestion pipeline (parsers, chunking, embeddings, index writers,
multi-source), a knowledge graph / GraphRAG, multimodal handling (figures/vision,
audio/voice + diarization), grounding/verification (a Verifier gate + citations),
safety & governance (content safety, PII redaction, ACLs, rate-limit, cost cap),
and a real evaluation surface (golden sets, adversarial/safety simulation, feedback
loop). Today "retrieval" is a one-line footnote under Infra and "eval" is a
sub-bullet of Tracing - so a RAG project can silently drop half its real components
and the matrix will not catch it.

## Goal

Restructure the planning docs so that (a) every project still answers the same
lightweight **core** matrix, and (b) any data/RAG project additionally answers a
**RAG addendum** that makes the tutor's component set first-class Build/Reuse/N/A
decisions. Mirror the tutor's ARCHITECTURE.md documentation shape in the plan
template's architecture section. Keep the dashboard checkbox roll-up mechanism
unchanged.

## Non-goals

- No changes to `scripts/new_agentic_project.py` code (it only reads the STATUS
  template; the template change flows through automatically).
- No changes to dashboard scripts (`build_dashboard.py`, `sync_status.py`), to
  `projects.json`, or to any other project repo.
- Not a full reformat of every plan doc into the tutor's CLAUDE.md sectioning -
  only the matrix and the plan template's architecture section change shape.

## Resolved decisions

1. **Core matrix + RAG addendum** (not one giant matrix). The core stays the
   always-answered set; RAG components live in a clearly-marked addendum only
   data/RAG apps fill. Keeps simple agents light.
2. **All four files** restructured in sync.

## The two matrices

### Core matrix - every project answers this (7 + cross-cutting)

| # | Component | Decision |
|---|-----------|----------|
| 1 | Infra & databases (runtime, DB, container, config, secrets) | Build/Reuse/N/A |
| 2 | Agents (single vs. supervisor + workers; routing) | Build/Reuse/N/A |
| 3 | Tools (registry; per-agent subsets; external APIs) | Build/Reuse/N/A |
| 4 | Memory (multi-turn; long-term) | Build/Reuse/N/A |
| 5 | Prompts (per-role registry; versioning) | Build/Reuse/N/A |
| 6 | Frontend / surface (chat/CLI/API) | Build/Reuse/N/A |
| 7 | Tracing / observability (spans, run id, cost/latency; light LLM-judge) | Build/Reuse/N/A |
| - | Auth & secrets | Build/Reuse/N/A |
| - | Deployment / hosting | Build/Reuse/N/A |
| - | Testing | Build/Reuse/N/A |
| - | Code review (`claude-review.yml`) | Build/Reuse/N/A |

Core is essentially today's matrix; the only change is that heavy eval moves to the
addendum (R7), leaving a light "LLM-judge if measuring quality" note in row 7.

### RAG addendum - data/retrieval apps also answer this (7 rows)

Non-retrieval apps skip the addendum entirely (or drop one `- [x] Addendum N/A -
not a retrieval app` line so the decision stays visible).

| # | Component | Decision | Covers (from the tutor) |
|---|-----------|----------|--------------------------|
| R1 | Retrieval / RAG | Build/Reuse/N/A | pluggable document retriever, vector store, hybrid BM25+vector, rerank, citation-grade store |
| R2 | Ingestion pipeline | Build/Reuse/N/A | parsers (pdf/html/csv/json/text/youtube/learn), chunking, embeddings, index writers, source strategies (files/learn/obsidian) |
| R3 | Knowledge graph / GraphRAG | Build/Reuse/N/A | entity extraction, community summaries, live graph store |
| R4 | Multimodal | Build/Reuse/N/A | figure crop/caption/embed, image vectors, audio speech-to-text + diarization |
| R5 | Grounding & verification | Build/Reuse/N/A | Verifier gate, claim-vs-evidence check, citations/evidence pills, "insufficient evidence" degrade |
| R6 | Safety & governance | Build/Reuse/N/A | content-safety screen, ingestion-time PII redaction, per-doc ACLs, rate-limit, per-session cost cap |
| R7 | Evaluation | Build/Reuse/N/A | golden set, offline eval (promptfoo/rag-evaluator), adversarial/safety sim, feedback loop |

## Architecture section reshape (plan template)

Replace the current flat "Architecture and design" bullets with slots mirroring the
tutor's ARCHITECTURE.md, so a filled plan reads like the tutor's architecture doc:

- **High-level shape** - an ascii box diagram (browser -> backend -> services),
  marking deployed vs optional/code where relevant.
- **Main components** - grouped by band (reasoning core / retrieval & data /
  trust-safety-quality / surface & infra), one line each pointing at where it lives.
- **Data flow** - ingestion path(s) and the query path, step-numbered.
- **Storage ownership** - which store owns what (vector store, chat history, graph,
  cache, blob), and which is source of truth.
- **Key technologies** - backend / frontend / infra / quality.

Non-RAG apps collapse the retrieval/data and data-flow slots to "N/A - no retrieval".

## Files changed (all four, kept in sync)

1. `docs/agentic-app-prep-workflow.md` - split the narrative "component matrix" into
   a **Core** section (categories 1-7 + cross-cutting, lightly edited) and a new
   **RAG addendum** section (R1-R7), each with the What / Template / Multi-agent /
   Decision-cue / Todos shape already used. Add a short "When does the addendum
   apply?" gate.
2. `templates/agentic-app-plan-template.md` - two matrices (core + addendum) and the
   reshaped architecture section.
3. `templates/agentic-app-STATUS.md` - core sections 1-7 + cross-cutting unchanged in
   spirit; append a `## RAG addendum (retrieval/data apps only)` block with R1-R7 as
   checkbox groups, plus the `- [x] Addendum N/A` escape hatch. This flows into
   `new_agentic_project.py` output automatically.
4. `docs/agents-plan.md` - the control-room's own plan. It is not a RAG app, so the
   addendum is marked N/A with a one-line reason; the core matrix is re-labelled to
   match the new structure and the architecture section adopts the new slots. Content
   otherwise preserved.

## Consistency / correctness checks

- All four files must use the identical row labels and numbering (core 1-7, addendum
  R1-R7) so the dashboard's checkbox counting stays coherent and cross-references
  line up.
- Prose uses single hyphens, never em dashes (portfolio rule).
- Agent/LLM references use `claude-sonnet-5`.
- The STATUS template keeps the exact `- [ ]` / `- [x]` checkbox format the dashboard
  counts; the addendum's N/A escape hatch is a real `- [x]` so a skipped addendum
  still reads as "resolved" not "unstarted".

## Test / verification plan

- `python scripts/new_agentic_project.py "Test RAG App"` renders without error and the
  output now contains the RAG addendum section.
- `python scripts/new_agentic_project.py "Test Simple App"` still renders; addendum
  present with the N/A escape hatch guidance.
- `pytest tests/` stays green (no code changed; guards against template-path breakage).
- Manual read-through: the four files agree on row labels/numbering; every internal
  cross-link (`agentic-app-prep-workflow.md` <-> template <-> STATUS) still resolves.

## Out of scope

- Retrofitting existing per-project `todos/*.md` to the new addendum (separate task;
  the tutor's own todo is already flagged in its STATUS for a later pivot update).
- Any change to how the dashboard renders or counts.
