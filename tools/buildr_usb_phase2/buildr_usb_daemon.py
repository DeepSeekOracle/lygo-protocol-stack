#!/usr/bin/env python3
"""
LYGO BUILDR USB daemon — 127.0.0.1:9630
Supervisor (Supervise, AnchorAudit, GetTrainingSignal) + local task queue for stick work.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import ssl
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any
from urllib.parse import parse_qs, urlparse

KEY = Path(__file__).resolve().parents[1]
PHASE2 = Path(__file__).resolve().parent
sys.path.insert(0, str(KEY / "hermes"))
sys.path.insert(0, str(PHASE2))

import lygo_hermes_audit as hermes  # noqa: E402

DEFAULT_PORT = 9630
SIGNATURE = "D9Phi963-BUILDR-DAEMON-v1"
SUPERVISOR_SIGNATURE = "D9Phi963-SUPERVISOR-v1"
TASK_TIMEOUT_SEC = 300


def _p0_sample(text: str, key_root: Path) -> dict:
    stack = key_root / "stack" / "lygo-protocol-stack"
    p0dir = stack / "protocol0_byte_entropy_filter" / "src" / "python"
    mnt = (
        key_root
        / "mnt_core"
        / "stack"
        / "lygo-protocol-stack"
        / "protocol0_byte_entropy_filter"
        / "src"
        / "python"
    )
    use = mnt if (mnt / "byte_entropy_filter.py").is_file() else p0dir
    if not (use / "byte_entropy_filter.py").is_file():
        return {"verdict": "SOFTEN", "skipped": "no p0 module"}
    sys.path.insert(0, str(use))
    try:
        import byte_entropy_filter as p0  # noqa: E402

        sample = text.encode("utf-8", errors="replace")[:8192]
        r = p0.validate_bytes(sample)
        return {"verdict": r.get("decision", "SOFTEN"), "phi_risk": r.get("phi_risk")}
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "QUARANTINE", "error": str(exc)}


def supervise(payload: dict, key_root: Path) -> dict:
    agent_id = payload.get("agent_id", "unknown")
    tool_call = payload.get("tool_call") or {}
    tool_name = tool_call.get("name", "unknown")
    args_preview = str(tool_call.get("args", ""))[:2048]
    hermes.pre_tool_call(tool_name, {"agent_id": agent_id})
    p0 = _p0_sample(args_preview, key_root)
    approved = p0.get("verdict") in ("AMPLIFY", "SOFTEN")
    alignment_score = 0.98 if approved else 0.12
    audit_entry = hermes.post_tool_call(
        tool_name,
        approved,
        {"agent_id": agent_id, "p0": p0, "alignment_score": alignment_score},
    )
    return {
        "signature": SUPERVISOR_SIGNATURE,
        "approved": approved,
        "alignment_score": alignment_score,
        "audit_hash": audit_entry.get("hash"),
        "p0_verdict": p0.get("verdict"),
        "agent_id": agent_id,
    }


def anchor_audit() -> dict:
    chain = hermes.validate_audit_chain()
    return {"signature": SUPERVISOR_SIGNATURE, "chain": chain, "ts": datetime.now(timezone.utc).isoformat()}


def training_signal() -> dict:
    return {
        "signature": SUPERVISOR_SIGNATURE,
        "signal": "maintain_p0_quarantine",
        "hints": [
            "verify_kernel_eggs before plant",
            "no auto git push",
            "hermes chain must stay valid",
        ],
    }


class TaskStore:
    def __init__(self, key_root: Path) -> None:
        self.key_root = key_root
        self.log_path = key_root / "data" / "user_data" / "buildr_daemon_tasks.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._q: queue.Queue[str] = queue.Queue()
        self._records: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def enqueue(self, task_type: str, payload: dict, agent_id: str) -> dict:
        task_id = str(uuid.uuid4())
        rec = {
            "task_id": task_id,
            "type": task_type,
            "payload": payload,
            "agent_id": agent_id,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": None,
        }
        with self._lock:
            self._records[task_id] = rec
            self._append(rec)
        self._q.put(task_id)
        return {"task_id": task_id, "status": "queued", "signature": SIGNATURE}

    def get(self, task_id: str) -> dict | None:
        with self._lock:
            return self._records.get(task_id)

    def recent(self, limit: int = 20) -> list[dict]:
        with self._lock:
            items = list(self._records.values())
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items[:limit]

    def _append(self, rec: dict) -> None:
        line = json.dumps(rec, ensure_ascii=False) + "\n"
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(line)

    def _update(self, task_id: str, **fields: Any) -> None:
        with self._lock:
            rec = self._records.get(task_id)
            if not rec:
                return
            rec.update(fields)
            self._append({**rec, "event": "update"})

    def run_worker(self) -> None:
        while True:
            task_id = self._q.get()
            try:
                self._execute(task_id)
            finally:
                self._q.task_done()

    def _execute(self, task_id: str) -> None:
        rec = self.get(task_id)
        if not rec:
            return
        self._update(task_id, status="running", started_at=datetime.now(timezone.utc).isoformat())
        task_type = rec["type"]
        payload = rec.get("payload") or {}
        try:
            result = _run_task(self.key_root, task_type, payload)
            self._update(
                task_id,
                status="done",
                finished_at=datetime.now(timezone.utc).isoformat(),
                result=result,
            )
            hermes.log_event("buildr_task_done", detail={"task_id": task_id, "type": task_type})
        except Exception as exc:  # noqa: BLE001
            self._update(
                task_id,
                status="failed",
                finished_at=datetime.now(timezone.utc).isoformat(),
                error=str(exc),
            )
            hermes.log_event("buildr_task_failed", detail={"task_id": task_id, "type": task_type, "error": str(exc)})


def _run_task(key_root: Path, task_type: str, payload: dict) -> dict:
    allowed = {
        "verify_standalone",
        "verify_bootstrap",
        "chat_once",
        "anchor_audit",
    }
    if task_type not in allowed:
        raise ValueError(f"task type not allowed: {task_type}")

    if task_type == "anchor_audit":
        return anchor_audit()

    py = sys.executable
    env = os.environ.copy()
    env["LYGO_BUILDER_KEY_ROOT"] = str(key_root)

    if task_type == "verify_standalone":
        cmd = [py, str(key_root / "scripts" / "verify_standalone_usb.py")]
    elif task_type == "verify_bootstrap":
        edition = str(payload.get("edition", "GROK_BUILDR"))
        cmd = [py, str(key_root / "verify_bootstrap.py"), "--edition", edition]
        if payload.get("phase2"):
            cmd.append("--phase2")
    elif task_type == "chat_once":
        prompt = str(payload.get("prompt", "Say OK in one word."))[:4000]
        cmd = [py, str(key_root / "scripts" / "usb_chat_once.py"), prompt]
        if payload.get("model"):
            cmd.extend(["--model", str(payload["model"])])
    else:
        raise ValueError(task_type)

    proc = subprocess.run(
        cmd,
        cwd=str(key_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=TASK_TIMEOUT_SEC,
    )
    out = (proc.stdout or "")[-8000:]
    err = (proc.stderr or "")[-2000:]
    parsed: Any = None
    try:
        parsed = json.loads(proc.stdout)
    except (json.JSONDecodeError, TypeError):
        parsed = None
    return {
        "exit_code": proc.returncode,
        "stdout": out,
        "stderr": err,
        "json": parsed,
        "ok": proc.returncode == 0,
    }


def make_handler(key_root: Path, store: TaskStore | None, *, supervisor_only: bool) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def _json(self, code: int, body: dict) -> None:
            raw = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in ("/health", "/"):
                body = {
                    "ok": True,
                    "service": "lygo-buildr-daemon" if not supervisor_only else "lygo-supervisor",
                    "signature": SIGNATURE,
                    "supervisor_signature": SUPERVISOR_SIGNATURE,
                    "task_queue": store is not None and not supervisor_only,
                    "key_root": str(key_root),
                }
                self._json(200, body)
            elif path == "/GetTrainingSignal":
                self._json(200, training_signal())
            elif path == "/tasks" and store and not supervisor_only:
                self._json(200, {"tasks": store.recent(), "signature": SIGNATURE})
            elif path.startswith("/Task") and store and not supervisor_only:
                qs = parse_qs(urlparse(self.path).query)
                tid = (qs.get("id") or [None])[0]
                if not tid:
                    self._json(400, {"error": "missing id query param"})
                    return
                rec = store.get(str(tid))
                if not rec:
                    self._json(404, {"error": "unknown task_id"})
                    return
                self._json(200, rec)
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid json"})
                return
            path = urlparse(self.path).path
            if path == "/Supervise":
                self._json(200, supervise(data, key_root))
            elif path == "/AnchorAudit":
                self._json(200, anchor_audit())
            elif path == "/Task" and store and not supervisor_only:
                task_type = data.get("type") or data.get("task_type")
                if not task_type:
                    self._json(400, {"error": "missing type"})
                    return
                agent_id = str(data.get("agent_id", "local"))
                payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
                hermes.log_event("buildr_task_queued", detail={"type": task_type, "agent_id": agent_id})
                self._json(202, store.enqueue(str(task_type), payload, agent_id))
            else:
                self._json(404, {"error": "not found"})

    return Handler


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def _maybe_tls(httpd: HTTPServer, key_root: Path) -> None:
    cert = key_root / "data" / "certs" / "supervisor.pem"
    key = key_root / "data" / "certs" / "supervisor.key"
    if cert.is_file() and key.is_file():
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)


def generate_self_signed(key_root: Path) -> None:
    certs = key_root / "data" / "certs"
    certs.mkdir(parents=True, exist_ok=True)
    pem = certs / "supervisor.pem"
    if pem.is_file():
        return
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            str(certs / "supervisor.key"),
            "-out",
            str(pem),
            "-days",
            "3650",
            "-nodes",
            "-subj",
            "/CN=LYGO-USB-Supervisor",
        ],
        check=False,
        capture_output=True,
    )


def _maybe_start_ollama(key_root: Path) -> None:
    script = key_root / "scripts" / "ensure_ollama_serve.ps1"
    if not script.is_file():
        return
    subprocess.Popen(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ],
        cwd=str(key_root),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO BUILDR USB daemon")
    ap.add_argument("--key-root", default=os.environ.get("LYGO_BUILDER_KEY_ROOT", str(KEY)))
    ap.add_argument("--port", type=int, default=int(os.environ.get("LYGO_SUPERVISOR_PORT", DEFAULT_PORT)))
    ap.add_argument("--tls", action="store_true")
    ap.add_argument(
        "--supervisor-only",
        action="store_true",
        help="Disable task queue (legacy supervisor mode)",
    )
    ap.add_argument(
        "--with-ollama",
        action="store_true",
        help="Start ensure_ollama_serve.ps1 in background (USB models)",
    )
    args = ap.parse_args()
    key_root = Path(args.key_root)
    audit = key_root / "data" / "hermes_audit" / "audit_trail.log"
    hermes.set_log_path(audit)
    if args.tls:
        generate_self_signed(key_root)
    if args.with_ollama:
        _maybe_start_ollama(key_root)

    store: TaskStore | None = None
    if not args.supervisor_only:
        store = TaskStore(key_root)
        worker = threading.Thread(target=store.run_worker, name="buildr-task-worker", daemon=True)
        worker.start()

    handler_cls = make_handler(key_root, store, supervisor_only=args.supervisor_only)
    host = "127.0.0.1"
    httpd = ThreadedHTTPServer((host, args.port), handler_cls)
    if args.tls:
        _maybe_tls(httpd, key_root)
    hermes.log_event(
        "buildr_daemon_start",
        detail={"port": args.port, "tls": args.tls, "supervisor_only": args.supervisor_only},
    )
    mode = "supervisor-only" if args.supervisor_only else "full+tasks"
    print(f"LYGO BUILDR daemon ({mode}) on http{'s' if args.tls else ''}://{host}:{args.port}")
    print("  POST /Task  GET /Task?id=...  GET /tasks  POST /Supervise")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("buildr daemon stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())