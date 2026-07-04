"""LYGO core image signing (HMAC-SHA256). Secret stays in _builder_vault only."""

from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path

SIGNATURE = "Δ9Φ963-CORE-SIGN-v1"


def _key_path(key_root: Path) -> Path:
    return key_root / "_builder_vault" / "core_signing.key"


def load_or_create_key(key_root: Path) -> bytes:
    path = _key_path(key_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        raw = path.read_bytes()
        if len(raw) >= 16:
            return raw[:64]
    key = os.urandom(32)
    path.write_bytes(key)
    return key


def sign_blob(data: bytes, key: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def verify_blob(data: bytes, signature_hex: str, key: bytes) -> bool:
    expected = sign_blob(data, key)
    return hmac.compare_digest(expected, signature_hex.strip().lower())


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()