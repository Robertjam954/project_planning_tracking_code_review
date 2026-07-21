"""Agent node functions for the control-room graph.

Each worker node is a callable that takes the current state, invokes the model
with the worker's system prompt and tool subset, and returns updated state.
The supervisor node routes to the correct worker.
"""
from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic
from langgraph.types import Command

from .config import settings
from .memory import ConversationStore
from .prompts import get_prompt
from .state import ControlRoomState
from .tools import (
    HISTORIAN_TOOLS,
    PLANNER_TOOLS,
    REVIEWER_TOOLS,
    TRACKER_TOOLS,
)


def _call_worker(
    state: ControlRoomState, role: str, tools: list
) -> dict[str, Any]:
    """Invoke a worker with the LLM, using its tool subset.

    Args:
        state: Current graph state
        role: Worker name (planner, tracker, reviewer, historian)
        tools: List of @tool callables available to this worker

    Returns:
        {"messages": updated messages} to append to state
    """
    settings.require_api_key()
    client = Anthropic()

    # Tool definitions for Claude
    tool_defs = []
    for tool_fn in tools:
        tool_defs.append({
            "name": tool_fn.name,
            "description": tool_fn.description,
            "input_schema": {
                "type": "object",
                "properties": tool_fn.input_schema.get("properties", {}),
                "required": tool_fn.input_schema.get("required", []),
            },
        })

    system = get_prompt(role)
    messages = [{"role": msg.get("role"), "content": msg.get("content")} for msg in state["messages"]]

    # Agentic loop: keep calling until model says DONE or we hit the step cap
    step = 0
    max_steps = settings.max_tool_steps
    while step < max_steps:
        step += 1
        response = client.messages.create(
            model=settings.model,
            max_tokens=2048,
            temperature=settings.temperature,
            system=system,
            tools=tool_defs,
            messages=messages,
        )

        # Append assistant response to message history
        assistant_content = []
        for block in response.content:
            if hasattr(block, "text"):
                assistant_content.append({"type": "text", "text": block.text})
            elif hasattr(block, "type") and block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        messages.append({"role": "assistant", "content": assistant_content})

        # If no tool calls, we're done
        tool_calls = [b for b in response.content if hasattr(b, "type") and b.type == "tool_use"]
        if not tool_calls or response.stop_reason == "end_turn":
            break

        # Execute tool calls
        tool_results = []
        for tool_call in tool_calls:
            try:
                tool_fn = next(t for t in tools if t.name == tool_call.name)
                result = tool_fn.invoke(tool_call.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": str(result),
                })
            except Exception as e:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": f"Error: {e}",
                })
        messages.append({"role": "user", "content": tool_results})

    return {"messages": messages}


def supervisor_node(state: ControlRoomState) -> Command[ControlRoomState]:
    """Route incoming requests to the correct worker.

    Uses the supervisor prompt to decide which worker to invoke (planner, tracker,
    reviewer, historian) based on the user's latest message. For ambiguous requests,
    clarifies intent before routing.
    """
    settings.require_api_key()
    client = Anthropic()

    system = get_prompt("supervisor")
    messages = [{"role": msg.get("role"), "content": msg.get("content")} for msg in state["messages"]]

    response = client.messages.create(
        model=settings.model,
        max_tokens=64,
        temperature=0.0,
        system=system,
        messages=messages,
    )

    worker_text = response.content[0].text.strip().lower()

    valid_workers = ("planner", "tracker", "reviewer", "historian", "end")
    if worker_text not in valid_workers:
        if "ambiguous" in worker_text or "clarify" in worker_text:
            first_line = worker_text.split("\n")[0]
            if first_line not in valid_workers:
                messages.append({
                    "role": "assistant",
                    "content": f"I need clarification: {first_line}"
                })
                return Command(
                    goto="end",
                    update={
                        "messages": messages,
                        "worker": "end",
                        "context": "clarified"
                    }
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
