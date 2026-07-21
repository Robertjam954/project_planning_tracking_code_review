# Multimodal RAG Tutor

> live on Azure · [multimodal_rag_application](https://github.com/Robertjam954/multimodal_rag_application)

## SchemaFlow SQL agent: ground against a real SQLite warehouse (dry-run)

**Why:** `agents/sql_schemaflow.py` emits a typed JSON bundle (`parsed -> impact -> plan -> sql`)
but nothing is grounded against a real database. Parse can't confirm the object/columns exist,
Impact hallucinates `affected_objects`/`dependent_views`, and `validate_bundle()` only checks that
JSON keys are present - the generated DDL/DML is never executed. Fix: seed a layered SQLite
warehouse, ground Parse/Impact against its catalog, and **dry-run** the generated SQL (execute in a
transaction, then `ROLLBACK`) so "it runs" is proven, not assumed.

**Decisions (locked 2026-07-19):** SQLite (embedded, stdlib `sqlite3`, zero cost/infra, works
locally + in the container, dry-runs DDL transactionally). **Single file** `data/warehouse.sqlite`;
layers are a **naming convention** (`landing_`/`stg_`/`dim_`+`fct_`/mart view) plus a `_warehouse_layers`
catalog table - NOT ATTACH-ed databases. (Probed 2026-07-19: SQLite forbids a view in one attached DB
from referencing tables in another, which would break the cross-layer `mart` view -> `core` table
dependency that makes Impact interesting; a single file keeps cross-layer views legal.) Dry-run
executes against an **in-memory clone** of the seed (`sqlite3.connect(":memory:")` + `source.backup(mem)`)
or a `BEGIN ... ROLLBACK` transaction - both proven to revert ALTER/UPDATE with the seed untouched.

Seed data + schema

- [x] `scripts/seed_warehouse.py`: builds the single-file 4-layer warehouse (landing/staging/core/mart)
  with tables + the cross-layer view `v_survival_by_gene` (so Impact has a real dependency to find) +
  minimal rows for backfill dry-runs + a `_warehouse_layers` catalog. Idempotent (`INSERT OR IGNORE`);
  `--removeall` rebuilds. Emits `data/warehouse.sqlite`. Verified: seed, idempotency, view-dependency
  discovery, and ALTER+backfill dry-run rollback all pass.
- [ ] Domain = **clinical/TCGA warehouse** (decided 2026-07-19; matches CLAUDE.md's advertised
  "TCGA-like clinical warehouse" and the rest of the portfolio). Concrete layered schema to seed:
  - `landing.landing_patient` (raw ingest: `patient_id`, `submitter_id`, `raw_payload`, `_loaded_at`)
  - `staging.stg_patient` (typed/cleaned: `patient_id`, `age_at_dx`, `sex`, `vital_status`)
  - `staging.stg_sample` (`sample_id`, `patient_id`, `sample_type`, `primary_site`)
  - `core.dim_patient` (`patient_id` PK, demographics), `core.dim_sample`, `core.fct_mutation`
    (`mutation_id`, `sample_id` FK, `gene`, `variant_class`, `vaf`)
  - `mart.fct_survival` (`patient_id`, `os_months`, `os_event`, `stage`) + VIEW
    `mart.v_survival_by_gene` (joins `fct_mutation` -> `fct_survival`; gives Impact a real dependent view)
  - Rewrite `app/frontend/src/pages/sql/Sql.tsx:SAMPLE` and the few-shot examples in the parse/impact/
    plan/sql prompts to a clinical change, e.g. "Add `msi_status VARCHAR(12)` to `core.dim_sample` as
    nullable; backfill from `staging.stg_sample`; propagate to mart." (drops a dependent-view refresh on
    `v_survival_by_gene` for Impact to catch).
- [ ] Container packaging: `.dockerignore` excludes `data/`, so a committed `.sqlite` will NOT ship.
  Either (a) run `seed_warehouse.py` at container startup in `app/start.sh`/gunicorn hook writing to a
  writable path (`SQL_WAREHOUSE_PATH`, default `/app/data/warehouse.sqlite`), or (b) un-ignore just the
  seed script (already under `scripts/`, which is copied) and generate on boot. Prefer (a) - keeps the
  image slim and the warehouse reproducible.

Backend: warehouse catalog + dry-run executor

