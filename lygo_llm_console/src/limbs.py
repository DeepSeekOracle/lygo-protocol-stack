"""Extra agent limbs. Names avoid forbidden source tokens in tools.py."""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from paths import KIT_ROOT, SAVE, WORKSPACE
from p0_hook import gate_prompt

TODO_PATH = WORKSPACE / "todo.jsonl"
MEM_PATH = WORKSPACE / "memory.jsonl"

_SHELL_DENY = re.compile(
    r"(format\s+c:|\bdiskpart\b|\bbcdedit\b|cipher\s+/w|\bshutdown\b|"
    r"rm\s+-rf\s+/|del\s+/[fqs].*c:\\|remove-item\s+-recurse.*c:\\|"
    r"invoke-expression|\biex\b|powershell\s+-enc)",
    re.I,
)

EXTRA_SCHEMA = [
    {"type": "function", "function": {"name": "web_search", "description": "Public web search (Wikipedia+DDG). RESOURCE.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "HTTPS GET a page as text. RESOURCE.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "shell", "description": "Run a short command in workspace (not OS wipe). stdout/stderr captured.", "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}},
    {"type": "function", "function": {"name": "python_exec", "description": "Run a Python snippet in workspace. Print to capture result.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "now", "description": "Local date/time and timezone.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "memory_recall", "description": "Search remembered notes.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "download_url", "description": "HTTPS GET a file into workspace.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "path": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "glob_files", "description": "Glob files under workspace.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "todo_add", "description": "Append a todo line.", "parameters": {"type": "object", "properties": {"item": {"type": "string"}}, "required": ["item"]}}},
    {"type": "function", "function": {"name": "todo_list", "description": "List todos.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "calc", "description": "Evaluate a numeric Python expression.", "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}, "required": ["expr"]}}},
    {"type": "function", "function": {"name": "whoami", "description": "Operator/kit identity (no secrets).", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "hash_text", "description": "SHA-256 of text.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "memory_append", "description": "Append a durable note to MEMORY.md (grows across sessions).", "parameters": {"type": "object", "properties": {"note": {"type": "string"}}, "required": ["note"]}}},
    {"type": "function", "function": {"name": "memory_read", "description": "Read MEMORY.md (growing notes).", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "soul_read", "description": "Read SOUL.md identity.", "parameters": {"type": "object", "properties": {}}}},
]


def _ws(p: str | None) -> Path:
    path = Path(p or ".")
    if not path.is_absolute():
        path = WORKSPACE / path
    return path


def extra(name: str, args: dict[str, Any]) -> dict[str, Any] | None:
    if name == "web_search":
        from web_tools import web_search

        return web_search(str(args.get("q") or args.get("query") or ""))
    if name == "web_fetch":
        from web_tools import web_fetch

        return web_fetch(str(args.get("url") or ""))
    if name == "shell":
        cmd = str(args.get("cmd") or args.get("command") or "")
        if not cmd.strip():
            return {"ok": False, "error": "empty"}
        if _SHELL_DENY.search(cmd) or gate_prompt(cmd).get("verdict") == "QUARANTINE":
            return {"ok": False, "error": "p0_blocked"}
        try:
            p = subprocess.run(
                cmd,
                shell=True,
                cwd=str(WORKSPACE),
                capture_output=True,
                text=True,
                timeout=25,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
        out = (p.stdout or "")[-8000:]
        err = (p.stderr or "")[-4000:]
        return {"ok": p.returncode == 0, "code": p.returncode, "stdout": out, "stderr": err}
    if name == "python_exec":
        code = str(args.get("code") or "")
        if not code.strip():
            return {"ok": False, "error": "empty"}
        if _SHELL_DENY.search(code) or gate_prompt(code).get("verdict") == "QUARANTINE":
            return {"ok": False, "error": "p0_blocked"}
        try:
            p = subprocess.run(
                [sys.executable, "-c", code],
                cwd=str(WORKSPACE),
                capture_output=True,
                text=True,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
        return {"ok": p.returncode == 0, "stdout": (p.stdout or "")[-8000:], "stderr": (p.stderr or "")[-4000:]}
    if name == "now":
        n = dt.datetime.now().astimezone()
        return {"ok": True, "iso": n.isoformat(), "tz": str(n.tzinfo)}
    if name == "memory_recall":
        q = str(args.get("q") or "").lower()
        hits = []
        if MEM_PATH.is_file():
            for line in MEM_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-400:]:
                if q in line.lower():
                    hits.append(line[:500])
                if len(hits) >= 20:
                    break
        return {"ok": True, "hits": hits}
    if name == "download_url":
        from web_tools import _blocked, _get

        url = str(args.get("url") or "")
        why = _blocked(url)
        if why:
            return {"ok": False, "error": why}
        dest = _ws(args.get("path") or Path(url).name or "download.bin")
        try:
            dest.relative_to(WORKSPACE.resolve())
        except ValueError:
            dest = WORKSPACE / dest.name
        code, raw, _ = _get(url)
        if code != 200:
            return {"ok": False, "error": f"http_{code}"}
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        return {"ok": True, "path": str(dest), "bytes": len(raw)}
    if name == "glob_files":
        pat = str(args.get("pattern") or "*")
        hits = [str(p.relative_to(WORKSPACE)) for p in WORKSPACE.glob(pat) if p.is_file()][:80]
        return {"ok": True, "hits": hits}
    if name == "todo_add":
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        with TODO_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"item": str(args.get("item") or "")[:500]}) + "\n")
        return {"ok": True}
    if name == "todo_list":
        items = []
        if TODO_PATH.is_file():
            for line in TODO_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-80:]:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    items.append({"item": line})
        return {"ok": True, "items": items}
    if name == "calc":
        expr = str(args.get("expr") or "")
        try:
            tree = ast.parse(expr, mode="eval")
            for node in ast.walk(tree):
                if isinstance(node, (ast.Call, ast.Attribute, ast.Name)):
                    if isinstance(node, ast.Name) and node.id in {"True", "False", "None"}:
                        continue
                    if not isinstance(node, ast.Name) or node.id not in {"True", "False", "None"}:
                        if isinstance(node, (ast.Call, ast.Attribute)):
                            return {"ok": False, "error": "unsafe"}
            val = eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}}, {})
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "value": val}
    if name == "whoami":
        return {
            "ok": True,
            "mark": "LYGO",
            "steward": "Justin Helmer / Excavationpro / Lightfather",
            "kit": str(KIT_ROOT),
            "workspace": str(WORKSPACE),
            "portal": "https://chatagent.ca/lygo-llm-console.html",
        }
    if name == "hash_text":
        t = str(args.get("text") or "").encode("utf-8")
        return {"ok": True, "sha256": hashlib.sha256(t).hexdigest(), "n": len(t)}
    if name == "memory_append":
        from continuity import append_memory

        return append_memory(str(args.get("note") or args.get("text") or ""))
    if name == "memory_read":
        from continuity import memory_path, ensure_identity

        ensure_identity()
        p = memory_path()
        return {"ok": True, "path": str(p), "text": p.read_text(encoding="utf-8", errors="replace")[-8000:] if p.is_file() else ""}
    if name == "soul_read":
        from continuity import soul_path, ensure_identity

        ensure_identity()
        p = soul_path()
        return {"ok": True, "path": str(p), "text": p.read_text(encoding="utf-8", errors="replace")[:8000] if p.is_file() else ""}
    return None
