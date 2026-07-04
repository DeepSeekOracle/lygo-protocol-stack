"""Multi-tool HTTP proxy: compress API + Anthropic / OpenAI / xAI forward shims."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from pxpipe_lygo.agent_helper import compress_text_for_tool
from pxpipe_lygo.compressor import LYGOCompressor
from pxpipe_lygo.config import PROXY_PORT
from pxpipe_lygo.message_adapters import normalize_target
from pxpipe_lygo.request_rewrite import rewrite_anthropic_messages, rewrite_openai_chat
from pxpipe_lygo.upstream import forward_request

ENDPOINTS = [
    "GET  /health",
    "POST /v1/compress",
    "POST /v1/transform",
    "POST /v1/messages          (Anthropic → compress + forward)",
    "POST /v1/chat/completions    (OpenAI + Grok → compress + forward)",
]


class PxpipeHandler(BaseHTTPRequestHandler):
    compressor = LYGOCompressor()

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, code: int, body: bytes, headers: dict[str, str]) -> None:
        self.send_response(code)
        for k, v in headers.items():
            if k.lower() in ("transfer-encoding", "connection"):
                continue
            self.send_header(k, v)
        if "Content-Type" not in headers and "content-type" not in {x.lower() for x in headers}:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/health"):
            self._send_json(
                200,
                {
                    "service": "pxpipe-lygo",
                    "status": "ok",
                    "multi_tool": True,
                    "endpoints": ENDPOINTS,
                    "client_env": {
                        "anthropic": "ANTHROPIC_BASE_URL=http://127.0.0.1:PORT",
                        "openai": "OPENAI_BASE_URL=http://127.0.0.1:PORT/v1",
                        "grok_xai": "XAI_BASE_URL=http://127.0.0.1:PORT/v1",
                    },
                },
            )
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"error": "invalid_json"})
            return

        if path == "/v1/compress":
            text = body.get("text") or ""
            provider = body.get("provider")
            include_blocks = body.get("include_blocks", True)
            target = normalize_target(body.get("target") or body.get("format") or provider)
            result = self.compressor.compress(text, provider=provider)
            if result.get("action") == "compress" and include_blocks:
                from pxpipe_lygo.message_adapters import compress_result_to_blocks

                blocks = compress_result_to_blocks(result, target=target)
                result = {**result, **blocks}
            if not body.get("include_png_base64"):
                result.pop("png_base64", None)
            self._send_json(200, result)
            return

        if path == "/v1/transform":
            text = body.get("text") or ""
            target = body.get("target", "auto")
            out_path = body.get("png_path")
            payload = compress_text_for_tool(text, target=target, keep_png_path=out_path)
            if not body.get("include_png_base64"):
                payload.pop("png_base64", None)
            self._send_json(200, payload)
            return

        if path.startswith("/v1/messages"):
            rewritten = rewrite_anthropic_messages(body, self.compressor)
            hdrs = {k: self.headers[k] for k in self.headers}
            status, out, rh = forward_request("claude", "/v1/messages", rewritten, hdrs)
            self._send_bytes(status, out, rh)
            return

        if path.startswith("/v1/chat/completions"):
            provider = (qs.get("provider") or ["grok"])[0]
            if provider not in ("openai", "grok"):
                provider = "grok"
            rewritten = rewrite_openai_chat(body, self.compressor, provider=provider)
            hdrs = {k: self.headers[k] for k in self.headers}
            status, out, rh = forward_request(provider, "/v1/chat/completions", rewritten, hdrs)
            self._send_bytes(status, out, rh)
            return

        self._send_json(404, {"error": "not_found", "hint": ENDPOINTS})


def main() -> int:
    host = "127.0.0.1"
    port = PROXY_PORT
    server = ThreadingHTTPServer((host, port), PxpipeHandler)
    print(f"pxpipe-lygo multi-tool proxy http://{host}:{port}/")
    for line in ENDPOINTS:
        print(f"  {line}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())