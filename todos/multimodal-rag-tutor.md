# Status

Live checklist of what is left to complete on this project, in the same checkbox
format the portfolio tracking dashboard reads. Check a box (`[ ]` -> `[x]`) as
you finish.

> Project: **Multimodal RAG AI Tutor** · Stage: **retrieval backend migration**
> Deployed: Azure Container Apps (RG `ai-tutor`, eastus2), Cosmos NoSQL retriever.
> Active direction (2026-07-16): local Obsidian-vault RAG with local AI models
> (Ollama); Azure AI Search implemented but gated off in infra to avoid the
> ~$75+/mo service cost.

## 1. Azure AI Search integration (code complete, provisioning gated off)
- [x] `infra/core/search/search-services.bicep` hardened: SKU/semantic params, `disableLocalAuth: true` (keyless-only)
- [x] Search module composed into `infra/main.bicep` behind `useAzureSearch` (default `false` - no billable service until flipped)
- [x] Search env vars wired into backend container (`AZURE_SEARCH_SERVICE/INDEX/SEMANTIC_RANKER`); `DOCUMENT_RETRIEVER` now a bicep param (default `cosmos`)
- [x] RBAC in `infra/app/rbac.bicep`: Search Service Contributor + Search Index Data Contributor for backend managed identity and deploying user
- [x] `prepdocslib/servicesetup.py`: index schema rebuilt as SDK model objects (raw dicts would fail `create_or_update_index`); `parent_id` added; image vector moved to top-level `image_vector` (vector fields can't live in complex collections)
- [x] `prepdocslib/searchmanager.py`: upsert writes `parent_id`, strips embeddings from `images`
- [x] `core/azure_search_retriever.py`: hybrid BM25+vector retriever with optional semantic rerank, keyless auth, `get_document` chunk reassembly; registered as `DOCUMENT_RETRIEVER=azure_search`
- [x] `infra/main.bicep` compiles clean (azd-bundled bicep)
- [ ] `python scripts/copy_prepdocslib.py` to sync function bundles (required after any prepdocslib change; now also covers new `obsidianstrategy.py`)
- [ ] Unit tests for `AzureSearchRetriever` + schema
- [ ] If ever enabled: `azd env set USE_AZURE_SEARCH true && azd provision`, run `prepdocs.sh`, eval parity vs Cosmos

## 2. Local Obsidian RAG with local AI models (active direction)
- [x] `prepdocslib/obsidianstrategy.py`: vault ingestion (frontmatter/#tag/[[wikilink]] parsing, chunk + embed, upsert to configured vector store, source_type='note', obsidian:// deep links); `prepdocs.py --source obsidian --vault <path>` wired (confirmed with user 2026-07-17)
- [ ] `core/embeddings_client.py`: `MODE=local` routes `embed_one`/`embed_texts` to Ollama's OpenAI-compatible `/v1/embeddings` (`OLLAMA_EMBED_MODEL`, default `nomic-embed-text`) - chat side already routes to Ollama via `agents/_llm.py`
- [ ] `core/obsidian_retriever.py`: scan `OBSIDIAN_VAULT_PATH` for `*.md`, parse `[[wikilinks]]`/#tags/frontmatter, chunk + embed with disk cache, cosine retrieval with link-neighbor expansion, `get_document` per note; register as `DOCUMENT_RETRIEVER=obsidian`
- [ ] Install Ollama + pull models (`nomic-embed-text` for embeddings, small chat model); not currently installed on this machine
- [ ] Smoke-test against the real vault (`~/Documents/Obsidian Vault` - currently only 2 notes; second stale copy in `Documents - Robert's iMac/Obsidian Vault`)
- [ ] Tests: temp-vault fixture with mocked embeddings
- [ ] Decide how/whether vault content reaches the cloud deploy (local-only demo vs prepdocs ingestion into Cosmos)

## 3. Deployment health
- [ ] Investigate: deployed app URL not responding (DNS resolves, HTTPS times out; `az` CLI blocked by corporate TLS reset - try ARM REST via curl or portal). URL: `https://ca-backend-terrjvrcuwxim.livelyisland-19dcdcfb.eastus2.azurecontainerapps.io`

## 4. Docs & repo hygiene
- [ ] Update CLAUDE.md + ARCHITECTURE.md: search now provisionable-but-gated, `azure_search` retriever exists, Obsidian/local-mode direction
- [ ] Update portfolio todos (`project_planning_tracking_code_review/todos/multimodal-rag-tutor.md`) to reflect the pivot
- [ ] Pre-existing: CI workflows, eval population, Stage 2 functions (see todos file)
