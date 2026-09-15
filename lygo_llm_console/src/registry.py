from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paths import REGISTRY_PATH, SAVE, ensure_dirs

SIGNATURE = "Δ9Φ963-LYGO-LLM-CONSOLE-REG-v1"


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
        chat = next((m["id"] for m in data["models"] if m.get("kind") == "chat" and m.get("runnable")), None)
        data["selected"] = chat
    save(data)
    return data


def get(model_id: str) -> dict[str, Any] | None:
    for m in load().get("models") or []:
        if m.get("id") == model_id:
            return m
    return None
