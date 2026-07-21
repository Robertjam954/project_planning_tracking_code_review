"""Memory: durable, queryable conversation store + LangGraph checkpointer.

Two layers (see docs/adr/0003):
  - `ConversationStore`: durable transcript in SQLite (data/agent_memory.db),
    listed / read / searched across sessions. This is what the Historian queries.
  - `get_checkpointer()`: a LangGraph SqliteSaver (data/agent_checkpoints.db) for
    multi-turn continuity within a run, keyed by thread id.

Both DB files are gitignored (per-user runtime state, not portfolio records).
"""
from __future__ import annotations

import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from .config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    title      TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    ts         REAL NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
"""


@dataclass
class Message:
    session_id: str
    ts: float
    role: str
    content: str


class ConversationStore:
    """Durable, queryable transcript of every agent conversation."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or settings.memory_db)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def new_session(self, title: str | None = None) -> str:
        session_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        self._conn.execute(
            "INSERT INTO sessions(session_id, created_at, title) VALUES (?,?,?)",
            (session_id, time.time(), title),
        )
        self._conn.commit()
        return session_id

    def ensure_session(self, session_id: str, title: str | None = None) -> None:
        row = self._conn.execute(
            "SELECT 1 FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row is None:
            self._conn.execute(
                "INSERT INTO sessions(session_id, created_at, title) VALUES (?,?,?)",
                (session_id, time.time(), title),
            )
            self._conn.commit()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        self.ensure_session(session_id)
        self._conn.execute(
            "INSERT INTO messages(session_id, ts, role, content) VALUES (?,?,?,?)",
            (session_id, time.time(), role, content),
        )
        # Title a session from its first user message.
        self._conn.execute(
            "UPDATE sessions SET title=? WHERE session_id=? AND (title IS NULL OR title='')",
            (content[:80], session_id),
        )
        self._conn.commit()

    def list_sessions(self, limit: int = 20) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT s.session_id, s.created_at, s.title, "
            "COUNT(m.id) AS n_messages "
            "FROM sessions s LEFT JOIN messages m ON m.session_id=s.session_id "
            "GROUP BY s.session_id ORDER BY s.created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    def get_messages(self, session_id: str) -> list[Message]:
        rows = self._conn.execute(
            "SELECT session_id, ts, role, content FROM messages "
            "WHERE session_id=? ORDER BY ts ASC",
            (session_id,),
        ).fetchall()
        return [Message(**dict(r)) for r in rows]

    def search(self, query: str, limit: int = 20) -> list[Message]:
        rows = self._conn.execute(
            "SELECT session_id, ts, role, content FROM messages "
            "WHERE content LIKE ? ORDER BY ts DESC LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        return [Message(**dict(r)) for r in rows]

    def close(self) -> None:
        self._conn.close()


def get_checkpointer():
    """LangGraph SqliteSaver for multi-turn continuity (short-term memory)."""
    from langgraph.checkpoint.sqlite import SqliteSaver

    settings.checkpoint_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.checkpoint_db, check_same_thread=False)
    return SqliteSaver(conn)
