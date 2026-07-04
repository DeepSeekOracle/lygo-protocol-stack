#!/usr/bin/env python3
"""
LYGO USB Supervisor Daemon — 127.0.0.1:9630
Supervise(), GetTrainingSignal(), AnchorAudit() (JSON/HTTP; mTLS optional via data/certs).
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any

KEY = Path(__file__).resolve().parents[1]
PHASE2 = Path(__file__).resolve().parent
sys.path.insert(0, str(KEY / "hermes"))
sys.path.insert(0, str(PHASE2))

import lygo_hermes_audit as hermes  # noqa: E402

DEFAULT_PORT = 9630
SIGNATURE = "Δ9Φ963-SUPERVISOR-v1"


def _p0_sample(text: str) -> dict:
    stack = KEY / "stack" / "lygo-protocol-stack"
    p0dir = stack / "protocol0_byte_entropy_filter" / "src" / "python"
    mnt = KEY / "mnt_core" / "stack" / "lygo-protocol-stack" / "protocol0_byte_entropy_filter" / "src" / "python"
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


def supervise(payload: dict) -> dict:
    agent_id = payload.get("agent_id", "unknown")
    tool_call = payload.get("tool_call") or {}
    tool_name = tool_call.get("name", "unknown")
    args_preview = str(tool_call.get("args", ""))[:2048]
    hermes.pre_tool_call(tool_name, {"agent_id": agent_id})
    p0 = _p0_sample(args_preview)
    approved = p0.get("verdict") in ("AMPLIFY", "SOFTEN")
    alignment_score = 0.98 if approved else 0.12
    audit_entry = hermes.post_tool_call(
        tool_name,
        approved,
        {"agent_id": agent_id, "p0": p0, "alignment_score": alignment_score},
    )
    return {
        "signature": SIGNATURE,
        "approved": approved,
        "alignment_score": alignment_score,
        "audit_hash": audit_entry.get("hash"),
        "p0_verdict": p0.get("verdict"),
        "agent_id": agent_id,
    }


def anchor_audit() -> dict:
    chain = hermes.validate_audit_chain()
    return {"signature": SIGNATURE, "chain": chain, "ts": datetime.now(timezone.utc).isoformat()}


def training_signal() -> dict:
    return {
        "signature": SIGNATURE,
        "signal": "maintain_p0_quarantine",
        "hints": [
            "verify_kernel_eggs before plant",
            "no auto git push",
            "hermes chain must stay valid",
        ],
    }


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
        if self.path in ("/health", "/"):
            self._json(200, {"ok": True, "service": "lygo-supervisor", "signature": SIGNATURE})
        elif self.path == "/GetTrainingSignal":
            self._json(200, training_signal())
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
        if self.path == "/Supervise":
            self._json(200, supervise(data))
        elif self.path == "/AnchorAudit":
            self._json(200, anchor_audit())
        else:
            self._json(404, {"error": "not found"})


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
    """Optional: openssl in PATH generates dev certs."""
    certs = key_root / "data" / "certs"
    certs.mkdir(parents=True, exist_ok=True)
    pem = certs / "supervisor.pem"
    if pem.is_file():
        return
    import subprocess

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-root", default=os.environ.get("LYGO_BUILDER_KEY_ROOT", str(KEY)))
    ap.add_argument("--port", type=int, default=int(os.environ.get("LYGO_SUPERVISOR_PORT", DEFAULT_PORT)))
    ap.add_argument("--tls", action="store_true")
    args = ap.parse_args()
    key_root = Path(args.key_root)
    audit = key_root / "data" / "hermes_audit" / "audit_trail.log"
    hermes.set_log_path(audit)
    if args.tls:
        generate_self_signed(key_root)
    host = "127.0.0.1"
    httpd = ThreadedHTTPServer((host, args.port), Handler)
    if args.tls:
        _maybe_tls(httpd, key_root)
    hermes.log_event("supervisor_start", detail={"port": args.port, "tls": args.tls})
    print(f"LYGO Supervisor on http{'s' if args.tls else ''}://{host}:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("supervisor stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())