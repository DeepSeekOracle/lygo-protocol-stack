"""Implant ledger — honest receipts (no fake permaweb)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


def anchor_root() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "prompt_vault"


class KernelEggAnchor:
    def __init__(self) -> None:
        self.runs = anchor_root() / "runs"
        self.runs.mkdir(parents=True, exist_ok=True)
        self.ledger = anchor_root() / "implant_runs.jsonl"

    def anchor(self, payload: dict[str, Any], *, enabled: bool = True) -> dict[str, str]:
        if not enabled:
            return {"status": "skipped", "receipt": ""}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        receipt_id = digest[:16]
        record = {
            "type": "LYGO_LPIS_IMPLANT",
            "timestamp": time.time(),
            "receipt": receipt_id,
            "payload_sha256": digest,
            "summary": {
                "prompt_id": payload.get("prompt_id") or payload.get("variant_id"),
                "target": payload.get("target"),
            },
        }
        (self.runs / f"{receipt_id}.json").write_text(
            json.dumps({**record, "payload": payload}, indent=2), encoding="utf-8"
        )
        with self.ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        return {
            "status": "ledger",
            "receipt": receipt_id,
            "kernel_egg_id": "lygo-lpis-v10",
            "note": "python tools/lpis_planter.py --i-consent",
        }