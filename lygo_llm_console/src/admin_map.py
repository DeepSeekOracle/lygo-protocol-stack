"""Admin unlock map. Loaded only if config/admin.json exists (not in public git)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from paths import KIT_ROOT, SAVE, WORKSPACE

_cache: dict[str, Any] | None = None


def invalidate() -> None:
    global _cache
    _cache = None


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


def _usb_root() -> str:
    env = os.environ.get("LYGO_USB_ROOT", "").strip()
    if env and Path(env).is_dir():
        return env
    for cand in (Path(r"E:\LYGO_BUILDER_KEY"), KIT_ROOT.parent):
        if cand.is_dir() and ((cand / "LYGO_CLAW.bat").is_file() or (cand / "lygo_llm_console").is_dir()):
            return str(cand)
    return ""


def _expand_path(raw: str) -> Path:
    usb = _usb_root()
    s = str(raw)
    s = s.replace("{kit}", str(KIT_ROOT))
    s = s.replace("{workspace}", str(WORKSPACE))
    if usb:
        s = s.replace("{usb}", usb)
    return Path(s)


def paths_of(key: str, fallback: tuple[Path, ...]) -> tuple[Path, ...]:
    raw = load().get(key)
    out: list[Path] = []
    seen: set[str] = set()
    try:
        from workspace_map import extra_paths, revoked_set

        revoked = revoked_set()
        extra = extra_paths("read" if key == "read_roots" else "write" if key == "write_roots" else "search")
    except Exception:
        revoked = set()
        extra = []
    seq = list(raw) if isinstance(raw, list) else []
    for x in seq:
        p = _expand_path(str(x))
        try:
            if not p.exists():
                continue
            keyp = str(p.resolve())
        except OSError:
            continue
        if keyp in revoked or keyp in seen:
            continue
        seen.add(keyp)
        out.append(p)
    for p in extra:
        try:
            keyp = str(p.resolve())
        except OSError:
            continue
        if keyp in seen or keyp in revoked:
            continue
        seen.add(keyp)
        out.append(p)
    if out:
        return tuple(out)
    return fallback


def read_roots() -> tuple[Path, ...]:
    return paths_of("read_roots", (WORKSPACE,))


def write_roots() -> tuple[Path, ...]:
    return paths_of("write_roots", (WORKSPACE, SAVE))


def search_roots() -> tuple[Path, ...]:
    return paths_of("search_roots", (WORKSPACE,))


def links() -> dict[str, Any]:
    return load().get("links") if isinstance(load().get("links"), dict) else {}


def credential_pointers() -> dict[str, str]:
    raw = load().get("credential_pointers")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in raw.items():
        if k == "note" or not isinstance(v, str):
            continue
        out[str(k)] = v
    return out


def drives() -> dict[str, str]:
    raw = load().get("drives")
    if isinstance(raw, dict) and raw:
        return {str(k): str(v) for k, v in raw.items()}
    return {
        "C": "Windows + profile",
        "D": "chatagent git (sites + games)",
        "E": "USB LYGO_BUILDER_KEY",
        "I": "stack, model vault, LYRA LOCAL",
        "U": "stream F:\\LYGO when mapped",
    }


def is_placeholder_url(url: str) -> bool:
    u = (url or "").strip().lower()
    if not u:
        return False
    if "example.com" in u or "example.org" in u:
        return True
    if "github.com/user/" in u or u.rstrip("/").endswith("github.com/user"):
        return True
    if "huggingface.co/models/transformers" in u:
        return True
    if "lattice.example" in u:
        return True
    return False


def brief() -> dict[str, Any]:
    ln = links()
    return {
        "ok": True,
        "role": "admin_kernel" if is_admin() else "public_kit",
        "steward": "Justin Helmer / Excavationpro / Lightfather",
        "drives": drives() if is_admin() else {},
        "read_roots": [str(p) for p in read_roots()],
        "write_roots": [str(p) for p in write_roots()],
        "search_roots": [str(p) for p in search_roots()],
        "github_org": ln.get("github_org") or "https://github.com/DeepSeekOracle",
        "hf_org": ln.get("hf_org") or "https://huggingface.co/DeepSeekOracle",
        "github_repos": ln.get("github_repos") or [
            "https://github.com/DeepSeekOracle/chatagent",
            "https://github.com/DeepSeekOracle/lygo-protocol-stack",
        ],
        "hf": ln.get("hf") or [ln.get("hf_org") or "https://huggingface.co/DeepSeekOracle"],
        "sites": ln.get("sites") or ["https://chatagent.ca/"],
        "lattice": ln.get("lattice")
        or [
            "https://chatagent.ca/",
            "https://chatagent.ca/join/",
            "https://chatagent.ca/agents/",
            "https://chatagent.ca/starchart/",
            "https://chatagent.ca/witness/",
            "https://chatagent.ca/lygoskillhub.html",
        ],
        "credential_tool": "credential_where",
        "rules": [
            "Never invent github.com/user/repo or lattice.example.com.",
            "Never print *.pass contents. Call credential_where; report path + exists only.",
            "Use list_dir / find_files on real drives. Use web_fetch on LINKS.md URLs.",
        ],
    }


def brief_text() -> str:
    b = brief()
    lines = [
        "ADMIN BRIEF (call steward_map if you need the full map):",
        f"role={b.get('role')} steward={b.get('steward')}",
        f"GitHub org: {b.get('github_org')}",
        f"Hugging Face: {b.get('hf_org')}",
        "Lattice: https://chatagent.ca/  join/ agents/ starchart/ witness/ lygoskillhub.html",
        "Forbidden placeholders: github.com/user/repo  lattice.example.com  example.com",
        "Passwords: credential_where — path only, never echo secrets.",
    ]
    if is_admin():
        lines.append("Drives: C Windows · D chatagent · E USB · I stack · U stream (if mapped)")
        lines.append("First tools: steward_map, whoami, list_dir, find_files, web_fetch real URLs.")
    return "\n".join(lines)
