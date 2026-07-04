#!/usr/bin/env python3
"""
LYGO Hermes Audit Trail — hash-chained tool/session log.
Aligned to Biophase7 reference; portable paths for BUILDR USB.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

SIGNATURE = "Δ9Φ963-LYGO-HERMES-v1"
DEFAULT_LOG = Path(__file__).resolve().parent / "audit_trail.log"


def set_log_path(path: str | Path) -> None:
    global _LOG
    _LOG = Path(path)


_LOG = Path(os.environ.get("LYGO_HERMES_AUDIT_LOG", str(DEFAULT_LOG)))


def _ensure_parent() -> None:
    _LOG.parent.mkdir(parents=True, exist_ok=True)


def get_last_hash() -> str | None:
    if not _LOG.is_file():
        return None
    lines = [ln for ln in _LOG.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1]).get("hash")
    except json.JSONDecodeError:
        return None


def compute_entry_hash(entry: dict[str, Any], prev_hash: str | None) -> str:
    payload = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    basis = (prev_hash or "") + payload
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def log_event(
    event_type: str,
    *,
    actor: str = "builder",
    detail: dict[str, Any] | None = None,
    tool: str | None = None,
) -> dict[str, Any]:
    _ensure_parent()
    prev = get_last_hash()
    entry = {
        "signature": SIGNATURE,
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event_type": event_type,
        "actor": actor,
        "tool": tool,
        "detail": detail or {},
        "prev_hash": prev,
    }
    entry["hash"] = compute_entry_hash(entry, prev)
    with _LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def pre_tool_call(tool: str, args_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    return log_event("pre_tool_call", tool=tool, detail=args_summary or {})


def post_tool_call(tool: str, ok: bool, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    return log_event("post_tool_call", tool=tool, detail={"ok": ok, **(summary or {})})


def validate_audit_chain(audit_log_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(audit_log_path) if audit_log_path else _LOG
    if not path.is_file():
        return {"valid": True, "empty": True, "count": 0, "signature": SIGNATURE}
    prev: str | None = None
    count = 0
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        expected = compute_entry_hash({k: v for k, v in row.items() if k != "hash"}, prev)
        if row.get("hash") != expected:
            return {"valid": False, "broken_at_line": i, "count": count, "signature": SIGNATURE}
        prev = row.get("hash")
        count += 1
    return {"valid": True, "count": count, "head": prev, "signature": SIGNATURE}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--log-path")
    ap.add_argument("--test-event", action="store_true")
    args = ap.parse_args()
    if args.log_path:
        set_log_path(args.log_path)
    if args.test_event:
        print(json.dumps(log_event("boot_test", actor="cli")))
    print(json.dumps(validate_audit_chain(), indent=2))