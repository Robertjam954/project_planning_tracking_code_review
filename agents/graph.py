"""LangGraph StateGraph for the control-room multi-agent supervisor.

Topology: supervisor (router) -> {planner, tracker, reviewer, historian} workers.
Workers report back to supervisor, which composes final answer. Recursion cap at
settings.recursion_limit to prevent loops (see docs/adr/0002).
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .config import settings
from .memory import get_checkpointer
from .nodes import (
    end_node,
    historian_node,
    planner_node,
    reviewer_node,
    supervisor_node,
    tracker_node,
)
from .state import ControlRoomState
from .tracing import setup_tracing


def build_graph() -> "CompiledGraph":
    """Assemble and compile the control-room StateGraph.

    Returns:
        A compiled graph ready for invoke() / stream().
    """
    setup_tracing()

    builder = StateGraph(ControlRoomState)

    # Add nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("planner", planner_node)
    builder.add_node("tracker", tracker_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_node("historian", historian_node)
    builder.add_node("end", end_node)

    # Routing: START -> supervisor, then supervisor decides
    builder.add_edge(START, "supervisor")

    # Supervisor can route to any worker or END
    builder.add_edge("supervisor", "planner")
    builder.add_edge("supervisor", "tracker")
    builder.add_edge("supervisor", "reviewer")
    builder.add_edge("supervisor", "historian")
    builder.add_edge("supervisor", "end")

    # Workers route back to supervisor (not to END, so supervisor can compose)
    builder.add_edge("planner", "supervisor")
    builder.add_edge("tracker", "supervisor")
    builder.add_edge("reviewer", "supervisor")
    builder.add_edge("historian", "supervisor")

    # End node -> END
    builder.add_edge("end", END)

    # Compile with checkpointer and recursion limit
    graph = builder.compile(
        checkpointer=get_checkpointer(),
        interrupt_before=[],
        interrupt_after=[],
    )
    graph.step_timeout = 30  # seconds per step

    return graph


# Module-level graph cache
_graph = None


def get_graph() -> "CompiledGraph":
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
