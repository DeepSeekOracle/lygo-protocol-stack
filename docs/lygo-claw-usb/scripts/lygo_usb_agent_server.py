#!/usr/bin/env python3
"""
LYGO USB Agent Server — OpenClaw-style control plane for the stick.

- Serves agent UI (http://127.0.0.1:9631/)
- Proxies chat to USB Ollama (offline)
- Status: models, gateway, daemon tasks, D: lattice live snapshot
- Lattice live under verify/lattice_live (read-only copy from D:/I: stack)
- NEVER mutates restore/, lattice_master/steward_vault, or E:\\LYGO_LATTICE_MEMORY

Signature: Delta9Phi963-LYGO-USB-AGENT-SERVER-v1.2
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

USB_ROOT = Path(__file__).resolve().parents[1]
DASH_DIR = USB_ROOT / "dashboard" / "agent-ui"
CONTROL_UI = USB_ROOT / "dashboard" / "control-ui"
LATTICE_LIVE = USB_ROOT / "verify" / "lattice_live"
OLLAMA = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434").replace("http://", "").replace("https://", "")
GATEWAY = os.environ.get("LYGO_GATEWAY", "127.0.0.1:18789").replace("http://", "").replace("https://", "")
PORT = int(os.environ.get("LYGO_AGENT_PORT", "9631"))
HOST = os.environ.get("LYGO_AGENT_HOST", "127.0.0.1")
SERVER_SIG = "Delta9Phi963-LYGO-USB-AGENT-SERVER-v1.2"

TASKS: list[dict[str, Any]] = []
TASK_LOCK = threading.Lock()
STARTED = time.time()

# Public lattice files safe to serve under /lattice/<name>
LATTICE_ALLOW = frozenset(
    {
        "LATTICE_LIVE_SYNC.json",
        "LATTICE_POINTERS.json",
        "DUAL_LEDGERS.json",
        "IMMUTABLE_ANCHORS.json",
        "haven_star_chart_feed.json",
        "haven_star_chart_meta.json",
        "haven_star_chart_queue.json",
        "LYGO_LATTICE_MEMORY_SNAPSHOT.json",
        "public_verify_manifest.json",
        "AGENT_MEMORY_SNAPSHOT.json",
        "SOVEREIGN_IDENTITY_MANIFESTO_ANCHOR.json",
        "KernelEggRegistry.json",
        "LYGO_PUBLIC_LINK_ARCHIVE.json",
        # large chart optional — only if sync brought it in
        "haven_star_chart_data.json",
    }
)


def _http_json(url: str, payload: dict | None = None, timeout: float = 120.0) -> Any:
    data = None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return json.loads(body) if body else None


def ollama_tags() -> dict[str, Any]:
    try:
        return _http_json(f"http://{OLLAMA}/api/tags", timeout=3.0) or {"models": []}
    except Exception as e:
        return {"ok": False, "error": str(e), "models": []}


def ollama_chat(model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    return _http_json(
        f"http://{OLLAMA}/api/chat",
        payload={"model": model, "messages": messages, "stream": False},
        timeout=300.0,
    )


def gateway_up() -> bool:
    try:
        req = urllib.request.Request(f"http://{GATEWAY}/", method="GET")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return 200 <= resp.status < 500
    except Exception:
        return False


def port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def load_json_file(path: Path) -> Any:
    try:
        if path.is_file():
            # utf-8-sig tolerates PowerShell Set-Content BOM
            return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        return {"error": str(e), "path": str(path)}
    return None


def resolve_stack_roots() -> dict[str, Any]:
    candidates = []
    env = os.environ.get("LYGO_STACK_ROOT")
    if env:
        candidates.append(Path(env))
    candidates.extend(
        [
            Path(r"D:\lygo-protocol-stack"),
            Path(r"I:\E Drive\lygo-protocol-stack"),
            USB_ROOT / "stack" / "lygo-protocol-stack",
        ]
    )
    found = []
    for p in candidates:
        try:
            if p.is_dir() and (p / "docs").is_dir():
                found.append(str(p))
        except OSError:
            pass
    authority = found[0] if found else None
    git_info = None
    if authority:
        git_info = _stack_git(Path(authority))
    return {
        "authority": authority,
        "candidates_ok": found,
        "usb_stack": str(USB_ROOT / "stack" / "lygo-protocol-stack"),
        "git": git_info,
        "env_LYGO_STACK_ROOT": env,
    }


def _stack_git(root: Path) -> dict[str, Any] | None:
    if not (root / ".git").exists():
        return None
    try:
        def _run(*args: str) -> str:
            r = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return (r.stdout or "").strip()

        commit = _run("rev-parse", "--short", "HEAD")
        branch = _run("rev-parse", "--abbrev-ref", "HEAD")
        subject = _run("log", "-1", "--pretty=%s")
        if commit:
            return {"commit": commit, "branch": branch, "subject": subject}
    except Exception as e:
        return {"error": str(e)}
    return None


def lattice_restore_readonly() -> dict[str, Any]:
    info: dict[str, Any] = {
        "note": "read-only; never mutated by agent server",
        "paths": {},
        "live_snapshot": {},
    }
    candidates = {
        "usb_restore": USB_ROOT / "restore",
        "usb_lattice_master": USB_ROOT / "lattice_master",
        "e_lattice_memory": Path(r"E:\LYGO_LATTICE_MEMORY"),
        "e_data_vault_align": Path(r"E:\Data Vault\LYGO_LATTICE_AGENT_RESTORE_ALIGN.txt"),
        "builder_key_anchor": USB_ROOT / "LYGO_CLAW_USB_RESTORE_ANCHOR.md",
        "d_stack": Path(r"D:\lygo-protocol-stack"),
        "i_stack": Path(r"I:\E Drive\lygo-protocol-stack"),
        "lattice_live": LATTICE_LIVE,
    }
    for k, p in candidates.items():
        try:
            info["paths"][k] = {
                "path": str(p),
                "exists": p.exists(),
                "is_dir": p.is_dir() if p.exists() else False,
                "size": p.stat().st_size if p.is_file() and p.exists() else None,
            }
        except OSError as e:
            info["paths"][k] = {"path": str(p), "exists": False, "error": str(e)}

    restore = USB_ROOT / "restore"
    if restore.is_dir():
        info["restore_files"] = [f.name for f in sorted(restore.iterdir())[:50]]

    sync = load_json_file(LATTICE_LIVE / "LATTICE_LIVE_SYNC.json")
    pointers = load_json_file(LATTICE_LIVE / "LATTICE_POINTERS.json")
    dual = load_json_file(LATTICE_LIVE / "DUAL_LEDGERS.json")
    anchors = load_json_file(LATTICE_LIVE / "IMMUTABLE_ANCHORS.json")
    feed = load_json_file(LATTICE_LIVE / "haven_star_chart_feed.json")
    snap = load_json_file(LATTICE_LIVE / "LYGO_LATTICE_MEMORY_SNAPSHOT.json")
    meta = load_json_file(LATTICE_LIVE / "haven_star_chart_meta.json")

    feed_summary = None
    if isinstance(feed, dict) and "error" not in feed:
        entries = feed.get("entries") or []
        # Prefer latest by list order (append-only — last is newest if reverse not used)
        latest_raw = list(reversed(entries[-12:])) if entries else []
        feed_summary = {
            "entry_count": feed.get("entry_count") or len(entries),
            "chain_valid": feed.get("chain_valid"),
            "chain_root": feed.get("chain_root"),
            "ledger_sha256": feed.get("ledger_sha256"),
            "updated_utc": feed.get("updated_utc"),
            "signature": feed.get("signature"),
            "latest": [
                {
                    "node_id": e.get("node_id"),
                    "status": e.get("status"),
                    "event_type": e.get("event_type"),
                    "seq": e.get("seq"),
                    "event_utc": e.get("event_utc"),
                }
                for e in latest_raw[:8]
            ],
            "status_counts": _status_counts(entries),
        }

    anchors_summary = None
    if isinstance(anchors, dict) and "error" not in anchors:
        groups = anchors.get("immutable_anchors") or {}
        cat_counts = {}
        if isinstance(groups, dict):
            for ck, cv in groups.items():
                if isinstance(cv, list):
                    cat_counts[ck] = len(cv)
                elif isinstance(cv, dict):
                    cat_counts[ck] = len(cv)
                else:
                    cat_counts[ck] = 1
        anchors_summary = {
            "signature": anchors.get("signature"),
            "version": anchors.get("version"),
            "updated_utc": anchors.get("updated_utc"),
            "categories": list(groups.keys()) if isinstance(groups, dict) else [],
            "category_counts": cat_counts,
            "source_seal": anchors.get("source_seal"),
        }

    live_files = []
    if LATTICE_LIVE.is_dir():
        for f in sorted(LATTICE_LIVE.iterdir()):
            if f.is_file():
                live_files.append({"name": f.name, "bytes": f.stat().st_size})

    sync_ok = isinstance(sync, dict) and sync.get("ok") is True
    info["live_snapshot"] = {
        "dir": str(LATTICE_LIVE),
        "present": LATTICE_LIVE.is_dir() and bool(live_files),
        "sync_ok": sync_ok,
        "sync": sync,
        "pointers": pointers,
        "dual_ledgers": dual,
        "star_feed": feed_summary,
        "anchors": anchors_summary,
        "star_meta": meta if isinstance(meta, dict) and "error" not in meta else None,
        "memory_snapshot_keys": list(snap.keys())[:20] if isinstance(snap, dict) and "error" not in snap else None,
        "files": live_files,
        "http_lattice_prefix": f"http://{HOST}:{PORT}/lattice/",
    }
    info["stack"] = resolve_stack_roots()
    info["harden"] = {
        "prefer_d_stack": True,
        "restore_never_mutate": True,
        "sync_script": str(USB_ROOT / "scripts" / "sync_lattice_live_readonly.ps1"),
        "boot": str(USB_ROOT / "LYGO_USB_BOOT.bat"),
    }
    return info


def _status_counts(entries: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        st = str(e.get("status") or "unknown")
        counts[st] = counts.get(st, 0) + 1
    return counts


def primary_model() -> str:
    for candidate in (
        USB_ROOT / "product" / "models" / "MODEL_MANIFEST.json",
        USB_ROOT / "models" / "MODEL_MANIFEST.json",
    ):
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                primary = data.get("primary") or {}
                if isinstance(primary, dict) and primary.get("name"):
                    return str(primary["name"])
                if isinstance(primary, str):
                    return primary
            except Exception:
                pass
    return "qwen2.5:3b"


def system_status() -> dict[str, Any]:
    tags = ollama_tags()
    models: list[str] = []
    for m in tags.get("models") or []:
        if isinstance(m, dict):
            models.append(str(m.get("name") or m.get("model") or m))
        else:
            models.append(str(m))
    with TASK_LOCK:
        tasks_n = len(TASKS)
        pending = sum(1 for t in TASKS if t.get("status") == "pending")
    return {
        "ok": True,
        "signature": SERVER_SIG,
        "uptime_sec": int(time.time() - STARTED),
        "usb_root": str(USB_ROOT),
        "ollama": {
            "host": f"http://{OLLAMA}",
            "reachable": "error" not in tags,
            "models": models,
            "primary": primary_model(),
            "models_env": os.environ.get("OLLAMA_MODELS"),
        },
        "gateway": {
            "host": f"http://{GATEWAY}",
            "ws": f"ws://{GATEWAY}",
            "reachable": gateway_up(),
            "token": "lygo-usb-standalone-token",
            "control_ui": f"http://{HOST}:{PORT}/control-ui/?token=lygo-usb-standalone-token",
        },
        "agent_ui": f"http://{HOST}:{PORT}/",
        "daemon": {
            "tasks": tasks_n,
            "pending": pending,
            "supervisor_launcher": str(USB_ROOT / "launchers" / "LYGO_Supervisor_Daemon.bat"),
        },
        "lattice_restore": lattice_restore_readonly(),
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASH_DIR), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[agent-ui] " + (fmt % args) + "\n")

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, obj: Any) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        raw = self.rfile.read(n)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _send_bytes(self, data: bytes, ctype: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/api/status", "/api/health"):
            return self._json(200, system_status())
        if path == "/api/models":
            return self._json(200, ollama_tags())
        if path == "/api/tasks":
            with TASK_LOCK:
                return self._json(200, {"tasks": list(TASKS)[-100:]})
        if path == "/api/lattice":
            return self._json(200, lattice_restore_readonly())

        # Read-only public lattice files (synced snapshot only)
        if path.startswith("/lattice/"):
            name = path[len("/lattice/") :].lstrip("/").replace("\\", "/")
            if not name or "/" in name or name not in LATTICE_ALLOW:
                return self._json(403, {"error": "forbidden", "allowed": sorted(LATTICE_ALLOW)})
            target = (LATTICE_LIVE / name).resolve()
            try:
                target.relative_to(LATTICE_LIVE.resolve())
            except ValueError:
                return self._json(403, {"error": "path escape"})
            if not target.is_file():
                return self._json(404, {"error": "not synced", "hint": "Run Master Manager option A or LYGO_USB_BOOT.bat"})
            data = target.read_bytes()
            ctype = "application/json; charset=utf-8" if target.suffix == ".json" else "application/octet-stream"
            return self._send_bytes(data, ctype)

        if path.startswith("/control-ui"):
            rel = path[len("/control-ui") :].lstrip("/") or "index.html"
            target = (CONTROL_UI / rel).resolve()
            try:
                target.relative_to(CONTROL_UI.resolve())
            except ValueError:
                return self._json(403, {"error": "forbidden"})
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                self.send_error(404)
                return
            data = target.read_bytes()
            ctype = "text/html; charset=utf-8"
            if target.suffix == ".js":
                ctype = "application/javascript; charset=utf-8"
            elif target.suffix == ".css":
                ctype = "text/css; charset=utf-8"
            elif target.suffix == ".svg":
                ctype = "image/svg+xml"
            elif target.suffix == ".png":
                ctype = "image/png"
            elif target.suffix == ".ico":
                ctype = "image/x-icon"
            elif target.suffix == ".webmanifest":
                ctype = "application/manifest+json"
            return self._send_bytes(data, ctype)

        if path == "/":
            self.path = "/index.html"
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        body = self._read_json()

        if path == "/api/chat":
            st = system_status()
            model = body.get("model") or st["ollama"]["primary"]
            messages = body.get("messages") or []
            if not messages and body.get("message"):
                lat = st.get("lattice_restore") or {}
                live = (lat.get("live_snapshot") or {})
                feed = live.get("star_feed") or {}
                stack = lat.get("stack") or {}
                system = body.get("system") or (
                    "You are LYGO CLAW on a sovereign USB stick. Local-first offline agent. "
                    "P0-first: no secrets, consent-gated publish. Help restore lattice context "
                    "read-only and set up the host PC for larger models when online. "
                    f"USB root: {USB_ROOT}. Primary model: {model}. "
                    f"Authority stack: {stack.get('authority')}. "
                    f"Star feed entries: {feed.get('entry_count')} chain_valid={feed.get('chain_valid')}."
                )
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": str(body["message"])},
                ]
            if not st["ollama"]["reachable"]:
                return self._json(
                    503,
                    {
                        "ok": False,
                        "error": "Ollama not reachable. Run LYGO_USB_BOOT.bat",
                    },
                )
            installed = st["ollama"]["models"]
            if installed and model not in installed:
                if st["ollama"]["primary"] in installed:
                    model = st["ollama"]["primary"]
                else:
                    model = installed[0]
            try:
                result = ollama_chat(model, messages)
                content = ""
                if isinstance(result, dict):
                    msg = result.get("message") or {}
                    content = msg.get("content") or result.get("response") or ""
                return self._json(
                    200,
                    {
                        "ok": True,
                        "model": model,
                        "message": {"role": "assistant", "content": content},
                        "raw": {k: result.get(k) for k in ("model", "created_at", "done") if isinstance(result, dict)},
                    },
                )
            except Exception as e:
                return self._json(500, {"ok": False, "error": str(e)})

        if path == "/api/tasks":
            title = str(body.get("title") or body.get("task") or "").strip()
            if not title:
                return self._json(400, {"ok": False, "error": "title required"})
            task = {
                "id": f"t{int(time.time() * 1000)}",
                "title": title,
                "status": "pending",
                "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "note": str(body.get("note") or ""),
            }
            with TASK_LOCK:
                TASKS.append(task)
            return self._json(200, {"ok": True, "task": task})

        if path == "/api/tasks/complete":
            tid = str(body.get("id") or "")
            with TASK_LOCK:
                for t in TASKS:
                    if t.get("id") == tid:
                        t["status"] = "done"
                        t["done_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        return self._json(200, {"ok": True, "task": t})
            return self._json(404, {"ok": False, "error": "task not found"})

        return self._json(404, {"error": "not found"})


def main() -> int:
    DASH_DIR.mkdir(parents=True, exist_ok=True)
    if port_in_use(HOST, PORT):
        print(
            json.dumps(
                {
                    "ok": True,
                    "already_running": True,
                    "agent_ui": f"http://{HOST}:{PORT}/",
                    "api": f"http://{HOST}:{PORT}/api/status",
                },
                indent=2,
            )
        )
        return 0

    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(
        json.dumps(
            {
                "ok": True,
                "signature": SERVER_SIG,
                "agent_ui": f"http://{HOST}:{PORT}/",
                "control_ui": f"http://{HOST}:{PORT}/control-ui/?token=lygo-usb-standalone-token",
                "api": f"http://{HOST}:{PORT}/api/status",
                "lattice": f"http://{HOST}:{PORT}/api/lattice",
                "usb_root": str(USB_ROOT),
            },
            indent=2,
        )
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
