"""Middleware for the control-room agents.

In-session (short-term) memory has two parts here:
  - a **checkpointer** (`get_checkpointer`, re-exported) keeps thread state across
    turns, keyed by `thread_id` - pass it to `create_agent(checkpointer=...)`.
  - `SummarizationMiddleware` compacts the transcript with `SESSION_MEMORY_PROMPT`
    once it grows past a threshold, so long sessions stay inside the context window.

**Runtime** is injected via `context_schema=ControlRoomContext`: hooks and tools read
per-invocation dependencies (user / session) off `runtime.context`, and run identity
off `runtime.execution_info`. Invoke with `context=ControlRoomContext(...)`.

Refs: docs.langchain.com/oss/python/langchain/{short-term-memory, middleware/built-in, runtime}.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from langchain.agents import AgentState
from langchain.agents.middleware import SummarizationMiddleware, before_model
from langgraph.runtime import Runtime

from .config import settings
from .memory import get_checkpointer  # short-term memory: re-exported for create_agent

__all__ = [
    "SESSION_MEMORY_PROMPT",
    "ControlRoomContext",
    "get_checkpointer",
    "session_summarization_middleware",
    "inject_runtime_context",
    "build_middleware",
]

log = logging.getLogger("control_room")

# When to compact and how much recent context to keep after compaction.
SUMMARIZE_TRIGGER_TOKENS = 3000
SUMMARIZE_TRIGGER_MESSAGES = 40
SUMMARIZE_KEEP_MESSAGES = 20


# In-session conversation summary / compaction prompt. Optimizes for the agent's
# ability to resume work, not human readability.
SESSION_MEMORY_PROMPT = """
Compress the conversation into a structured summary
that preserves all information needed to continue work seamlessly. Optimize for the assistant's
ability to continue working, not human readability.

<analysis-instructions>
Before generating your summary, analyze the transcript in <think>...</think> tags:
1. What did the user originally request? (Exact phrasing)
2. What actions succeeded? What failed and why?
3. Did the user correct or redirect the assistant at any point?
4. What was actively being worked on at the end?
5. What tasks remain incomplete or pending?
6. What specific details (IDs, paths, values, names) must survive compression?
</analysis-instructions>

<summary-format>
## User Intent
The user's original request and any refinements. Use direct quotes for key requirements.
If the user's goal evolved during the conversation, capture that progression.

## Completed Work
Actions successfully performed. Be specific:
- What was created, modified, or deleted
- Exact identifiers (file paths, record IDs, URLs, names)
- Specific values, configurations, or settings applied

## Errors & Corrections
- Problems encountered and how they were resolved
- Approaches that failed (so they aren't retried)
- User corrections: "don't do X", "actually I meant Y", "that's wrong because..."
Capture corrections verbatim - these represent learned preferences.

## Active Work
What was in progress when the session ended. Include:
- The specific task being performed
- Direct quotes showing exactly where work left off
- Any partial results or intermediate state

## Pending Tasks
Remaining items the user requested that haven't been started.
Distinguish between "explicitly requested" and "implied/assumed."

## Key References
Important details needed to continue:
- Identifiers: IDs, paths, URLs, names, keys
- Values: numbers, dates, configurations, credentials (redacted)
- Context: relevant background information, constraints, preferences
- Citations: sources referenced during the conversation
</summary-format>

<preserve-rules>
Always preserve when present:
- Exact identifiers (IDs, paths, URLs, keys, names)
- Error messages verbatim
- User corrections and negative feedback
- Specific values, formulas, or configurations
- Technical constraints or requirements discovered
- The precise state of any in-progress work
</preserve-rules>

<compression-rules>
- Weight recent messages more heavily - the end of the transcript is the active context
- Omit pleasantries, acknowledgments, and filler ("Sure!", "Great question")
- Omit system context that will be re-injected separately
- Keep each section under 500 words; condense older content to make room for recent
- If you must cut details, preserve: user corrections > errors > active work > completed work
</compression-rules>
""".strip()


@dataclass
class ControlRoomContext:
    """Runtime context (dependency injection) for a single agent invocation.

    Pass as `create_agent(..., context_schema=ControlRoomContext)` and supply on
    invoke: `agent.invoke(payload, context=ControlRoomContext(user_id=..., session_id=...))`.
    """

    user_id: str = "local"
    session_id: str = ""


@before_model
def inject_runtime_context(
    state: AgentState, runtime: Runtime[ControlRoomContext]
) -> dict[str, Any] | None:
    """Log run identity + context each turn from the Runtime. Does not mutate state.

    Demonstrates reading `runtime.context` (per-invocation deps) and, when available,
    `runtime.execution_info` (thread/run id) for correlating traces.
    """
    ctx = runtime.context
    thread_id = run_id = ""
    try:  # execution_info needs langgraph>=1.1.5; degrade quietly otherwise
        info = runtime.execution_info
        thread_id, run_id = info.thread_id, info.run_id
    except Exception:
        pass
    log.info(
        "agent turn | user=%s session=%s thread=%s run=%s messages=%d",
        getattr(ctx, "user_id", "?"),
        getattr(ctx, "session_id", "?"),
        thread_id,
        run_id,
        len(state["messages"]),
    )
    return None


def session_summarization_middleware(model: Any | None = None) -> SummarizationMiddleware:
    """In-session compaction: summarize with SESSION_MEMORY_PROMPT past a threshold."""
    return SummarizationMiddleware(
        model=model or f"anthropic:{settings.model}",
        summary_prompt=SESSION_MEMORY_PROMPT,
        trigger=[
            ("tokens", SUMMARIZE_TRIGGER_TOKENS),
            ("messages", SUMMARIZE_TRIGGER_MESSAGES),
        ],
        keep=("messages", SUMMARIZE_KEEP_MESSAGES),
    )


def build_middleware(model: Any | None = None) -> list:
    """The middleware stack: runtime-context hook, then in-session summarization.

    Consumed by a `create_agent(..., middleware=build_middleware(),
    context_schema=ControlRoomContext, checkpointer=get_checkpointer())`.
    """
    return [inject_runtime_context, session_summarization_middleware(model)]
