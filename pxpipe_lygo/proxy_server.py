"""Minimal local HTTP proxy: health, compress API, optional Anthropic forward shim."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pxpipe_lygo.compressor import LYGOCompressor
from pxpipe_lygo.config import PROXY_PORT
from pxpipe_lygo.router import select_provider, upstream_base_url


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

    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self._send_json(
                200,
                {
                    "service": "pxpipe-lygo",
                    "status": "ok",
                    "endpoints": ["/health", "/v1/compress", "/v1/messages (forward)"],
                },
            )
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json"})
            return

        if self.path == "/v1/compress":
            text = body.get("text") or ""
            provider = body.get("provider")
            result = self.compressor.compress(text, provider=provider)
            if result["action"] == "compress":
                result.pop("png_base64", None)
            self._send_json(200, result)
            return

        if self.path.startswith("/v1/messages"):
            self._forward_anthropic(body)
            return

        self._send_json(404, {"error": "not_found"})

    def _forward_anthropic(self, body: dict[str, Any]) -> None:
        """Compress `system` string when profitable, then forward to Anthropic."""
        system = body.get("system")
        if isinstance(system, str) and system.strip():
            comp = self.compressor.compress(system, provider="claude")
            if comp.get("action") == "compress":
                body = dict(body)
                body["system"] = (
                    "[LYGO pxpipe compressed context — see image block]\n"
                    + "\n".join(f"EXACT:{x}" for x in comp.get("exact_identifiers", [])[:32])
                )
                body.setdefault("metadata", {})["lygo_pxpipe"] = {
                    "manifest_id": comp["manifest_id"],
                    "tokens_saved_estimate": comp.get("tokens_saved_estimate"),
                }

        provider = select_provider("claude")
        base = upstream_base_url(provider)
        if not base:
            self._send_json(502, {"error": "no_upstream_provider"})
            return

        import os

        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            self._send_json(401, {"error": "missing_ANTHROPIC_API_KEY"})
            return

        url = f"{base}/v1/messages"
        data = json.dumps(body).encode("utf-8")
        req = Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-api-key", api_key)
        req.add_header("anthropic-version", self.headers.get("anthropic-version", "2023-06-01"))
        try:
            with urlopen(req, timeout=120) as resp:
                out = resp.read()
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(out)
        except HTTPError as exc:
            err_body = exc.read()
            self.send_response(exc.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_body)
        except URLError as exc:
            self._send_json(502, {"error": "upstream_failed", "detail": str(exc.reason)})


def main() -> int:
    host = "127.0.0.1"
    port = PROXY_PORT
    server = ThreadingHTTPServer((host, port), PxpipeHandler)
    print(f"pxpipe-lygo proxy http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())