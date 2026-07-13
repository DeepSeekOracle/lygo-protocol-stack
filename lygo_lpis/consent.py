"""Consent gate for LPIS ingest — authorized sources only."""

from __future__ import annotations

import os
from typing import Any

INGEST_WARNING = (
    "LPIS ingest handles sensitive prompt text locally. "
    "Only ingest prompts you own or are explicitly authorized to analyze. "
    "Do not ingest leaked, proprietary, or third-party confidential system prompts."
)


def ingest_authorized(*, flag: bool = False) -> bool:
    if flag:
        return True
    return os.environ.get("LYGO_LPIS_INGEST_AUTHORIZED", "").strip().lower() in (
        "yes",
        "1",
        "true",
    )


def require_ingest_authorization(*, flag: bool = False) -> dict[str, Any] | None:
    if ingest_authorized(flag=flag):
        return None
    return {
        "ok": False,
        "error": "ingest_not_authorized",
        "message": INGEST_WARNING,
        "hint": "Pass --i-authorize on CLI or set LYGO_LPIS_INGEST_AUTHORIZED=yes after user attestation.",
    }