- [x] `app/backend/core/warehouse.py`: read-only catalog - `objects()`, `layers()`/`layer_of()`,
  `columns()` (name/type/nullable/pk via `PRAGMA table_info`), `has_object`/`has_column`, `ddl()`,
  `dependent_views()` (word-boundary scan of `sqlite_master` view SQL - SQLite has no `pg_depend`), and
  `schema_snapshot()` for prompt grounding + UI. RO connection via `file:...?mode=ro`. `get_warehouse()`
  cached accessor. Verified against the seed.
- [x] Dry-run executor (`Warehouse.dry_run`): clones the seed into `:memory:` via `backup()`, runs
  statements in layer order, stops at first failure (rest marked skipped), skips stray BEGIN/COMMIT,
  returns `DryRunResult{ok, per_statement[{layer,statement,ok,error,skipped}]}`. Verified: valid change
  passes, bad SQL reports the real engine error, seed file stays pristine.

Ground the agents (`agents/sql_schemaflow.py`)

- [x] Parse grounding: after `parse_request`, validate `object` exists and column existence matches the
  operation (must exist for drop/alter, must NOT exist for add); annotate parsed JSON with a
  `catalog_check` block. Inject the target table's real DDL into the parse/sql prompt context so the LLM
  writes against true column names/types (`complete(system, user, ...)` already takes free-form user
  text - pass the DDL in).
- [x] Impact grounding: replace hallucinated `affected_objects`/`dependent_views` with catalog truth
  from `dependent_views(object)`; keep the LLM's `integration_callouts`/`pii_concerns` as advisory
  overlay. Mark which of the LLM's claims were confirmed vs. unsupported by the catalog.
- [x] Extend `validate_bundle()` (or add a `validate` stage in `sql_schemaflow_approach.py`): keep the
  key-presence checks AND attach `validation.dry_run = {ok, per_statement[]}` from the executor.
- [x] Self-correction loop (implemented): if dry-run fails, feed the failing
  statement + engine error back into `write_sql` for **one** retry (mirror the Verifier retry pattern
  on the chat side). Cap at 1 retry; record both attempts in the bundle.

Wiring / config

- [x] `app.py:_setup_clients()`: constructs the warehouse via `get_warehouse()` and passes it into
  `SchemaFlowSQLApproach(prompt_manager=pm, warehouse=...)`; threaded through `run_for_change_request`.
  Absent seed -> `wh.exists()` is False -> pure-LLM fallback (verified). `USE_SQL_DEMO` flag already
  exists (app.py:324).
- [ ] Add `SQL_WAREHOUSE_PATH` to CLAUDE.md env table; keep `USE_SQL_DEMO=false` in the deploy default
  unless we want the SQL route live (route already guarded at app.py:197).

Frontend (`SchemaFlowPanel.tsx` + `api/models.ts`)

- [ ] Extend the `SqlBundle` type: `validation` gains `dry_run: { ok: boolean; per_statement: {layer:
  string; stmt: string; ok: boolean; error?: string}[] }`; `parsed`/`impact` gain the grounding
  annotations.
- [ ] Render dry-run results in `SchemaFlowPanel`: per-statement green/red pass/fail with the engine
  error inline on failures; show catalog-confirmed dependencies distinctly from LLM-guessed callouts.

Tests

- [ ] New `tests/test_sql_schemaflow.py` (none today): temp-warehouse fixture (seed into a tmp path),
  test catalog introspection + `dependent_views`, dry-run **pass** on valid DDL, dry-run **fail** on
  bad DDL (missing table / duplicate column), and grounded-impact matches the seeded views. Mock
  `agents._llm.complete` at the httpx layer per repo convention (`tests/conftest.py`).

Docs

