# Content to Blog Agent

> restructuring to app-template · [agentic_content_extraction_blog_writer](https://github.com/Robertjam954/agentic_content_extraction_blog_writer)

## Restructure to the agentic-ai-app-template
- [ ] Decide restructure depth: full copier scaffold (backend + frontend + compose + Postgres) vs structure-only skeleton (backend/app/agents + docs + STATUS.md, defer the web UI until the pipeline needs one)
- [ ] Adopt the template layout: `backend/app/` (FastAPI + `agents/{client,service,tools}.py`), `docs/AGENTS.md`, `.agents/` + `.claude/skills/`, `pyproject.toml` + uv, `.pre-commit-config.yaml`
- [ ] Add `STATUS.md` in the portfolio-dashboard checkbox format (Scaffold / Agent / Product / Deploy) so status rolls up to the board
- [ ] Map existing assets into the new tree: `scripts/` ingestion -> `backend/app`; agent briefs (`obisidian-knowledge-graph/`, `notion-db-to-technical-blog/`, `claude-md-memory-workflow/`) -> `docs/` or `backend/app/agents`; `Inbox/` -> `data/`
- [ ] Fold `requirements.in`/`.txt` into pyproject/uv (or keep for the stdlib-only ingestion scripts) and re-point the weekly-maintenance workflow
- [ ] Keep `.github/workflows/claude.yml` + `weekly-maintenance.yml`; align action versions (checkout @v6 vs @v4)

## Pipeline build (existing modules)
- [ ] Wire the `rag/` retrieval into the content writing agent (search -> context object)
- [ ] Re-index `rag/` after the processing agents write `Resources/` notes; add a few retrieval tests
- [ ] Module 2: transcript processing + vault connectivity agents (ingestion scripts + `Inbox/` already done)
- [ ] Module 3: content writing agent - spec to runnable
- [ ] Module 4: self-documenting agent - install `update-claude-md.yml` + prompt into `.github/workflows/`, add secret, create initial `CLAUDE.md`
- [ ] Commit pending changes (workflows, doc edits, requirements; SQL EDA removed)

## Done
- [x] Built the `rag/` ChromaDB index over notes + docs (local embeddings) with `index`/`search` CLI - 449 chunks from 66 files, search verified
- [x] Removed the text-to-SQL EDA path (Module 5 / `genie-sql-eda/`) for now
- [x] Saved the AI-app-template structure as a Claude memory (all AI app projects follow it)
