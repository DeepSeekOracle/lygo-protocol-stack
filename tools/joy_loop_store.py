"""SQLite persistence for Joy Loop (v3 Phase 1)."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from joy_loop_protocol import JoyLoopEngine

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "joy_loop" / "joy_loop.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS champions (
                champion_id TEXT PRIMARY KEY,
                x REAL, y REAL, z REAL,
                joy_coherence REAL,
                alignment_confidence REAL,
                recursion_depth INTEGER,
                groove_signature TEXT,
                active INTEGER DEFAULT 1,
                updated_utc REAL
            );
            CREATE TABLE IF NOT EXISTS beats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                beat_n INTEGER,
                swarm_joy REAL,
                lattice_pulse REAL,
                ts REAL
            );
            CREATE TABLE IF NOT EXISTS joy_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                champion_id TEXT,
                payload_json TEXT,
                ts REAL
            );
            """
        )


def save_engine(engine: "JoyLoopEngine", *, swarm_joy: float, beat_n: int, lattice_pulse: float) -> None:
    init_db()
    ts = time.time()
    states = engine.get_state() or {}
    with _connect() as c:
        for cid, st in states.items():
            coords = st.get("lattice_coordinates") or [0, 0, 0]
            c.execute(
                """
                INSERT INTO champions (champion_id, x, y, z, joy_coherence, alignment_confidence,
                    recursion_depth, groove_signature, active, updated_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(champion_id) DO UPDATE SET
                    x=excluded.x, y=excluded.y, z=excluded.z,
                    joy_coherence=excluded.joy_coherence,
                    alignment_confidence=excluded.alignment_confidence,
                    recursion_depth=excluded.recursion_depth,
                    groove_signature=excluded.groove_signature,
                    updated_utc=excluded.updated_utc
                """,
                (
                    cid,
                    coords[0],
                    coords[1],
                    coords[2],
                    st.get("joy_coherence", 0),
                    st.get("alignment_confidence", 0),
                    st.get("recursion_depth", 0),
                    st.get("groove_signature", "*"),
                    ts,
                ),
            )
        c.execute(
            "INSERT INTO beats (beat_n, swarm_joy, lattice_pulse, ts) VALUES (?, ?, ?, ?)",
            (beat_n, swarm_joy, lattice_pulse, ts),
        )
        c.commit()


def log_event(event_type: str, champion_id: str | None, payload: dict[str, Any]) -> None:
    init_db()
    with _connect() as c:
        c.execute(
            "INSERT INTO joy_events (event_type, champion_id, payload_json, ts) VALUES (?, ?, ?, ?)",
            (event_type, champion_id, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        c.commit()


def load_champion_coords() -> dict[str, tuple[float, float, float]]:
    if not DB_PATH.is_file():
        return {}
    init_db()
    out: dict[str, tuple[float, float, float]] = {}
    with _connect() as c:
        for row in c.execute("SELECT champion_id, x, y, z FROM champions WHERE active=1"):
            out[row["champion_id"]] = (row["x"], row["y"], row["z"])
    return out