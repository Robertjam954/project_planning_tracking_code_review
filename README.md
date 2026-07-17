# Project Planning, Tracking & Code Review

One control room for the whole AI-engineering portfolio. It does three things:

1. **Holds every project's todo list** as plain markdown in [`todos/`](todos/).
2. **Tracks progress visually, every day** - a scheduled job counts checked
   boxes, records a snapshot, and rebuilds a dashboard published to GitHub Pages.
3. **Runs a Claude code-quality review** on every pull request across all
   project repos, from one centrally-managed workflow.

## Live dashboard

Once Pages is enabled: `https://robertjam954.github.io/project_planning_tracking_code_review/`

The board shows an overall completion ring, per-project progress bars, and a
30-day trend sparkline for each project (and for the portfolio as a whole).

## How todos work

Each project has one file in `todos/`, e.g. `todos/genie-tcga-brainmet.md`:

```markdown
# GENIE TCGA BrainMet
> research pipeline · [repo](https://github.com/Robertjam954/genie_tcga_impact_brainmet)

- [ ] Run the ETL: harmonize scripts never executed
- [x] Add requirements.txt with pinned versions
```

To update progress, **check a box** (`[ ]` -> `[x]`) and push. The daily job
(or any push touching `todos/`) recounts and refreshes the dashboard.
[`projects.json`](projects.json) is the registry that maps each todo file to its
repo, colour, and live URL.

### Source of truth: each project's `STATUS.md`

Every project repo carries its own `STATUS.md` (same checkbox format). The daily
job runs `scripts/sync_status.py` first, which pulls each repo's `STATUS.md` into
`todos/<slug>.md` - so a project's live status rolls up to this board
automatically. Public repos sync with the default token; private repos need a
PAT with `repo` scope in a `PORTFOLIO_TOKEN` secret. Repos without a `STATUS.md`
keep their local `todos/<slug>.md` as the source.

## Planning a new agentic app

Every agentic AI app is planned against one fixed **component matrix** so nothing
gets silently dropped — infra/DB, agents, tools, memory, prompts, frontend, and
tracing are each either built, reused, or explicitly marked N/A with a reason.

- **Prep workflow:** [`docs/agentic-app-prep-workflow.md`](docs/agentic-app-prep-workflow.md)
  — the three phases (curate context → plan → implement) and what each component
  category means, mapped to both the FastAPI+Anthropic template and multi-agent
  frameworks (LangGraph / MS Agent Framework).
- **Plan template:** [`templates/agentic-app-plan-template.md`](templates/agentic-app-plan-template.md)
  — includes a mandatory component-coverage matrix.
- **Status ledger:** [`templates/agentic-app-STATUS.md`](templates/agentic-app-STATUS.md)
  — one checkbox section per category; rolls up to the dashboard.
- **Generate a starter ledger** for a new project:

  ```bash
  python scripts/new_agentic_project.py "My Agent App" --framework LangGraph -o STATUS.md
  ```

The reference implementation
([`agentic-ai-app-template`](https://github.com/Robertjam954/agentic-ai-app-template))
has a part for every category.

## Preview the dashboard (demo)

`scripts/build_demo_dashboard.py` regenerates a public, fake-data copy of the
board (same renderer, invented projects) for portfolio screenshots — published at
`portfolio-dashboard-demo`. It never touches real data.

## Daily tracking

`.github/workflows/daily-dashboard.yml` runs at **07:00 UTC** (and on every push
to `todos/`). It runs `scripts/build_dashboard.py`, which:

- counts `- [ ]` / `- [x]` lines per project,
- appends today's counts to `data/history.json` (one row per day, idempotent),
- renders `docs/index.html`,
- commits the refreshed board + history and deploys it to Pages.

## Code-quality reviews

`templates/claude-review.yml` is the review workflow (based on
`anthropics/claude-code-action@v1` with `track_progress: true`). It reviews each
PR for quality, bugs, security, and performance, posting inline comments.

Deploy it to every project repo in one shot:

```bash
# sets the workflow file AND the ANTHROPIC_API_KEY secret on each repo
ANTHROPIC_API_KEY=sk-ant-...  ./scripts/deploy_review_workflows.sh

# or just push the workflow files and set secrets yourself later
./scripts/deploy_review_workflows.sh --no-secret
```

Repos covered are read from `projects.json`. Each repo needs an
`ANTHROPIC_API_KEY` secret for the review to run.

## Re-seeding todos from the todo app

The initial lists were generated from the Portfolio Ops todo app export:

```bash
python scripts/seed_todos_from_app.py path/to/todos.json
```

After the first seed the markdown files are the source of truth - edit them
directly.

## Layout

```
todos/                 one markdown todo list per project
projects.json          registry: track -> repo, colour, live URL
data/history.json      daily progress snapshots (trend data)
docs/index.html        generated dashboard (GitHub Pages)
scripts/
  build_dashboard.py   count todos, snapshot, render dashboard
  seed_todos_from_app.py   one-time seed from the todo app export
  deploy_review_workflows.sh   push the review workflow to every repo
templates/claude-review.yml    the per-repo PR review workflow
.github/workflows/daily-dashboard.yml   daily build + Pages deploy
```
