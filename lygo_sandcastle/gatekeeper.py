"""P0 gatekeeper for workflow YAML — stack byte_entropy_filter when available."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
P0_SRC = ROOT / "protocol0_byte_entropy_filter" / "src" / "python"
if str(P0_SRC) not in sys.path:
    sys.path.insert(0, str(P0_SRC))

try:
    from byte_entropy_filter import validate_bytes as _validate_bytes  # type: ignore

    P0_AVAILABLE = True
except ImportError:
    P0_AVAILABLE = False
    _validate_bytes = None  # type: ignore


class P0Gatekeeper:
    def __init__(self, max_bytes: int = 65536):
        self.max_bytes = max_bytes

    def validate(self, workflow_yaml: str) -> dict[str, Any]:
        data = workflow_yaml.encode("utf-8")
        if len(data) > self.max_bytes:
            return {
                "verdict": "QUARANTINE",
                "reason": "size_exceeded",
                "reasoning": f"Workflow YAML {len(data)} > {self.max_bytes}",
            }
        if P0_AVAILABLE and _validate_bytes:
            out = _validate_bytes(data)
            return {
                "verdict": out.get("verdict", "SOFTEN"),
                "reasoning": out.get("reasoning", ""),
                "phi_risk": out.get("phi_risk"),
                "entropy": out.get("entropy"),
            }
        return {
            "verdict": "SOFTEN",
            "reasoning": "P0 shim: size OK, byte_entropy_filter unavailable",
        }