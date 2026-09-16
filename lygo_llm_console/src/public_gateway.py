"""Public LYGO inference gateway — chat only, P0, rate-limited, no disks/shell.

Run on the always-on node (stream PC) behind Caddy/HTTPS. Never load admin.json.
Requires --i-consent to bind beyond loopback.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from p0_hook import gate_output_window, gate_prompt  # noqa: E402

ALLOW_ORIGINS = (
    "https://chatagent.ca",
    "https://www.chatagent.ca",
    "https://eternalhaven.ca",
    "https://www.eternalhaven.ca",
    "https://excavationpro.ca",
    "https://www.excavationpro.ca",
    "https://deepseekoracle.com",
    "https://www.deepseekoracle.com",
    "https://asiancoastline.com",
    "https://bpmfinder.ca",
    "https://deepseekoracle.github.io",
    "http://127.0.0.1:9641",
    "http://localhost:9641",
    "http://127.0.0.1:8080",
    "http://10.0.0.209:8080",
)
PUBLIC_SYSTEM = (
    "You are the public LYGO LLM portal. Assist the human. Never replace them. "
    "CANON is dual ledgers / Haven Star Chart. This chat is RESOURCE. "
    "No shell, no disk, no passwords. P0: refuse OS wipe and fabricated receipts. "
    "Δ9 champions are optional lenses (ARKOS, LYRΔ, …) if the user invokes one. "
    "Donate: PayPal.me/ExcavationPro. Arcade: https://chatagent.ca/games/"
)
WINDOW = 600
MAX_REQ = 24
MAX_CHARS = 4000
MAX_MSGS = 10
_hits: dict[str, deque[float]] = defaultdict(deque)


def _cors_ok(origin: str) -> bool:
    o = (origin or "").rstrip("/")
    if o in ALLOW_ORIGINS:
        return True
    if o.startswith("https://") and o.endswith(".hf.space"):
        return True
    return False


def _rate(ip: str) -> bool:
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= MAX_REQ:
        return False
    q.append(now)
    return True


def _ollama_chat(base: str, model: str, messages: list[dict[str, Any]]) -> str:
    payload = json.dumps({"model": model, "messages": messages, "stream": False, "options": {"num_predict": 384}}).encode()
    req = urllib.request.Request(
        base.rstrip("/") + "/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    msg = data.get("message") or {}
    return str(msg.get("content") or "")


def _openai_chat(url: str, model: str, messages: list[dict[str, Any]], key: str) -> str:
    payload = json.dumps({"model": model, "messages": messages, "max_tokens": 384, "stream": False}).encode()
    h = {"Content-Type": "application/json"}
    if key:
        h["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, data=payload, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    return str(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "")


class Handler(BaseHTTPRequestHandler):
    backend = "ollama"
    ollama = "http://127.0.0.1:11434"
    openai_url = "http://127.0.0.1:11441/v1/chat/completions"
    openai_key = ""
    model = "qwen2.5:3b"
    server_version = "LYGO-PublicGateway/1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _origin(self) -> str:
        return (self.headers.get("Origin") or "").strip()

    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        origin = self._origin()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        if _cors_ok(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: Any) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"))

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, b"")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/health", "/api/health"):
            self._json(
                200,
                {
                    "ok": True,
                    "public": True,
                    "full_lygo": False,
                    "tools": False,
                    "model": self.model,
                    "portal": "https://chatagent.ca/portal/",
                    "note": "Public chat only. Full limbs require a local LYGO LLM Console.",
                },
            )
            return
        if path in ("/v1/models", "/api/models"):
            self._json(200, {"object": "list", "data": [{"id": self.model, "object": "model"}]})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in ("/v1/chat/completions", "/api/chat"):
            self._json(404, {"error": "not_found"})
            return
        origin = self._origin()
        if origin and not _cors_ok(origin):
            self._json(403, {"error": "origin"})
            return
        ip = (self.client_address or ("", 0))[0]
        if not _rate(ip):
            self._json(429, {"error": "rate_limited"})
            return
        n = int(self.headers.get("Content-Length") or 0)
        if n > 48_000:
            self._json(413, {"error": "too_large"})
            return
        raw = self.rfile.read(n) if n else b"{}"
        try:
            obj = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "bad_json"})
            return
        msgs_in = obj.get("messages") if isinstance(obj.get("messages"), list) else []
        msgs: list[dict[str, str]] = [{"role": "system", "content": PUBLIC_SYSTEM}]
        for m in msgs_in[-MAX_MSGS:]:
            if not isinstance(m, dict):
                continue
            role = m.get("role") if m.get("role") in {"user", "assistant"} else "user"
            content = str(m.get("content") or "")[:MAX_CHARS]
            msgs.append({"role": role, "content": content})
        user = " ".join(m["content"] for m in msgs if m["role"] == "user")[-MAX_CHARS:]
        gate = gate_prompt(user)
        if gate.get("reason") == "p0_import_failed":
            gate = {"verdict": "ALLOW", "reason": "p0_regex_only"}
        if gate.get("verdict") == "QUARANTINE":
            self._json(451, {"error": "quarantine", "gate": gate})
            return
        model = str(obj.get("model") or self.model)
        try:
            if self.backend == "openai":
                text = _openai_chat(self.openai_url, model, msgs, self.openai_key)
            else:
                text = _ollama_chat(self.ollama, model, msgs)
        except Exception as e:
            self._json(502, {"error": "upstream", "detail": str(e)[:200]})
            return
        if gate_output_window(text[:8000]).get("verdict") == "QUARANTINE":
            text = "[output quarantined]"
        if path == "/api/chat":
            self._json(200, {"text": text, "public": True, "gate": gate, "model": model})
            return
        self._json(
            200,
            {
                "id": "lygo-public",
                "object": "chat.completion",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                "model": model,
            },
        )


def main() -> int:
    ap = argparse.ArgumentParser(description="Public LYGO chat gateway (no admin, no shell).")
    ap.add_argument("--port", type=int, default=9642)
    ap.add_argument("--bind", default="127.0.0.1")
    ap.add_argument("--i-consent", action="store_true")
    ap.add_argument("--lan", action="store_true")
    ap.add_argument("--backend", choices=("ollama", "openai"), default="ollama")
    ap.add_argument("--ollama", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ap.add_argument("--openai-url", default="http://127.0.0.1:11441/v1/chat/completions")
    ap.add_argument("--model", default=os.environ.get("LYGO_PUBLIC_MODEL", "qwen2.5:3b"))
    args = ap.parse_args()
    bind = args.bind
    if args.lan:
        if not args.i_consent:
            print("Refusing LAN bind without --i-consent", file=sys.stderr)
            return 2
        bind = "0.0.0.0"
    Handler.backend = args.backend
    Handler.ollama = args.ollama if args.ollama.startswith("http") else "http://" + args.ollama
    Handler.openai_url = args.openai_url
    Handler.model = args.model
    httpd = ThreadingHTTPServer((bind, args.port), Handler)
    print(f"LYGO public gateway {bind}:{args.port} backend={args.backend} model={args.model}  (chat only)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