- [ ] Write **ADR-0002** (`docs/adr/`, format `.claude/adr-template.md`): "Ground the SchemaFlow SQL
  agent against a seeded SQLite warehouse with rollback dry-run" - records the SQLite/ATTACH/in-memory
  decision and trade-offs (per ADR-0001's policy).
- [ ] Update CLAUDE.md (SchemaFlow section + integration matrix: add SQLite warehouse as a local/demo
  tier), ARCHITECTURE.md, README SchemaFlow row, and STATUS.md.

## Azure AI Search as runtime retriever (deployment)

Infra (Bicep + azd)

- [ ] Compose `infra/core/search/search-services.bicep` into `main.bicep`; decide SKU (module hardcodes `standard` ~$250/mo; `basic` ~$75/mo also supports semantic ranker and fits a portfolio app) and set `semanticSearch: 'free'` unless paid reranking is wanted
- [ ] Harden the search module for the keyless posture: add `disableLocalAuth: true` (or `authOptions: aadOrApiKey`) and a managed-identity-friendly `publicNetworkAccess` setting; add `sku`/`semanticSearch` as params instead of hardcoding
- [ ] Add search RBAC to `infra/app/rbac.bicep`: Search Index Data Reader (`1407120a-...`) for the backend container app; Search Service Contributor (`7ca78c08-...`) + Search Index Data Contributor (`8ebe5a00-...`) for the deploying user `principalId` so `prepdocs.sh` can create/populate the index locally
- [ ] Wire env into the backend container in `main.bicep`: `AZURE_SEARCH_SERVICE`, `AZURE_SEARCH_INDEX` (e.g. `rag-index`), and flip `DOCUMENT_RETRIEVER` to `azure_search`; surface as params in `main.parameters.json`; add `AZURE_SEARCH_SERVICE` to main.bicep outputs so `azd env get-values` feeds prepdocs

Backend code

- [ ] Implement `AzureSearchRetriever` in `app/backend/core/` satisfying the `Retriever` protocol (`retrieve()` + `get_document()`): hybrid query (BM25 + vector against `embedding`, 3072 dims), `DefaultAzureCredential` keyless auth, filters mapped from `source_type`/`tag` to the index's `source_type`/`category` fields; register as `azure_search` in `document_retriever.get_retriever()`
- [ ] Fix `prepdocslib/servicesetup.search_index_schema()`: it returns raw dicts, but `SearchIndexClient.create_or_update_index` expects `SearchIndex`/`SearchField`/`VectorSearch` model objects - convert (or serialize via `SearchIndex.deserialize`) and verify the HNSW profile + semantic config are valid against the installed `azure-search-documents` (pinned `>=11.6.0b4` preview)
- [ ] `get_document()` for the search backend: reassemble full docs by filtering on `parent_id`/`sourcefile` and ordering chunks (add an ordinal field to the schema if needed)
- [ ] Decide Cosmos coexistence: keep Cosmos NoSQL as chat-history store (unchanged) and either dual-write vectors during migration or cut over cleanly; remove `USE_VECTOR_SEARCH`/retriever ambiguity in `config.py`/`app.py` (`AZURE_SEARCH_SEMANTIC_RANKER` flag already read at app.py:332)

Ingestion + deploy

- [ ] Run `./scripts/prepdocs.sh` against the new service (postprovision hook already calls it); confirm `SearchManager.upsert` writes real documents - today it silently skips when `AZURE_SEARCH_SERVICE` is unset
- [ ] Validate before deploy: `az deployment group what-if` (or azure-validate flow) against RG `ai-tutor`, then `azd up`; verify keyless data-plane access from the container app identity with a live `/chat` query
- [ ] Smoke-test retrieval parity: run `evals/evaluate.py` against both `DOCUMENT_RETRIEVER=cosmos` and `=azure_search`, compare groundedness/citation metrics before making search the default
- [ ] Tests: add `AzureSearchRetriever` unit tests mocking at the httpx layer per repo convention; extend `tests/conftest.py` search mocks
- [ ] Update CLAUDE.md + ARCHITECTURE.md deployed-reality sections (both currently state "Azure AI Search is NOT the runtime retriever") and the integration matrix

Later / optional

- [ ] Integrated vectorization (`integratedvectorizerstrategy.py` has TODO markers) so the index embeds at indexing time instead of client-side
- [ ] Semantic ranker on hybrid results (`AZURE_SEARCH_SEMANTIC_RANKER`) once on a paid semantic tier
- [ ] `USE_AGENTIC_KNOWLEDGEBASE` knowledge-agent path (needs `knowledgebases` preview SDK pin per CLAUDE.md gotcha)

- [ ] Add CI workflows (tests + lint); only pages.yml + doc-update exist
- [ ] Expand scaffold tests into real integration coverage (multi-agent, verifier, GraphRAG, voice)
- [ ] Expand site/index.html portfolio content (feature matrix, use cases)
- [ ] Populate production evals; ground_truth_multimodal.jsonl is empty
- [ ] Resolve TODO markers in integratedvectorizerstrategy.py and cloudingestionstrategy.py
- [ ] Stage 2 cloud Functions: wire functions.bicep into main.bicep + enable functions service, or document as deferred
