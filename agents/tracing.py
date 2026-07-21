"""LangSmith tracing setup.

When LANGCHAIN_API_KEY is present, every LangGraph node and tool call is captured
as a span in the configured project. No-op (local logging only) otherwise, so the
agents run fine without a LangSmith account. See docs/agents-plan.md matrix row 7.
"""
from __future__ import annotations

import logging
import os

from .config import settings

log = logging.getLogger("control_room")


def setup_tracing() -> bool:
    """Enable LangSmith tracing if a key is configured. Returns True if enabled."""
    if not settings.langsmith_api_key:
        return False
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    log.info("LangSmith tracing enabled -> project %s", settings.langsmith_project)
    return True
