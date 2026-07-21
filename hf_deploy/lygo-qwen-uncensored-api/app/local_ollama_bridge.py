#!/usr/bin/env python3
"""Optional local OpenAI-compatible proxy → Ollama uncensored model.

Run on home PC when you want OpenClaw to use local AI-TAVS quant with the same
API shape as the HF Space.

  python -m app.local_ollama_bridge
  # → http://127.0.0.1:8787/v1
"""
from __future__ import annotations

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

OLLAMA = os.environ.get("OLLAMA_BASE", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get(
    "OLLAMA_MODEL", "AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b"
)
PORT = int(os.environ.get("BRIDGE_PORT", "8787"))


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code: int, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/health"):
            self._json(200, {"ok": True, "backend": OLLAMA, "model": MODEL})
            return
        if path == "/v1/models":
            self._json(
                200,
                {
                    "object": "list",
                    "data": [{"id": MODEL, "object": "model", "owned_by": "ollama"}],
                },
            )
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            data = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "bad_json"})
            return
        if path != "/v1/chat/completions":
            self._json(404, {"error": "not_found"})
            return
        messages = data.get("messages") or []
        payload = {
            "model": data.get("model") or MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": data.get("temperature", 0.85),
                "top_p": data.get("top_p", 0.95),
                "num_predict": data.get("max_tokens", 512),
            },
        }
        req = urllib.request.Request(
            OLLAMA + "/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                o = json.loads(r.read().decode())
        except Exception as e:
            self._json(502, {"error": str(e)})
            return
        msg = (o.get("message") or {}).get("content") or ""
        self._json(
            200,
            {
                "id": "chatcmpl-local",
                "object": "chat.completion",
                "model": payload["model"],
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": msg},
                        "finish_reason": "stop",
                    }
                ],
            },
        )


if __name__ == "__main__":
    print(f"[LYGO bridge] {MODEL} via {OLLAMA} on :{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
