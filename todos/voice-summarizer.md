# Voice Summarizer

> transcription app · [local-ai-transcript-app](https://github.com/Robertjam954/local-ai-transcript-app)

- [ ] Add pytest for backend (/api/transcribe, /api/clean) + vitest for React components
- [ ] Clean up the 3 'ok' commits on main (rebase with real messages)
- [ ] Decide Azure App Service vs Pages-only; finish azd up or revert azure.yaml/infra/scripts
- [ ] Investigate/remove infra/core/compose_docker_app sample app (likely noise)
- [ ] Local RAG (backend scaffolded, guarded/off): install Ollama + pull nomic-embed-text & a chat model, free disk (~6-10GB), `uv sync --extra rag`, set RAG_ENABLED=true, then smoke-test /api/rag/index + /api/rag/ask. Design adapted from [ObsidianRAG](https://github.com/Vasallo94/ObsidianRAG); see .azure/deployment-plan.md
- [ ] Local RAG: persist transcripts + auto-index after cleanup (app is stateless today; index must be called explicitly)
- [ ] Local RAG: frontend "Ask your transcripts" panel calling /api/rag/ask with answer + citation chips
- [ ] Local RAG: add tests (chunking, RRF fusion, guarded endpoints); optional streaming + GraphRAG wikilink expansion
