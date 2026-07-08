"""P0 gatekeeper for prompt bodies (chunk sample + size cap)."""

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

MAX_PROMPT_BYTES = 2_000_000
SAMPLE_BYTES = 32768


class P0Gatekeeper:
    def __init__(self, max_bytes: int = MAX_PROMPT_BYTES, sample_bytes: int = SAMPLE_BYTES):
        self.max_bytes = max_bytes
        self.sample_bytes = sample_bytes

    def validate_text(self, text: str) -> dict[str, Any]:
        data = text.encode("utf-8", errors="replace")
        if len(data) > self.max_bytes:
            return {
                "verdict": "QUARANTINE",
                "reason": "size_exceeded",
                "reasoning": f"Prompt {len(data)} > {self.max_bytes}",
            }
        p0_cap = 8192
        sample = data[: min(self.sample_bytes, p0_cap)]
        if P0_AVAILABLE and _validate_bytes:
            out = _validate_bytes(sample)
            return {
                "verdict": out.get("verdict", "SOFTEN"),
                "reasoning": out.get("reasoning", ""),
                "sampled_bytes": len(sample),
                "total_bytes": len(data),
            }
        return {
            "verdict": "SOFTEN",
            "reasoning": "P0 shim: size OK",
            "sampled_bytes": len(sample),
            "total_bytes": len(data),
        }