"""Workflow run ledger — honest git-stack manifest (no fake permaweb URLs)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

SIGNATURE = "Δ9Φ963-SANDCASTLE-ANCHOR-v1.0"


def anchor_root() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "sandcastle"


class KernelEggAnchor:
    """Append run receipts; optional kernel egg via workflow_orchestrator_planter."""

    def __init__(self) -> None:
        self.runs_dir = anchor_root() / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = anchor_root() / "workflow_runs.jsonl"

    def anchor(self, payload: dict[str, Any], *, enabled: bool = True) -> dict[str, str]:
        if not enabled:
            return {"status": "skipped", "receipt": ""}
        manifest = {
            "type": "LYGO_WORKFLOW_RUN",
            "timestamp": time.time(),
            "signature": SIGNATURE,
            "payload_sha256": hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode()
            ).hexdigest(),
            "summary": {
                "workflow_name": payload.get("workflow_name"),
                "node_id": payload.get("node_id"),
                "memory_id": payload.get("memory_id"),
                "verdict": payload.get("verdict"),
            },
        }
        receipt_id = manifest["payload_sha256"][:16]
        run_path = self.runs_dir / f"{receipt_id}.json"
        run_path.write_text(json.dumps({**manifest, "payload": payload}, indent=2), encoding="utf-8")
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(manifest, sort_keys=True) + "\n")
        return {
            "status": "ledger",
            "receipt": receipt_id,
            "path": str(run_path.relative_to(anchor_root().parent)),
            "kernel_egg_id": "lygo-sandcastle-v10",
            "note": "Plant permaweb capsule with tools/workflow_orchestrator_planter.py --i-consent",
        }