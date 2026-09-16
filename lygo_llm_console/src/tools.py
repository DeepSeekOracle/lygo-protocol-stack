from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from admin_map import brief, credential_pointers, is_admin, is_placeholder_url, read_roots, search_roots, write_roots
from paths import KIT_ROOT, SAVE, WORKSPACE, RECEIPTS
from p0_hook import gate_prompt
from limbs import EXTRA_SCHEMA, extra as extra_dispatch

# Public kit default. Admin json expands roots at call time.

# Split literals so public source does not contain steward path tokens.
DENY_SUB = (
    "I:\\" + "LYGO" + "_" + "SERVER" + "_" + "KEYS",
    "gitea.pass",
    ".lygo_llm_token",
    ".llama_api_key",
    "save/logs",
    "save\\logs",
    "engine.pid.json",
    r"projects\gitea\home",
    r"C:\Windows",
    r"C:\Program Files",
    "Data" + " " + "Vault",
)

TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "steward_map", "description": "Canonical admin map: drives, GitHub/HF/lattice URLs, roots. Call this BEFORE fetching GitHub/HF/sites. Never invent URLs.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "find_files", "description": "Find files on mapped disks (admin search/read roots). pattern e.g. *.md or SOUL.md", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "root": {"type": "string"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "credential_where", "description": "Locate steward credential files by name. Returns path + exists. NEVER returns secret contents.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "list_dir", "description": "List a directory (admin: real disks on the map; else workspace). Empty path lists mapped roots.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a text file. Never echo *.pass / token files — report exists only.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write a text file under allowed roots", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "remember", "description": "Append a short note to workspace memory", "parameters": {"type": "object", "properties": {"note": {"type": "string"}}, "required": ["note"]}}},
    {"type": "function", "function": {"name": "notepad_list", "description": "List console notepad notes. Use ONLY if the steward asks to look at notes/notepad.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "notepad_read", "description": "Read one notepad note by id. Use ONLY if the steward asks to look at notes.", "parameters": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}}},
    {"type": "function", "function": {"name": "notepad_write", "description": "Save text into the console notepad. Use ONLY if the steward asks to save a note.", "parameters": {"type": "object", "properties": {"id": {"type": "string"}, "title": {"type": "string"}, "text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "kernel_status", "description": "Console + engine status (no secrets)", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "search_corpus", "description": "Lexical search under mapped search roots", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "p0_gate", "description": "Run P0 gate on supplied text", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "stack_health", "description": "Optional protocol-stack demo_cycle", "parameters": {"type": "object", "properties": {}}}},
]

TOOLS_SCHEMA = TOOLS_SCHEMA + EXTRA_SCHEMA
ALIASES = {"read": "read_file", "write": "write_file", "bash": "shell", "exec": "shell", "terminal": "shell"}


def _denied(path: Path) -> bool:
    s = str(path.resolve()).replace("/", "\\")
    low = s.lower()
    for d in DENY_SUB:
        if d.lower().replace("/", "\\") in low:
            return True
    return False


def _under(path: Path, roots: tuple[Path, ...]) -> bool:
    try:
        rp = path.resolve()
    except OSError:
        return False
    for r in roots:
        try:
            rp.relative_to(r.resolve())
            return True
        except ValueError:
            continue
    return False


def _find_files(pattern: str, root: str | None = None) -> dict[str, Any]:
    pat = (pattern or "").strip() or "*"
    if not any(ch in pat for ch in "*?["):
        pat = f"*{pat}*"
    roots: list[Path] = []
    if root:
        p = Path(root)
        if not p.is_absolute():
            p = WORKSPACE / p
        if _denied(p) or not _under(p, read_roots()):
            return {"ok": False, "error": "denied"}
        roots = [p]
    else:
        seen: set[str] = set()
        for r in list(search_roots()) + list(read_roots()):
            try:
                key = str(r.resolve())
            except OSError:
                continue
            if key in seen:
                continue
            seen.add(key)
            roots.append(r)
    hits: list[str] = []
    visited = 0
    for r in roots:
        if len(hits) >= 50:
            break
        try:
            it = r.rglob(pat)
        except OSError:
            continue
        for p in it:
            visited += 1
            if visited > 6000 or len(hits) >= 50:
                break
            try:
                if not p.is_file() or _denied(p) or not _under(p, read_roots()):
                    continue
            except OSError:
                continue
            hits.append(str(p))
    return {"ok": True, "pattern": pat, "hits": hits, "n": len(hits), "visited": visited}


def dispatch(name: str, args: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    name = ALIASES.get(name, name)
    extra = extra or {}
    if name == "steward_map":
        return brief()
    if name == "find_files":
        return _find_files(str(args.get("pattern") or args.get("q") or "*"), args.get("root"))
    if name == "credential_where":
        q = str(args.get("q") or args.get("name") or "").lower()
        rows = []
        for k, v in credential_pointers().items():
            blob = (k + " " + v).lower()
            if q and q not in blob:
                continue
            p = Path(v)
            rows.append({"name": k, "path": v, "exists": p.is_file(), "redacted": True})
        return {"ok": True, "pointers": rows, "rule": "never echo secret contents; path + exists only"}
    if name == "list_dir":
        raw = str(args.get("path") or "").strip()
        if not raw or raw in {".", "drives", "roots"}:
            return {"ok": True, "roots": [str(p) for p in read_roots()], "hint": "pass a root path to list entries"}
        p = Path(raw)
        if not p.is_absolute():
            p = WORKSPACE / p
        if _denied(p) or not _under(p, read_roots()):
            return {"ok": False, "error": "denied", "hint": "path not on admin map; call steward_map"}
        if not p.is_dir():
            return {"ok": False, "error": "not_dir"}
        names = []
        for child in list(p.iterdir())[:200]:
            names.append(child.name + ("/" if child.is_dir() else ""))
        return {"ok": True, "path": str(p), "entries": names, "n": len(names)}
    if name == "read_file":
        p = Path(args.get("path") or "")
        if not p.is_absolute():
            p = WORKSPACE / p
        if _denied(p) or not _under(p, read_roots()):
            return {"ok": False, "error": "denied"}
        if not p.is_file():
            return {"ok": False, "error": "not_file"}
        low = p.name.lower()
        if low.endswith(".pass") or low in {".lygo_llm_token", ".llama_api_key"} or "lygo.pass" in low:
            return {"ok": True, "exists": True, "redacted": True, "path": str(p), "bytes": p.stat().st_size, "note": "credential file present; content not echoed"}
        data = p.read_text(encoding="utf-8", errors="replace")[:64_000]
        return {"ok": True, "text": data}
    if name == "write_file":
        p = Path(args.get("path") or "")
        if not p.is_absolute():
            p = WORKSPACE / p
        if _denied(p) or not _under(p, write_roots()):
            return {"ok": False, "error": "denied"}
        p.parent.mkdir(parents=True, exist_ok=True)
        content = str(args.get("content") or "")
        p.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(p), "bytes": len(content.encode("utf-8"))}
    if name == "remember":
        from continuity import append_memory

        return append_memory(str(args.get("note") or args.get("text") or ""))
    if name == "notepad_list":
        from notepad import list_notes

        return list_notes()
    if name == "notepad_read":
        from notepad import read_note

        return read_note(str(args.get("id") or args.get("name") or "scratch"))
    if name == "notepad_write":
        from notepad import write_note

        return write_note(args.get("id"), str(args.get("title") or ""), str(args.get("text") or args.get("content") or ""))
    if name == "kernel_status":
        from engine import ollama_port_open, resolve_binary, runner_for
        from paths import LLAMA_PORT
        from p0_hook import PHYSICS_AVAILABLE

        r = runner_for(LLAMA_PORT)
        return {
            "ok": True,
            "physics": PHYSICS_AVAILABLE,
            "engine_binary": bool(resolve_binary()),
            "chat_runner": bool(r),
            "ollama_port_open": ollama_port_open(),
            "kit": str(KIT_ROOT),
            "admin": is_admin(),
        }
    if name == "search_corpus":
        q = str(args.get("q") or "").lower()
        hits = []
        if q:
            for root in search_roots():
                if len(hits) >= 30:
                    break
                try:
                    it = root.rglob("*")
                except OSError:
                    continue
                for p in it:
                    if not p.is_file():
                        continue
                    try:
                        if p.stat().st_size > 256_000:
                            continue
                    except OSError:
                        continue
                    if p.suffix.lower() not in {".md", ".txt", ".json", ".html", ".py", ".bat"}:
                        continue
                    try:
                        t = p.read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        continue
                    if q in t.lower():
                        hits.append(str(p))
                    if len(hits) >= 30:
                        break
        return {"ok": True, "hits": hits, "admin": is_admin()}
    if name == "p0_gate":
        return {"ok": True, "gate": gate_prompt(str(args.get("text") or ""))}
    if name == "stack_health":
        from stack_health import run_stack_health

        return run_stack_health()
    if name in {"web_fetch", "jina_fetch", "download_url", "page_thumbnail", "http_json", "wayback"}:
        url = str(args.get("url") or "")
        if is_placeholder_url(url):
            return {
                "ok": False,
                "error": "placeholder_url",
                "url": url,
                "hint": "never invent example.com or github.com/user/repo — use steward_map",
                "map": brief(),
            }
    got = extra_dispatch(name, args)
    if got is not None:
        return got
    return {"ok": False, "error": f"unknown_tool:{name}"}


def parse_fence_tool(text: str) -> dict[str, Any] | None:
    marker = "```tool"
    i = text.find(marker)
    if i < 0:
        marker = "```json"
        i = text.find(marker)
        if i < 0:
            return None
    rest = text[i + len(marker) :]
    end = rest.find("```")
    if end < 0:
        return None
    blob = rest[:end].strip()
    try:
        obj = json.loads(blob)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    name = obj.get("name") or obj.get("tool")
    if not name:
        return None
    args = obj.get("arguments") or obj.get("args") or obj.get("parameters") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {"value": args}
    return {"name": str(name), "arguments": args}
