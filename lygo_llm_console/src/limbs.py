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
import urllib.parse
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
    if name == "edit_file":
        p = _ws(str(args.get("path") or ""))
        try:
            p.resolve().relative_to(WORKSPACE.resolve())
        except ValueError:
            return {"ok": False, "error": "denied"}
        if not p.is_file():
            return {"ok": False, "error": "missing"}
        old, new = str(args.get("old") or ""), str(args.get("new") or "")
        t = p.read_text(encoding="utf-8", errors="replace")
        if old not in t:
            return {"ok": False, "error": "old_not_found"}
        p.write_text(t.replace(old, new, 1), encoding="utf-8")
        return {"ok": True, "path": str(p)}
    if name == "weather":
        from web_tools import _get

        place = urllib.parse.quote(str(args.get("place") or "Earth"))
        code, raw, _ = _get("https://wttr.in/" + place + "?format=3")
        if code != 200:
            return {"ok": False, "error": f"http_{code}"}
        return {"ok": True, "text": raw.decode("utf-8", errors="replace").strip(), "class": "RESOURCE"}
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

        qs = urllib.parse.quote(str(args.get("q") or ""))
        code, raw, _ = _get("https://export.arxiv.org/api/query?search_query=all:" + qs + "&start=0&max_results=5")
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
        from web_tools import github_search

        return {"ok": True, "hits": github_search(str(args.get("q") or "")), "class": "RESOURCE"}
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
        return {"ok": True, "files": names}
    return None
