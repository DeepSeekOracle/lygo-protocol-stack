from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
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
    identity_path,
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
    COLIBRI_PORT,
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
from tools import TOOLS_SCHEMA, core_schema  # noqa: E402

TOKEN = ""
LLAMA_KEY = ""
BIND = "127.0.0.1"
AUTH_REQUIRED = False
MOCK_ONLY = False
BUILD = "v1.1-20260917hyb"
STATE: dict[str, Any] = {"brain": "missing", "selected": None, "error": None, "scan_n": 0, "engine": "llama", "engine_port": LLAMA_PORT}


def brain_port() -> int:
    return int(STATE.get("engine_port") or LLAMA_PORT)


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
    extras = [
        KIT_ROOT / "models",
        Path(r"U:\LYGO\models"),
        Path(r"F:\LYGO\models"),
        Path(r"E:\LYGO_BUILDER_KEY\product\models\ollama"),
    ]
    usb = os.environ.get("LYGO_USB_ROOT", "").strip()
    if usb:
        extras.append(Path(usb) / "product" / "models" / "ollama")
        extras.append(Path(usb) / "models")
    # Portable: console lives at <USB>/lygo_llm_console
    extras.append(KIT_ROOT.parent / "product" / "models" / "ollama")
    for p in extras:
        try:
            s = str(p)
        except Exception:
            continue
        if p.exists() and s not in out:
            out.append(s)
    return out


