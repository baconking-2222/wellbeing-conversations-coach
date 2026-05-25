"""Local SQLite store for practice sessions."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from scoring.score import Scorecard

DB_PATH = Path(__file__).parent / "data" / "sessions.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    mode TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    scenario_title TEXT NOT NULL,
    persona_id TEXT NOT NULL,
    activity_id TEXT,
    status TEXT NOT NULL,
    transcript TEXT,
    scorecard_json TEXT,
    overall_score INTEGER,
    overall_max INTEGER,
    safeguarding_flag INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)


def create_session(*, mode: str, scenario: dict, persona_id: str, activity_id: str | None) -> str:
    sid = uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (id, created_at, mode, scenario_id, scenario_title, persona_id, activity_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (sid, now, mode, scenario["id"], scenario["title"], persona_id, activity_id),
        )
    return sid


def save_transcript(session_id: str, transcript: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE sessions SET transcript = ?, status = 'transcript' WHERE id = ?",
            (transcript, session_id),
        )


def save_scorecard(session_id: str, sc: Scorecard) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE sessions
               SET scorecard_json = ?,
                   overall_score = ?,
                   overall_max = ?,
                   safeguarding_flag = ?,
                   status = 'scored'
             WHERE id = ?
            """,
            (
                sc.to_json(),
                sc.overall_score,
                sc.overall_max,
                int(sc.safeguarding_flag),
                session_id,
            ),
        )


def get_session(session_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        return None
    out = dict(row)
    if out.get("scorecard_json"):
        out["scorecard"] = json.loads(out["scorecard_json"])
    return out


def list_sessions(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, mode, scenario_title, overall_score, overall_max, "
            "safeguarding_flag, status FROM sessions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_session(session_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def delete_all_sessions() -> None:
    """Wipe every session row. Used by the Clear history button."""
    with _connect() as conn:
        conn.execute("DELETE FROM sessions")
