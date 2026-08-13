"""Agent node functions for the control-room graph.

Each worker node is a LangChain agent (built with `create_agent`) that takes the
current state, invokes its model with the worker's system prompt and tool subset,
and returns updated state. The supervisor node routes to the correct worker.

Refactored onto the LangChain agent template (`langchain.agents.create_agent`):
one shared model config, one agent object per role. See the LangChain "Core
components" docs (Model / Tools / System prompt) for the template this follows.
"""
from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command

from .config import settings
from .prompts import get_prompt
from .state import ControlRoomState
from .tools import (
    HISTORIAN_TOOLS,
    PLANNER_TOOLS,
    REVIEWER_TOOLS,
    TRACKER_TOOLS,
)

# Tool subset per worker role.
_ROLE_TOOLS = {
    "planner": PLANNER_TOOLS,
    "tracker": TRACKER_TOOLS,
    "reviewer": REVIEWER_TOOLS,
    "historian": HISTORIAN_TOOLS,
}

# Lazily-built, cached agent objects + shared model, keyed so a CLI `--model`
# override (which mutates settings.model) rebuilds them instead of going stale.
_MODEL: Any = None
_MODEL_KEY: tuple[str, float] | None = None
_AGENTS: dict[str, Any] = {}


def _model_key() -> tuple[str, float]:
    return (settings.model, settings.temperature)


def _get_model() -> Any:
    """Return the shared chat model, rebuilding it if settings changed."""
    global _MODEL, _MODEL_KEY, _AGENTS
    key = _model_key()
    if _MODEL is None or _MODEL_KEY != key:
        _MODEL = init_chat_model(
            f"anthropic:{settings.model}",
            temperature=settings.temperature,
        )
        _MODEL_KEY = key
        _AGENTS = {}  # invalidate cached agents bound to the old model
    return _MODEL


def _get_agent(role: str) -> Any:
    """Return the cached `create_agent` for a role, building it on first use."""
    model = _get_model()  # may reset _AGENTS if the model changed
    if role not in _AGENTS:
        _AGENTS[role] = create_agent(
            model=model,
            tools=_ROLE_TOOLS[role],
            system_prompt=get_prompt(role),
        )
    return _AGENTS[role]


def _call_worker(state: ControlRoomState, role: str, tools: list) -> dict[str, Any]:
    """Invoke a worker agent with its tool subset.

    Args:
        state: Current graph state
        role: Worker name (planner, tracker, reviewer, historian)
        tools: Kept for signature compatibility; the tool subset is bound to the
            agent via `_ROLE_TOOLS[role]` at build time.

    Returns:
        {"messages": [...]} to append to state (LangChain message objects).
    """
    settings.require_api_key()
    agent = _get_agent(role)

    result = agent.invoke(
        {"messages": state["messages"]},
        config={"recursion_limit": max(2, settings.max_tool_steps * 2)},
    )
    # `create_agent` returns the full running message list; the graph's
    # MessagesState reducer de-duplicates by id, so returning it is safe and
    # appends only the new turns.
    return {"messages": result["messages"]}


def supervisor_node(state: ControlRoomState) -> Command[ControlRoomState]:
    """Route incoming requests to the correct worker.

    Uses the supervisor prompt to decide which worker to invoke (planner, tracker,
    reviewer, historian) based on the user's latest message. For ambiguous requests,
    clarifies intent before routing. Uses the shared LangChain chat model rather
    than a raw provider client, for consistency with the worker agents.
    """
    settings.require_api_key()
    model = _get_model()

    system = get_prompt("supervisor")
    response = model.invoke(
        [SystemMessage(content=system), *state["messages"]],
    )

    text = response.content
    if isinstance(text, list):
        text = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in text
        )
    worker_text = str(text).strip().lower()

    valid_workers = ("planner", "tracker", "reviewer", "historian", "end")
    if worker_text not in valid_workers:
        if "ambiguous" in worker_text or "clarify" in worker_text:
            first_line = worker_text.split("\n")[0]
            if first_line not in valid_workers:
                return Command(
                    goto="end",
                    update={
                        "messages": [
                            HumanMessage(content=f"I need clarification: {first_line}")
                        ],
                        "worker": "end",
                        "context": "clarified",
                    },
                )
        worker = "end"
    else:
        worker = worker_text

    return Command(
        goto=worker,
        update={"worker": worker, "context": worker},
    )


def planner_node(state: ControlRoomState) -> dict:
    return _call_worker(state, "planner", PLANNER_TOOLS)


def tracker_node(state: ControlRoomState) -> dict:
    return _call_worker(state, "tracker", TRACKER_TOOLS)


def reviewer_node(state: ControlRoomState) -> dict:
    return _call_worker(state, "reviewer", REVIEWER_TOOLS)


def historian_node(state: ControlRoomState) -> dict:
    return _call_worker(state, "historian", HISTORIAN_TOOLS)


def end_node(state: ControlRoomState) -> None:
    """Cleanup and finalize the run (optional)."""
    pass
