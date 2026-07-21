# Project Planning, Tracking & Code Review

The control room for the whole AI-engineering portfolio. Aggregates status, tracks todos, seeds new projects, and runs review workflows across the other portfolio repos.

## Quick Facts
- **Type**: Automation / process repo (Python scripts + agents), not a deployed app
- **Deps**: `agents-requirements.txt` (runtime), `test-requirements.txt` (tests)
- **State**: `projects.json` (portfolio registry), `STATUS.md` (rolled-up board)
- **Todos**: markdown files under `todos/` - the canonical location for portfolio project todos

## Commands
- Install: `pip install -r agents-requirements.txt` (+ `-r test-requirements.txt` for tests)
- Build dashboard: `python scripts/build_dashboard.py`
- Sync status: `python scripts/sync_status.py`
- New project: `python scripts/new_agentic_project.py`
- Tests: `pytest tests/`

## Key Directories
- `agents/` - portfolio automation agents
- `scripts/` - dashboard build, status sync, project seeding
- `templates/` - project/document templates
- `todos/` - per-project todo markdown (source of truth for tracking)
- `data/`, `docs/` - supporting data and docs

## Working Rules
- **Single source of truth**: `projects.json` + `todos/` drive dashboards; update those, not derived artifacts.
- **Prose**: single hyphen (-), never em dashes.
- **Models**: agent/LLM work uses `claude-sonnet-5`.
- A `settings.json` hook blocks edits on `main`/`master` - branch first.
