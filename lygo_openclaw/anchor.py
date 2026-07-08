"""Action ledger — honest stack receipts (no fake permaweb)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


def anchor_root() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "openclaw"


class KernelEggAnchor:
    def __init__(self) -> None:
        self.runs_dir = anchor_root() / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = anchor_root() / "action_runs.jsonl"

    def anchor(self, payload: dict[str, Any], *, enabled: bool = True) -> dict[str, str]:
        if not enabled:
            return {"status": "skipped", "receipt": ""}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        receipt_id = digest[:16]
        record = {
            "type": "LYGO_OPENCLAW_ACTION",
            "timestamp": time.time(),
            "receipt": receipt_id,
            "payload_sha256": digest,
            "summary": {
                "command": payload.get("command"),
                "node_id": payload.get("node_id"),
                "verdict": payload.get("verdict"),
            },
        }
        (self.runs_dir / f"{receipt_id}.json").write_text(
            json.dumps({**record, "payload": payload}, indent=2), encoding="utf-8"
        )
        with self.ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        return {
            "status": "ledger",
            "receipt": receipt_id,
            "kernel_egg_id": "lygo-openclaw-v10",
            "note": "python tools/openclaw_planter.py --i-consent",
        }