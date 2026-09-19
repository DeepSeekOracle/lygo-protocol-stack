"""SOUL.md + IDENTITY.md + MEMORY.md + session history so the agent can grow and reference."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from align import load_align
from paths import KIT_ROOT, SAVE, WORKSPACE, ensure_dirs
from atomicio import atomic_write_text

SOUL_NAME = "SOUL.md"
IDENTITY_NAME = "IDENTITY.md"
MEMORY_NAME = "MEMORY.md"
SESSIONS = SAVE / "sessions"
CURRENT = SESSIONS / "current.json"
SOUL_MAX = 6000
IDENTITY_MAX = 4000
MEMORY_MAX = 8000
MEMORY_PROMPT_CAP = 2800  # chars of MEMORY.md the prompt carries (memory is the section that yields)
PROMPT_CEILING = 16300  # the composed identity block, capped well inside the engine window (16,384 tokens):
#                        the headroom belongs to history, tool traces and the answer, not to longer prompts
# The compacted-conversation digest is a second, bounded block that rides with the identity block on a
# real turn (compose_system(..., carry=True)). It is capped separately so that the digest can never
# squeeze SOUL/IDENTITY/MEMORY out of the prompt: the two ceilings together are what the history budget
# is measured against (see compaction.system_reserve).
CARRY_CAP = 1400
PROMPT_CEILING_TOTAL = PROMPT_CEILING + CARRY_CAP
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
            atomic_write_text(dest, f"# {name}\n\n")


def _read_cap(path: Path, cap: int) -> str:
    """Prefer the head (protocol). Tail logs are not required every turn."""
    if not path.is_file():
        return ""
    t = path.read_text(encoding="utf-8", errors="replace")
    if len(t) <= cap:
        return t
    return t[: max(0, cap - 24)] + "\n\n…[truncated]…\n"


def _read_cap_tail(path: Path, cap: int, tail_share: float = 0.38) -> str:
    """Head (protocol) + tail (what `remember` just wrote).

    MEMORY.md grows at the bottom, so a head-only cap meant the agent could never see the notes it
    had just appended. Keep both ends.
    """
    if not path.is_file():
        return ""
    t = path.read_text(encoding="utf-8", errors="replace")
    if len(t) <= cap:
        return t
    tail = int(cap * tail_share)
    head = max(0, cap - tail - 40)
    return t[:head] + "\n\n…[middle of file omitted]…\n\n" + t[-tail:]


def _split_note(line: str) -> tuple[str, str] | None:
    """`- (2026-09-17 17:05) note text` → (stamp, note), else None."""
    s = line.strip()
    if not (s.startswith("- (") and ") " in s):
        return None
    ts, _, note = s[3:].partition(") ")
    return (ts.strip(), note.strip()) if note.strip() else None


def dedupe_notes(text: str) -> str:
    """Collapse repeated `remember` lines, keeping the newest stamp.

    Identical notes piled up and crowded out the tail window that the agent actually needs.
    """
    idx: dict[str, int] = {}
    count: dict[str, int] = {}
    out: list[str] = []
    for line in text.splitlines():
        parsed = _split_note(line)
        if not parsed:
            out.append(line)
            continue
        stamp, note = parsed
        key = note.lower()
        count[key] = count.get(key, 0) + 1
        if key in idx:
            out[idx[key]] = "- (" + stamp + ") " + note
            continue
        idx[key] = len(out)
        out.append(line)
    for key, pos in idx.items():
        if count[key] > 1 and count[key] > 0:
            out[pos] = out[pos].rstrip() + "  (repeated " + str(count[key]) + "x)"
    return "\n".join(out)


def read_memory_block(cap: int = 3200, tail_share: float = 0.5) -> str:
    """MEMORY.md for the prompt: head (protocol) + tail (newest notes), de-duplicated first."""
    p = memory_path()
    if not p.is_file():
        return ""
    t = dedupe_notes(p.read_text(encoding="utf-8", errors="replace"))
    if len(t) <= cap:
        return t
    tail = int(cap * tail_share)
    head = max(0, cap - tail - 40)
    return t[:head] + "\n\n…[middle of file omitted]…\n\n" + t[-tail:]


def _fits(out: str, mem: str) -> str:
    """Shrink the MEMORY.md block - never SOUL/IDENTITY - until the prompt fits the engine window.

    The window is fixed while the skill catalog and the notes grow, so memory is the section that
    gives way. Bounded: it stops at 600 chars instead of looping.
    """
    if len(out) <= PROMPT_CEILING or not mem:
        return out
    cap = len(mem)
    while len(out) > PROMPT_CEILING and cap > 600:
        cap = max(600, cap - (len(out) - PROMPT_CEILING) - 120)
        smaller = read_memory_block(cap)
        if smaller == mem:
            break
        out = out.replace(mem, smaller, 1)
        mem = smaller
    return out



def compose_system(brain: str | None = None, carry: bool = False) -> str:
    """The identity block. `carry=True` appends the compacted-conversation digest.

    The digest is opt-in so that the identity block keeps its own, separately tested ceiling: a caller
    that wants the agent to remember what left the window asks for it, and the two blocks together stay
    inside `PROMPT_CEILING_TOTAL`.
    """
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
        from runtime_facts import limb_catalog, prompt_block

        block = prompt_block(brain)
        if block:
            parts.append(block)
            parts.append("")
        limbs = limb_catalog()
        if limbs:
            parts.append(limbs)
            parts.append("")
        parts.append(
            "Answer the operator's NEWEST message only. Never repeat or paraphrase a previous answer; "
            "if nothing new applies, say what changed in one line."
        )
        parts.append("")
    except Exception:
        pass
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
    soul = _read_cap(soul_path(), 2400)
    ident = _read_cap(identity_path(), 1400)
    mem = read_memory_block(MEMORY_PROMPT_CAP)
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
    out = _fits("\n".join(parts), mem)
    if carry:
        try:
            from compaction import carry_over

            block = carry_over()
            if block:
                out = out + "\n\n" + block
        except Exception:
            pass
    return out


def append_memory(note: str) -> dict[str, Any]:
    ensure_identity()
    note = (note or "").strip()[:4000]
    if not note:
        return {"ok": False, "error": "empty"}
    stamp = time.strftime("%Y-%m-%d %H:%M")
    line = f"\n- ({stamp}) {note}\n"
    p = memory_path()
    if p.is_file():
        recent = p.read_text(encoding="utf-8", errors="replace")[-8000:].lower()
        if (") " + note.lower()) in recent:
            return {"ok": True, "duplicate": True, "path": str(p),
                    "note": "already in MEMORY.md - not appended twice"}
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
    atomic_write_text(CURRENT, payload)


def new_session() -> None:
    ensure_identity()
    # The conversation about to be wiped is FILED FIRST: pressing New session must never cost the
    # operator the chat they just had. vault_live() copies the journal into the vault - it never
    # moves or deletes anything - and a failure here is not allowed to block the new session.
    try:
        import sessions

        sessions.vault_live(reason="new_session")
    except Exception:  # noqa: BLE001
        pass
    if CURRENT.is_file():
        bak = SESSIONS / f"session-{int(time.time())}.json"
        try:
            shutil.copy2(CURRENT, bak)
        except OSError:
            pass
    atomic_write_text(CURRENT, json.dumps({"updated": time.time(), "messages": []}, indent=2))
