"""Tests for the session-memory + runtime middleware."""
from agents.middleware import (
    SESSION_MEMORY_PROMPT,
    ControlRoomContext,
    build_middleware,
    inject_runtime_context,
    session_summarization_middleware,
)
from langchain.agents.middleware import SummarizationMiddleware


def test_session_memory_prompt_has_required_sections():
    """The compaction prompt keeps the structured summary format."""
    for marker in (
        "## User Intent",
        "## Completed Work",
        "## Errors & Corrections",
        "## Active Work",
        "## Pending Tasks",
        "## Key References",
    ):
        assert marker in SESSION_MEMORY_PROMPT


def test_context_schema_defaults():
    ctx = ControlRoomContext()
    assert ctx.user_id == "local"
    assert ctx.session_id == ""


def test_summarization_middleware_wires_session_prompt():
    mw = session_summarization_middleware()
    assert isinstance(mw, SummarizationMiddleware)
    # summary_prompt should carry our compaction prompt when exposed as an attribute.
    assert getattr(mw, "summary_prompt", SESSION_MEMORY_PROMPT) == SESSION_MEMORY_PROMPT


def test_build_middleware_order():
    """Runtime-context hook runs first, then in-session summarization."""
    stack = build_middleware()
    assert stack[0] is inject_runtime_context
    assert isinstance(stack[1], SummarizationMiddleware)
