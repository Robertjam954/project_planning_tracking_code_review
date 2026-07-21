"""Agent state and type definitions for the control-room graph."""
from __future__ import annotations

from typing import Literal

from langgraph.graph import MessagesState


class ControlRoomState(MessagesState):
    """State for the control-room supervisor graph.

    Extends MessagesState with fields for routing and context. The supervisor
    will set worker to the next node to invoke, and context tracks what the
    user asked for (for historian recall and multi-turn coherence).
    """

    worker: Literal["planner", "tracker", "reviewer", "historian", "END"] = "END"
    context: str = ""  # e.g., "planning a new app", "checking progress", "asking history"
