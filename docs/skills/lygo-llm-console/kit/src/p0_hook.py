from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

from paths import KIT_ROOT, VENDOR_P0, stack_root

SIGNATURE = "Δ9Φ963-LYGO-LLM-CONSOLE-P0-v1"
POLICY_MAX_CHARS = 12000
PHYSICS_WINDOW = 8192

_QUARANTINE = re.compile(
    r"("
    r"rm\s+-rf\s+/|"
    r"format\s+c:|"
    r"mimikatz|"
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions|"
    r"exfiltrate\s+secrets|"
    r"disable\s+safety|"
    r"child\s+sexual|"
    r"make\s+a\s+bomb\s+detailed|"
    r"\bdiskpart\b|"
    r"\bbcdedit\b|"
    r"cipher\s+/w|"
    r"\bshutdown\b"
    r")",
    re.I,
)

PHYSICS_AVAILABLE = False
_validate_bytes = None
_import_error = ""


def _try_import(dirpath: Path) -> bool:
    global _validate_bytes
    d = str(dirpath.resolve())
    if d not in sys.path:
        sys.path.insert(0, d)
    try:
        from byte_entropy_filter import validate_bytes  # type: ignore

        _validate_bytes = validate_bytes
        return True
    except Exception:
        if d in sys.path:
            try:
                sys.path.remove(d)
            except ValueError:
                pass
        return False


def _init() -> None:
    global PHYSICS_AVAILABLE, _import_error
    root = stack_root()
    overlay = None
    if root:
        overlay = root / "protocol0_byte_entropy_filter" / "src" / "python" / "byte_entropy_filter.py"
    if overlay and overlay.is_file():
        if _try_import(overlay.parent):
            PHYSICS_AVAILABLE = True
            return
    if _try_import(VENDOR_P0):
        PHYSICS_AVAILABLE = True
        return
    PHYSICS_AVAILABLE = False
    _import_error = "p0_import_failed"


_init()


def _policy(text: str) -> dict[str, Any]:
    t = text or ""
    if not t.strip():
        return {"verdict": "ALLOW", "reason": "empty", "signature": SIGNATURE}
    if len(t) > POLICY_MAX_CHARS:
        return {
            "verdict": "QUARANTINE",
            "reason": f"payload_exceeds_{POLICY_MAX_CHARS}",
            "signature": SIGNATURE,
        }
    if _QUARANTINE.search(t):
        return {
            "verdict": "QUARANTINE",
            "reason": "matched_p0_policy_pattern",
            "signature": SIGNATURE,
        }
    if len(t) > 4000 and len(set(t)) > 80 and " " not in t[:200]:
        return {
            "verdict": "QUARANTINE",
            "reason": "high_entropy_blob",
            "signature": SIGNATURE,
        }
    return {"verdict": "ALLOW", "reason": "ok", "signature": SIGNATURE}


def gate_output_window(text: str) -> dict[str, Any]:
    """Policy regex only (no physics). QUARANTINE aborts the stream."""
    return _policy(text)


def gate_prompt(text: str) -> dict[str, Any]:
    if not PHYSICS_AVAILABLE or _validate_bytes is None:
        return {
            "verdict": "QUARANTINE",
            "reason": "p0_import_failed",
            "policy": "QUARANTINE",
            "physics": None,
            "signature": SIGNATURE,
        }
    pol = _policy(text)
    raw = (text or "").encode("utf-8")
    truncated = len(raw) > PHYSICS_WINDOW
    phys = _validate_bytes(raw[:PHYSICS_WINDOW])
    if pol["verdict"] == "QUARANTINE":
        out = {
            "verdict": "QUARANTINE",
            "reason": pol["reason"],
            "policy": "QUARANTINE",
            "physics": phys,
            "p0_truncated": truncated,
            "signature": SIGNATURE,
        }
        return out
    if phys.get("verdict") == "QUARANTINE":
        return {
            "verdict": "QUARANTINE",
            "reason": "physics_quarantine",
            "policy": "ALLOW",
            "physics": phys,
            "p0_truncated": truncated,
            "signature": SIGNATURE,
        }
    return {
        "verdict": phys.get("verdict", "AMPLIFY"),
        "reason": pol.get("reason", "ok"),
        "policy": "ALLOW",
        "physics": phys,
        "p0_truncated": truncated,
        "signature": SIGNATURE,
    }