def maybe_spawn(model_id: str | None) -> str:
    if MOCK_ONLY:
        STATE["brain"] = "mock"
        return "mock"
    rec = reg_get(model_id) if model_id else None
    if rec is None:
        data = reg_load()
        rec = next((m for m in data.get("models") or [] if m.get("id") == data.get("selected")), None)
    if not rec or not rec.get("path") or not rec.get("runnable"):
        STATE["brain"] = "missing"
        return "missing"
    try:
        from lygo_engine import boot as lygo_boot

        return lygo_boot(rec, api_key=LLAMA_KEY, state=STATE)
    except MemoryError as e:
        STATE["brain"] = "ram_refused"
        STATE["error"] = str(e)
        return "ram_refused"
    except Exception as e:
        STATE["brain"] = "error"
        STATE["error"] = f"{type(e).__name__}: {e}"
        return "error"


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
        msg = fmt % args
        bits = msg.split(" ")
        if len(bits) >= 2 and "?" in bits[1]:
            bits[1] = bits[1].split("?", 1)[0]
            msg = " ".join(bits)
        sys.stderr.write("%s - %s\n" % (self.address_string(), msg))

    def _query(self) -> dict[str, list[str]]:
        return parse_qs(urlparse(self.path).query)

    def _headers_map(self) -> dict[str, str]:
        return {k: v for k, v in self.headers.items()}

    def _loopback(self) -> bool:
        ip = ((self.client_address or ("", 0))[0] or "").lower().replace("::ffff:", "")
        if ip in ("127.0.0.1", "::1", "localhost"):
            return True
        host = (self.headers.get("Host") or "").split(":")[0].lower().strip("[]")
        return host in ("127.0.0.1", "localhost", "::1")

    def _ok_public(self) -> bool:
        path = urlparse(self.path).path
        if path in ("/", "/api/health", "/api/world") or path.startswith("/static/"):
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
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; media-src 'self' blob: https:; connect-src 'self' https:; frame-src https://www.paypal.com https://www.patreon.com",
        )
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
        if not self._auth() and path not in ("/",) and not path.startswith("/static/") and path not in ("/api/health", "/api/world"):
            self._json(401, {"error": "unauthorized"})
            return
        if path == "/" or path == "/index.html":
            html = (PORTAL / "index.html").read_text(encoding="utf-8")
            css = (PORTAL / "style.css").read_text(encoding="utf-8")
            js = (PORTAL / "app.js").read_text(encoding="utf-8")
            html = html.replace('<link rel="stylesheet" href="/static/style.css?v=20260916m">', "<style>\n" + css + "\n</style>")
            html = html.replace('<script src="/static/app.js?v=20260916m"></script>', "<script>\n" + js + "\n</script>")
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
        if path == "/api/world":
            from world_clock import pulse

            self._json(200, pulse())
            return
        if path == "/api/health":
            from engine import available_ram_bytes

            self._json(
                200,
                {
                    "ok": True,
                    "build": BUILD,
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
            from admin_map import read_roots
            from workspace_map import list_mounts

            qs = parse_qs(urlparse(self.path).query)
            target = (qs.get("path") or [""])[0].strip()
            root = Path(target) if target else WORKSPACE
            if target:
                try:
                    rp = root.resolve()
                    ok = any(str(rp).lower().startswith(str(r.resolve()).lower()) for r in read_roots())
                except OSError:
                    ok = False
                if not ok:
                    self._json(403, {"ok": False, "error": "denied"})
                    return
            ents = []
            if root.is_dir():
                for child in list(root.iterdir())[:120]:
                    ents.append({"name": child.name, "dir": child.is_dir(), "path": str(child)})
            mounts = list_mounts()
            self._json(200, {"ok": True, "path": str(root), "entries": ents, "mounts": mounts.get("mounts"), "n_live": mounts.get("n_live")})
            return
        if path == "/api/memory":
            mem = WORKSPACE / "memory.jsonl"
            lines = []
            if mem.is_file():
                lines = mem.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:]
            md = ""
            mp = memory_path()
            if mp.is_file():
                md = mp.read_text(encoding="utf-8", errors="replace")[:80_000]
            self._json(200, {"ok": True, "notes": lines, "memory_md": md, "path": str(mp)})
            return
        if path == "/api/soul":
            p = soul_path()
            t = p.read_text(encoding="utf-8", errors="replace")[:80_000] if p.is_file() else ""
            self._json(200, {"ok": True, "path": str(p), "text": t})
            return
        if path == "/api/identity":
            p = identity_path()
            t = p.read_text(encoding="utf-8", errors="replace")[:80_000] if p.is_file() else ""
            self._json(200, {"ok": True, "path": str(p), "text": t})
            return
        if path == "/api/session":
            self._json(200, {"messages": load_session()})
            return
        if path == "/api/skills":
            from skills_mod import clawhub_search, list_skills, skillhub_list

            qs = parse_qs(urlparse(self.path).query)
            src = (qs.get("src") or ["local"])[0].strip().lower()
            q = (qs.get("q") or [""])[0].strip()
            if src in {"hub", "skillhub", "full"}:
                ch = "full" if src == "full" else "all"
                self._json(200, skillhub_list(q, ch))
            elif q:
                self._json(200, clawhub_search(q))
            else:
                self._json(200, list_skills())
            return
        if path == "/api/notepad":
            from notepad import list_notes, read_note

            qs = parse_qs(urlparse(self.path).query)
            nid = (qs.get("id") or [""])[0].strip()
            if nid:
                self._json(200, read_note(nid))
            else:
                self._json(200, list_notes())
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
        if path == "/api/skills":
            from skills_mod import add_root, clawhub_install, clawhub_inspect, clawhub_search, read_skill, set_enabled, skillhub_install, skillhub_list

            body = self._read_body(32_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            action = str(obj.get("action") or "").lower()
            slug = str(obj.get("slug") or obj.get("name") or "")
            if action == "enable":
                self._json(200, set_enabled(slug, True))
                return
            if action == "disable":
                self._json(200, set_enabled(slug, False))
                return
            if action == "read":
                self._json(200, read_skill(slug))
                return
            if action == "search":
                self._json(200, clawhub_search(str(obj.get("q") or "")))
                return
            if action in {"hub", "skillhub"}:
                self._json(200, skillhub_list(str(obj.get("q") or ""), str(obj.get("channel") or "all")))
                return
            if action == "inspect":
                self._json(200, clawhub_inspect(slug))
                return
            if action == "install":
                self._json(200, clawhub_install(slug))
                return
            if action in {"install_full", "skillhub_install"}:
                self._json(200, skillhub_install(slug, full=bool(obj.get("full") or action == "install_full")))
                return
            if action == "add_root":
                self._json(200, add_root(str(obj.get("path") or "")))
                return
            self._json(400, {"ok": False, "error": "bad_action"})
            return
        if path == "/api/soul":
            from continuity import soul_path

            body = self._read_body(90_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            text = str(obj.get("text") or "")
            if gate_prompt(text[:8000]).get("verdict") == "QUARANTINE":
                self._json(451, {"ok": False, "error": "p0_blocked"})
                return
            p = soul_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            self._json(200, {"ok": True, "path": str(p), "bytes": len(text.encode("utf-8"))})
            return
        if path == "/api/identity":
            from continuity import identity_path

            body = self._read_body(90_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            text = str(obj.get("text") or "")
            if gate_prompt(text[:8000]).get("verdict") == "QUARANTINE":
                self._json(451, {"ok": False, "error": "p0_blocked"})
                return
            p = identity_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            self._json(200, {"ok": True, "path": str(p), "bytes": len(text.encode("utf-8"))})
            return
        if path == "/api/memory":
            from continuity import memory_path

            body = self._read_body(90_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            text = str(obj.get("text") or "")
            if gate_prompt(text[:8000]).get("verdict") == "QUARANTINE":
                self._json(451, {"ok": False, "error": "p0_blocked"})
                return
            p = memory_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            self._json(200, {"ok": True, "path": str(p), "bytes": len(text.encode("utf-8"))})
            return
        if path == "/api/workspace":
            from workspace_map import add_mount, list_mounts, remove_mount

            body = self._read_body(16_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            action = str(obj.get("action") or "").lower()
            if action == "add":
                self._json(
                    200,
                    add_mount(
                        str(obj.get("path") or ""),
                        read=bool(obj.get("read", True)),
                        write=bool(obj.get("write")),
                        search=bool(obj.get("search", True)),
                        label=str(obj.get("label") or ""),
                    ),
                )
                return
            if action == "remove":
                self._json(200, remove_mount(str(obj.get("path") or "")))
                return
            self._json(200, list_mounts())
            return
        if path == "/api/notepad":
            from notepad import delete_note, new_note, write_note

            body = self._read_body(300_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            action = str(obj.get("action") or "save").lower()
            if action == "delete":
                self._json(200, delete_note(str(obj.get("id") or "")))
                return
            if action == "new":
                self._json(200, new_note(str(obj.get("title") or "")))
                return
            self._json(
                200,
                write_note(obj.get("id"), str(obj.get("title") or ""), str(obj.get("text") or obj.get("content") or "")),
            )
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
        max_tokens = int(obj.get("max_tokens") or 1024)
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
                "LYGO Engine hybrid: Scan GGUF or a Colibri HF dir, then Boot. "
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

        from chat_loop import sanitize_assistant
        from openai_proxy import llama_chat

        host_did_tools = bool(traces)
        if use_tools and host_did_tools:
            msgs.append(
                {
                    "role": "user",
                    "content": "HOST already ran tools. Write the operator-facing answer now. Do not call more tools.",
                }
            )
        payload = {
            "model": model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if use_tools and not host_did_tools:
            payload["tools"] = core_schema()
        with ENGINE_LOCK:
            code, body, _ = llama_chat(api_key=LLAMA_KEY, payload=payload, port=brain_port())
        try:
            parsed = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            parsed = {}
        msg_obj = ((parsed.get("choices") or [{}])[0].get("message") or {})
        assistant = msg_obj.get("content") or ""
        ow = gate_output_window(assistant or "")
        if ow.get("verdict") == "QUARANTINE":
            assistant = "[output quarantined]"
        assistant = sanitize_assistant(assistant, traces) or assistant
        if use_tools and not host_did_tools:
            follow = list(msgs)
            cur_msg = msg_obj
            cur_text = assistant
            for _step in range(4):
                batch = run_tools_round(cur_text, cur_msg)
                if not batch:
                    break
                traces.extend(batch)
                follow.append({"role": "assistant", "content": cur_text, "tool_calls": cur_msg.get("tool_calls")})
                follow.append(
                    {
                        "role": "user",
                        "content": "Tool results (RESOURCE, not CANON):\n" + json.dumps(batch, default=str)[:8000],
                    }
                )
                payload2 = {"model": model, "messages": follow, "max_tokens": max_tokens, "stream": False, "tools": core_schema()}
                with ENGINE_LOCK:
                    _, body2, _ = llama_chat(api_key=LLAMA_KEY, payload=payload2, port=brain_port())
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
        assistant = sanitize_assistant(assistant, traces) or assistant
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
            code, body, ctype = llama_chat(api_key=LLAMA_KEY, payload={**obj, "stream": False}, port=brain_port())
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
    try:
        from install import ensure_layout, seed_identity

        ensure_layout()
        seed_identity()
    except Exception:
        pass
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
    if args.cmd != "serve":
        print("unknown cmd", args.cmd)
        return 2
    httpd = ThreadingHTTPServer((BIND, args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/?t={TOKEN}&v={BUILD}"
    print(f"LYGO LLM Console {BUILD}  {url}")
    print(f"kit {KIT_ROOT}")
    print(f"signature Δ9Φ963-LYGO-LLM-CONSOLE-v1  physics={PHYSICS_AVAILABLE}  bind={BIND}")

    def warmup() -> None:
      try:
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
            print("scanning models…")
            scanned = scan_roots(default_scan_roots(cfg))
            data = reg_upsert(scanned.get("models") or [])
            STATE["selected"] = data.get("selected")
            STATE["scan_n"] = len(data.get("models") or [])
            print(f"scan models={STATE['scan_n']} truncated={scanned.get('scan_truncated')} selected={STATE.get('selected')}")
        if not MOCK_ONLY and STATE.get("selected"):
            print(f"booting {STATE.get('selected')} …")
            boot_async(str(STATE.get("selected")))
      except Exception as e:
        STATE["brain"] = "error"
        STATE["error"] = f"warmup:{e}"
        print("warmup failed", e)

    def watchdog() -> None:
        from engine import runner_for

        while True:
            time.sleep(20)
            try:
                r = runner_for(LLAMA_PORT)
                if STATE.get("brain") == "ready" and r and r.proc.poll() is not None:
                    STATE["brain"] = "missing"
                    STATE["error"] = "llama_exited"
                    sel = STATE.get("selected")
                    if sel:
                        boot_async(str(sel))
            except Exception:
                pass

    threading.Thread(target=warmup, daemon=True, name="lygo-warmup").start()
    threading.Thread(target=watchdog, daemon=True, name="lygo-watchdog").start()
    if not args.no_browser:
        def open_when_ready() -> None:
            for _ in range(40):
                if STATE.get("scan_n"):
                    break
                time.sleep(0.25)
            time.sleep(0.3)
            try:
                webbrowser.open(url)
            except Exception:
                pass

        threading.Thread(target=open_when_ready, daemon=True, name="lygo-browser").start()
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
