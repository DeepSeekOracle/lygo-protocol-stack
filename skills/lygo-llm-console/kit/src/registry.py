from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paths import REGISTRY_PATH, SAVE, ensure_dirs

SIGNATURE = "Δ9Φ963-LYGO-LLM-CONSOLE-REG-v1"
PREFER_IDS = ("qwen2.5:3b", "llama3.2:1b", "llama3.1:8b")


def _pick_default(models: list[dict[str, Any]]) -> str | None:
    chats = [m for m in models if m.get("kind") == "chat" and m.get("runnable") and m.get("id")]
    ids = {m["id"]: m for m in chats}
    for pid in PREFER_IDS:
        if pid in ids:
            return pid
    if not chats:
        return None
    return min(chats, key=lambda m: int(m.get("bytes") or 10**18)).get("id")


def load() -> dict[str, Any]:
    if REGISTRY_PATH.is_file():
        try:
            data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return {"signature": SIGNATURE, "selected": None, "models": []}


def save(data: dict[str, Any]) -> None:
    ensure_dirs()
    SAVE.mkdir(parents=True, exist_ok=True)
    data["signature"] = SIGNATURE
    REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def upsert(models: list[dict[str, Any]], selected: str | None = None) -> dict[str, Any]:
    data = load()
    by_id = {m.get("id"): m for m in data.get("models") or [] if m.get("id")}
    for m in models:
        if m.get("id"):
            by_id[m["id"]] = {**by_id.get(m["id"], {}), **m}
    data["models"] = list(by_id.values())
    if selected:
        data["selected"] = selected
    elif not data.get("selected"):
        data["selected"] = _pick_default(data["models"])
    save(data)
    return data


def get(model_id: str) -> dict[str, Any] | None:
    for m in load().get("models") or []:
        if m.get("id") == model_id:
            return m
    return None
