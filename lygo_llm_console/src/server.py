from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# kit src on path
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from auth import check, ensure_llama_key, ensure_token, token_from_request  # noqa: E402
from chat_loop import (  # noqa: E402
    extract_user_text,
    has_image,
    host_prefetch,
    prefetch_message,
    run_tools_round,
)
from continuity import (  # noqa: E402
    compose_system,
    ensure_identity,
    load_session,
    memory_path,
    new_session,
    save_session,
    soul_path,
)
from engine import (  # noqa: E402
    ENGINE_LOCK,
    ollama_port_open,
    ram_ok,
    resolve_binary,
    runner_for,
    spawn_runner,
    stop_port,
)
from p0_hook import PHYSICS_AVAILABLE, gate_output_window, gate_prompt  # noqa: E402
from paths import (  # noqa: E402
    CONSOLE_JSON,
    DEFAULT_PORT,
    EMBED_PORT,
    ENGINE_DIR,
    KIT_ROOT,
    LLAMA_PORT,
    LOCAL_JSON,
    PORTAL,
    WORKSPACE,
    ensure_dirs,
)
from receipts import write_receipt  # noqa: E402
from registry import get as reg_get  # noqa: E402
from registry import load as reg_load  # noqa: E402
from registry import upsert as reg_upsert  # noqa: E402
from scanner import scan_roots  # noqa: E402
from tools import TOOLS_SCHEMA  # noqa: E402

TOKEN = ""
LLAMA_KEY = ""
BIND = "127.0.0.1"
AUTH_REQUIRED = True
MOCK_ONLY = False
STATE: dict[str, Any] = {"brain": "missing", "selected": None, "error": None, "scan_n": 0}


def load_console() -> dict[str, Any]:
    cfg: dict[str, Any] = {}
    if CONSOLE_JSON.is_file():
        cfg = json.loads(CONSOLE_JSON.read_text(encoding="utf-8"))
    if LOCAL_JSON.is_file():
        loc = json.loads(LOCAL_JSON.read_text(encoding="utf-8"))
        if isinstance(loc, dict):
            cfg = {**cfg, **loc}
    return cfg


def default_scan_roots(cfg: dict[str, Any]) -> list[str]:
    raw = cfg.get("scan_roots")
    if not isinstance(raw, list) or not raw:
        raw = ["./models", r"%USERPROFILE%\.ollama\models"]
    out: list[str] = []
    for r in raw:
        s = os.path.expandvars(os.path.expanduser(str(r)))
        p = Path(s)
        if not p.is_absolute():
            p = (KIT_ROOT / s).resolve()
        out.append(str(p))
    home_cas = Path(os.path.expandvars(r"%USERPROFILE%\.ollama\models"))
    if home_cas.is_dir() and str(home_cas) not in out:
        out.append(str(home_cas))
    kit_models = KIT_ROOT / "models"
    if str(kit_models) not in out:
        out.append(str(kit_models))
    return out


def maybe_spawn(model_id: str | None) -> str:
    if MOCK_ONLY:
        STATE["brain"] = "mock"
        return "mock"
    exe = resolve_binary()
    if exe is None:
        STATE["brain"] = "missing"
        return "missing"
    rec = reg_get(model_id) if model_id else None
    if rec is None:
        data = reg_load()
        rec = next((m for m in data.get("models") or [] if m.get("id") == data.get("selected")), None)
    if not rec or not rec.get("path") or not rec.get("runnable"):
        STATE["brain"] = "missing"
        return "missing"
    p = Path(rec["path"])
    size = int(rec.get("bytes") or (p.stat().st_size if p.is_file() else 0))
    if not ram_ok(size):
        STATE["brain"] = "ram_refused"
        return "ram_refused"
    with ENGINE_LOCK:
        existing = runner_for(LLAMA_PORT)
        if existing and existing.gguf == str(p):
            STATE["brain"] = "ready"
            return "ready"
        mm = Path(rec["mmproj"]) if rec.get("mmproj") else None
        try:
            spawn_runner(
                port=LLAMA_PORT,
                gguf=p,
                kind=rec.get("kind") or "chat",
                mmproj=mm,
                ctx=int(rec.get("ctx") or 4096),
                ngl=int(rec.get("n_gpu_layers") or 0),
                alias=rec.get("id") or p.stem,
                api_key=LLAMA_KEY,
            )
        except MemoryError as e:
            STATE["brain"] = "ram_refused"
            STATE["error"] = str(e)
            return "ram_refused"
        except Exception as e:
            STATE["brain"] = "error"
            STATE["error"] = f"{type(e).__name__}: {e}"
            return "error"
    STATE["brain"] = "ready"
    STATE["error"] = None
    STATE["selected"] = rec.get("id")
    return "ready"


