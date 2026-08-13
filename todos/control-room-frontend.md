# Control Room — Chat frontend TODO

Remaining work for the React chat surface in [`frontend/`](../frontend), modeled
on the `markdown-messages` LangChain UI pattern. The surface talks to the
existing **Python** LangGraph graph (`agents/graph.py:get_graph`) served by
`langgraph dev`, via the `control_room` graph id in [`langgraph.json`](../langgraph.json).

Full frontend run instructions: [`frontend/README.md`](../frontend/README.md).

> Stage: **scaffolded, not yet installed/run** · Framework: React + TS + Vite

## Scaffolded (files written)
- [x] Vite + React + TS project under `frontend/` (`package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `postcss.config.js`)
- [x] Self-contained Tailwind v4 theme tokens + markdown prose styles (`src/styles.css`)
- [x] Chat UI primitives ported from markdown-messages: `Bubble`, `ChatContainer`, `ChatInput`, `PresetPrompts`, `TypingIndicator`, `Markdown`, `icons`
- [x] Pattern preview `src/patterns/control-room/preview.tsx`: streaming via LangGraph SDK `useStream`, markdown AI replies, control-room presets, empty state, error state, new-session button
- [x] Same-origin proxy config: Vite proxies `/api/langgraph` -> `http://127.0.0.1:2024` (no CORS in dev)
- [x] `langgraph.json` added at repo root so `langgraph dev` serves the graph as `control_room`

## Open — setup & verification
- [ ] `npm install` in `frontend/` (deferred — will run manually)
- [ ] Install `langgraph-cli`: `pip install "langgraph-cli[inmem]"`
- [ ] Typecheck / build: `npm run build` passes with no TS errors
- [ ] Confirm the SDK import + API: `useStream` from `@langchain/langgraph-sdk/react`
      (or switch to `@langchain/react` `useStream` to match markdown-messages exactly — decide one)
- [ ] End-to-end smoke: `langgraph dev` up + `npm run dev`, send a preset, see a streamed markdown reply at http://localhost:4100

## Open — decisions / polish
- [ ] SDK stack: standardize on `@langchain/langgraph-sdk` vs the markdown-messages
      `@langchain/react` + workspace `@langchain/playground-agents` stack
- [ ] Verify the Python graph streams assistant tokens over the SDK (nodes use
      `graph.stream()`; confirm message events reach `useStream`)
- [ ] Wire the durable `ConversationStore` session id to the SDK thread id so the
      Historian can recall UI sessions (today CLI uses `--session`; UI uses SDK threadId)
- [ ] Ambiguous/empty request UX: supervisor should return a clarifying question,
      not route to END silently (shared with STATUS.md item 6 + `docs/agents-todo.md`)
- [ ] Auth on the surface if deployed beyond localhost (today: local only, N/A)

## Notes
- Backend stays Python; the React app is a thin client over the LangGraph SDK.
- This satisfies the STATUS.md "(Optional) chat surface" frontend item; the
  original line said "Streamlit" — now realized as a React surface instead.
