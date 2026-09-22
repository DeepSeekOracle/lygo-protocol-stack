"""Public gateway tests.

The CORS/rate/portal checks are unit-level. The request-envelope checks are over a real socket,
because the status line and the headers ARE the answer — and because both defects they cover were
invisible to the router logic:

  * an over-limit body was refused **unread**, so a caller still writing it lost the answer to a
    reset instead of being told `too_large` (defect 27, same class as `/api/session` in the kernel);
  * a non-numeric `Content-Length` raised `ValueError` out of the handler, so the connection closed
    with no answer at all and the operator got a traceback on stderr.
"""
from __future__ import annotations

import json
import socket
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import public_gateway  # noqa: E402
from public_gateway import ALLOW_ORIGINS, Handler, _cors_ok, _rate  # noqa: E402

NL = chr(13) + chr(10)
_state: dict = {}


def setUpModule() -> None:  # noqa: N802
    _state["rate"] = public_gateway._rate
    public_gateway._rate = lambda ip: True  # the limiter is not what these tests are about
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    _state["httpd"] = httpd
    _state["port"] = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()


def tearDownModule() -> None:  # noqa: N802
    _state["httpd"].shutdown()
    _state["httpd"].server_close()
    public_gateway._rate = _state["rate"]


def post(body: bytes, declared: str) -> str:
    """Send a hand-built request and return the whole answer, headers and body."""
    head = ("POST /api/chat HTTP/1.1" + NL + "Host: 127.0.0.1" + NL
            + "Content-Length: " + declared + NL + NL).encode()
    raw = b""
    with socket.create_connection(("127.0.0.1", _state["port"]), timeout=10) as sock:
        sock.sendall(head + body)
        sock.settimeout(5)
        try:
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                raw += chunk
        except OSError:
            pass
    return raw.decode("latin-1", "replace")


def body_of(answer: str) -> dict:
    return json.loads(answer.split(NL + NL, 1)[1]) if NL + NL in answer else {}


class PublicGatewayTests(unittest.TestCase):
    def test_cors_allowlist(self):
        self.assertTrue(_cors_ok("https://chatagent.ca"))
        self.assertTrue(_cors_ok("https://eternalhaven.ca"))
        self.assertTrue(_cors_ok("https://foo.hf.space"))
        self.assertFalse(_cors_ok("https://evil.example"))

    def test_rate_limit(self):
        ip = "203.0.113.9"
        ok = 0
        for _ in range(40):
            if _rate(ip):
                ok += 1
        self.assertLessEqual(ok, 24)
        self.assertGreater(ok, 0)

    def test_web_portal_files(self):
        p = ROOT / "web_portal"
        self.assertTrue((p / "index.html").is_file())
        html = (p / "index.html").read_text(encoding="utf-8")
        self.assertIn("LYGO Free LLM Portal", html)
        self.assertIn("Hugging Face", html)
        self.assertNotIn("LYGO_SERVER", html)


class RefusedBodyTest(unittest.TestCase):
    """A caller whose request is refused must still receive the refusal."""

    def test_an_over_limit_body_is_answered_with_the_reason(self):
        body = b"x" * 60_000
        answer = post(body, str(len(body)))
        self.assertIn("413", answer.split(NL, 1)[0], answer[:200])
        self.assertEqual(body_of(answer).get("error"), "too_large", answer[:200])

    def test_the_caller_is_told_the_connection_is_closing(self):
        body = b"x" * 60_000
        answer = post(body, str(len(body)))
        self.assertIn("Connection: close", answer, "a caller that reuses this socket fails its next request on it")

    def test_an_over_limit_body_is_consumed(self):
        """The mechanism, at the unit both surfaces share: `http_body.drain` must read the body."""
        import http_body

        class Peer:
            def __init__(self, declared):
                self.headers = {"Content-Length": str(declared)}
                self.connection = None
                self.sent = 0
                self.remaining = declared

            class _Stream:
                def __init__(self, peer):
                    self.peer = peer

                def read(self, n=-1):
                    take = min(n if n and n > 0 else self.peer.remaining, self.peer.remaining)
                    self.peer.remaining -= take
                    self.peer.sent += take
                    return b"x" * take

            rfile = None

        peer = Peer(60_000)
        peer.rfile = Peer._Stream(peer)
        self.assertEqual(http_body.drain(peer, 60_000), 60_000, "a refused body must be consumed")

        huge = Peer(http_body.CAP + 9_000_000)
        huge.rfile = Peer._Stream(huge)
        self.assertLessEqual(http_body.drain(huge, huge.remaining), http_body.CAP,
                             "a caller declaring tens of megabytes must not cost us tens of megabytes")


class MalformedContentLengthTest(unittest.TestCase):
    """Both of these used to end the connection with no answer: `int()` raised out of the handler."""

    def test_a_non_numeric_length_is_a_400(self):
        answer = post(b"", "abc")
        self.assertTrue(answer, "the caller must get an answer, not a dropped connection")
        self.assertIn("400", answer.split(NL, 1)[0], answer[:200])
        self.assertEqual(body_of(answer).get("error"), "bad_request", answer[:200])

    def test_a_negative_length_is_a_400(self):
        answer = post(b"", "-5")
        self.assertTrue(answer, "the caller must get an answer, not a dropped connection")
        self.assertIn("400", answer.split(NL, 1)[0], answer[:200])


if __name__ == "__main__":
    unittest.main()
