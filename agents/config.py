"""Configuration for the control-room agent layer.

Reads .env (never committed). Paths point at the repo's existing state files -
projects.json, data/history.json, todos/*.md, scripts/ - which are the agents'
source of truth (see docs/adr/0002). Import-safe: reading config never requires
the LLM SDKs, so `python -m agents --help` works before `pip install`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Default model per user memory: pipeline work uses a Sonnet-tier model; the old
# claude-sonnet-4-20250514 pin is RETIRED - use claude-sonnet-5.
DEFAULT_MODEL = "claude-sonnet-5"


def _load_dotenv() -> None:
    """Best-effort .env load; no hard dependency on python-dotenv."""
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except Exception:
        # Fall back to whatever is already in the environment.
        pass


@dataclass
class Settings:
    anthropic_api_key: str = ""
    model: str = DEFAULT_MODEL
    temperature: float = 0.0

    # GitHub token for the Reviewer (private repos need `repo` scope).
    github_token: str = ""

    # LangSmith tracing (optional).
    langsmith_api_key: str = ""
    langsmith_project: str = "control-room-agents"

    # Loop safety.
    max_supervisor_steps: int = 8      # soft guard: force FINISH past this
    max_tool_steps: int = 6            # per-worker tool-call loop cap
    recursion_limit: int = 40          # LangGraph hard cap

    # Paths (the agents' state).
    root: Path = ROOT
    data_dir: Path = field(default_factory=lambda: ROOT / "data")
    todos_dir: Path = field(default_factory=lambda: ROOT / "todos")
    scripts_dir: Path = field(default_factory=lambda: ROOT / "scripts")
    projects_json: Path = field(default_factory=lambda: ROOT / "projects.json")
    history_json: Path = field(default_factory=lambda: ROOT / "data" / "history.json")
    memory_db: Path = field(default_factory=lambda: ROOT / "data" / "agent_memory.db")
    checkpoint_db: Path = field(default_factory=lambda: ROOT / "data" / "agent_checkpoints.db")

    @classmethod
    def load(cls) -> "Settings":
        _load_dotenv()
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=os.getenv("CONTROL_ROOM_MODEL", DEFAULT_MODEL),
            temperature=float(os.getenv("CONTROL_ROOM_TEMPERATURE", "0.0")),
            github_token=os.getenv("PORTFOLIO_TOKEN", "") or os.getenv("GH_TOKEN", ""),
            langsmith_api_key=os.getenv("LANGCHAIN_API_KEY", "") or os.getenv("LANGSMITH_API_KEY", ""),
            langsmith_project=os.getenv("LANGCHAIN_PROJECT", "control-room-agents"),
        )

    def require_api_key(self) -> None:
        if not self.anthropic_api_key:
            raise SystemExit(
                "ANTHROPIC_API_KEY is not set. Add it to "
                f"{self.root / '.env'} (copy .env.example) and retry."
            )


settings = Settings.load()
