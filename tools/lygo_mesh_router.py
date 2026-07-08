#!/usr/bin/env python3
"""LYGO Mesh Router — SQLite cache of seen anchor hashes (BLE + local)."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from lygo_anchor_config import AnchorProfile, ROOT


class LygoMeshRouter:
    def __init__(self, db_path: Path | None = None):
        profile = AnchorProfile.load()
        self.db_path = db_path or profile.resolve_paths(ROOT)["mesh_db"]
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS anchors_seen (
                    hash_hex TEXT PRIMARY KEY,
                    source TEXT,
                    hop INTEGER DEFAULT 0,
                    permaweb_url TEXT,
                    first_seen REAL,
                    last_seen REAL
                )
                """
            )
            conn.commit()

    def record(self, hash_hex: str, source: str, permaweb_url: str = "", hop: int = 0) -> bool:
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT hash_hex FROM anchors_seen WHERE hash_hex=?", (hash_hex,))
            if cur.fetchone():
                conn.execute(
                    "UPDATE anchors_seen SET last_seen=?, hop=MIN(hop, ?) WHERE hash_hex=?",
                    (now, hop, hash_hex),
                )
                return False
            conn.execute(
                "INSERT INTO anchors_seen VALUES (?,?,?,?,?,?)",
                (hash_hex, source, hop, permaweb_url, now, now),
            )
            return True

    def list_recent(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM anchors_seen ORDER BY last_seen DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]