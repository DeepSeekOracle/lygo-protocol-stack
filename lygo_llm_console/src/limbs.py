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
    {"type": "function", "function": {"name": "python_exec", "description": "Run Python and read the result: compute, test, verify. Use this instead of doing arithmetic or file work in your head. Print to capture output; argv, timeout, cwd optional.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "argv": {"type": "array", "items": {"type": "string"}}, "timeout": {"type": "integer"}, "cwd": {"type": "string"}, "interpreter": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "rust_exec", "description": "Run Rust and read the result: a single-file program (rustc) or a cargo crate. Use for native code, benchmarks and real compile errors. Diagnostics and program output are captured; on a machine without a linker it type-checks and says so.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "crate": {"type": "string"}, "name": {"type": "string"}, "release": {"type": "boolean"}, "timeout": {"type": "integer"}}, "required": []}}},
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
    {"type": "function", "function": {"name": "image_info", "description": "For a picture FILE on disk - a picture attached to this conversation you already see. Inspect one image file: kind, byte size and pixel dimensions. `path` may be an absolute path on this PC under a mapped read root (config/admin.json read_roots) or a workspace path. This reads metadata only - it does not describe or generate pictures.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "image_see", "description": "For a picture FILE on disk. A photo attached to this conversation is already visible to you directly, so do not call this for it. LOOK AT a picture: sends the image file to the local vision model and returns a written description. `path` may be an absolute path on this PC under a mapped read root or a workspace path. Use for 'check this photo', 'what is in this image'. Runs our own engine (llama-server with --mmproj) on the registered vision model - no daemon; failures name the rule.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "prompt": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "image_save", "description": "Save a base64 or data-URL image into workspace/images.", "parameters": {"type": "object", "properties": {"b64": {"type": "string"}, "path": {"type": "string"}}, "required": ["b64"]}}},
    {"type": "function", "function": {"name": "image_list", "description": "List workspace/images files.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "page_thumbnail", "description": "Capture a public HTTPS page thumbnail into workspace/images.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "image_generate", "description": "MAKE A NEW PICTURE from words - generation, not inspection. Renders with the local stable-diffusion backend and writes a PNG into workspace/images, returning its path. Slow on this machine: a first run also loads the checkpoint, so allow minutes. Use image_info or image_see to inspect a picture that ALREADY exists; never call this to look at one. Example: 'draw a red apple on a wooden table'.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "negative": {"type": "string"}, "width": {"type": "integer"}, "height": {"type": "integer"}, "steps": {"type": "integer"}, "cfg_scale": {"type": "number"}, "model": {"type": "string", "description": "Which generator to use. Leave empty for the default fast checkpoint. Or pass a declared model id such as 'qwen-image-2.1' - a slower, higher-quality flow model that needs its own VAE and text encoder. media_status lists the ids this machine actually has."}, "cpu": {"type": "boolean"}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "sound_speak", "description": "GENERATE SPEECH: turn text into a spoken WAV file with the local voice engine, written into workspace/audio, returning its path and its length in seconds. Use it when the operator asks to hear something read aloud or wants an audio file made.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "voice": {"type": "string"}, "length_scale": {"type": "number"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "media_status", "description": "Report whether picture generation and voice generation are wired on THIS machine: which binaries and checkpoints were found, and where they live. Call it before promising a picture or a voice, or after a generation fails.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "jina_fetch", "description": "Readable extract of a page via r.jina.ai.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "sessions_list", "description": "List saved chat session files.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "session_list", "description": "List the filed session vault: title, id, turns, date, tags, note. Filters: q, tag, month.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}, "tag": {"type": "string"}, "month": {"type": "string"}, "limit": {"type": "integer"}}}}},
    {"type": "function", "function": {"name": "session_open", "description": "Read a filed session back: its transcript, manifest and where it sits on disk. Use it to revisit or quote an older conversation.", "parameters": {"type": "object", "properties": {"sid": {"type": "string"}, "chars": {"type": "integer"}}, "required": ["sid"]}}},
    {"type": "function", "function": {"name": "session_search", "description": "Find a past session by phrase. Searches the vault's titles, tags, notes and the transcripts themselves.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}, "k": {"type": "integer"}}, "required": ["q"]}}},
    {"type": "function", "function": {"name": "session_label", "description": "Name, tag or annotate a filed session so it can be found again later. Omit sid to label the conversation in progress.", "parameters": {"type": "object", "properties": {"sid": {"type": "string"}, "title": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}, "note": {"type": "string"}, "pinned": {"type": "boolean"}}}}},
    {"type": "function", "function": {"name": "session_resume", "description": "Reopen a filed session as the live conversation. The session in progress is filed first, so nothing is lost.", "parameters": {"type": "object", "properties": {"sid": {"type": "string"}}, "required": ["sid"]}}},
    {"type": "function", "function": {"name": "recall_history", "description": "Search everything said in this chat: the live journal and sealed sessions. Use it when the operator refers to something older than your window.", "parameters": {"type": "object", "properties": {"q": {"type": "string"}, "k": {"type": "integer"}}, "required": ["q"]}}},
        # ------------------------------------------------------------ self-build harness
        # Four limbs that close the loop the console was missing: it could read and edit its own
        # source, but could not run its own tests, seal its own build, restart onto a change, or
        # install a toolchain it lacked. Everything that changes the system needs consent=true, in
        # the kit's own --i-consent language.
        {"type": "function", "function": {"name": "self_test", "description": "Run this console's OWN test suite and read the result: pass/fail counts, which tests failed, seconds. Use after changing any code in this kit, before believing the change.", "parameters": {"type": "object", "properties": {"target": {"type": "string", "description": "one file under tests/, e.g. tests/test_tool_routing.py; empty runs the fast core set"}, "timeout": {"type": "integer", "description": "seconds, 30-1800 (default 900)"}}, "required": []}}},
        {"type": "function", "function": {"name": "self_seal", "description": "SEAL THIS BUILD: refresh the kit's manifests and certify it. Needs consent=true. Use after self_test passes - sealing certifies whatever is on disk, so test first.", "parameters": {"type": "object", "properties": {"consent": {"type": "boolean", "description": "true approves rewriting the kit's own manifests"}, "dry_run": {"type": "boolean", "description": "show the steps without running them"}}, "required": []}}},
        {"type": "function", "function": {"name": "self_restart", "description": "RESTART THIS CONSOLE through its own doorbell so a code change takes effect. Needs consent=true. The page drops for about a minute while the model reloads.", "parameters": {"type": "object", "properties": {"consent": {"type": "boolean"}, "wait": {"type": "integer", "description": "seconds to wait after ringing, 0-600"}}, "required": []}}},
        {"type": "function", "function": {"name": "toolchain_install", "description": "Check what this machine can build with, or install what it lacks. what=check lists compilers and linkers (always safe). rust_gnu_target adds a user-space Rust linker - no administrator needed. pip and winget need a package id. Plan only unless consent=true.", "parameters": {"type": "object", "properties": {"what": {"type": "string", "description": "check | rust_gnu_target | pip | winget"}, "package": {"type": "string", "description": "package id, required for pip and winget"}, "consent": {"type": "boolean", "description": "true approves the install for real"}}, "required": []}}},
        # ------------------------------------------------------------ tasking, cron, keeper
        # The console could only work inside a turn: a slow job held the conversation still and
        # nothing outlived it. These let the agent hand work to a queue, schedule it, and read the
        # daemon that keeps the console alive. Modelled on the Hermes task, cron and liveness code.
        {"type": "function", "function": {"name": "task_add", "description": "START SLOW WORK IN THE BACKGROUND and answer straight away: queue a limb call and get a task id back. Use for self_test, a build, a long fetch - anything that would otherwise make the user wait. Read it with task_list.", "parameters": {"type": "object", "properties": {"target": {"type": "string", "description": "the limb to run, e.g. self_test"}, "args": {"type": "object", "description": "arguments for that limb"}, "note": {"type": "string", "description": "what this job is for, in your own words"}, "deadline": {"type": "number", "description": "seconds before the job counts as stalled (default 900)"}}, "required": ["target"]}}},
        {"type": "function", "function": {"name": "task_list", "description": "Read the background queue: queued, running, done, failed, stalled counts and the recent tasks.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}, "state": {"type": "string", "description": "queued | running | done | failed | stalled | cancelled"}}, "required": []}}},
        {"type": "function", "function": {"name": "task_show", "description": "Read one background task in full: its result, how long it ran, what it was for.", "parameters": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}}},
        {"type": "function", "function": {"name": "task_cancel", "description": "Cancel a background task that has not started yet.", "parameters": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}}},
        {"type": "function", "function": {"name": "cron_add", "description": "SCHEDULE RECURRING WORK: run a limb every N seconds or daily at a time. The keeper daemon runs it, so it happens without anyone asking again.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "limb": {"type": "string", "description": "the limb to run, e.g. self_test"}, "args": {"type": "object"}, "every": {"type": "integer", "description": "seconds between runs"}, "at": {"type": "string", "description": "daily time HH:MM, 24-hour"}, "note": {"type": "string"}}, "required": ["name", "limb"]}}},
        {"type": "function", "function": {"name": "cron_list", "description": "List the scheduled jobs: when each is next due, how often it has run, and how the last run went.", "parameters": {"type": "object", "properties": {}}}},
        {"type": "function", "function": {"name": "cron_remove", "description": "Delete a scheduled job by name.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
        {"type": "function", "function": {"name": "keeper_status", "description": "Report the keeper daemon: is it alive, is the console up, is the doorbell up, what has it restarted lately.", "parameters": {"type": "object", "properties": {}}}},
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
    "shell": ("cmd",), "python_exec": ("code",), "rust_exec": ("code", "source"), "calc": ("expr",), "hash_text": ("text",),
    "p0_gate": ("text",), "remember": ("note",), "memory_append": ("note",), "todo_add": ("item",),
    "read_file": ("path",), "write_file": ("path", "content"), "list_dir": ("path",),
    "find_files": ("pattern", "root"), "glob_files": ("pattern",), "image_info": ("path",),
    "image_see": ("path", "prompt"), "image_save": ("b64", "path"), "edit_file": ("path", "old", "new"), "weather": ("place",),
    "image_generate": ("prompt",), "sound_speak": ("text",), "media_status": (),
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
    "prompt": ("text", "description", "q", "prompt_text", "message", "input", "value"),
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


def _tool_env() -> dict[str, str]:
    """The full environment, for compilers and interpreters.

    `_win_env()` narrows the environment on purpose - that is right for `shell`, which must not
    inherit whatever a parent happened to export. It is wrong for a toolchain: measured here, the very
    same `rustc -O` command that builds successfully with the inherited environment fails under the
    narrowed one with "linker `link.exe` not found", because the linker is found through a variable the
    narrow list drops. So compilers get the real environment; only shell gets the scrubbed one.
    """
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


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
    # errors="replace": a compiler may emit bytes the console's locale codec cannot decode, and a
    # UnicodeDecodeError here would kill the limb instead of reporting the program (seen live).
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            errors="replace", env=env)
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


RUST_DIR = WORKSPACE / "rust"


def _find_rust() -> tuple[str | None, str | None]:
    """(rustc, cargo) - PATH first, then the usual rustup install. (None, None) when absent."""
    import shutil  # local: this module must import with nothing but the stdlib

    def pick(name: str) -> str | None:
        got = shutil.which(name)
        if got:
            return got
        guess = Path.home() / ".cargo" / "bin" / (name + ".exe")
        return str(guess) if guess.is_file() else None

    return pick("rustc"), pick("cargo")


def _looks_like_a_linker_failure(text: str) -> bool:
    """Did the build fail at LINK time rather than in the code? Then a type-check is still useful."""
    low = (text or "").lower()
    return any(k in low for k in ("linker `link.exe` not found", "linking with `link.exe` failed",
                                  "link.exe", "extra operand", "linker", "link --help"))


_RUST_PROBE: dict[str, Any] = {}


def _is_real_linker(path: str) -> bool:
    """Is this `link` the Microsoft linker, or the coreutils hardlink tool git-bash ships?"""
    low = re.sub(r"/+", "/", str(path or "").replace("\\", "/").lower())
    if not low:
        return False
    return not ("/usr/bin/" in low or "git/usr" in low or "/msys" in low or "mingw64/usr" in low)


def _rust_probe(force: bool = False) -> dict[str, Any]:
    """Ask the toolchain whether it can really build AND run, instead of guessing from the PATH.

    Name-based guessing lies in both directions. git-bash ships a `link.exe` that is coreutils, so a
    machine looks equipped when it is not; and a machine with no `link.exe` on PATH at all can still
    link, because rustc ships its own linker (`rust-lld`), measured working here. So the probe builds a
    trivial program and runs it. Cached per process: that is what "can this machine build Rust" means
    once it has been answered.
    """
    import shutil as _sh
    import tempfile as _tf

    if _RUST_PROBE and not force:
        return _RUST_PROBE
    out: dict[str, Any] = {"can_run": False, "via": "", "detail": "", "stdout": ""}
    rustc = _sh.which("rustc")
    if not rustc:
        out["detail"] = "rustc is not on PATH"
        _RUST_PROBE.update(out)
        return out

    host = ""
    try:
        vv = subprocess.run(["rustc", "-vV"], capture_output=True, text=True, errors="replace", timeout=60).stdout or ""
        m = re.search(r"host:\s*(\S+)", vv)
        host = m.group(1) if m else ""
    except Exception:
        pass
    lld = _sh.which("rust-lld") or _find_rust_lld(rustc, host)

    attempts = [("plain", [])]
    if lld:
        attempts.append(("rust-lld", ["-C", f"linker={lld}"]))
    with _tf.TemporaryDirectory(prefix="lygo-rust-probe-") as d:
        work = Path(d)
        (work / "probe.rs").write_text('fn main() { println!("{}", 6 * 7); }\n', encoding="utf-8")
        exe = work / "probe.exe"
        first_error = ""
        for label, extra in attempts:
            try:
                b = subprocess.run([rustc, "-O", *extra, "probe.rs", "-o", str(exe)], cwd=str(d),
                                   capture_output=True, text=True, timeout=300)
            except Exception as exc:
                first_error = first_error or f"{type(exc).__name__}"
                continue
            if b.returncode == 0 and exe.is_file():
                try:
                    run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=60)
                except Exception as exc:
                    first_error = first_error or f"run: {type(exc).__name__}"
                    continue
                out.update({"can_run": run.returncode == 0, "via": label,
                            "stdout": (run.stdout or "").strip()[:40],
                            "detail": f"built and ran a probe program ({label})"})
                _RUST_PROBE.update(out)
                return out
            first_error = first_error or " ".join((b.stderr or b.stdout or "").strip().splitlines()[-1:])[:200]
        try:
            c = subprocess.run([rustc, "--emit=metadata", "probe.rs", "-o", str(work / "probe.rmeta")],
                               cwd=str(d), capture_output=True, text=True, timeout=300)
            out["checked"] = c.returncode == 0
        except Exception:
            out["checked"] = False
        out["detail"] = (first_error or "no linker worked") + (" - the program type-checks" if out.get("checked") else "")
    _RUST_PROBE.update(out)
    return out


def _find_rust_lld(rustc: str = "", host: str = "") -> str:
    """Find the linker Rust ships. `~/.cargo/bin/rustc` is a rustup shim, so its neighbours are not
    the toolchain: ask rustup, then look in the real rustlib. Measured: rust-lld alone can link a
    Windows program here, which is what makes the Rust limb work on a machine with no MSVC linker."""
    import shutil as _sh

    hit = _sh.which("rust-lld")
    if hit:
        return hit
    real = ""
    try:
        got = subprocess.run(["rustup", "which", "rustc"], capture_output=True, text=True, errors="replace", timeout=60)
        if got.returncode == 0:
            real = (got.stdout or "").strip().splitlines()[0] if got.stdout.strip() else ""
    except Exception:
        real = ""
    roots = []
    if real:
        roots.append(Path(real).parent.parent / "lib" / "rustlib")
    if rustc:
        roots.append(Path(rustc).parent.parent / "lib" / "rustlib")
    roots.append(Path.home() / ".rustup" / "toolchains")
    for root in roots:
        for pat in ([f"{host}/bin/rust-lld.exe"] if host else []) + ["*/bin/rust-lld.exe", "*/lib/rustlib/*/bin/rust-lld.exe"]:
            for cand in root.glob(pat):
                if cand.is_file():
                    return str(cand)
    return ""


def _find_real_linker() -> str:
    """The Microsoft linker by path, ignoring anything git-bash put on PATH under the same name.

    Measured: in a clean PATH `rustc` links fine here; in a git-bash PATH it is handed coreutils'
    `link.exe` and fails. `rust-lld` alone is not enough (no MSVC import libraries), so the fix is to
    name the real linker explicitly.
    """
    import shutil as _sh

    for name in ("link", "lld-link"):
        got = _sh.which(name) or ""
        if got and _is_real_linker(got):
            return got
    for root in (Path(r"C:\Program Files\Microsoft Visual Studio"),
                 Path(r"C:\Program Files (x86)\Microsoft Visual Studio")):
        if root.is_dir():
            for cand in root.glob("*/*/VC/Tools/MSVC/*/bin/Host*/x64/link.exe"):
                if cand.is_file():
                    return str(cand)
    return ""


def _rust_link_args(srcf: Path, binp: Path, rustc: str) -> list[str]:
    """How to build a single-file program here, decided by measurement rather than by name.

    plain rustc if that links; otherwise the linker Rust ships; otherwise a metadata-only check. The
    old version asked `_rust_linker_ok()` and, when it said no, never tried the linker that works.
    """
    probe = _rust_probe()
    if probe.get("can_run") and probe.get("via") == "rust-lld":
        lld = _find_rust_lld(rustc, "")
        if lld:
            return [rustc, "-O", "-C", f"linker={lld}", str(srcf), "-o", str(binp)]
    if probe.get("can_run"):
        return [rustc, "-O", str(srcf), "-o", str(binp)]
    real = _find_real_linker()
    if real:
        return [rustc, "-O", "-C", f"linker={real}", str(srcf), "-o", str(binp)]
    lld = _find_rust_lld(rustc, _rust_host(rustc))
    if lld:
        return [rustc, "-O", "-C", f"linker={lld}", str(srcf), "-o", str(binp)]
    return [rustc, "--emit=metadata", "--crate-type=bin", str(srcf), "-o", str(srcf.with_suffix(".rmeta"))]


def _rust_host(rustc: str = "") -> str:
    """The host triple, for finding the right rustlib directory."""
    try:
        vv = subprocess.run([rustc or "rustc", "-vV"], capture_output=True, text=True, errors="replace", timeout=60).stdout or ""
        m = re.search(r"host:\s*(\S+)", vv)
        return m.group(1) if m else ""
    except Exception:
        return ""


def _rust_linker_ok() -> bool:
    """Can rustc actually link here? Measured, not guessed."""
    return bool(_rust_probe().get("can_run"))


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
    if name == "rust_exec":
        code = str(args.get("code") or args.get("source") or "")
        crate = str(args.get("crate") or "").strip()
        rustc, cargo = _find_rust()
        if not rustc and not cargo:
            # fail soft and say where it looked: an absent toolchain is not a bug in the turn
            return {"ok": False, "error": "rust_missing",
                    "hint": "no rustc or cargo on PATH or in %USERPROFILE%\\.cargo\\bin - install from rustup.rs",
                    "checked": ["PATH", str(Path.home() / ".cargo" / "bin")]}
        if code.strip() and (_SHELL_DENY.search(code) or gate_prompt(code).get("verdict") == "QUARANTINE"):
            return {"ok": False, "error": "p0_blocked"}
        seconds = max(1, min(300, int(args.get("timeout") or 90)))
        RUST_DIR.mkdir(parents=True, exist_ok=True)
        if crate:
            proj = _ws("rust/" + crate)
            if not (proj / "Cargo.toml").is_file():
                if not code.strip():
                    return {"ok": False, "error": "crate_missing", "path": str(proj),
                            "hint": "no Cargo.toml there: pass code to create the crate, or the name of one that exists"}
                (proj / "src").mkdir(parents=True, exist_ok=True)
                pkg = re.sub(r"[^a-z0-9_]", "_", crate.lower())[:40] or "crate"
                (proj / "Cargo.toml").write_text(
                    f'[package]\nname = "{pkg}"\nversion = "0.1.0"\nedition = "2021"\n', encoding="utf-8")
                (proj / "src" / "main.rs").write_text(code, encoding="utf-8")
            if not cargo:
                return {"ok": False, "error": "cargo_missing", "hint": "cargo is needed for a crate; pass code for a single file"}
            # without a linker, `cargo check` is the honest thing to run: full type-check, real
            # diagnostics, and it never pretends to have executed the program
            argv = [cargo, "run", "--quiet"] + (["--release"] if args.get("release") else [])
            cwd, binp, srcf = proj, None, proj / "src" / "main.rs"
        else:
            if not code.strip():
                return {"ok": False, "error": "empty",
                        "hint": "rust_exec needs 'code' (a single-file program) or 'crate' (a project folder)"}
            if not rustc:
                return {"ok": False, "error": "rustc_missing", "hint": "cargo is present but rustc is not"}
            slug = re.sub(r"[^a-z0-9_]", "_", str(args.get("name") or "main").lower())[:40] or "main"
            cwd = _ws("rust/" + slug)
            cwd.mkdir(parents=True, exist_ok=True)
            srcf = cwd / "main.rs"
            srcf.write_text(code, encoding="utf-8")
            binp = cwd / (slug + ".exe")
            argv = _rust_link_args(srcf, binp, rustc)
            metadata_only = "--emit=metadata" in " ".join(argv)
        try:
            rc, out, err, timed_out = _run_capture(argv, timeout=seconds, cwd=str(cwd), env=_tool_env())
        except OSError as exc:
            return {"ok": False, "error": f"spawn_failed:{type(exc).__name__}"}
        if timed_out:
            return {"ok": False, "error": "timeout", "timed_out": True, "stderr": err[-2000:]}
        if crate and rc != 0 and _looks_like_a_linker_failure(err):
            try:
                rc4, _o4, err4, _t4 = _run_capture([cargo, "check", "--quiet"],
                                                 timeout=seconds, cwd=str(cwd), env=_tool_env())
            except OSError as exc:
                return {"ok": False, "error": f"spawn_failed:{type(exc).__name__}"}
            if rc4 == 0:
                return {"ok": True, "code": 0, "ran": False, "checked": True, "stdout": "",
                        "stderr": err4[-2000:], "timed_out": False, "via": "cargo", "crate": crate,
                        "project": str(cwd),
                        "note": "the crate type-checks, but this machine has no usable linker, so "
                                "it was not built or run. VS Build Tools (C++) or the "
                                "x86_64-pc-windows-gnu target is what enables that.",
                        "linker": err[-1200:]}
            err = err4 or err
        if crate:
            return {"ok": rc == 0, "code": rc, "stdout": out[-8000:], "stderr": err[-4000:],
                    "timed_out": False, "via": "cargo", "project": str(cwd), "crate": crate,
                    "checked": True, "ran": True, "built": bool(_rust_probe().get("can_run"))}
        if rc != 0 and _looks_like_a_linker_failure(err) and "-C" not in argv:
            real = _find_real_linker()
            if real:
                retry = [rustc, "-O", "-C", f"linker={real}", str(srcf), "-o", str(binp)]
                rc_r, out_r, err_r, _to_r = _run_capture(retry, timeout=seconds, cwd=str(cwd), env=_tool_env())
                if rc_r == 0:
                    argv, rc, out, err, metadata_only = retry, rc_r, out_r, err_r, False
        if rc != 0 and _looks_like_a_linker_failure(err):
            # A machine can have rustc and still no usable linker. Do not call that a broken
            # program: type-check it and say precisely what is missing.
            try:
                rc3, _o3, err3, _t3 = _run_capture(
                    [rustc, "--emit=metadata", "--crate-type=bin", str(srcf), "-o", str(cwd / "main.rmeta")],
                    timeout=seconds, cwd=str(cwd), env=_tool_env())
            except OSError as exc:
                return {"ok": False, "error": f"spawn_failed:{type(exc).__name__}"}
            if rc3 == 0:
                return {"ok": True, "code": 0, "ran": False, "checked": True, "stdout": "",
                        "stderr": err3[-2000:], "timed_out": False, "via": "rustc", "file": str(srcf),
                        "note": "the program type-checks, but this machine has no usable linker "
                                "(link.exe missing, or present but not MSVC's), so it was neither "
                                "built nor run. Install VS Build Tools with the C++ workload, or "
                                "`rustup target add x86_64-pc-windows-gnu`, to run Rust programs.",
                        "linker": err[-1200:]}
            err = err3 or err
        if metadata_only and rc == 0:
            return {"ok": True, "code": 0, "ran": False, "checked": True, "stdout": "", "stderr": err[-4000:],
                    "timed_out": False, "via": "rustc", "file": str(srcf),
                    "note": "no linker on this machine (link.exe/gcc absent), so the program was "
                            "type-checked but not built or run. Install VS Build Tools with the C++ "
                            "option, or `rustup target add x86_64-pc-windows-gnu`, to run it.",
                    "compiler": (out + err)[-1500:]}
        if rc != 0:
            # the compiler's own diagnostics, verbatim: that is what makes a Rust limb useful
            return {"ok": False, "error": "compile_failed", "code": rc, "stderr": err[-6000:],
                    "stdout": out[-2000:], "file": str(srcf)}
        try:
            rc2, out2, err2, to2 = _run_capture([str(binp)], timeout=seconds, cwd=str(cwd), env=_tool_env())
        except OSError as exc:
            return {"ok": False, "error": f"spawn_failed:{type(exc).__name__}"}
        if to2:
            return {"ok": False, "error": "timeout", "timed_out": True, "stderr": err2[-2000:]}
        return {"ok": rc2 == 0, "code": rc2, "stdout": out2[-8000:], "stderr": err2[-4000:],
                "timed_out": False, "via": "rustc", "file": str(srcf), "binary": str(binp),
                "ran": True, "checked": True,
                "compiler": (out + err)[-1500:]}
    if name == "python_exec":
        code = str(args.get("code") or "")
        _interp = str(args.get("interpreter") or sys.executable or "python")
        _argv = [_interp, "-c", code] + [str(a) for a in (args.get("argv") or [])]
        _secs = max(1, min(120, int(args.get("timeout") or 20)))
        _where = _ws(str(args.get("cwd"))) if args.get("cwd") else WORKSPACE
        if not code.strip():
            # name the missing argument: a bare "empty" told the operator nothing and the model
            # then answered from its own arithmetic (measured: {"value": "print(6*7)"} -> 42).
            return {"ok": False, "error": "empty", "hint": "python_exec needs 'code' - a python snippet that prints its result", "got_keys": sorted(args)}
        if _SHELL_DENY.search(code) or gate_prompt(code).get("verdict") == "QUARANTINE":
            return {"ok": False, "error": "p0_blocked"}
        try:
            code, out, err, timed_out = _run_capture(
                _argv, timeout=_secs, cwd=str(_where), env=_tool_env()
            )
        except OSError as exc:
            return {"ok": False, "error": f"spawn_failed:{type(exc).__name__}"}
        if timed_out:
            return {"ok": False, "error": "timeout"}
        return {"ok": code == 0, "code": code, "stdout": out[-8000:], "stderr": err[-4000:],
                "timed_out": False, "interpreter": Path(_interp).name}
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
    if name == "image_see":
        from image_tools import image_see

        return image_see(str(args.get("path") or ""), args.get("prompt"))
    if name == "image_save":
        from image_tools import image_save

        return image_save(str(args.get("b64") or args.get("data") or ""), args.get("path"))
    if name == "image_list":
        from image_tools import image_list

        return image_list()
    if name == "page_thumbnail":
        from image_tools import page_thumbnail

        return page_thumbnail(str(args.get("url") or ""))
    if name == "image_generate":
        from media_tools import image_generate

        return image_generate(
            str(args.get("prompt") or ""),
            str(args.get("negative") or ""),
            args.get("width"),
            args.get("height"),
            args.get("steps"),
            args.get("cfg_scale"),
            str(args.get("model") or ""),
            bool(args.get("cpu")),
            args.get("timeout"),
        )
    if name == "sound_speak":
        from media_tools import sound_speak

        return sound_speak(
            str(args.get("text") or ""),
            str(args.get("voice") or ""),
            args.get("length_scale"),
            args.get("timeout"),
        )
    if name == "media_status":
        from media_tools import media_status

        return media_status()
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
    if name == "self_test":
        return _self_test(str(args.get("target") or ""), args.get("timeout") or 900)
    if name == "self_seal":
        return _self_seal(bool(args.get("consent")), bool(args.get("dry_run")))
    if name == "self_restart":
        return _self_restart(bool(args.get("consent")), args.get("wait") or 0)
    if name == "toolchain_install":
        return _toolchain_install(str(args.get("what") or ""), str(args.get("package") or ""), bool(args.get("consent")))
    if name == "task_add":
        import tasking

        got = tasking.add(str(args.get("target") or ""), args.get("args") or {},
                          deadline=args.get("deadline") or 900, note=str(args.get("note") or ""),
                          origin="agent")
        if got.get("ok"):
            got["hint"] = "queued - answer the user now, and read it later with task_list"
        return got
    if name == "task_list":
        import tasking

        return tasking.list_tasks(args.get("limit") or 20, str(args.get("state") or ""))
    if name == "task_show":
        import tasking

        return tasking.show(str(args.get("id") or ""))
    if name == "task_cancel":
        import tasking

        return tasking.cancel(str(args.get("id") or ""))
    if name == "cron_add":
        import crons

        return crons.add_job(str(args.get("name") or ""), str(args.get("limb") or ""), args.get("args") or {},
                             every=args.get("every") or 0, at=str(args.get("at") or ""),
                             note=str(args.get("note") or ""))
    if name == "cron_list":
        import crons

        return crons.list_jobs()
    if name == "cron_remove":
        import crons

        return crons.remove_job(str(args.get("name") or ""))
    if name == "keeper_status":
        return _keeper_status()
    return None


# ------------------------------------------------------------------ self-build harness
# The console can read and edit its own source; these four let it check, seal, restart and equip
# itself. Every limb that changes the system refuses without consent=true and says why, mirroring
# the --i-consent rule the kit's own scripts already follow.

_TC_ACTIONS = ("check", "rust_gnu_target", "pip", "winget")


def _kit_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _consent_refused(what: str, hint: str) -> dict[str, Any]:
    return {"ok": False, "error": "consent_required",
            "hint": f"{what} Call it again with consent=true to approve. {hint}"}


def _self_test(target: str = "", timeout: int = 900) -> dict[str, Any]:
    """Run the kit's own pytest and report real numbers. Read-only: it never writes the tree."""
    import time as _time

    root = _kit_root()
    tests = (root / "tests").resolve()
    try:
        limit = max(30, min(1800, int(timeout)))
    except (TypeError, ValueError):
        limit = 900
    args = [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider", "--tb=line"]
    if target:
        cand = Path(target)
        if not cand.is_absolute():
            cand = root / cand
        try:
            cand = cand.resolve()
        except OSError:
            return {"ok": False, "error": "bad_target", "target": target}
        if not str(cand).lower().startswith(str(tests).lower()):
            return {"ok": False, "error": "outside_tests",
                    "hint": "self_test only runs the kit's own tests/ - pass e.g. tests/test_tool_routing.py"}
        args.append(str(cand))
    t0 = _time.time()
    code, out, err, timed_out = _run_capture(args, timeout=limit, cwd=str(root), env=_win_env())
    blob = (out or "") + "\n" + (err or "")
    m_pass = re.search(r"(\d+) passed", blob)
    m_fail = re.search(r"(\d+) failed", blob)
    m_sub = re.search(r"(\d+) subtests? passed", blob)
    failures = [ln.split("::")[-1].strip() for ln in blob.splitlines() if ln.startswith("FAILED")][:6]
    return {"ok": (not timed_out) and m_fail is None,
            "passed": int(m_pass.group(1)) if m_pass else 0,
            "failed": int(m_fail.group(1)) if m_fail else 0,
            "subtests": int(m_sub.group(1)) if m_sub else 0,
            "seconds": round(_time.time() - t0, 1), "timed_out": timed_out, "failures": failures,
            "target": target or "fast core set", "command": " ".join(args[1:]),
            "tail": " ".join(blob.strip().splitlines()[-1:])[:200] if blob.strip() else ""}


def _self_seal(consent: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not consent:
        return _consent_refused("Sealing rewrites this kit's own manifests (refresh + certify).",
                                "Certification is the operator's signature on a build, so it never happens by itself.")
    root = _kit_root()
    steps = ["scripts/refresh_manifests.py", "scripts/certify_build.py"]
    if dry_run:
        return {"ok": True, "ran": False, "would_run": [f"{sys.executable} {s}" for s in steps]}
    report = []
    for step in steps:
        code, out, err, timed_out = _run_capture([sys.executable, step], timeout=900, cwd=str(root), env=_win_env())
        blob = (out or "") + "\n" + (err or "")
        last = " ".join(blob.strip().splitlines()[-1:])[:200] if blob.strip() else ""
        report.append({"step": step, "code": code, "last": last, "timed_out": timed_out})
    verdict = report[-1]["last"] if report else ""
    return {"ok": "CERTIFIED BUILD" in verdict or "already correct" in json.dumps(report), "steps": report,
            "verdict": verdict,
            "next": "self_restart with consent=true loads the sealed build into the running console"}


def _self_restart(consent: bool = False, wait: int = 0) -> dict[str, Any]:
    if not consent:
        return _consent_refused("Restarting drops the page for about a minute while the model reloads.",
                                "Seal first, then restart - an unsealed change would be certified by nobody.")
    import time as _time
    import urllib.request as _url

    root = _kit_root()
    port = 9641
    try:
        cfg = json.loads((root / "config" / "console.json").read_text(encoding="utf-8"))
        port = int(cfg.get("port") or cfg.get("console_port") or port)
    except Exception:
        pass
    doorbell = port - 1
    tokf = root / "data" / ".lygo_doorbell_token"
    tok = tokf.read_text(encoding="utf-8").strip() if tokf.is_file() else ""
    if not tok:
        return {"ok": False, "error": "no_doorbell_token", "doorbell_port": doorbell,
                "hint": "start the console through LYGO_LLM_CONSOLE.bat so it writes data/.lygo_doorbell_token"}
    try:
        with _url.urlopen(f"http://127.0.0.1:{doorbell}/boot?token={tok}", timeout=90) as fh:
            body = fh.read(300).decode("utf-8", "replace")
    except Exception as exc:
        return {"ok": False, "error": "doorbell_down", "doorbell_port": doorbell,
                "detail": type(exc).__name__,
                "hint": "the doorbell is not listening - start it with tools/doorbell.py --detach, or the launcher"}
    if wait:
        _time.sleep(max(0, min(600, int(wait))))
    return {"ok": True, "rang": True, "doorbell_port": doorbell, "answer": body[:200],
            "note": "the console is relaunching itself; the page returns in about a minute"}


def _toolchain_install(what: str = "", package: str = "", consent: bool = False) -> dict[str, Any]:
    import shutil as _shutil
    import subprocess as _sub

    what = (what or "").strip().lower()
    pkg = (package or "").strip()
    if what not in _TC_ACTIONS:
        return {"ok": False, "error": "unknown_action", "hint": f"what must be one of: {', '.join(_TC_ACTIONS)}",
                "note": "this limb runs a known action, never a command line composed for it"}
    if what in ("pip", "winget") and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,64}", pkg or ""):
        return {"ok": False, "error": "bad_package",
                "hint": "package must match [A-Za-z0-9][A-Za-z0-9._+-]* - no spaces, no flags, no shell"}
    if what == "check":
        found = {}
        for name in ("rustc", "cargo", "rustup", "link", "gcc", "cc", "clang", "ld", "winget", "cl"):
            where = _shutil.which(name)
            if where:
                found[name] = where
        host, rustc_out = "", ""
        if found.get("rustc"):
            r = _sub.run(["rustc", "-vV"], capture_output=True, text=True, timeout=120)
            rustc_out = (r.stdout or "")[:400]
            m = re.search(r"host:\s*(\S+)", rustc_out)
            host = m.group(1) if m else ""
        # Ask the toolchain, not the PATH: git-bash's `link.exe` is coreutils and answers to the name.
        fake = [n for n in ("link", "ld", "cc", "clang", "gcc") if found.get(n) and not _is_real_linker(found[n])]
        probe = _rust_probe()
        note = (f"Rust builds and runs here - a probe program was compiled and run via {probe.get('via')}."
                if probe.get("can_run") else
                f"Rust cannot link here yet: {probe.get('detail') or 'no working linker'}. "
                "what=rust_gnu_target adds a user-space linker target; VS Build Tools (C++ option) is the other way.")
        return {"ok": True, "ran": True, "found": found, "host": host, "rustc": rustc_out,
                "linker_present": bool(probe.get("can_run")), "rust_builds_and_runs": bool(probe.get("can_run")),
                "probe": probe, "not_a_linker": {n: found[n] for n in fake},
                "checked_but_not_run": bool(probe.get("checked")) and not probe.get("can_run"),
                "note": note}
    command = {"rust_gnu_target": ["rustup", "target", "add", "x86_64-pc-windows-gnu"],
               "pip": [sys.executable, "-m", "pip", "install", pkg],
               "winget": ["winget", "install", "--id", pkg, "--accept-source-agreements",
                          "--accept-package-agreements"]}[what]
    printable = " ".join(command)
    installs = {"rust_gnu_target": "a user-space MinGW-w64 linker through rustup - no administrator needed",
                "pip": f"the Python package {pkg} into {sys.executable}",
                "winget": f"the package {pkg} through winget - Windows may raise a UAC prompt"}[what]
    if not consent:
        return {"ok": True, "ran": False, "command": printable, "action": what, "installs": installs,
                "note": "plan only: call again with consent=true to run it, or run it yourself"}
    if not (_shutil.which(command[0]) or Path(command[0]).is_file()):
        return {"ok": False, "error": "missing_installer", "command": printable,
                "hint": f"{command[0]} was not found on PATH"}
    code, out, err, timed_out = _run_capture(command, timeout=900, cwd=str(_kit_root()), env=_win_env())
    return {"ok": code == 0 and not timed_out, "ran": True, "command": printable, "code": code,
            "timed_out": timed_out, "stdout": (out or "")[-800:], "stderr": (err or "")[-800:],
            "next": "run toolchain_install with what=check to confirm; then rust_exec can build and run"}


def _keeper_status() -> dict[str, Any]:
    """Ask the keeper what it is doing. Reads its state file; never starts it as a side effect."""
    import sys as _sys

    tools_dir = str(_kit_root() / "tools")
    if tools_dir not in _sys.path:
        _sys.path.insert(0, tools_dir)
    try:
        import keeper as _keeper

        st = _keeper.status()
    except Exception as exc:
        return {"ok": False, "error": "keeper_unavailable", "detail": type(exc).__name__,
                "hint": "run python tools/keeper.py --detach to supervise this console"}
    state = st.get("state") or {}
    return {"ok": True, "keeper_alive": st.get("keeper_alive"), "keeper_pid": st.get("keeper_pid"),
            "console_up": (st.get("console") or {}).get("up"),
            "doorbell_up": (st.get("doorbell") or {}).get("up"),
            "sweeps": state.get("sweeps"), "last_ring": state.get("last_ring"), "actions": state.get("actions"),
            "interval_s": st.get("interval_s"), "log": st.get("log"),
            "hint": "start it with: python tools/keeper.py --detach"}
