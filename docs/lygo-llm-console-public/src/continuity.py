"""SOUL.md + IDENTITY.md + MEMORY.md + session history so the agent can grow and reference."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from align import load_align
from paths import KIT_ROOT, SAVE, WORKSPACE, ensure_dirs

SOUL_NAME = "SOUL.md"
IDENTITY_NAME = "IDENTITY.md"
MEMORY_NAME = "MEMORY.md"
SESSIONS = SAVE / "sessions"
CURRENT = SESSIONS / "current.json"
SOUL_MAX = 6000
IDENTITY_MAX = 4000
MEMORY_MAX = 8000
HISTORY_MAX = 40


def soul_path() -> Path:
    return WORKSPACE / SOUL_NAME


def identity_path() -> Path:
    return WORKSPACE / IDENTITY_NAME


def memory_path() -> Path:
    return WORKSPACE / MEMORY_NAME


def ensure_identity() -> None:
    ensure_dirs()
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    SESSIONS.mkdir(parents=True, exist_ok=True)
    for name in (SOUL_NAME, IDENTITY_NAME, MEMORY_NAME):
        dest = WORKSPACE / name
        src = KIT_ROOT / "prompts" / name
        if not dest.is_file() and src.is_file():
            shutil.copy2(src, dest)
        elif not dest.is_file():
            dest.write_text(f"# {name}\n\n", encoding="utf-8")


def _read_cap(path: Path, cap: int) -> str:
    """Prefer the head (protocol). Tail logs are not required every turn."""
    if not path.is_file():
        return ""
    t = path.read_text(encoding="utf-8", errors="replace")
    if len(t) <= cap:
        return t
    return t[: max(0, cap - 24)] + "\n\n…[truncated]…\n"


def compose_system() -> str:
    ensure_identity()
    parts: list[str] = []
    try:
        from admin_map import brief_text, is_admin

        parts.append(brief_text())
        parts.append("")
        if is_admin():
            parts.append(
                "ADMIN RULE: For GitHub, Hugging Face, lattice, websites, drives, or passwords, "
                "the host may already inject steward_map. Use those URLs. "
                "Never invent github.com/user/repo, huggingface.co/models/transformers, or lattice.example.com."
            )
            parts.append("")
    except Exception:
        pass
    parts.append(load_align())
    parts.append("")
    try:
        from world_clock import pulse_stamps

        w = pulse_stamps()
        parts.append(
            f"NOW UTC {w.get('utc_iso')} · local {w.get('local_iso')} ({w.get('local_tz')}) · unix {w.get('unix')} · {w.get('weekday')}."
        )
        parts.append("Call world_pulse for city clocks + weather. RESOURCE, not CANON.")
        parts.append("")
    except Exception:
        pass
    soul = _read_cap(soul_path(), 2200)
    ident = _read_cap(identity_path(), 1400)
    mem = _read_cap(memory_path(), 4800)
    if soul:
        parts.append("=== SOUL.md ===")
        parts.append(soul)
        parts.append("")
    if ident:
        parts.append("=== IDENTITY.md ===")
        parts.append(ident)
        parts.append("")
    if mem:
        parts.append("=== MEMORY.md ===")
        parts.append(mem)
        parts.append("")
    parts.append("When the steward states a durable fact, call remember so MEMORY.md grows.")
    parts.append("Never invent github.com/user/repo or lattice.example.com. Use steward_map / LINKS.md.")
    parts.append("Never print *.pass file contents. Call credential_where. Point at the path only.")
    parts.append(
        "Console notepad lives in save/notepad. Do NOT read it unless the steward asks to look at notes. "
        "Then call notepad_list / notepad_read. notepad_write only if they ask to save a note."
    )
    try:
        from skills_mod import prompt_catalog

        parts.append("")
        parts.append(prompt_catalog())
        parts.append("When the operator invokes a champion or /skill, call skill_read then follow that SKILL.md.")
    except Exception:
        pass
    return "\n".join(parts)


def append_memory(note: str) -> dict[str, Any]:
    ensure_identity()
    note = (note or "").strip()[:4000]
    if not note:
        return {"ok": False, "error": "empty"}
    stamp = time.strftime("%Y-%m-%d %H:%M")
    line = f"\n- ({stamp}) {note}\n"
    with memory_path().open("a", encoding="utf-8") as f:
        f.write(line)
    jl = WORKSPACE / "memory.jsonl"
    with jl.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": stamp, "note": note}) + "\n")
    return {"ok": True, "path": str(memory_path())}


def load_session() -> list[dict[str, Any]]:
    ensure_identity()
    if not CURRENT.is_file():
        return []
    try:
        data = json.loads(CURRENT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    msgs = data.get("messages") if isinstance(data, dict) else data
    if not isinstance(msgs, list):
        return []
    out = []
    for m in msgs[-HISTORY_MAX:]:
        if isinstance(m, dict) and m.get("role") in {"user", "assistant"}:
            out.append({"role": m["role"], "content": m.get("content")})
    return out


def save_session(messages: list[dict[str, Any]]) -> None:
    ensure_identity()
    slim = []
    for m in messages[-HISTORY_MAX:]:
        if not isinstance(m, dict):
            continue
        slim.append({"role": m.get("role"), "content": m.get("content")})
    payload = json.dumps({"updated": time.time(), "messages": slim}, indent=2)
    tmp = CURRENT.with_suffix(".json.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(CURRENT)


def new_session() -> None:
    ensure_identity()
    if CURRENT.is_file():
        bak = SESSIONS / f"session-{int(time.time())}.json"
        try:
            shutil.copy2(CURRENT, bak)
        except OSError:
            pass
    CURRENT.write_text(json.dumps({"updated": time.time(), "messages": []}, indent=2), encoding="utf-8")
