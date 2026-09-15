from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any

from paths import MYCELIUM, RECEIPTS, ensure_dirs
from p3_note import vortex_signature


def create_node(command: str, args: list[str] | None = None) -> dict[str, Any]:
    args = args or []
    raw = f"{time.time():.6f}|{command}|{' '.join(args)}"
    light = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    mass = max(0.1, min(1.0, 1.0 - len(command) / 500.0))
    return {
        "light_code": light,
        "ethical_mass": round(mass, 3),
        "command": command,
        "signature": "Δ9Φ963-SDA-P5-v1",
    }


def write_receipt(*, prompt: str, output: str, model: str, gate: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_dirs()
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    MYCELIUM.mkdir(parents=True, exist_ok=True)
    rid = str(uuid.uuid4())
    node = create_node("chat")
    rec = {
        "id": rid,
        "ts": time.time(),
        "model": model,
        "message_sha256": hashlib.sha256((prompt or "").encode("utf-8")).hexdigest(),
        "output_sha256": hashlib.sha256((output or "").encode("utf-8")).hexdigest(),
        "gate_verdict": gate.get("verdict"),
        "p3": vortex_signature(prompt or ""),
        "p5": node,
        "has_image": bool((extra or {}).get("has_image")),
    }
    (RECEIPTS / f"{rid}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    row = {"id": rid, "ts": rec["ts"], "bundle": {"receipt_id": rid, "model": model, "verdict": rec["gate_verdict"]}}
    with (MYCELIUM / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return rec
