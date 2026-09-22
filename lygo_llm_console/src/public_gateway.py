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

try:  # kit ports (a stick runs 9651/11451); never hard-code the desktop pair here
    from paths import DEFAULT_PORT, LLAMA_PORT  # noqa: E402
except Exception:  # standalone copy of this file
    DEFAULT_PORT, LLAMA_PORT = 9641, 11441

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from p0_hook import PHYSICS_AVAILABLE, gate_output_window, gate_prompt  # noqa: E402

try:  # the body-refusal policy is shared with the kernel (defect 27); this file also ships alone
    from http_body import drain as drain_body  # noqa: E402
except Exception:  # a copy without http_body: same job, same bounds, inline

    def drain_body(handler: Any, declared: int) -> int:
        want, got = min(int(declared or 0), 1 << 20), 0
        try:
            while got < want:
                chunk = handler.rfile.read(min(65_536, want - got))
                if not chunk:
                    break
                got += len(chunk)
        except (OSError, ValueError):
            pass
        return got

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
    f"http://127.0.0.1:{DEFAULT_PORT}",
    f"http://localhost:{DEFAULT_PORT}",
    "http://127.0.0.1:8080",
    # A machine-specific origin (a LAN dev box, a staging host) does not belong in shipped source:
    # it is a permanent hole nobody remembers. Set LYGO_PUBLIC_ORIGINS="https://a,https://b".
) + tuple(
    o.strip().rstrip("/")
    for o in os.environ.get("LYGO_PUBLIC_ORIGINS", "").split(",")
    if o.strip()
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
# A public endpoint may not answer behind a quieter gate than the console it fronts. The deep
# layer missing is a degraded mode, not a free pass: it is marked in every verdict, warned about
# once, and reported on /health. LYGO_PUBLIC_REQUIRE_PHYSICS=1 refuses instead of degrading.
STRICT_PHYSICS = os.environ.get("LYGO_PUBLIC_REQUIRE_PHYSICS", "").strip().lower() in ("1", "true", "yes")
_degraded_warned = False


def _warn_degraded_once() -> None:
    global _degraded_warned
    if not _degraded_warned:
        _degraded_warned = True
        sys.stderr.write(
            "[public-gateway] P0 physics layer unavailable: answering with the policy regex only. "
            "Set LYGO_PUBLIC_REQUIRE_PHYSICS=1 to refuse instead of degrade.\n"
        )
        sys.stderr.flush()


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
    # Our own engine is the backend, full stop. There is no daemon path here: a gateway that can
    # reach another service is a gateway that will be pointed at one, and this kit is standalone by
    # design - it boots its own llama-server on its own port.
    backend = "local"
    openai_url = f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions"
    openai_key = ""
    model = ""   # empty = resolve from our own registry when the caller names no model
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
        if getattr(self, "close_connection", False):
            # Say it, don't just do it (defect 27): a caller that read Content-Length would treat
            # this socket as reusable and fail its next request on it.
            self.send_header("Connection", "close")
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
                    "physics": PHYSICS_AVAILABLE,
                    "gate": "physics" if PHYSICS_AVAILABLE else "regex_only",
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
        declared = (self.headers.get("Content-Length") or "0").strip()
        try:
            n = int(declared)
        except ValueError:
            # `int()` used to raise out of the handler: the connection closed with no answer at all
            # and the operator got a traceback on stderr. A malformed envelope is the caller's
            # problem, and it gets an answer like any other.
            self.close_connection = True
            self._json(400, {"error": "bad_request", "detail": "Content-Length: " + declared[:32]})
            return
        if n < 0:
            self.close_connection = True
            self._json(400, {"error": "bad_request", "detail": "Content-Length: " + str(n)})
            return
        if n > 48_000:
            # Refuse the body *and consume it*: answering while the caller is still writing resets
            # the rest of that write, so the caller never reads this reason (defect 27).
            drain_body(self, n)
            self.close_connection = True
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
            _c = m.get("content")
            if isinstance(_c, list):
                # An OpenAI-style content list can carry an image part whose url is a base64 blob.
                # `str()` of that list pastes the blob into the prompt (truncated, so not even a
                # usable URL) and hands it to the gate as prose. A public caller gets the words plus
                # a marker that a picture came with them - never the blob.
                bits = []
                for _p in _c:
                    if isinstance(_p, dict):
                        if _p.get("type") == "image_url" or _p.get("image_url"):
                            bits.append("[image]")
                        elif _p.get("text"):
                            bits.append(str(_p["text"]))
                content = " ".join(bits)[:MAX_CHARS]
            else:
                content = str(_c or "")[:MAX_CHARS]
            msgs.append({"role": role, "content": content})
        user = " ".join(m["content"] for m in msgs if m["role"] == "user")[-MAX_CHARS:]
        gate = gate_prompt(user)
        if gate.get("reason") == "p0_import_failed":
            # p0_hook fails CLOSED when its physics layer cannot be imported. This endpoint used
            # to override that closed gate with a fabricated {"verdict": "ALLOW"} labelled
            # "p0_regex_only" - a label for a regex that never ran. The public surface therefore
            # answered with no gating whatsoever. Run the real policy stage instead and say out
            # loud that only the shallow layer is active.
            gate = {**gate_output_window(user), "reason": "p0_regex_only", "degraded": True, "physics": None}
            _warn_degraded_once()
            if STRICT_PHYSICS:
                self._json(503, {"error": "gate_unavailable", "gate": gate})
                return
        if gate.get("verdict") == "QUARANTINE":
            self._json(451, {"error": "quarantine", "gate": gate})
            return
        model = str(obj.get("model") or self.model or _selected_model())
        try:
            # "local" and "openai" are the same route: our own engine, OpenAI-compatible.
            text = _openai_chat(self.openai_url, model, msgs, self.openai_key)
        except Exception as e:
            # This endpoint is public: upstream internals (host, port, stack frames) belong in the
            # operator's stderr, not in the caller's response.
            sys.stderr.write(f"[public-gateway] upstream failed: {type(e).__name__}: {e}\n")
            sys.stderr.flush()
            self._json(502, {"error": "upstream"})
            return
        # The whole reply, not its first 8 KB: _policy also QUARANTINEs a payload over its
        # POLICY_MAX_CHARS, so slicing the head let an oversized answer through unchecked.
        if gate_output_window(text).get("verdict") == "QUARANTINE":
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


def _selected_model() -> str:
    """The console's own default brain, so a public gateway starts on a model this machine has."""
    import json

    reg = Path(__file__).resolve().parents[1] / "save" / "registry.json"
    try:
        return str(json.loads(reg.read_text(encoding="utf-8")).get("selected") or "qwen2.5-coder:7b")
    except Exception:
        return "qwen2.5-coder:7b"


def main() -> int:
    ap = argparse.ArgumentParser(description="Public LYGO chat gateway (no admin, no shell).")
    ap.add_argument("--port", type=int, default=9642)
    ap.add_argument("--bind", default="127.0.0.1")
    ap.add_argument("--i-consent", action="store_true")
    ap.add_argument("--lan", action="store_true")
    # Our own engine is the backend. There is no daemon option: the kit never needs one, and offering
    # it is how a standalone system starts to depend on something outside itself.
    ap.add_argument("--backend", choices=("local", "openai"), default="local")
    ap.add_argument("--openai-url", default=f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions")
    ap.add_argument("--model", default=os.environ.get("LYGO_PUBLIC_MODEL") or _selected_model())
    args = ap.parse_args()
    bind = args.bind
    if args.lan:
        if not args.i_consent:
            print("Refusing LAN bind without --i-consent", file=sys.stderr)
            return 2
        bind = "0.0.0.0"
    Handler.backend = args.backend
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