def boot_async(model_id: str | None) -> None:
    STATE["brain"] = "booting"
    STATE["error"] = None

    def _run() -> None:
        try:
            maybe_spawn(model_id)
        except Exception as e:
            STATE["brain"] = "error"
            STATE["error"] = str(e)

    threading.Thread(target=_run, daemon=True, name="lygo-llm-boot").start()


class Handler(BaseHTTPRequestHandler):
    server_version = "LYGO-LLM-Console/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _query(self) -> dict[str, list[str]]:
        return parse_qs(urlparse(self.path).query)

    def _headers_map(self) -> dict[str, str]:
        return {k: v for k, v in self.headers.items()}

    def _loopback(self) -> bool:
        ip = (self.client_address or ("", 0))[0]
        return ip in ("127.0.0.1", "::1", "localhost")

    def _ok_public(self) -> bool:
        path = urlparse(self.path).path
        if path in ("/", "/api/health") or path.startswith("/static/"):
            return True
        return False

    def _auth(self) -> bool:
        if not AUTH_REQUIRED:
            return True
        if self._loopback():
            return True
        if self._ok_public() and urlparse(self.path).path != "/":
            if urlparse(self.path).path.startswith("/static/") or urlparse(self.path).path == "/api/health":
                return True
        tok = token_from_request(self._headers_map(), self._query())
        if urlparse(self.path).path == "/":
            return True
        return check(tok, TOKEN)

    def _send(self, code: int, body: bytes, ctype: str = "application/json", extra: dict[str, str] | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)
        try:
            self.wfile.flush()
        except Exception:
            pass

    def _json(self, code: int, obj: Any) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"))

    def _read_body(self, limit: int) -> bytes:
        n = int(self.headers.get("Content-Length") or 0)
        if n > limit:
            return b""
        return self.rfile.read(n) if n else b""

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._auth() and path not in ("/",) and not path.startswith("/static/") and path != "/api/health":
            self._json(401, {"error": "unauthorized"})
            return
        if path == "/" or path == "/index.html":
            html = (PORTAL / "index.html").read_text(encoding="utf-8")
            html = html.replace("/*LYGO_TOKEN*/", json.dumps(TOKEN))
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            name = path[len("/static/") :]
            fp = PORTAL / name
            if not fp.is_file() or not str(fp.resolve()).startswith(str(PORTAL.resolve())):
                self._json(404, {"error": "missing"})
                return
            ctype = "text/plain"
            if name.endswith(".css"):
                ctype = "text/css"
            elif name.endswith(".js"):
                ctype = "application/javascript"
            self._send(200, fp.read_bytes(), ctype)
            return
        if path == "/api/health":
            from engine import available_ram_bytes

            self._json(
                200,
                {
                    "ok": True,
                    "signature": "Δ9Φ963-LYGO-LLM-CONSOLE-v1",
                    "authenticated": check(token_from_request(self._headers_map(), self._query()), TOKEN),
                    "physics": PHYSICS_AVAILABLE,
                    "brain": STATE.get("brain"),
                    "selected": STATE.get("selected") or reg_load().get("selected"),
                    "error": STATE.get("error"),
                    "scan_n": STATE.get("scan_n") or len(reg_load().get("models") or []),
                    "ollama_port_open": ollama_port_open(),
                    "engine_present": bool(resolve_binary()),
                    "ram_avail": available_ram_bytes(),
                    "bind": BIND,
                    "port": DEFAULT_PORT,
                    "tools": [t["function"]["name"] for t in TOOLS_SCHEMA],
                    "workspace": str(WORKSPACE),
                },
            )
            return
        if path == "/api/models" or path == "/v1/models":
            if not self._auth():
                self._json(401, {"error": "unauthorized"})
                return
            data = reg_load()
            if path.startswith("/v1"):
                self._json(
                    200,
                    {
                        "object": "list",
                        "data": [{"id": m.get("id"), "object": "model"} for m in data.get("models") or []],
                    },
                )
                return
            self._json(200, data)
            return
        if path == "/api/tools":
            self._json(200, {"tools": TOOLS_SCHEMA, "names": [t["function"]["name"] for t in TOOLS_SCHEMA]})
            return
        if path == "/api/workspace":
            ents = []
            if WORKSPACE.is_dir():
                for child in list(WORKSPACE.iterdir())[:80]:
                    ents.append({"name": child.name, "dir": child.is_dir()})
            self._json(200, {"path": str(WORKSPACE), "entries": ents})
            return
        if path == "/api/memory":
            mem = WORKSPACE / "memory.jsonl"
            lines = []
            if mem.is_file():
                lines = mem.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:]
            md = ""
            mp = memory_path()
            if mp.is_file():
                md = mp.read_text(encoding="utf-8", errors="replace")[-6000:]
            self._json(200, {"notes": lines, "memory_md": md, "path": str(mp)})
            return
        if path == "/api/soul":
            p = soul_path()
            t = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
            self._json(200, {"path": str(p), "text": t})
            return
        if path == "/api/session":
            self._json(200, {"messages": load_session()})
            return
        if path == "/api/receipts":
            if not check(token_from_request(self._headers_map(), self._query()), TOKEN):
                self._json(401, {"error": "unauthorized"})
                return
            from paths import RECEIPTS

            items = []
            if RECEIPTS.is_dir():
                for f in sorted(RECEIPTS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:50]:
                    try:
                        items.append(json.loads(f.read_text(encoding="utf-8")))
                    except Exception:
                        continue
            self._json(200, {"receipts": items})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._auth():
            self._json(401, {"error": "unauthorized"})
            return
        if path == "/api/scan":
            body = self._read_body(256_000)
            cfg = load_console()
            roots = default_scan_roots(cfg)
            if body:
                try:
                    extra = json.loads(body.decode("utf-8"))
                    if extra.get("roots"):
                        roots = list(extra["roots"])
                except json.JSONDecodeError:
                    pass
            result = scan_roots(roots)
            data = reg_upsert(result["models"])
            STATE["scan_n"] = len(data.get("models") or [])
            if data.get("selected"):
                STATE["selected"] = data.get("selected")
            self._json(200, {**result, "registry": data, "roots": roots})
            return
        if path == "/api/select" or path == "/api/boot":
            body = self._read_body(16_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            mid = obj.get("id") or STATE.get("selected") or reg_load().get("selected")
            data = reg_load()
            data["selected"] = mid
            from registry import save as reg_save

            reg_save(data)
            STATE["selected"] = mid
            boot_async(mid)
            self._json(200, {"ok": True, "brain": STATE.get("brain"), "selected": mid, "error": STATE.get("error")})
            return
        if path == "/api/session":
            body = self._read_body(512_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            if obj.get("new"):
                new_session()
                self._json(200, {"ok": True, "messages": []})
                return
            msgs = obj.get("messages")
            if isinstance(msgs, list):
                save_session(msgs)
            self._json(200, {"ok": True, "messages": load_session()})
            return
        if path == "/api/limb":
            body = self._read_body(64_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            from tools import dispatch as tool_dispatch

            name = str(obj.get("name") or "")
            args = obj.get("arguments") or obj.get("args") or {}
            if not isinstance(args, dict):
                args = {}
            self._json(200, tool_dispatch(name, args))
            return
        if path == "/api/shutdown":
            stop_port(LLAMA_PORT)
            stop_port(EMBED_PORT)
            self._json(200, {"ok": True})
            threading.Thread(target=lambda: self.server.shutdown(), daemon=True).start()
            return
        if path == "/api/chat":
            self._api_chat()
            return
        if path == "/v1/chat/completions":
            self._v1_chat()
            return
        if path == "/v1/embeddings":
            self._json(501, {"error": "embed_runner_optional"})
            return
        self._json(404, {"error": "not_found"})

    def _api_chat(self) -> None:
        raw = self._read_body(4 * 1024 * 1024)
        if not raw:
            cl = int(self.headers.get("Content-Length") or 0)
            if cl > 4 * 1024 * 1024:
                self._json(413, {"error": "too_large"})
                return
        try:
            obj = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "bad_json"})
            return
        messages = obj.get("messages") or []
        if obj.get("prompt") and not messages:
            messages = [{"role": "user", "content": obj["prompt"]}]
        user = extract_user_text(messages)
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                c = m.get("content")
                last_user = c if isinstance(c, str) else extract_user_text([m])
                break
        gate = gate_prompt(user)
        if gate.get("verdict") == "QUARANTINE":
            self._json(451, {"error": "quarantine", "gate": gate})
            return
        use_tools = bool(obj.get("tools", True))
        model = obj.get("model") or STATE.get("selected") or "lygo-local"
        max_tokens = int(obj.get("max_tokens") or 768)
        want_stream = bool(obj.get("stream", True))
        brain = maybe_spawn(model if reg_get(str(model)) else None)
        msgs = [{"role": "system", "content": compose_system()}] + messages
        assistant = ""
        traces: list[Any] = []
        if use_tools and last_user:
            pre = host_prefetch(last_user)
            if pre:
                traces.extend(pre)
                msgs.append({"role": "user", "content": prefetch_message(pre)})

        def emit_sse(event: dict[str, Any]) -> None:
            line = json.dumps(event) + "\n"
            self.wfile.write(b"data: " + line.encode("utf-8") + b"\n")
            self.wfile.flush()

        if want_stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()

        if brain != "ready":
            # mock / missing
            assistant = (
                "LYGO LLM Console is up. Engine brain is "
                f"{brain}. P0 verdict {gate.get('verdict')}. "
                "Scan a GGUF or Ollama CAS tree, then Select a chat model. "
                "This console does not call ollama.exe."
            )
            if use_tools and "status" in user.lower():
                name, result = "kernel_status", __import__("tools").dispatch("kernel_status", {})
                traces.append({"name": name, "result": result})
            if want_stream:
                emit_sse({"type": "token", "delta": assistant, "verdict": gate.get("verdict")})
                emit_sse({"type": "done", "traces": traces})
                return
            rec = write_receipt(prompt=user, output=assistant, model=str(model), gate=gate, extra={"has_image": has_image(messages)})
            self._json(200, {"text": assistant, "gate": gate, "brain": brain, "receipt": rec["id"], "traces": traces})
            return

        from openai_proxy import llama_chat

        payload = {
            "model": model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if use_tools:
            payload["tools"] = TOOLS_SCHEMA
        with ENGINE_LOCK:
            code, body, _ = llama_chat(api_key=LLAMA_KEY, payload=payload)
        try:
            parsed = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            parsed = {}
        msg_obj = ((parsed.get("choices") or [{}])[0].get("message") or {})
        assistant = msg_obj.get("content") or ""
        ow = gate_output_window(assistant or "")
        if ow.get("verdict") == "QUARANTINE":
            assistant = "[output quarantined]"
        if use_tools:
            follow = list(msgs)
            cur_msg = msg_obj
            cur_text = assistant
            for _step in range(8):
                batch = run_tools_round(cur_text, cur_msg)
                if not batch:
                    break
                traces.extend(batch)
                follow.append({"role": "assistant", "content": cur_text, "tool_calls": cur_msg.get("tool_calls")})
                follow.append(
                    {
                        "role": "user",
                        "content": "Tool results (RESOURCE, not CANON):\n" + json.dumps(batch, default=str)[:12000],
                    }
                )
                payload2 = {"model": model, "messages": follow, "max_tokens": max_tokens, "stream": False, "tools": TOOLS_SCHEMA}
                with ENGINE_LOCK:
                    _, body2, _ = llama_chat(api_key=LLAMA_KEY, payload=payload2)
                try:
                    p2 = json.loads(body2.decode("utf-8"))
                except json.JSONDecodeError:
                    break
                cur_msg = ((p2.get("choices") or [{}])[0].get("message") or {})
                cur_text = cur_msg.get("content") or ""
                assistant = cur_text or assistant
                if gate_output_window(assistant).get("verdict") == "QUARANTINE":
                    assistant = "[output quarantined]"
                    break
        rec = write_receipt(prompt=user, output=assistant, model=str(model), gate=gate, extra={"has_image": has_image(messages)})
        try:
            save_session(list(messages) + [{"role": "assistant", "content": assistant}])
        except Exception:
            pass
        if want_stream:
            emit_sse({"type": "token", "delta": assistant, "verdict": gate.get("verdict")})
            emit_sse({"type": "done", "traces": traces, "receipt": rec["id"]})
            return
        self._json(200, {"text": assistant, "gate": gate, "brain": brain, "receipt": rec["id"], "traces": traces})

    def _v1_chat(self) -> None:
        raw = self._read_body(256_000)
        if not raw and int(self.headers.get("Content-Length") or 0) > 256_000:
            self._json(413, {"error": "too_large"})
            return
        try:
            obj = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "bad_json"})
            return
        messages = obj.get("messages") or []
        user = extract_user_text(messages)
        gate = gate_prompt(user)
        if gate.get("verdict") == "QUARANTINE":
            self._json(451, {"error": "quarantine", "gate": gate})
            return
        obj["max_tokens"] = int(obj.get("max_tokens") or 512)
        # do not execute Console tools; strip injection
        brain = maybe_spawn(obj.get("model") if reg_get(str(obj.get("model") or "")) else None)
        if brain != "ready":
            mock = {
                "id": "lygo-mock",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": f"brain={brain}; P0={gate.get('verdict')}"},
                        "finish_reason": "stop",
                    }
                ],
            }
            self._json(200, mock)
            return
        from openai_proxy import llama_chat

        with ENGINE_LOCK:
            code, body, ctype = llama_chat(api_key=LLAMA_KEY, payload={**obj, "stream": False})
        try:
            parsed = json.loads(body.decode("utf-8"))
            txt = (((parsed.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
            if gate_output_window(txt).get("verdict") == "QUARANTINE":
                parsed["choices"][0]["message"]["content"] = "[output quarantined]"
                body = json.dumps(parsed).encode("utf-8")
        except Exception:
            pass
        self._send(code, body, ctype or "application/json")


def main() -> int:
    global TOKEN, LLAMA_KEY, BIND, AUTH_REQUIRED, MOCK_ONLY
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="serve")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--lan", action="store_true")
    ap.add_argument("--i-consent", action="store_true", dest="i_consent")
    ap.add_argument("--gguf", default="")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    ensure_dirs()
    ensure_identity()
    TOKEN = ensure_token()
    LLAMA_KEY = ensure_llama_key()
    MOCK_ONLY = bool(args.mock)
    if args.lan:
        if not args.i_consent:
            print("LAN bind requires --i-consent", file=sys.stderr)
            return 2
        BIND = "0.0.0.0"
        AUTH_REQUIRED = True
    cfg = load_console()
    if args.gguf:
        p = Path(args.gguf)
        rec = {
            "id": p.stem,
            "path": str(p),
            "kind": "chat",
            "ctx": 4096,
            "n_gpu_layers": 0,
            "runnable": p.is_file(),
            "source": "cli",
            "bytes": p.stat().st_size if p.is_file() else 0,
        }
        reg_upsert([rec], selected=p.stem)
        STATE["selected"] = p.stem
        STATE["scan_n"] = 1
    else:
        scanned = scan_roots(default_scan_roots(cfg))
        data = reg_upsert(scanned.get("models") or [])
        STATE["selected"] = data.get("selected")
        STATE["scan_n"] = len(data.get("models") or [])
        print(f"scan models={STATE['scan_n']} truncated={scanned.get('scan_truncated')} selected={STATE.get('selected')}")
    if args.cmd != "serve":
        print("unknown cmd", args.cmd)
        return 2
    httpd = ThreadingHTTPServer((BIND, args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/?t={TOKEN}"
    print(f"LYGO LLM Console  {url}")
    print(f"signature Δ9Φ963-LYGO-LLM-CONSOLE-v1  physics={PHYSICS_AVAILABLE}  bind={BIND}")
    if not MOCK_ONLY and STATE.get("selected"):
        print(f"booting {STATE.get('selected')} …")
        boot_async(str(STATE.get("selected")))
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_port(LLAMA_PORT)
        stop_port(EMBED_PORT)
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
