"""Extra agent limbs. Names avoid forbidden source tokens in tools.py."""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import atomicio
from paths import KIT_ROOT, SAVE, WORKSPACE, under_workspace
from p0_hook import gate_prompt

TODO_PATH = WORKSPACE / "todo.jsonl"
MEM_PATH = WORKSPACE / "memory.jsonl"

# Deny list only: these patterns are matched to REFUSE a command (see the shell and python_exec
# limbs below) - nothing here is executed, and no limb in this file stages a recursive delete.
_SHELL_DENY = re.compile(
    r"(format\s+c:|\bdiskpart\b|\bbcdedit\b|cipher\s+/w|\bshutdown\b|"
    r"rm\s+-rf\s+/|del\s+/[fqs].*c:\\|remove-item\s+-recurse.*c:\\|"
    r"invoke-expression|\biex\b|powershell\s+-enc)",
    re.I,
)

EXTRA_SCHEMA = [
    {"type": "function", "function": {"name": "web_search", "description": "Public web search (Wikipedia+DDG) for external facts. RESOURCE. Not for arithmetic - use calc.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "HTTPS GET a page as text. RESOURCE. Use for a URL you already have, not for arithmetic - use calc.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "shell", "description": "Run a short command in workspace (not OS wipe). stdout/stderr captured.", "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}},
    {"type": "function", "function": {"name": "python_exec", "description": "Run a Python snippet in workspace. Print to capture result.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "now", "description": "Local date/time and timezone.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "world_pulse", "description": "UTC/local stamps plus world city clocks and Open-Meteo weather. Use for time/place/past-present. RESOURCE.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "memory_recall", "description": "Search remembered notes.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "download_url", "description": "HTTPS GET a file into workspace.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "path": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "glob_files", "description": "Glob files under workspace.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "todo_add", "description": "Append a todo line.", "parameters": {"type": "object", "properties": {"item": {"type": "string"}}, "required": ["item"]}}},
    {"type": "function", "function": {"name": "todo_list", "description": "List todos.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "calc", "description": "Exact arithmetic - use this for any numeric computation, never web search.", "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}, "required": ["expr"]}}},
    {"type": "function", "function": {"name": "whoami", "description": "Operator/kit identity (no secrets). Admin includes GitHub/HF/lattice links.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "hash_text", "description": "SHA-256 of text.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "memory_append", "description": "Append a durable note to MEMORY.md (grows across sessions).", "parameters": {"type": "object", "properties": {"note": {"type": "string"}}, "required": ["note"]}}},
    {"type": "function", "function": {"name": "memory_read", "description": "Read MEMORY.md (growing notes).", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "soul_read", "description": "Read SOUL.md (soul / decision spine).", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "identity_read", "description": "Read IDENTITY.md (who is on this console).", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Replace a string in a workspace file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}}},
    {"type": "function", "function": {"name": "weather", "description": "Current weather via wttr.in (RESOURCE).", "parameters": {"type": "object", "properties": {"place": {"type": "string"}}, "required": ["place"]}}},
    {"type": "function", "function": {"name": "geocode", "description": "Place name to lat/lon (Nominatim).", "parameters": {"type": "object", "properties": {"place": {"type": "string"}}, "required": ["place"]}}},
    {"type": "function", "function": {"name": "http_json", "description": "HTTPS GET JSON from a public URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "wayback", "description": "Internet Archive availability for a URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "arxiv_search", "description": "Search arXiv papers.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "hn_search", "description": "Hacker News Algolia search.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "github_search", "description": "GitHub repository search.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "image_info", "description": "PNG/JPEG/GIF size of a workspace image.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "image_save", "description": "Save a base64 or data-URL image into workspace/images.", "parameters": {"type": "object", "properties": {"b64": {"type": "string"}, "path": {"type": "string"}}, "required": ["b64"]}}},
    {"type": "function", "function": {"name": "image_list", "description": "List workspace/images files.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "page_thumbnail", "description": "Capture a public HTTPS page thumbnail into workspace/images.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "jina_fetch", "description": "Readable extract of a page via r.jina.ai.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "sessions_list", "description": "List saved chat session files.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "session_list", "description": "List the filed session vault: title, id, turns, date, tags, note. Filters: q, tag, month.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}, "tag": {"type": "string"}, "month": {"type": "string"}, "limit": {"type": "integer"}}}}},
    {"type": "function", "function": {"name": "session_open", "description": "Read a filed session back: its transcript, manifest and where it sits on disk. Use it to revisit or quote an older conversation.", "parameters": {"type": "object", "properties": {"sid": {"type": "string"}, "chars": {"type": "integer"}}, "required": ["sid"]}}},
    {"type": "function", "function": {"name": "session_search", "description": "Find a past session by phrase. Searches the vault's titles, tags, notes and the transcripts themselves.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}, "k": {"type": "integer"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "session_label", "description": "Name, tag or annotate a filed session so it can be found again later. Omit sid to label the conversation in progress.", "parameters": {"type": "object", "properties": {"sid": {"type": "string"}, "title": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}, "note": {"type": "string"}, "pinned": {"type": "boolean"}}}}},
    {"type": "function", "function": {"name": "session_resume", "description": "Reopen a filed session as the live conversation. The session in progress is filed first, so nothing is lost.", "parameters": {"type": "object", "properties": {"sid": {"type": "string"}}, "required": ["sid"]}}},
    {"type": "function", "function": {"name": "recall_history", "description": "Search everything said in this chat: the live journal and sealed sessions. Use it when the operator refers to something older than your window.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}, "k": {"type": "integer"}}, "required": ["q"]}}},
]


def _safe_arith(expr: str) -> float | int:
    import operator as op

    ops = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.FloorDiv: op.floordiv,
        ast.Mod: op.mod,
        ast.Pow: op.pow,
        ast.USub: op.neg,
        ast.UAdd: op.pos,
    }

    def walk(node: ast.AST) -> float | int:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
            return ops[type(node.op)](walk(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](walk(node.left), walk(node.right))
        raise ValueError("unsafe")

    tree = ast.parse(expr, mode="eval")
    return walk(tree)


# --- argument aliases: a small model labels the same argument differently ---------------------
# Measured 2026-09-18: the agent called python_exec with {"value": "print(6*7)"} (the schema says
# "code") and got a bare {"ok": false, "error": "empty"}; arxiv_search with {"query": ...} (schema
# says "q") and got http_400. Same limb, same intent, unusable key. Fill the canonical key from the
# aliases before any branch reads args, so a limb fails only when the *value* is actually missing.
CANON_KEYS: dict[str, tuple[str, ...]] = {
    "web_search": ("q",), "web_fetch": ("url",), "jina_fetch": ("url",), "wayback": ("url",),
    "http_json": ("url",), "page_thumbnail": ("url",), "download_url": ("url", "path"),
    "arxiv_search": ("q",), "hn_search": ("q",), "github_search": ("q",), "search_corpus": ("q",),
    "memory_recall": ("q",), "clawhub_search": ("q",), "credential_where": ("q",),
    "recall_history": ("q",),
    "session_list": ("q", "tag", "month"), "session_open": ("sid",), "session_search": ("q",),
    "session_label": ("sid", "title"), "session_resume": ("sid",),
    "skillhub_list": ("q", "channel"), "clawhub_install": ("slug",), "skillhub_install": ("slug", "full"),
    "skill_read": ("slug",), "skill_enable": ("slug",), "skill_disable": ("slug",),
    "shell": ("cmd",), "python_exec": ("code",), "calc": ("expr",), "hash_text": ("text",),
    "p0_gate": ("text",), "remember": ("note",), "memory_append": ("note",), "todo_add": ("item",),
    "read_file": ("path",), "write_file": ("path", "content"), "list_dir": ("path",),
    "find_files": ("pattern", "root"), "glob_files": ("pattern",), "image_info": ("path",),
    "image_save": ("b64", "path"), "edit_file": ("path", "old", "new"), "weather": ("place",),
    "geocode": ("place",), "notepad_read": ("id",), "notepad_write": ("id", "title", "text"),
}
ALIAS_POOL: dict[str, tuple[str, ...]] = {
    "q": ("query", "term", "terms", "search", "search_query", "keywords", "question", "input", "text", "value"),
    "url": ("link", "uri", "address", "site", "page", "href"),
    "slug": ("skill", "skill_name", "name", "key"),
    "cmd": ("command", "shell_command", "line", "script", "run"),
    "code": ("value", "src", "source", "snippet", "script", "python", "body"),
    "expr": ("expression", "formula", "equation", "math", "sum", "query", "value", "input"),
    "text": ("value", "content", "body", "message", "input", "src", "data"),
    "note": ("text", "content", "message", "value", "body"),
    "item": ("text", "todo", "task", "value", "content"),
    "path": ("file", "filepath", "file_path", "filename", "target", "dest", "destination", "dir", "directory"),
    "pattern": ("glob", "mask", "wildcard", "query"),
    "place": ("location", "city", "town", "where", "query"),
    "id": ("name", "key", "slug"),
    "content": ("text", "body", "data", "value"),
    "b64": ("base64", "data", "image", "img"),
    "old": ("from", "find", "search"),
    "new": ("to", "replace", "with"),
    "root": ("dir", "directory", "path"),
    "channel": ("type",),
}


def canonicalize(name: str, args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Fill a limb's canonical argument names from the aliases a small model reaches for."""
    keys = CANON_KEYS.get(name)
    if not keys or not isinstance(args, dict):
        return name, args
    out = dict(args)
    # taken = keys already CONSUMED as an alias source. Pre-seeding it with every present key
    # skipped the alias itself ({"value": ...} never filled "code"), which is how this helper first
    # shipped broken. Canonical keys that already carry a value are skipped by the guard above.
    taken: set[str] = set()
    for key in keys:
        if str(out.get(key) or "").strip():
            continue
        for alt in ALIAS_POOL.get(key, ()):
            if alt in taken:
                continue
            val = out.get(alt)
            if isinstance(val, str) and val.strip():
                if key == "url" and not val.strip().lower().startswith("http"):
                    continue
                out[key] = val.strip()
                taken.add(alt)
                break
            if val not in (None, "", [], {}):
                out[key] = val
                taken.add(alt)
                break
    if name == "edit_file" and not str(out.get("old") or "").strip():
        # Measured 2026-09-18: asked to replace "old-value" with "agent-value", the model emitted
        # those words AS KEY NAMES. Two loose string args beside "path" are the replacement pair,
        # in the order the model wrote them - a mechanical fill, not an invention.
        loose = [k for k in out if k not in keys and str(out.get(k) or "").strip()]
        if loose:
            out["old"] = out[loose[0]]
            if len(loose) > 1:
                out["new"] = out[loose[1]]
    return name, out


def _win_env() -> dict[str, str]:
    keys = ("PATH", "SystemRoot", "COMSPEC", "PATHEXT", "TEMP", "TMP", "USERNAME", "USERPROFILE", "WINDIR")
    env = {k: os.environ[k] for k in keys if k in os.environ}
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _ws(p: str | None) -> Path:
    # under_workspace also accepts the redundant leading "workspace/" that models add by habit
    # (workspace/gauntlet_edit.txt used to resolve to workspace/workspace/gauntlet_edit.txt).
    return under_workspace(p or ".")


def _kill_tree(pid: int) -> None:
    """Kill a pid and everything it spawned.

    subprocess's own timeout handling kills only the direct child: `cmd.exe /c <exe>` leaves the
    real program (browser, installer) alive as an orphan, still holding files on the stick.
    taskkill /T walks the tree first, so a grandchild dies with its parent.
    """
    if not pid:
        return
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(int(pid))], capture_output=True, timeout=20)
            return
        except Exception:
            pass
    try:
        os.kill(int(pid), signal.SIGTERM)
    except Exception:
        pass


def _run_capture(argv: list[str], *, timeout: int, cwd: str, env: dict[str, str]) -> tuple[int | None, str, str, bool]:
    """Run argv, capturing text output; on timeout kill the whole process TREE.

    Returns (returncode, stdout, stderr, timed_out). returncode is None when it timed out.
    """
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    try:
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out or "", err or "", False
    except subprocess.TimeoutExpired:
        _kill_tree(proc.pid)
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.communicate(timeout=10)
        except Exception:
            pass
        return None, "", "", True
    finally:
        for stream in (proc.stdout, proc.stderr):
            try:
                if stream is not None and not stream.closed:
                    stream.close()
            except Exception:
                pass


def extra(name: str, args: dict[str, Any]) -> dict[str, Any] | None:
    name, args = canonicalize(name, args or {})
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
        if re.search(r"[|&><`$]", cmd):
            return {"ok": False, "error": "metachar"}
        try:
            code, out, err, timed_out = _run_capture(
                ["cmd.exe", "/c", cmd], timeout=25, cwd=str(WORKSPACE), env=_win_env()
            )
        except OSError as exc:
            return {"ok": False, "error": f"spawn_failed:{type(exc).__name__}"}
        if timed_out:
            return {"ok": False, "error": "timeout"}
        return {"ok": code == 0, "code": code, "stdout": out[-8000:], "stderr": err[-4000:]}
    if name == "python_exec":
        code = str(args.get("code") or "")
        if not code.strip():
            # name the missing argument: a bare "empty" told the operator nothing and the model
            # then answered from its own arithmetic (measured: {"value": "print(6*7)"} -> 42).
            return {"ok": False, "error": "empty", "hint": "python_exec needs 'code' - a python snippet that prints its result", "got_keys": sorted(args)}
        if _SHELL_DENY.search(code) or gate_prompt(code).get("verdict") == "QUARANTINE":
            return {"ok": False, "error": "p0_blocked"}
        try:
            code, out, err, timed_out = _run_capture(
                [sys.executable, "-c", code], timeout=20, cwd=str(WORKSPACE), env=_win_env()
            )
        except OSError as exc:
            return {"ok": False, "error": f"spawn_failed:{type(exc).__name__}"}
        if timed_out:
            return {"ok": False, "error": "timeout"}
        return {"ok": code == 0, "stdout": out[-8000:], "stderr": err[-4000:]}
    if name == "now":
        n = dt.datetime.now().astimezone()
        u = dt.datetime.now(dt.timezone.utc)
        return {"ok": True, "iso": n.isoformat(), "utc": u.isoformat(), "unix": int(n.timestamp()), "tz": str(n.tzinfo), "weekday": n.strftime("%A")}
    if name == "world_pulse":
        from world_clock import pulse

        return pulse()
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
        from admin_map import is_admin
        from tools import dispatch as _dispatch

        pat = str(args.get("pattern") or "*")
        if is_admin() and (":" in pat or any(ch in pat for ch in "\\/")):
            return _dispatch("find_files", {"pattern": Path(pat).name, "root": str(Path(pat).parent)})
        if is_admin():
            return _dispatch("find_files", {"pattern": pat})
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
            val = _safe_arith(expr)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "value": val}
    if name == "whoami":
        from admin_map import brief, is_admin

        from runtime_facts import facts as _facts

        b = brief()
        f = _facts()
        return {
            "ok": True,
            "mark": "LYGO",
            "role": b.get("role"),
            "seat": "LYRA-Δ9 architect seat on this console",
            "steward": b.get("steward"),
            "kit": str(KIT_ROOT),
            "workspace": str(WORKSPACE),
            "portal": "https://chatagent.ca/lygo-llm-console.html",
            "model": f.get("model"),
            "engine": f.get("engine"),
            "engine_port": f.get("engine_port"),
            "brain": f.get("brain"),
            "brain_label": f.get("brain_label"),
            "build": f.get("build"),
            "n_limbs": f.get("n_limbs"),
            "github": b.get("github_org"),
            "huggingface": b.get("hf_org"),
            "links": {
                "github_org": b.get("github_org"),
                "hf_org": b.get("hf_org"),
                "github_repos": b.get("github_repos"),
                "sites": b.get("sites"),
                "lattice": b.get("lattice"),
            }
            if is_admin()
            else {},
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
    if name == "identity_read":
        from continuity import identity_path, ensure_identity

        ensure_identity()
        p = identity_path()
        return {"ok": True, "path": str(p), "text": p.read_text(encoding="utf-8", errors="replace")[:8000] if p.is_file() else ""}
    if name == "edit_file":
        p = _ws(str(args.get("path") or ""))
        try:
            p.resolve().relative_to(WORKSPACE.resolve())
        except ValueError:
            return {"ok": False, "error": "denied"}
        if not p.is_file():
            return {"ok": False, "error": "missing"}
        old, new = str(args.get("old") or ""), str(args.get("new") or "")
        if not old:
            # "" is a substring of every string, so the old_not_found guard below could never fire:
            # a call that named neither "old" nor "new" replaced nothing and still returned ok:True.
            return {"ok": False, "error": "empty",
                    "hint": "edit_file needs 'old' (the exact text to replace) and 'new'",
                    "got_keys": sorted(args)}
        t = p.read_text(encoding="utf-8", errors="replace")
        if old not in t:
            return {"ok": False, "error": "old_not_found",
                    "hint": "'old' does not appear in this file - read the file first",
                    "head": t[:200]}
        atomicio.atomic_write_text(p, t.replace(old, new, 1))
        return {"ok": True, "path": str(p), "replaced": 1, "occurrences": t.count(old),
                "bytes": len(t) - len(old) + len(new)}
    if name == "weather":
        from web_tools import _get, _json_get

        place = str(args.get("place") or "Earth")
        # wttr.in answers a browser-like agent with its HTML page even when Accept says text/plain,
        # so read the JSON form (format=j1) and render one line ourselves.
        data = _json_get("https://wttr.in/" + urllib.parse.quote(place) + "?format=j1")
        cur = {}
        if isinstance(data, dict):
            rows = data.get("current_condition") or []
            if rows and isinstance(rows[0], dict):
                cur = rows[0]
        if cur:
            desc = ""
            wd = cur.get("weatherDesc") or []
            if wd and isinstance(wd[0], dict):
                desc = str(wd[0].get("value") or "").strip()
            bits = [
                "{}C".format(cur.get("temp_C")),
                desc,
                "feels {}C".format(cur.get("FeelsLikeC")),
                "wind {}km/h".format(cur.get("windspeedKmph")),
                "humidity {}%".format(cur.get("humidity")),
            ]
            text = place + ": " + ", ".join([b for b in bits if b and "None" not in b])
            return {"ok": True, "text": text, "class": "RESOURCE"}
        code, raw, _ = _get(
            "https://wttr.in/" + urllib.parse.quote(place) + "?format=3",
            headers={"Accept": "text/plain", "User-Agent": "curl/8.4.0"},
        )
        if code != 200:
            return {"ok": False, "error": f"http_{code}"}
        text = raw.decode("utf-8", errors="replace").strip()
        if "<html" in text[:400].lower():
            return {"ok": False, "error": "html_page_not_weather"}
        return {"ok": True, "text": text, "class": "RESOURCE"}
    if name == "geocode":
        from web_tools import _json_get

        qs = urllib.parse.urlencode({"q": str(args.get("place") or ""), "format": "json", "limit": "3"})
        data = _json_get("https://nominatim.openstreetmap.org/search?" + qs)
        if not data:
            return {"ok": False, "error": "none"}
        rows = [{"name": x.get("display_name"), "lat": x.get("lat"), "lon": x.get("lon")} for x in data[:3]]
        return {"ok": True, "results": rows, "class": "RESOURCE"}
    if name == "http_json":
        from web_tools import _blocked, _json_get

        url = str(args.get("url") or "")
        why = _blocked(url)
        if why:
            return {"ok": False, "error": why}
        data = _json_get(url)
        if data is None:
            return {"ok": False, "error": "not_json"}
        blob = json.dumps(data, default=str)
        return {"ok": True, "data": blob[:12000]}
    if name == "wayback":
        from web_tools import _blocked, _json_get

        url = str(args.get("url") or "")
        why = _blocked(url)
        if why:
            return {"ok": False, "error": why}
        data = _json_get("https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe=""))
        return {"ok": True, "data": data, "class": "RESOURCE"}
    if name == "arxiv_search":
        from web_tools import _get
        import xml.etree.ElementTree as ET

        q = str(args.get("q") or "").strip()
        # Date-sorted results are precise only if the phrase is exact; an unquoted multi-word q
        # matches any paper sharing one word, so quote it before it goes to arXiv.
        if " " in q and '"' not in q:
            q = '"' + q + '"'
        qs = urllib.parse.quote(q)
        # arXiv's default order is relevance, which surfaced 2003-2016 papers as "newest"; ask for
        # submission-date order explicitly.
        url = (
            "https://export.arxiv.org/api/query?search_query=all:"
            + qs
            + "&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending"
        )
        code, raw, _ = _get(url)
        if code != 200:
            return {"ok": False, "error": f"http_{code}"}
        papers = []
        try:
            root = ET.fromstring(raw)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            for ent in root.findall("a:entry", ns)[:5]:
                title = (ent.findtext("a:title", default="", namespaces=ns) or "").strip()
                link = ""
                for l in ent.findall("a:link", ns):
                    if l.get("type") == "text/html":
                        link = l.get("href") or ""
                papers.append({"title": title, "url": link})
        except ET.ParseError:
            return {"ok": False, "error": "xml"}
        return {"ok": True, "papers": papers, "class": "RESOURCE"}
    if name == "hn_search":
        from web_tools import hn_search

        return {"ok": True, "hits": hn_search(str(args.get("q") or "")), "class": "RESOURCE"}
    if name == "github_search":
        from admin_map import is_admin
        from web_tools import github_search

        q = str(args.get("q") or "")
        if is_admin() and "user:" not in q.lower() and "org:" not in q.lower():
            scoped = github_search("user:DeepSeekOracle " + q)
            if scoped:
                return {"ok": True, "hits": scoped, "query": "user:DeepSeekOracle " + q, "scope": "steward", "class": "RESOURCE"}
            # An empty answer is worse than a broad one: the steward-scoped search matched nothing,
            # so search GitHub generally and say plainly that the scope was widened.
            return {"ok": True, "hits": github_search(q), "query": q, "scope": "global_fallback", "class": "RESOURCE"}
        return {"ok": True, "hits": github_search(q), "query": q, "scope": "global", "class": "RESOURCE"}
    if name == "image_info":
        from image_tools import image_info

        return image_info(str(args.get("path") or ""))
    if name == "image_save":
        from image_tools import image_save

        return image_save(str(args.get("b64") or args.get("data") or ""), args.get("path"))
    if name == "image_list":
        from image_tools import image_list

        return image_list()
    if name == "page_thumbnail":
        from image_tools import page_thumbnail

        return page_thumbnail(str(args.get("url") or ""))
    if name == "jina_fetch":
        from web_tools import jina_fetch

        return jina_fetch(str(args.get("url") or ""))
    if name == "sessions_list":
        from paths import SAVE

        d = SAVE / "sessions"
        names = [p.name for p in d.glob("*.json")] if d.is_dir() else []
        # The record of truth lives beside the session snapshots: one journal per session, plus the
        # sealed archive. Listing only *.json would hide exactly the conversations worth finding.
        journals = sorted(p.name for p in d.glob("journal-*.jsonl")) if d.is_dir() else []
        out: dict[str, Any] = {"ok": True, "files": names, "journals": journals}
        try:
            import compaction

            st = compaction.status()
            out["sealed"] = st.get("sessions_sealed")
            out["sealed_bytes"] = st.get("sealed_bytes")
            out["session_id"] = st.get("session_id")
        except Exception:  # noqa: BLE001
            pass
        return out
    if name in {"session_list", "session_catalog"}:
        import sessions

        out = sessions.safe_catalog(int(args.get("limit") or 50), str(args.get("q") or ""),
                                    str(args.get("tag") or ""), str(args.get("month") or ""))
        if not out.get("ok"):
            return out
        rows = out.get("sessions") or []
        return {
            "ok": True, "vault": out.get("vault"), "count": out.get("count"), "shown": len(rows),
            "turns": out.get("turns"), "tags": out.get("tags"),
            "sessions": [{"sid": r.get("sid"), "title": r.get("title"), "turns": r.get("turns"),
                          "started": str(r.get("created_iso") or "")[:16], "tags": r.get("tags") or [],
                          "note": r.get("note") or "", "pinned": bool(r.get("pinned")),
                          "folder": r.get("folder")} for r in rows],
        }
    if name == "session_open":
        import sessions

        out = sessions.safe_open(str(args.get("sid") or args.get("id") or ""),
                                 int(args.get("chars") or 12000))
        if out.get("ok"):
            out.pop("messages", None)  # the transcript is the readable form; this would double it
        return out
    if name == "session_search":
        import sessions

        return sessions.safe_search(str(args.get("q") or args.get("query") or ""),
                                    int(args.get("k") or 6))
    if name == "session_label":
        import sessions

        sid = str(args.get("sid") or args.get("id") or "")
        kw: dict = {}
        if args.get("title") is not None:
            kw["title"] = str(args["title"])
        if args.get("note") is not None:
            kw["note"] = str(args["note"])
        if args.get("tags") is not None:
            tags = args["tags"]
            kw["tags"] = (tags if isinstance(tags, list)
                          else [p.strip() for p in str(tags).split(",") if p.strip()])
        if args.get("pinned") is not None:
            kw["pinned"] = bool(args["pinned"])
        if not sid:
            filed = sessions.safe_vault("manual")  # no id: file the conversation in progress
            sid = str(filed.get("sid") or "")
            if not sid:
                return filed
        return sessions.safe_label(sid, **kw)
    if name == "session_resume":
        import sessions

        out = sessions.safe_resume(str(args.get("sid") or args.get("id") or ""))
        if out.get("ok"):
            out.pop("messages", None)  # the console reads those from its own session file
        return out
    if name == "recall_history":
        import compaction

        q = str(args.get("q") or args.get("query") or args.get("term") or "")
        try:
            k = int(args.get("k") or args.get("limit") or 6)
        except (TypeError, ValueError):
            k = 6
        return compaction.recall(q, k=k)
    return None
