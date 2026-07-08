"""P0 byte-entropy gate + profitability estimate (honest scope per P0_HONEST_SPEC)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_P0 = _ROOT / "protocol0_byte_entropy_filter" / "src" / "python"
if str(_P0) not in sys.path:
    sys.path.insert(0, str(_P0))

from byte_entropy_filter import validate_bytes  # noqa: E402

from pxpipe_lygo.config import MIN_CHARS_TO_COMPRESS, MIN_TOKEN_SAVINGS_RATIO


def estimate_text_tokens(char_count: int) -> int:
    return max(1, char_count // 4)


def estimate_vision_tokens(width: int, height: int) -> int:
    """Rough vision-token cost (tile model; conservative for savings gate)."""
    tiles_w = max(1, (width + 511) // 512)
    tiles_h = max(1, (height + 511) // 512)
    return tiles_w * tiles_h * 170


def p0_analyze(data: bytes) -> dict[str, Any]:
    return validate_bytes(data)


def should_compress_payload(
    text: str,
    *,
    png_width: int | None = None,
    png_height: int | None = None,
) -> tuple[bool, dict[str, Any]]:
    """Return (compress?, diagnostics)."""
    diag: dict[str, Any] = {"chars": len(text)}
    if len(text) < MIN_CHARS_TO_COMPRESS:
        diag["reason"] = "below_min_chars"
        return False, diag

    data = text.encode("utf-8", errors="replace")
    p0 = p0_analyze(data)
    diag["p0"] = {
        "verdict": p0.get("verdict"),
        "entropy": p0.get("entropy"),
        "compression": p0.get("compression"),
    }
    if p0.get("verdict") == "QUARANTINE":
        diag["reason"] = "p0_quarantine"
        return False, diag

    text_tokens = estimate_text_tokens(len(text))
    diag["estimated_text_tokens"] = text_tokens

    if png_width is not None and png_height is not None:
        vision = estimate_vision_tokens(png_width, png_height)
    else:
        lines = max(1, text.count("\n") + 1)
        est_h = min(1928, lines * 18)
        est_w = min(1928, max(400, max((len(line) for line in text.split("\n")), default=0) * 8))
        vision = estimate_vision_tokens(est_w, est_h)

    diag["estimated_vision_tokens"] = vision
    if text_tokens < vision * MIN_TOKEN_SAVINGS_RATIO:
        diag["reason"] = "insufficient_token_savings"
        return False, diag

    diag["reason"] = "ok"
    return True, diag