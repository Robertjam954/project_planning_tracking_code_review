# Content to Blog Agent

> restructuring to app-template · [agentic_content_extraction_blog_writer](https://github.com/Robertjam954/agentic_content_extraction_blog_writer)

## Restructure to the agentic-ai-app-template
- [ ] Decide restructure depth: full copier scaffold (backend + frontend + compose + Postgres) vs structure-only skeleton (backend/app/agents + docs + STATUS.md, defer the web UI until the pipeline needs one)
- [ ] Adopt the template layout: `backend/app/` (FastAPI + `agents/{client,service,tools}.py`), `docs/AGENTS.md`, `.agents/` + `.claude/skills/`, `pyproject.toml` + uv, `.pre-commit-config.yaml`
- [ ] Add `STATUS.md` in the portfolio-dashboard checkbox format (Scaffold / Agent / Product / Deploy) so status rolls up to the board
- [ ] Map existing assets into the new tree: `scripts/` ingestion -> `backend/app`; agent briefs (`obisidian-knowledge-graph/`, `notion-db-to-technical-blog/`, `claude-md-memory-workflow/`) -> `docs/` or `backend/app/agents`; `Inbox/` -> `data/`
- [ ] Fold `requirements.in`/`.txt` into pyproject/uv (or keep for the stdlib-only ingestion scripts) and re-point the weekly-maintenance workflow
- [ ] Keep `.github/workflows/claude.yml` + `weekly-maintenance.yml`; align action versions (checkout @v6 vs @v4)

## Obsidian RAG (knowledge-rag)
- [x] Installed the engine venv at `github_clones/infra and deployment/local_rag/local_claude_knowledge_rag_search` (knowledge-rag 4.5.0)
- [x] Pre-built the index over the vault - 95 files / 1123 chunks; embedding + reranker models cached; live search verified
- [ ] Register the `knowledge-rag` MCP server with Claude Code (command in `obsidian-rag/README.md`), then restart Claude Code
- [ ] Decide final vault target (this repo vs a dedicated Obsidian vault) in `obsidian-rag/config.yaml`

## Portfolio (publish)
- [x] Build static showcase page (`site/index.html`) + Pages deploy workflow (`.github/workflows/pages.yml`)
- [x] Enabled Pages (Actions source, via `gh api`) and deployed - LIVE at https://robertjam954.github.io/agentic_content_extraction_blog_writer/
- [ ] Drop the demo screencast into the site's demo slot once recorded
- [ ] (Optional) bump the Pages workflow action versions - checkout@v4/deploy-pages@v4/upload-artifact@v4 warn about Node 20 deprecation (non-blocking)
- [ ] (Optional) live demo: containerize the app (Dockerfile) on a container host (HF Spaces / Render / Fly / Azure Container Apps) and link it from the Pages site - Pages can't run the backend

## Pipeline: sources -> Obsidian RAG -> structured summary -> Notion review
- [ ] Have the writing/summary agent emit a structured summary dict (title/summary/key_points/tags), then `notion_review.create_review_page()` it
- [ ] Set up Notion: create the review database (Name/Status/Source/Type/Tags), a `NOTION_TOKEN` integration, share the DB, set `NOTION_REVIEW_DB`; test `python -m notion_review summary.json`

## Pipeline build (existing modules)
- [ ] Run `scripts/fetch_semantic_scholar.py --query ...` with `S2_API_KEY` (shared pool 429s) to populate `Inbox/Papers_to_Process/`, then re-index `rag/`
- [ ] For other-format notes, import into the vault via the obsidian-importer plugin (`example_projects/_agentic_blog_obsidian-importer_template`)
- [ ] Live-test `writer/` end to end with `ANTHROPIC_API_KEY` (dry-run + retrieval already verified); check the draft against the brief's review checklist
- [ ] Re-index `rag/` after the processing agents write `Resources/` notes; add retrieval + content-object tests
- [ ] Module 2: transcript processing + vault connectivity agents (ingestion scripts + `Inbox/` already done)
- [ ] Module 3: content writing agent - spec to runnable
- [ ] Module 4: self-documenting agent - install `update-claude-md.yml` + prompt into `.github/workflows/`, add secret, create initial `CLAUDE.md`
- [ ] Commit pending changes (workflows, doc edits, requirements; SQL EDA removed)

## Done
- [x] Removed the merged `agentic-research-team/` (redundant - it added nothing over the existing pipeline) and refreshed all docs (PRODUCT/ARCHITECTURE/README/site) to the current components; scaffolded the Notion review output (`notion_review/`, dry-run verified)
- [x] Installed + indexed the Obsidian RAG (knowledge-rag) for Claude - 95 files / 1123 chunks, live search verified; fixed the retired `claude-sonnet-4-20250514` -> `claude-sonnet-5` in `writer/`
- [x] Built Semantic Scholar paper extractor (`scripts/fetch_semantic_scholar.py`) - Obsidian notes (frontmatter, author/field wikilinks, TL;DR + abstract); formatting verified, live fetch pending an API key / rate-limit window
- [x] Wired RAG into the content writing agent: `writer/` retrieves via `rag.search()`, assembles the content object, and drafts via Claude (`claude-sonnet-4-20250514`); dry-run verified offline
- [x] Built the `rag/` ChromaDB index over notes + docs (local embeddings) with `index`/`search` CLI - 449 chunks from 66 files, search verified
- [x] Removed the text-to-SQL EDA path (Module 5 / `genie-sql-eda/`) for now
- [x] Saved the AI-app-template structure as a Claude memory (all AI app projects follow it)
