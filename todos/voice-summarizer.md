# Voice Summarizer

> transcription app · [local-ai-transcript-app](https://github.com/Robertjam954/local-ai-transcript-app)

- [ ] Add pytest for backend (/api/transcribe, /api/clean) + vitest for React components
- [ ] Clean up the 3 'ok' commits on main (rebase with real messages)
- [ ] Decide Azure App Service vs Pages-only; finish azd up or revert azure.yaml/infra/scripts
- [ ] Investigate/remove infra/core/compose_docker_app sample app (likely noise)
- [ ] FUTURE: add RAG + voice search over transcripts, adapting the VoiceRAG pattern from [aisearch-openai-rag-audio](https://github.com/Robertjam954/aisearch-openai-rag-audio) (GPT-4o Realtime + Azure AI Search + citations). Resolve local-first vs Azure-cloud tension first. See Future Enhancements in .azure/deployment-plan.md
