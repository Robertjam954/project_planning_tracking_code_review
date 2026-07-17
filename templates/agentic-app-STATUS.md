# Status

Live checklist of what is left to complete for this agentic app, one section per
component category (see the portfolio prep workflow). Check a box (`[ ]` -> `[x]`)
as you finish. Same checkbox format the portfolio dashboard reads, so this rolls
up automatically. If a whole category does not apply, keep the heading and add a
single `- [x] N/A — <reason>` so the decision stays visible.

> Project: **<name>** · Framework: **<FastAPI+Anthropic | LangGraph | MS Agent Framework>** · Stage: **<scoping | build | integrate | deploy>**

## 1. Infra & databases
- [ ] Database provisioned + migrations (schema for app + agent state)
- [ ] Config + env schema defined (`.env.example`)
- [ ] Secrets management (no keys in git)
- [ ] Container / deploy target chosen (compose / serverless)
- [ ] Vector store (only if retrieval) — else `- [x] N/A`

## 2. Agents
- [ ] Agent roster + responsibilities defined
- [ ] Single agent OR supervisor/router + workers implemented
- [ ] Routing / hand-off ("report back") contract
- [ ] Model + params per agent; step/recursion cap

## 3. Tools
- [ ] Tools enumerated with input schemas
- [ ] Registered; per-agent tool subsets assigned
- [ ] Auth/secrets for external APIs; timeouts + error handling
- [ ] Unit test per tool

## 4. Memory
- [ ] Short-term: multi-turn conversation history wired (load/save per session)
- [ ] Persistence (DB) with graceful fallback
- [ ] Long-term / retrieval memory — else `- [x] N/A`
- [ ] History window / summarization strategy

## 5. Prompts
- [ ] Prompt registry (separate from code)
- [ ] One system/role prompt per agent
- [ ] Variables/placeholders documented; versioned

## 6. Frontend components
- [ ] Chat / agent surface wired to the agent endpoint
- [ ] Streaming / partial output
- [ ] Session UI (new / continue) + error & empty states
- [ ] Auth on the surface — else `- [x] N/A`

## 7. Tracing / observability / eval
- [ ] Per-turn + per-tool tracing (spans/logs) with a run/session id
- [ ] Token / latency / cost metrics
- [ ] Eval harness / LLM-judge — else `- [x] N/A`

## Cross-cutting
- [ ] Auth & secrets
- [ ] Deployment / hosting configured
- [ ] Tests: agent-loop + end-to-end smoke
- [ ] Claude PR code-review workflow enabled (`claude-review.yml`)
- [ ] README + ARCHITECTURE updated to final state
