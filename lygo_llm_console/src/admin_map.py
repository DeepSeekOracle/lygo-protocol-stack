"""Admin unlock map. Loaded only if config/admin.json exists (not in public git)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paths import KIT_ROOT, SAVE, WORKSPACE

_cache: dict[str, Any] | None = None


def load() -> dict[str, Any]:
    global _cache
    if _cache is not None:
        return _cache
    p = KIT_ROOT / "config" / "admin.json"
    if not p.is_file():
        _cache = {}
        return _cache
    try:
        _cache = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _cache = {}
    return _cache


def is_admin() -> bool:
    return bool(load())


def paths_of(key: str, fallback: tuple[Path, ...]) -> tuple[Path, ...]:
    raw = load().get(key)
    if not isinstance(raw, list) or not raw:
        return fallback
    out: list[Path] = []
    for x in raw:
        p = Path(str(x))
        if p.exists():
            out.append(p)
    return tuple(out) if out else fallback


def read_roots() -> tuple[Path, ...]:
    return paths_of("read_roots", (WORKSPACE,))


def write_roots() -> tuple[Path, ...]:
    return paths_of("write_roots", (WORKSPACE, SAVE))


def search_roots() -> tuple[Path, ...]:
    return paths_of("search_roots", (WORKSPACE,))


def links() -> dict[str, Any]:
    return load().get("links") if isinstance(load().get("links"), dict) else {}
