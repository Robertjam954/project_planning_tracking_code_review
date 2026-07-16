# Multimodal RAG Tutor

> live on Azure · [multimodal_rag_application](https://github.com/Robertjam954/multimodal_rag_application)

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
