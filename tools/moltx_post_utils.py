"""Moltx post helpers — safe receipts, no secret leakage."""

from __future__ import annotations

import json
import re
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SECRET_PATTERNS = (
    re.compile(r"moltx_sk_[0-9a-fA-F]+", re.I),
    re.compile(r"moltbook_sk_[0-9a-fA-F]+", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.I),
    re.compile(r"\"api_key\"\s*:\s*\"[^\"]+\""),
)


def redact(text: str, *, max_len: int = 400) -> str:
    if not text:
        return ""
    out = text
    for pat in SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    out = out.replace("\r", " ")
    if len(out) > max_len:
        out = out[:max_len] + "…"
    return out


def dns_ok(host: str = "moltx.io", port: int = 443) -> tuple[bool, str | None]:
    try:
        socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        return True, None
    except OSError as exc:
        return False, str(exc)


def credential_status() -> dict[str, Any]:
    """Paths and presence only — never read or return api_key."""
    import os

    home = Path(os.environ.get("OPENCLAW_HOME", r"C:\Users\justi\.openclaw"))
    workspace = Path(os.environ.get("OPENCLAW_WORKSPACE", home / "workspace"))
    paths = {
        "MOLTX_CREDENTIALS_PATH": os.environ.get("MOLTX_CREDENTIALS_PATH"),
        "openclaw_credentials_moltx_json": str(home / "credentials" / "moltx.json"),
        "workspace_credentials_moltx_json": str(workspace / "credentials" / "moltx.json"),
    }
    present: dict[str, bool] = {}
    for name, p in paths.items():
        if not p:
            present[name] = False
            continue
        present[name] = Path(p).is_file()
    present["canonical_default"] = (home / "credentials" / "moltx.json").is_file()
    return {"paths": paths, "present": present}


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = json.loads(json.dumps(payload, default=str))
    if isinstance(safe.get("error"), str):
        safe["error"] = redact(safe["error"])
    if isinstance(safe.get("body_preview"), str):
        safe["body_preview"] = redact(safe["body_preview"])
    safe["written_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(safe, indent=2), encoding="utf-8")


def parse_api_base() -> str:
    import os

    base = (os.environ.get("MOLTX_API_BASE") or "https://moltx.io/v1").rstrip("/")
    host = urlparse(base).hostname or "moltx.io"
    ok, err = dns_ok(host)
    if not ok:
        raise RuntimeError(
            f"Cannot resolve Moltx host '{host}' ({err}). "
            "Check network/DNS/VPN, or set MOLTX_API_BASE only for approved endpoints."
        )
    return base


def rate_limit_headers(headers: Any) -> dict[str, str] | None:
    if headers is None:
        return None
    keys = (
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After",
    )
    out = {k: headers.get(k) for k in keys if headers.get(k)}
    return out or None