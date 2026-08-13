# Control Room — Chat frontend

A standalone **React + TypeScript + Vite** chat surface for the control-room
agent layer, modeled on the `markdown-messages` LangChain UI pattern. It renders
assistant replies as markdown and streams turns from the existing **Python**
LangGraph graph (`agents/graph.py:get_graph`) over the LangGraph SDK.

The Python graph is kept as-is; this frontend talks to it through the LangGraph
dev server. No CORS in local dev — Vite proxies `/api/langgraph` to the server.

## Prerequisites

- Node.js 22+
- The Python agent deps installed (`pip install -r agents-requirements.txt`)
  plus `langgraph-cli`: `pip install "langgraph-cli[inmem]"`
- `ANTHROPIC_API_KEY` in the repo-root `.env` (copy `.env.example`)

## Running

Two processes. From the **repo root**, start the agent server:

```bash
langgraph dev --port 2024
```

This serves the `control_room` graph declared in `langgraph.json`.

Then, from this `frontend/` directory:

```bash
npm install
npm run dev
```

Open http://localhost:4100. The Vite dev server proxies `/api/langgraph` to
`http://127.0.0.1:2024`, and the app uses that same-origin URL for the LangGraph
SDK.

## Pointing at a different server

Append `?agentServer=<url>` to the URL to target a remote LangGraph server
instead of the local proxy (e.g. `?agentServer=https://my-host/api`).

## Layout

- `src/patterns/control-room/preview.tsx` — the chat pattern (streaming, presets,
  empty + error states, new-session button)
- `src/components/` — chat UI primitives (bubbles, input, markdown, typing)
- `src/agent-config.ts` — server URL resolution + `control_room` assistant id
