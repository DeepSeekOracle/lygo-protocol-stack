"""Boot chain measurement — golden reference compare when fixture exists."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_BOOT = ROOT / "protocol6_quantum_attest" / "fixtures" / "boot_golden.sha256"


def measure_boot_chain() -> dict[str, Any]:
    """Synthetic boot measurement (OS + kernel identity); replace with measured boot when available."""
    payload = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "boot_layer": "software-measurement-v1",
    }
    canonical = json.dumps(payload, sort_keys=True).encode("utf-8")
    boot_hash = hashlib.sha256(canonical).hexdigest()
    golden_match: bool | None = None
    if GOLDEN_BOOT.is_file():
        golden = GOLDEN_BOOT.read_text(encoding="utf-8").strip().split()[0]
        golden_match = boot_hash == golden
    return {
        "boot_hash": boot_hash,
        "golden_match": golden_match,
        "golden_file": str(GOLDEN_BOOT) if GOLDEN_BOOT.is_file() else None,
    }