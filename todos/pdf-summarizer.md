# Academic Paper Analyst

> PDF summarizer chatbot · [local_pdf_summarizer_chatbot](https://github.com/Robertjam954/local_pdf_summarizer_chatbot) · [project page](https://robertjam954.github.io/local_pdf_summarizer_chatbot/)

Deployment decision (2026-07-17): **GitHub Pages only** - the `site/` landing page is the
project's public deployment; the app runs locally against LM Studio (default model
`qwen/qwen3-vl-4b`). No Azure/Render app deploy.

- [x] Decide on paper library + RAG search - RESOLVED 2026-07-17: removed; project stays a pure PDF summarizer (implementation preserved in git history, commit `0436757`; plan `docs/plans/0003` marked withdrawn)
- [x] Decide deployment target - RESOLVED 2026-07-17: GitHub Pages only, no Azure app
- [ ] Recreate the dev venv after the src/ flatten (`cd src && python -m venv .venv && pip install -r requirements.txt`)
- [ ] Smoke-test the app end-to-end with qwen/qwen3-vl-4b (vision) and google/gemma-3-1b (text fallback)
- [ ] Decide whether to restructure the repo to match agentic-ai-app-template (raised 2026-07-17, then paused)
