// Same-origin proxy path (see vite.config.ts) so there are no browser CORS
// issues in local dev. The proxy forwards to the Python `langgraph dev` server
// on http://127.0.0.1:2024. Override with ?agentServer=<url> for a remote host.
const LOCAL_AGENT_SERVER_URL = `${window.location.origin}/api/langgraph`;

function resolveAgentServerUrl(): string {
  const params = new URLSearchParams(window.location.search);
  const value = params.get("agentServer");
  if (!value || value === "local") return LOCAL_AGENT_SERVER_URL;
  return value;
}

export const AGENT_SERVER_URL = resolveAgentServerUrl();

// Graph id registered in the Python project's langgraph.json.
export const ASSISTANT_ID = "control_room";
