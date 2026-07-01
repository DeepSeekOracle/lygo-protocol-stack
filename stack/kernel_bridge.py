"""Unified Nano-Kernel adapter for Protocols 2–5 (wraps P0.4 byte gate + optional Lyra validator)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Union

ROOT = Path(__file__).resolve().parents[1]
P0_PY = ROOT / "protocol0_nano_kernel" / "src" / "python"
if str(P0_PY) not in sys.path:
    sys.path.insert(0, str(P0_PY))

from lygo_p0 import validate_bytes  # noqa: E402


class NanoKernelBridge:
    """Protocol-facing kernel with stable IDs and verdict shapes."""

    kernel_id = "LYGO_P0_BRIDGE_v1.0"

    def validate(self, data: Any) -> Dict[str, Any]:
        raw = self._to_bytes(data)
        result = validate_bytes(raw)
        verdict = result["verdict"]
        risk = float(result.get("risk", 0.0))
        resonance = max(0.0, min(2.0, 1.618 - risk))
        return {
            "action": verdict,
            "verdict": verdict,
            "risk": risk,
            "phi_risk": result.get("phi_risk", risk),
            "entropy": result.get("entropy"),
            "compression": result.get("compression"),
            "reasoning": result.get("reasoning"),
            "resonance": round(resonance, 4),
            "hash": result.get("hash"),
        }

    def validate_verdict_token(self, data: Any) -> str:
        """Cognitive Bridge legacy: amplify | soften | quarantine."""
        v = self.validate(data)["verdict"].lower()
        return v if v in {"amplify", "soften", "quarantine"} else "quarantine"

    @staticmethod
    def _to_bytes(data: Any) -> bytes:
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        return json.dumps(data, sort_keys=True, default=str).encode("utf-8")