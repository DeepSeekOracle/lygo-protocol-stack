from __future__ import annotations

import hmac
import json
import os
import secrets
from pathlib import Path

from paths import DATA, TOKEN_PATH, LLAMA_KEY_PATH, ensure_dirs

HEADER = "X-LYGO-LLM-Token"


def _chmod600(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def ensure_token() -> str:
    ensure_dirs()
    DATA.mkdir(parents=True, exist_ok=True)
    if TOKEN_PATH.is_file():
        t = TOKEN_PATH.read_text(encoding="utf-8").strip()
        if t:
            return t
    t = secrets.token_urlsafe(24)
    TOKEN_PATH.write_text(t, encoding="utf-8")
    _chmod600(TOKEN_PATH)
    return t


def ensure_llama_key() -> str:
    ensure_dirs()
    if LLAMA_KEY_PATH.is_file():
        k = LLAMA_KEY_PATH.read_text(encoding="utf-8").strip()
        if k:
            return k
    k = secrets.token_urlsafe(32)
    LLAMA_KEY_PATH.write_text(k, encoding="utf-8")
    _chmod600(LLAMA_KEY_PATH)
    return k


def check(provided: str | None, expected: str) -> bool:
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided.strip(), expected.strip())


def token_from_request(headers: dict[str, str], query: dict[str, list[str]]) -> str | None:
    h = headers.get(HEADER) or headers.get(HEADER.lower())
    if h:
        return h.strip()
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    qs = query.get("t") or query.get("token")
    if qs:
        return qs[0]
    return None
