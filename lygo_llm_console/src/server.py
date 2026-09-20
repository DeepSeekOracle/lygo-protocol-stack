from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import sys as _sys

# A stick console is often cp437: a print() of a non-ASCII line (the Delta9Phi963 signature,
# a model answer) must degrade, never raise.
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:  # noqa: BLE001 - not a real console (pipe, IDE, pytest capture)
        pass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# kit src on path
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:  # the module layer must never be able to cost the operator the console (WO-0001)
    from modules import host as module_host  # noqa: E402
except Exception as _module_err:  # noqa: BLE001
    module_host = None
    print(f"[modules] module layer unavailable: {type(_module_err).__name__}: {_module_err}", flush=True)

import version  # noqa: E402  (the release number lives in VERSION - see src/version.py)
from atomicio import atomic_write_text  # noqa: E402
from atomicio import read_text as read_text_locked  # noqa: E402
from auth import check, ensure_llama_key, ensure_token, token_from_request  # noqa: E402
from chat_loop import (  # noqa: E402
    extract_user_text,
    has_image,
    host_prefetch,
    normalise_messages,
    prefetch_message,
    run_tools_round,
    trim_history,
    user_text_of,
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
try:  # the record module must never be able to cost the operator the console
    import compaction  # noqa: E402
    from compaction import (  # noqa: E402
        carry_over,
        live_ctx,
        safe_pre_turn,
        safe_record,
        safe_status,
        trim_messages,
    )

    COMPACTION_AVAILABLE = True
    COMPACTION_ERROR = ""
except Exception as _compact_err:  # noqa: BLE001  (a broken record module, not a broken console)
    import traceback as _tb

    COMPACTION_AVAILABLE = False
    COMPACTION_ERROR = f"{type(_compact_err).__name__}: {_compact_err}"
    _tb.print_exc()

    class _NoRecord:
        """Every read answers honestly instead of raising, so the routes stay 200 and say why."""

        BUILD_TAG = "unavailable"
        RECALL_K = 6
        ARCHIVE = INDEX = SESSIONS = ROLLUPS = CHECKPOINTS = None  # type: ignore[assignment]
        CARRY_CAP = 0

        def __getattr__(self, name: str):
            def _missing(*a, **k):
                return {"ok": False, "error": "compaction_unavailable", "detail": COMPACTION_ERROR}

            return _missing

    compaction = _NoRecord()  # type: ignore[assignment]

    def live_ctx() -> int:  # noqa: D103
        try:
            from paths import console_limits

            return int(console_limits().get("ctx_max") or 8192)
        except Exception:  # noqa: BLE001
            return 8192

    def carry_over(cap: int = 0) -> str:  # noqa: D103
        return ""

    def _no_record(*a, **k) -> dict:
        return {"ok": False, "error": "compaction_unavailable", "detail": COMPACTION_ERROR}

    safe_pre_turn = safe_record = safe_status = _no_record  # type: ignore[assignment]

    def trim_messages(messages: list, ctx: int | None = None, keep_turns: int | None = None):
        """Fall back to the console's own message window - the behaviour before the record existed."""
        kept = trim_history(messages)
        return kept, max(0, len(messages) - len(kept)), {"ok": False, "fallback": "trim_history"}
try:  # the vault is a second, independent subsystem: its absence must not cost the console either
    import sessions  # noqa: E402
    from sessions import (  # noqa: E402
        safe_catalog,
        safe_open,
        safe_resume,
        safe_search,
        safe_stats,
        safe_vault_live,
    )

    SESSIONS_AVAILABLE = True
    SESSIONS_ERROR = ""
except Exception as _sessions_err:  # noqa: BLE001  (a broken vault module, not a broken console)
    SESSIONS_AVAILABLE = False
    SESSIONS_ERROR = f"{type(_sessions_err).__name__}: {_sessions_err}"

    class _NoVault:
        """Every session read answers honestly instead of raising."""

        BUILD_TAG = "unavailable"

        def __getattr__(self, name: str):
            def _missing(*a, **k):
                return {"ok": False, "error": "sessions_unavailable", "detail": SESSIONS_ERROR}

            return _missing

    sessions = _NoVault()  # type: ignore[assignment]

    def _no_vault(*a, **k) -> dict:
        return {"ok": False, "error": "sessions_unavailable", "detail": SESSIONS_ERROR}

    safe_catalog = safe_open = safe_resume = safe_search = safe_stats = safe_vault_live = _no_vault  # type: ignore[assignment]
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
from receipts import prune_at_startup, write_receipt  # noqa: E402
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
# The release number lives in ONE file (VERSION); see src/version.py for why. A bump there
# moves the header, this health line and the runtime facts together.
BUILD = version.stamp()
STATE: dict[str, Any] = {"brain": "missing", "selected": None, "error": None, "scan_n": 0, "engine": "llama", "engine_port": LLAMA_PORT}


def brain_port() -> int:
    return int(STATE.get("engine_port") or LLAMA_PORT)


# A peer that opens a socket and stalls must not hold a handler thread until it decides to close.
try:
    REQUEST_TIMEOUT = float(os.environ.get("LYGO_REQUEST_TIMEOUT", "120"))
except ValueError:
    REQUEST_TIMEOUT = 120.0

# host_prefetch fetches URLs out of the user's text before the model answers. On by default, but
# switchable: a fetched page is untrusted input landing beside the shell and python limbs.
HOST_PREFETCH = os.environ.get("LYGO_HOST_PREFETCH", "1").strip().lower() not in ("0", "false", "no")


class _BadRequest(Exception):
    """A malformed request envelope (Content-Length, transfer encoding) -> 400, not a 500."""


class _BodyTooLarge(Exception):
    """Request body over the endpoint's limit: answers 413 instead of a misleading 400."""


# A half-written or hand-edited console.json used to raise out of load_console(): startup
# aborted before the server existed and every endpoint that reads the config answered 500.
# Bad config now costs the operator the config, never the console, and the reason is reported
# through /api/health instead of vanishing into a stderr traceback.
CONFIG_ERRORS: list[str] = []
_CONFIG_CACHE: dict[str, Any] = {"key": None, "cfg": {}}


def _note_config_error(msg: str) -> None:
    if msg not in CONFIG_ERRORS:
        CONFIG_ERRORS.append(msg)
    del CONFIG_ERRORS[5:]


def _config_key() -> tuple[Any, ...] | None:
    try:
        return tuple(
            (p.stat().st_mtime_ns, p.stat().st_size) if p.is_file() else None
            for p in (CONSOLE_JSON, LOCAL_JSON)
        )
    except OSError:
        return None


def load_console() -> dict[str, Any]:
    """config/console.json, optionally overlaid by config/local.json.

    Parsed once per file state: every POST used to re-read and re-parse both files.
    """
    key = _config_key()
    if key is not None and _CONFIG_CACHE.get("key") == key:
        return dict(_CONFIG_CACHE["cfg"])
    cfg: dict[str, Any] = {}
    for path in (CONSOLE_JSON, LOCAL_JSON):
        if not path.is_file():
            continue
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 - a broken config must not kill the console
            _note_config_error(f"{path.name}: {type(e).__name__}: {e}"[:200])
            continue
        if isinstance(loaded, dict):
            cfg = {**cfg, **loaded}
        else:
            _note_config_error(f"{path.name}: not a JSON object")
    if key is not None:
        _CONFIG_CACHE.update(key=key, cfg=cfg)
    return dict(cfg)


def default_scan_roots(cfg: dict[str, Any]) -> list[str]:
    raw = cfg.get("scan_roots")
    if not isinstance(raw, list) or not raw:
        raw = ["./models"]
    out: list[str] = []
    for r in raw:
        s = os.path.expandvars(os.path.expanduser(str(r)))
        p = Path(s)
        if not p.is_absolute():
            p = (KIT_ROOT / s).resolve()
        out.append(str(p))
    # No implicit %USERPROFILE%\.ollama\models any more: this kit boots its own engine on its own
    # GGUF vault, so an Ollama folder is only ever read when the operator maps it on purpose (the
    # one-time read-only import in src/ollama_import.py). Requiring it would be a dependency; a
    # dependency is the difference between a walking agent and an empty shell when it is absent.
    # Declared roots first, kit-relative second, raw drive letters last: a kit packaged onto
    # another drive must find its own models without a stale letter being the only candidate.
    extras = [KIT_ROOT / "models"]
    for env_name in ("LYGO_STACK_ROOT", "LYGO_BUILDER_KEY_ROOT"):
        declared = os.environ.get(env_name, "").strip()
        if declared:
            base = Path(os.path.expandvars(declared))
            extras.extend([base / "models", base / "product" / "models" / "ollama"])
    extras.extend(
        [
            Path(r"I:\LYGO_MODELS"),
            Path(r"U:\LYGO\models"),
            Path(r"F:\LYGO\models"),
            Path(r"E:\LYGO_BUILDER_KEY\product\models\ollama"),
        ]
    )
    usb = os.environ.get("LYGO_USB_ROOT", "").strip()
    if usb:
        extras.append(Path(usb) / "product" / "models" / "ollama")
        extras.append(Path(usb) / "models")
    # LYGO_MODELS is the kit's own declaration of its model vault (the launchers set it; a machine
    # can set it too). OLLAMA_MODELS is tolerated because launchers written before the vault existed
    # used it to point at their own folder - it is still only ever read as files, never executed.
    for env_name in ("LYGO_MODELS", "OLLAMA_MODELS"):
        declared = os.environ.get(env_name, "").strip()
        if declared:
            extras.append(Path(os.path.expandvars(declared)))
    # A CAS is a folder holding manifests/ + blobs/, and it usually sits one level down
    # (<usb>\models\ollama), so descend from the declared parents too.
    for parent in list(extras):
        child = parent / "ollama"
        if (child / "manifests").is_dir() and (child / "blobs").is_dir():
            extras.append(child)
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


def _next_model_rec(models: list[dict[str, Any]], exclude: list[str]) -> dict[str, Any] | None:
    """Next brain to try after one failed to load here: registry order, minus what we tried."""
    try:
        import registry as _reg

        for mid in _reg.candidates(models, prefer_ram=_reg.prefer_by_ram()):
            if mid in exclude:
                continue
            rec = next((m for m in models if m.get("id") == mid), None)
            if rec and rec.get("runnable") and rec.get("path"):
                return rec
    except Exception:  # noqa: BLE001 - the fallback picker must never be what fails
        return None
    return None


VISION_BLIND_NOTE = (
    "\u26a0 the picture attached to this message was not looked at: {model} has no vision projector on "
    "this machine, so only your text was read. Attach the picture with the FILE button to keep it in the "
    "workspace, or boot a model with vision."
)


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
    # A record can name a file this machine does not have - the stick's registry was measured carrying
    # eight such records, its only vision model among them. Failing here, naming the path it wanted, is
    # answerable; the engine's own "failed to load model" inside a log tail is not.
    from registry import reach as _reach

    _where = _reach(rec)
    if not _where["reachable"]:
        STATE["brain"] = "error"
        STATE["error"] = "model_not_on_this_machine: %s - %s" % (rec.get("id"), _where["why"])
        return "error"
    from lygo_engine import boot as lygo_boot

    # A model whose header parses but which this engine cannot actually load (wrong tensor
    # offsets, unsupported quant, half-copied file) used to be fatal: brain=error and a dark
    # console. Remember the verdict for THIS host and boot the next-best brain instead.
    tried: list[str] = []
    last_err = ""
    for attempt in range(3):
        try:
            if attempt == 0:
                STATE.pop("model_fallback", None)
            return lygo_boot(rec, api_key=LLAMA_KEY, state=STATE)
        except MemoryError as e:
            STATE["brain"] = "ram_refused"
            STATE["error"] = str(e)
            return "ram_refused"
        except Exception as e:  # noqa: BLE001 - never let one bad file take the console down
            last_err = f"{type(e).__name__}: {e}"
            mid = str(rec.get("id") or "")
            if mid:
                tried.append(mid)
            try:
                import model_verdicts

                model_verdicts.mark_bad(mid, str(rec.get("path") or ""), last_err)
            except Exception:  # noqa: BLE001
                pass
            nxt = _next_model_rec(reg_load().get("models") or [], exclude=tried)
            if not nxt:
                break
            rec = nxt
            STATE["model_fallback"] = (
                f"{tried[-1]} could not load here ({last_err}); trying {rec.get('id')}"
            )
    STATE["brain"] = "error"
    STATE["error"] = last_err
    return "error"


def local_system_message(brain: str = "local") -> dict[str, Any]:
    """The system message every local turn opens with - built in ONE place.

    The prefix primer below has to send the identical opening, so both callers come through here. If
    they ever drift apart the primer silently stops helping, which is the kind of defect that looks
    like "the engine got slow again" months later.
    """
    from continuity import compose_system

    return {"role": "system", "content": compose_system(brain)}


def warm_prefix(model_id: str | None = None) -> None:
    """Put the fixed opening of a local turn into the engine's prompt cache after a boot.

    A local turn sends local_system_message() + history + core_schema(). The fixed part is large: on
    this class of machine prefilling it costs ~40 s at ~130 tokens/s, and llama-server streams nothing
    until prefill finishes - so the operator's first ask after pressing Boot looked like a dead engine
    and the portal stopped the answer after 60 s of silence. One 1-token completion with the identical
    opening, sent as soon as the engine reports ready, makes that first real ask cost seconds instead
    of a minute.

    This is an optimisation and never a reason for a turn to fail: it takes no engine lock (a request
    that arrives while it runs simply queues behind it, exactly as it would have anyway) and any error
    is logged and dropped.
    """
    if MOCK_ONLY or STATE.get("brain") != "ready":
        return
    model = str(model_id or STATE.get("selected") or "")
    if not model or STATE.get("prefix_primed_for") == model:
        return

    def _run() -> None:
        try:
            from openai_proxy import llama_chat
            from tools import core_schema

            from openai_proxy import for_local_engine

            payload = for_local_engine({
                "model": model,
                "messages": [local_system_message("local"), {"role": "user", "content": "ready"}],
                "max_tokens": 1,
                "stream": False,
                "tools": core_schema(),
            })
            t0 = time.time()
            code, _body, _ = llama_chat(api_key=LLAMA_KEY, payload=payload, port=brain_port(), timeout=900.0)
            if STATE.get("brain") == "ready" and STATE.get("selected") == model:
                STATE["prefix_primed_for"] = model
            print(f"prefix primed for {model} in {time.time() - t0:.1f}s (code {code})")
        except Exception as e:  # noqa: BLE001 - an optimisation may never break a turn
            print(f"prefix prime skipped: {type(e).__name__}: {e}")

    threading.Thread(target=_run, daemon=True, name="lygo-prefix").start()


def boot_async(model_id: str | None) -> None:
    STATE["brain"] = "booting"
    STATE["error"] = None

    def _run() -> None:
        try:
            status = maybe_spawn(model_id)
            if status == "ready":
                warm_prefix(model_id)
        except Exception as e:
            STATE["brain"] = "error"
            STATE["error"] = str(e)

    threading.Thread(target=_run, daemon=True, name="lygo-llm-boot").start()


GATE_CHUNK = 8000


def gate_all(text: str) -> dict[str, Any]:
    """Gate the WHOLE text, not just its head.

    soul / identity / memory accept up to 90 KB but were only scanned as text[:8000]; anything
    appended past the first chunk reached disk unscanned. Every chunk is judged now, and the
    first QUARANTINE verdict wins.
    """
    if len(text) <= GATE_CHUNK:
        return gate_prompt(text)
    head: dict[str, Any] = {}
    for i in range(0, len(text), GATE_CHUNK):
        verdict = gate_prompt(text[i : i + GATE_CHUNK])
        if verdict.get("verdict") == "QUARANTINE":
            return verdict
        head = head or verdict
    return head


def _read_text_locked(path: Any, limit: int = 80_000) -> str:
    """Read a state file through the retrying reader - a writer may be mid-swap right now."""
    p = Path(path)
    if not p.is_file():
        return ""
    try:
        return read_text_locked(p, errors="replace")[:limit]
    except OSError:
        return ""


class Handler(BaseHTTPRequestHandler):
    # StreamRequestHandler applies this to the socket, so one stalled peer cannot pin a thread.
    timeout = REQUEST_TIMEOUT
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
        """Is this request from this machine? Judged on the socket, never on the Host header.

        Trusting Host let any LAN client send "Host: localhost" and collect the loopback
        shortcut - and with the token spliced into the page it fetched, that was a full
        bypass of the token layer. A local reverse proxy does rewrite Host, so that case is
        explicit opt-in instead of a default.
        """
        ip = ((self.client_address or ("", 0))[0] or "").lower().replace("::ffff:", "")
        if ip in ("127.0.0.1", "::1", "localhost"):
            return True
        if os.environ.get("LYGO_TRUSTED_PROXY", "").strip().lower() not in ("1", "true", "yes"):
            return False
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
        path = urlparse(self.path).path
        # The portal shell and the health bar stay reachable without a token - that is how a
        # remote operator gets in. Everything else needs one, and the shell hands the token out
        # only to a loopback caller (see _dispatch_GET).
        if path in ("/", "/api/health", "/api/world") or path.startswith("/static/"):
            return True
        return check(token_from_request(self._headers_map(), self._query()), TOKEN)

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
        """Read the body, refusing a malformed or oversized Content-Length.

        Three ways this went wrong: `Content-Length: -1` reached rfile.read(-1), which reads until
        the peer closes, so a loop of such requests wedged a handler thread each; a non-numeric
        length raised ValueError out of the handler as a 500; and an over-limit body was emptied,
        which made the endpoint report 400 no_input for a payload that was merely large.
        """
        raw_len = (self.headers.get("Content-Length") or "0").strip()
        try:
            n = int(raw_len)
        except ValueError:
            raise _BadRequest(f"Content-Length: {raw_len[:32]!r}") from None
        if n < 0:
            raise _BadRequest(f"Content-Length: {n}")
        if n > limit:
            raise _BodyTooLarge(f"{n} > {limit}")
        return self.rfile.read(n) if n else b""

    def _contain(self, exc: BaseException) -> None:
        """Answer 500 instead of dropping the connection when a handler raises."""
        try:
            # Detail carries absolute paths and internals: right for the operator on this
            # machine, not for whoever else can reach a LAN-bound console.
            detail = f"{type(exc).__name__}: {exc}"[:300] if self._loopback() else type(exc).__name__
        except Exception:  # noqa: BLE001
            detail = "unprintable_error"
        try:
            self._json(500, {"error": "handler_failed", "detail": detail})
        except Exception:  # noqa: BLE001 - the socket may already be gone
            pass

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._dispatch_GET()
        except _BodyTooLarge as exc:
            # The body is deliberately left unread; this answer closes the connection.
            self.close_connection = True
            self._json(413, {"error": "too_large", "limit": str(exc)[:60]})
        except _BadRequest as exc:
            self.close_connection = True
            self._json(400, {"error": "bad_request", "detail": str(exc)[:60]})
        except Exception as exc:  # noqa: BLE001 - one bad request must not end the console
            self._contain(exc)

    def _dispatch_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        # One gate, not two: _auth() already exempts the shell, its assets, the health bar and the
        # world clock. This used to re-implement the same check with a slightly different list, so
        # the two could disagree about what was public. Behaviour is unchanged.
        if not self._auth():
            self._json(401, {"error": "unauthorized"})
            return
        # --- LYGO module host (Δ9Φ963-LYGO-MODULE-CORE-v1) ---------------------------------------
        # Modules own the routes they declare in their own module.json. The kernel routes below are
        # untouched: if the host answers the request this returns, if it does not, nothing changed.
        if module_host is not None and module_host.handle(self, "GET", path):
            return
        if path == "/" or path == "/index.html":
            html = (PORTAL / "index.html").read_text(encoding="utf-8")
            css = (PORTAL / "style.css").read_text(encoding="utf-8")
            js = (PORTAL / "app.js").read_text(encoding="utf-8")

            def _splice(src: str, pattern: str, block: str) -> str:
                m = re.search(pattern, src)
                if not m:
                    return src
                return src[: m.start()] + block + src[m.end() :]

            html = _splice(html, r'<link rel="stylesheet" href="/static/style\.css[^"]*">', "<style>\n" + css + "\n</style>")
            html = _splice(html, r'<script src="/static/app\.js[^"]*"></script>', "<script>\n" + js + "\n</script>")
            # The portal needs the token to talk to its own console, but this page is served
            # WITHOUT one. Hand the real token only to a loopback caller: a LAN client used to
            # fetch "/" and be handed the secret in the page source.
            html = html.replace("/*LYGO_TOKEN*/", json.dumps(TOKEN if self._loopback() else ""))
            _sys = __import__("surface").report(local_ready=(STATE.get("brain") == "ready"))
            html = html.replace("/*LYGO_SYSTEM*/", _sys["label"])
            extra: dict[str, str] = {}
            if AUTH_REQUIRED and check(token_from_request(self._headers_map(), self._query()), TOKEN):
                # The operator has already proven the token: keep it in a SameSite cookie so the
                # URL, the browser history and the printed launcher line need not carry it again.
                extra["Set-Cookie"] = f"lygo_token={TOKEN}; Path=/; SameSite=Strict; Max-Age=43200"
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8", extra or None)
            return
        if path.startswith("/static/"):
            name = path[len("/static/") :].split("?")[0]
            if "/" in name or "\\" in name or not name:
                self._json(404, {"error": "missing"})
                return
            if name.lower().endswith((".html", ".htm")):
                # The only HTML this console serves is the one document assembled at "/" with the
                # token, system label and assets spliced in. Served raw, the template's
                # `window.LYGO_TOKEN = /*LYGO_TOKEN*/;` is a SyntaxError and the page dies silent.
                self._json(404, {"error": "use_shell_route"})
                return
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

            local_caller = self._loopback()
            self._json(
                200,
                {
                    "ok": True,
                    "build": BUILD,
            "release": version.release(),
            "release_tag": version.tag(),
                    "signature": "Δ9Φ963-LYGO-LLM-CONSOLE-v1",
                    "authenticated": check(token_from_request(self._headers_map(), self._query()), TOKEN),
                    "physics": PHYSICS_AVAILABLE,
                    "brain": STATE.get("brain"),
                    "selected": STATE.get("selected") or reg_load().get("selected"),
                    "vision": __import__("registry").selected_vision(),
                    "error": STATE.get("error"),
                    "model_fallback": STATE.get("model_fallback"),
                    "scan_n": STATE.get("scan_n") or len(reg_load().get("models") or []),
                    "ollama_port_open": ollama_port_open(),
                    "engine_present": bool(resolve_binary()),
                    "engine_dir": str(__import__("paths").engine_dir()) if local_caller else Path(__import__("paths").engine_dir()).name,
                    "backend_layer": __import__("backends").report(),
                    "system": __import__("surface").report(local_ready=(STATE.get("brain") == "ready")),
                    "ram_avail": available_ram_bytes(),
                    "ram_auto": __import__("registry").prefer_by_ram(),
                    "ram_fit": __import__("registry").ram_choice(
                        reg_load().get("models") or [], available_ram_bytes()
                    ),
                    "perf": __import__("perf").report(STATE),
                    "selected_source": reg_load().get("selected_source"),
                    "bind": BIND,
                    "port": DEFAULT_PORT,
                    "tools": [t["function"]["name"] for t in TOOLS_SCHEMA],
                    "workspace": str(WORKSPACE) if local_caller else WORKSPACE.name,
                    "config_errors": CONFIG_ERRORS,
                    "cloud": __import__("cloud_api").public_status(),
                    "last_brain": STATE.get("last_brain"),
                    "last_perf": STATE.get("last_perf"),
                    "fallback": STATE.get("fallback"),
                    },
            )
            return
        if path == "/api/cloud":
            if not self._auth():
                self._json(401, {"error": "unauthorized"})
                return
            self._json(200, __import__("cloud_api").public_status())
            return
        if path == "/api/models" or path == "/v1/models":
            if not self._auth():
                self._json(401, {"error": "unauthorized"})
                return
            data = reg_load()
            # Hand back what each record IS on this machine, not just what it claims: reachable (the
            # files are here) and portable (they sit in storage this kit carries). Without this the
            # stick advertises models that live on the PC it was built on.
            from registry import reach as _reach

            data = {
                **data,
                "models": [{**m, "reach": _reach(m)} for m in data.get("models") or []],
            }
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
            total = 0
            if root.is_dir():
                kids = list(root.iterdir())
                total = len(kids)
                for child in kids[:120]:
                    ents.append({"name": child.name, "dir": child.is_dir(), "path": str(child)})
            mounts = list_mounts()
            # The 120-entry cap was silent: a large folder looked complete and an unreadable one
            # looked empty. Report the true count and whether it was cut.
            self._json(200, {"ok": True, "path": str(root), "entries": ents, "total": total, "truncated": total > len(ents), "limit": 120, "mounts": mounts.get("mounts"), "n_live": mounts.get("n_live")})
            return
        if path == "/api/memory":
            mem = WORKSPACE / "memory.jsonl"
            lines = []
            if mem.is_file():
                lines = mem.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:]
            mp = memory_path()
            md = _read_text_locked(mp)
            self._json(200, {"ok": True, "notes": lines, "memory_md": md, "path": str(mp)})
            return
        if path == "/api/soul":
            p = soul_path()
            t = _read_text_locked(p)
            self._json(200, {"ok": True, "path": str(p), "text": t})
            return
        if path == "/api/identity":
            p = identity_path()
            t = _read_text_locked(p)
            self._json(200, {"ok": True, "path": str(p), "text": t})
            return
        if path == "/api/session":
            self._json(200, {"messages": load_session()})
            return
        if path == "/api/sessions":
            # The vault, read-only: ?stats=1 for the summary, ?sid=… to read one session back,
            # ?search=1&q=… to find one, otherwise the catalog.
            qs = parse_qs(urlparse(self.path).query)
            sid = (qs.get("sid") or [""])[0].strip()
            if sid:
                self._json(200, safe_open(sid, int((qs.get("chars") or ["24000"])[0] or 24000)))
                return
            if (qs.get("stats") or [""])[0].strip() in {"1", "true", "yes"}:
                self._json(200, safe_stats())
                return
            q = (qs.get("q") or [""])[0].strip()
            # `q` alone FILTERS the catalog (titles, ids, tags, notes) - that is what the panel's
            # Find box means. Reading inside the transcripts is the heavier search: ask for it.
            if q and (qs.get("search") or [""])[0].strip() in {"1", "true", "yes"}:
                self._json(200, safe_search(q, int((qs.get("k") or ["8"])[0] or 8)))
                return
            self._json(200, safe_catalog(
                int((qs.get("limit") or ["200"])[0] or 200),
                q,
                (qs.get("tag") or [""])[0].strip(),
                (qs.get("month") or [""])[0].strip(),
            ))
            return
        if path == "/api/compaction":
            # The live window report: what the engine will actually see this turn, how full it is,
            # and what has been folded/sealed behind it.
            self._json(200, safe_status(live_ctx()))
            return
        if path == "/api/archive":
            qs = parse_qs(urlparse(self.path).query)
            sid = (qs.get("sid") or [""])[0].strip()
            if sid:
                self._json(200, compaction.read_transcript(sid))
                return
            self._json(
                200,
                {
                    "ok": True,
                    "sessions": compaction.index_entries(limit=500),
                    "archive": str(compaction.ARCHIVE),
                    "index": str(compaction.INDEX),
                    "bytes": compaction._dir_bytes(compaction.ARCHIVE),
                },
            )
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

    def do_OPTIONS(self) -> None:  # noqa: N802
        """Answer a capability probe - until now OPTIONS fell through to the stdlib's 501 page.

        `BaseHTTPRequestHandler` has no `do_OPTIONS`, so every OPTIONS request was answered 501
        ("Unsupported method") with an HTML error page. Wrong twice: 501 means the server does not
        implement the method at all, and this console's API never answers HTML - a client parsing
        JSON got a page of markup. The answer carries no CORS headers, on purpose: the console is
        loopback-bound and token-gated, and an Access-Control-Allow-Origin here would let any page
        the operator visits read their local console. The public web edition keeps its own
        allowlist (see `public_gateway._cors_ok`).
        """
        path = urlparse(self.path).path
        served = (path in ("/", "/index.html") or path.startswith("/static/")
                  or path.startswith("/api/") or path.startswith("/v1/"))
        if not served:
            self._json(404, {"error": "not_found"})
            return
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._dispatch_POST()
        except _BodyTooLarge as exc:
            # The body is deliberately left unread; this answer closes the connection.
            self.close_connection = True
            self._json(413, {"error": "too_large", "limit": str(exc)[:60]})
        except _BadRequest as exc:
            self.close_connection = True
            self._json(400, {"error": "bad_request", "detail": str(exc)[:60]})
        except Exception as exc:  # noqa: BLE001 - one bad request must not end the console
            self._contain(exc)

    def _dispatch_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._auth():
            self._json(401, {"error": "unauthorized"})
            return
        # --- LYGO module host (Δ9Φ963-LYGO-MODULE-CORE-v1) ---------------------------------------
        if module_host is not None and module_host.handle(self, "POST", path):
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
            # An explicit switch is a human decision: pin it so the RAM-auto brain stops re-picking.
            data["selected_source"] = "manual" if obj.get("id") else data.get("selected_source", "auto")
            from registry import save as reg_save

            reg_save(data)
            STATE["selected"] = mid
            boot_async(mid)
            self._json(200, {"ok": True, "brain": STATE.get("brain"), "selected": mid, "error": STATE.get("error")})
            return
        if path == "/api/cloud":
            body = self._read_body(16_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            from cloud_api import save as cloud_save

            self._json(200, cloud_save(obj if isinstance(obj, dict) else {}))
            return
        if path == "/api/brain":
            # one clear switch: local (default, always complete) <-> api (cloud, engine as safety net)
            if not self._auth():
                self._json(401, {"error": "unauthorized"})
                return
            body = self._read_body(16_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            if not isinstance(obj, dict):
                obj = {}
            want = str(obj.get("mode") or "").strip().lower()
            if want not in ("local", "api"):
                self._json(400, {"error": "mode_must_be_local_or_api", "got": want})
                return
            import cloud_api

            if want == "api":
                patch: dict[str, Any] = {"enabled": True, "clear_error": True}
                for k in ("provider", "model", "url", "key"):
                    if obj.get(k):
                        patch[k] = obj[k]
                if isinstance(obj.get("keys"), dict):
                    # second (and further) provider keys: {"gemini": "AIza..."} wires the backup
                    patch["keys"] = obj["keys"]
                if isinstance(obj.get("fallbacks"), list):
                    patch["fallbacks"] = obj["fallbacks"]
                st = cloud_api.public_status()
                if not st.get("has_key") and not patch.get("key"):
                    self._json(
                        409,
                        {
                            "error": "no_api_key",
                            "hint": "paste the key in the API row then Save key (or send key with this call)",
                            "cloud": st,
                        },
                    )
                    return
                cloud_api.save(patch)
                # the API is an option — keep the local engine booted as the safety net
                if not MOCK_ONLY and STATE.get("brain") != "ready":
                    sel = STATE.get("selected") or reg_load().get("selected")
                    if sel:
                        boot_async(str(sel))
            else:
                cloud_api.save({"enabled": False})
            st = cloud_api.public_status()
            self._json(
                200,
                {
                    "ok": True,
                    "mode": st.get("mode"),
                    "brain": STATE.get("brain"),
                    "selected": STATE.get("selected"),
                    "cloud": st,
                },
            )
            return
        if path == "/api/session":
            body = self._read_body(512_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            if obj.get("new"):
                new_session()
                # Where did the conversation that just ended go? Say it, instead of leaving the
                # operator to wonder whether pressing the button threw their chat away.
                filed = {}
                try:
                    filed = (compaction._load_state() or {}).get("last_vault") or {}
                except Exception:  # noqa: BLE001
                    filed = {}
                self._json(200, {"ok": True, "messages": [], "vault": filed})
                return
            msgs = obj.get("messages")
            if isinstance(msgs, list):
                save_session(msgs)
            self._json(200, {"ok": True, "messages": load_session()})
            return
        if path == "/api/sessions":
            # One route for the operator's Sessions panel and for the agent's own session limbs.
            body = self._read_body(512_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            action = str(obj.get("action") or "catalog").lower()
            if action == "catalog":
                self._json(200, safe_catalog(
                    int(obj.get("limit") or 200), str(obj.get("q") or ""),
                    str(obj.get("tag") or ""), str(obj.get("month") or "")))
                return
            if action == "stats":
                self._json(200, safe_stats())
                return
            if action == "open":
                self._json(200, safe_open(str(obj.get("sid") or ""), int(obj.get("chars") or 24000)))
                return
            if action == "vault":
                title = str(obj.get("title") or "").strip() or None
                sid = str(obj.get("sid") or "").strip() or None
                self._json(200, sessions.safe_vault(sid, title, "manual"))
                return
            if action in {"vault_live", "file"}:
                # File the conversation in progress without ending it - the manual save button.
                self._json(200, safe_vault_live("manual"))
                return
            if action == "adopt":
                self._json(200, sessions.safe_adopt(int(obj.get("limit") or 300)))
                return
            if action == "label":
                kw: dict = {}
                if obj.get("title") is not None:
                    kw["title"] = str(obj["title"])
                if obj.get("note") is not None:
                    kw["note"] = str(obj["note"])
                if obj.get("tags") is not None:
                    tags = obj["tags"]
                    kw["tags"] = (tags if isinstance(tags, list)
                                  else [p.strip() for p in str(tags).split(",") if p.strip()])
                if obj.get("pinned") is not None:
                    kw["pinned"] = bool(obj["pinned"])
                self._json(200, sessions.safe_label(str(obj.get("sid") or ""), **kw))
                return
            if action == "search":
                self._json(200, safe_search(str(obj.get("q") or ""), int(obj.get("k") or 8)))
                return
            if action == "resume":
                self._json(200, safe_resume(str(obj.get("sid") or ""), bool(obj.get("file_current", True))))
                return
            if action == "rebuild":
                self._json(200, sessions.safe_rebuild())
                return
            if action == "transcript":
                info = sessions.find_session(str(obj.get("sid") or ""))
                self._json(200, info or {"ok": False, "error": "not_found"})
                return
            self._json(400, {"ok": False, "error": "bad_action", "action": action,
                             "actions": ["catalog", "stats", "open", "vault", "vault_live", "adopt",
                                         "label", "search", "resume", "rebuild", "transcript"]})
            return
        if path == "/api/compaction":
            # One route, one switch: the portal's Save & Compact button, the auto-trigger, the
            # archive browser and the model's own recall limb all come through here.
            body = self._read_body(512_000)
            try:
                obj = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                obj = {}
            action = str(obj.get("action") or "status").lower()
            msgs = obj.get("messages") if isinstance(obj.get("messages"), list) else None
            if action == "status":
                self._json(200, safe_status(live_ctx(), msgs))
                return
            if action in {"save", "autosave"}:
                self._json(200, compaction.save_now("button" if action == "save" else "autosave"))
                return
            if action == "compact":
                out = compaction.compact(reason="manual", keep_turns=obj.get("keep_turns"))
                out["status"] = safe_status(live_ctx(), msgs)
                self._json(200, out)
                return
            if action in {"roll", "seal"}:
                out = compaction.seal(reason="manual")
                out["status"] = safe_status(live_ctx())
                self._json(200, out)
                return
            if action == "recall":
                q = str(obj.get("q") or obj.get("query") or "")
                if gate_prompt(q).get("verdict") == "QUARANTINE":
                    self._json(451, {"ok": False, "error": "quarantine"})
                    return
                out = compaction.recall(q, k=int(obj.get("k") or compaction.RECALL_K))
                out["text"] = compaction.recall_text(q, k=int(obj.get("k") or 3))
                self._json(200, out)
                return
            if action == "index":
                self._json(
                    200,
                    {
                        "ok": True,
                        "sessions": compaction.index_entries(limit=500),
                        "archive": str(compaction.ARCHIVE),
                        "bytes": compaction._dir_bytes(compaction.ARCHIVE),
                    },
                )
                return
            if action == "transcript":
                self._json(200, compaction.read_transcript(str(obj.get("sid") or "")))
                return
            if action == "bundle":
                self._json(200, compaction.bundle_archives(int(obj.get("older_than_days") or 30)))
                return
            self._json(400, {"ok": False, "error": "bad_action", "action": action,
                             "actions": ["status", "save", "compact", "roll", "recall", "index", "transcript", "bundle"]})
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
            if gate_all(text).get("verdict") == "QUARANTINE":
                self._json(451, {"ok": False, "error": "p0_blocked"})
                return
            p = soul_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(p, text)
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
            if gate_all(text).get("verdict") == "QUARANTINE":
                self._json(451, {"ok": False, "error": "p0_blocked"})
                return
            p = identity_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(p, text)
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
            if gate_all(text).get("verdict") == "QUARANTINE":
                self._json(451, {"ok": False, "error": "p0_blocked"})
                return
            p = memory_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(p, text)
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
            if not (obj.get("id") or obj.get("text") or obj.get("content") or obj.get("title")):
                # A junk or empty body used to reach write_note(None, "", "") and mint a phantom
                # empty note, answered {"ok": true, ...} - a write the caller never asked for.
                self._json(400, {"error": "nothing_to_save",
                                 "hint": 'send {"id": "..."} or {"text": "..."}, or action:"new"'})
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
        if path == "/api/upload":
            self._api_upload()
            return
        self._json(404, {"error": "not_found"})

    def _api_upload(self) -> None:
        """Put an attached file where the agent's own limbs can read it.

        The portal cannot hand the engine an arbitrary path on the operator's disk, and the engine only
        ever sees the messages. So anything the browser cannot inline as text is written under
        workspace/uploads/ - a root read_file, list_dir and search_corpus already cover - and the chat
        message then carries that path with the instruction to open it. Refusing a file with no home is
        why a picked file used to go nowhere.
        """
        raw = self._read_body(32 * 1024 * 1024)
        if not raw:
            self._json(400, {"error": "empty", "detail": "no bytes in the body"})
            return
        from urllib.parse import unquote

        from paths import WORKSPACE

        name = unquote(str(self.headers.get("X-Lygo-Filename") or "attachment.bin"))
        name = name.replace("\\", "/").split("/")[-1].strip() or "attachment.bin"
        safe = "".join(ch for ch in name if ch.isalnum() or ch in "._- ()").strip() or "attachment.bin"
        dest_dir = WORKSPACE / "uploads"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / (time.strftime("%Y%m%d-%H%M%S") + "-" + safe)
        dest.write_bytes(raw)
        self._json(200, {
            "path": str(dest),
            "name": safe,
            "bytes": len(raw),
            "note": "saved in the workspace: the agent opens it with the read_file limb",
        })

    def _api_chat(self) -> None:
        # 12 MB, not 4: an attached photo arrives as base64 inside this JSON, and a phone photo encoded
        # is 1.3x its size - the old limit turned "attach a photo" into a silent 413 on the operator.
        raw = self._read_body(12 * 1024 * 1024)
        if not raw:
            cl = int(self.headers.get("Content-Length") or 0)
            if cl > 12 * 1024 * 1024:
                self._json(413, {"error": "too_large", "limit": "12 MB - the photo is probably too large"})
                return
        try:
            obj = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "bad_json"})
            return
        # D13: `messages[]` is the contract; `prompt`/`message` are tolerated shorthands. A payload
        # that carries no user text at all is refused loudly (400 no_input) instead of being
        # answered with an empty turn — except image-only turns, which are legitimate.
        messages = normalise_messages(obj)
        if not messages and obj.get("messages"):
            self._json(400, {"error": "no_input", "hint": "messages[] entries must be objects with role/content"})
            return
        user = extract_user_text(messages)
        last_user = user_text_of(messages)
        if not (str(user).strip() or str(last_user).strip()) and not has_image(messages):
            self._json(400, {"error": "no_input", "hint": "send messages:[{\"role\":\"user\",\"content\":\"...\"}] (prompt or message also accepted)"})
            return
        gate = gate_prompt(user)
        if gate.get("verdict") == "QUARANTINE":
            self._json(451, {"error": "quarantine", "gate": gate})
            return
        use_tools = bool(obj.get("tools", True))
        model = obj.get("model") or STATE.get("selected") or "lygo-local"
        max_tokens = int(obj.get("max_tokens") or 1024)
        want_stream = bool(obj.get("stream", True))
        from cloud_api import chat as cloud_chat
        import brain_router
        import cloud_api

        # LOCAL is the default brain and always stays complete; the API is an option that hands
        # the turn back to the engine whenever it cannot answer (tokens, rate limit, outage).
        local_model = str(obj.get("model") or STATE.get("selected") or reg_load().get("selected") or "lygo-local")
        st_cloud = cloud_api.public_status()
        api_label = brain_router.label_of(st_cloud)
        want_api = obj.get("use_api")
        force_api = bool(obj.get("force_api"))
        has_key = bool(st_cloud.get("has_key"))
        if want_api is None:
            use_cloud = bool(st_cloud.get("enabled") and has_key)
        else:
            use_cloud = bool(want_api) and has_key
        handoff: dict[str, Any] | None = None
        if use_cloud and st_cloud.get("degraded") and not force_api and cloud_api.cooldown_active():
            # this API already handed off moments ago — answer locally, don't burn another call
            use_cloud = False
            handoff = brain_router.handoff_info(
                st_cloud.get("last_code") or 0, st_cloud.get("last_error") or "", api_label, skipped=True
            )
        if use_cloud:
            brain = "cloud"
            model = st_cloud.get("model") or model
        else:
            brain = maybe_spawn(local_model if reg_get(str(local_model)) else None)
        # Conversation compaction, before the prompt is built: stamp a checkpoint on its own cadence,
        # fold whatever has left the live window, and seal a session that has outgrown its caps. All
        # three are deterministic and bounded - a compaction must never be why a turn stalls.
        _ctx = live_ctx()
        pre_note = safe_pre_turn(messages, _ctx)
        kept, dropped, trim_info = trim_messages(messages, _ctx)
        # Journal the operator's own turn BEFORE generating, so a crash or a stopped answer still
        # leaves the question in the record of truth.
        _last = messages[-1] if messages else None
        if isinstance(_last, dict) and _last.get("role") == "user":
            safe_record("user", _last.get("content"), {"turn": True})
        elif str(user).strip():
            safe_record("user", user, {"turn": True})
        msgs = [local_system_message("api" if use_cloud else "local")] + kept
        assistant = ""
        traces: list[Any] = []
        # Hoisted out of the `if use_tools:` block below: it used to be initialised there and read
        # unconditionally at the end of the turn, so `"tools": false` (the portal's unticked
        # "Agent limbs" box, and the documented test payload) raised UnboundLocalError and answered
        # HTTP 500 handler_failed on EVERY turn. Initialise every turn variable before any branch.
        honest_pending = ""
        # Engine telemetry: llama.cpp reports its own tokens/s per call, so the console can show
        # the real generation speed of every turn instead of the operator having to benchmark it.
        timing_log: list[dict[str, Any]] = []

        def note_timings(parsed_obj: Any) -> None:
            """Keep the engine's own timing block. Never raises: telemetry must not break a turn."""
            try:
                t = parsed_obj.get("timings") if isinstance(parsed_obj, dict) else None
                if not isinstance(t, dict) or not (t.get("predicted_n") or t.get("prompt_n")):
                    return
                timing_log.append(
                    {
                        "prompt_n": int(t.get("prompt_n") or 0),
                        "prompt_tok_s": round(float(t.get("prompt_per_second") or 0), 1),
                        "gen_n": int(t.get("predicted_n") or 0),
                        "gen_tok_s": round(float(t.get("predicted_per_second") or 0), 1),
                    }
                )
            except Exception:  # noqa: BLE001 - a missing timing block is not a turn failure
                return

        def perf_summary() -> dict[str, Any]:
            """What this turn's engine calls actually did: tokens/s, token counts, last few blocks."""
            if not timing_log:
                return {}
            deep = max(timing_log, key=lambda e: int(e.get("prompt_n") or 0))
            last = timing_log[-1]
            return {
                "engine_calls": len(timing_log),
                "gen_tokens": sum(int(e.get("gen_n") or 0) for e in timing_log),
                "gen_tok_s": last.get("gen_tok_s"),
                "prompt_tokens": deep.get("prompt_n"),
                "prompt_tok_s": deep.get("prompt_tok_s"),
                "calls": timing_log[-4:],
            }
        if use_tools and last_user and HOST_PREFETCH:
            # host_prefetch pulls URLs out of the user's text and fetches them before the model
            # answers, so a pasted or forwarded link becomes untrusted content in the same context
            # as the shell and python limbs. On by default - it is how the small local models get
            # live context - but the operator can switch it off with LYGO_HOST_PREFETCH=0.
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
            emit_sse(
                {
                    "type": "brain",
                    "active": "cloud" if use_cloud else "local",
                    "brain": brain,
                    "model": str(model),
                    "api": api_label,
                    "fallback": handoff,
                }
            )

        if brain != "ready" and brain != "cloud":
            # mock / missing
            assistant = (
                "LYGO LLM Console is up. Engine brain is "
                f"{brain}. P0 verdict {gate.get('verdict')}. "
                "Local: Scan drives, pick a model, Boot LLM (it stays the default). "
                "Or press API in the brain switch to run the chat on a cloud key. Same full limbs either way."
            )
            if handoff:
                assistant = (
                    brain_router.banner(handoff["why"], handoff.get("api") or "", "", skipped=bool(handoff.get("skipped")))
                    + "\n\n"
                    + assistant
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

        from chat_loop import auto_limb, is_tool_call_echo, named_tool, sanitize_assistant, same_answer, tool_card, tool_prose
        from openai_proxy import llama_chat

        host_did_tools = bool(traces)
        if use_tools and host_did_tools:
            msgs.append(
                {
                    "role": "user",
                    "content": (
                        "HOST already ran the readout above. Write the operator-facing answer now, in your "
                        "own words. You may call at most ONE more limb if a specific path or URL is still "
                        "missing — otherwise answer."
                    ),
                }
            )
        payload = {
            "model": model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "stream": False,
        }
        tool_schema = TOOLS_SCHEMA if use_cloud else core_schema()
        if use_tools:
            payload["tools"] = tool_schema
        if use_cloud:
            code, body, _ = cloud_chat(payload)
            if code >= 400 and payload.get("tools"):
                payload.pop("tools", None)
                code, body, _ = cloud_chat(payload)
            if code >= 400 and brain_router.should_fallback(code):
                # the API is not going to answer this turn — the local engine takes over
                try:
                    perr = json.loads(body.decode("utf-8"))
                    e0 = perr.get("error") if isinstance(perr, dict) else perr
                    msg0 = e0.get("message") if isinstance(e0, dict) else str(e0 or "")
                except Exception:
                    msg0 = body[:300].decode("utf-8", "replace")
                why = brain_router.reason(code, msg0)
                cloud_api.note_error(code, why)
                handoff = brain_router.handoff_info(code, msg0, api_label)
                STATE["fallback"] = handoff
                brain = maybe_spawn(local_model if reg_get(str(local_model)) else None)
                if brain == "ready":
                    tool_schema = core_schema()
                    payload.pop("tools", None)
                    with ENGINE_LOCK:
                        code, body, _ = llama_chat(api_key=LLAMA_KEY, payload=payload, port=brain_port())
                    model = local_model
                    use_cloud = False
                else:
                    brain = "cloud"
        else:
            with ENGINE_LOCK:
                code, body, _ = llama_chat(api_key=LLAMA_KEY, payload=payload, port=brain_port())
        try:
            parsed = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            parsed = {}
        note_timings(parsed)
        if use_cloud and code >= 400:
            err = parsed.get("error") if isinstance(parsed, dict) else parsed
            msg_err = err.get("message") if isinstance(err, dict) else str(err or body[:400])
            assistant = "API error HTTP " + str(code) + ": " + str(msg_err)[:800]
            msg_obj = {}
        else:
            msg_obj = ((parsed.get("choices") or [{}])[0].get("message") or {})
            assistant = msg_obj.get("content") or ""
        ow = gate_output_window(assistant or "")
        if ow.get("verdict") == "QUARANTINE":
            assistant = "[output quarantined]"
        assistant = sanitize_assistant(assistant, traces) or assistant
        if use_tools:
            # A host-prefetched turn still gets one extra step so the agent can follow up when the
            # readout did not answer the question; model-initiated turns get the full loop.
            follow = list(msgs)
            cur_msg = msg_obj
            cur_text = assistant
            for _step in range(1 if host_did_tools else 4):
                batch = run_tools_round(cur_text, cur_msg)
                if not batch:
                    break
                traces.extend(batch)
                follow.append({"role": "assistant", "content": cur_text, "tool_calls": cur_msg.get("tool_calls")})
                follow.append(
                    {
                        "role": "user",
                        "content": "Tool results (RESOURCE, not CANON):\n"
                        + json.dumps(batch, default=str)[:8000]
                        + "\n\nNow answer the operator's newest message in plain prose using these results."
                        " Do not emit another tool call, and do not repeat the call JSON.",
                    }
                )
                payload2 = {"model": model, "messages": follow, "max_tokens": max_tokens, "stream": False, "tools": tool_schema}
                if use_cloud:
                    _, body2, _ = cloud_chat(payload2)
                else:
                    with ENGINE_LOCK:
                        _, body2, _ = llama_chat(api_key=LLAMA_KEY, payload=payload2, port=brain_port())
                try:
                    p2 = json.loads(body2.decode("utf-8"))
                except json.JSONDecodeError:
                    break
                note_timings(p2)
                cur_msg = ((p2.get("choices") or [{}])[0].get("message") or {})
                cur_text = cur_msg.get("content") or ""
                assistant = cur_text or assistant
                if gate_output_window(assistant).get("verdict") == "QUARANTINE":
                    assistant = "[output quarantined]"
                    break
        if use_tools:
            # The operator's OWN newest text, not msgs[-1] — the host-readout instruction is
            # appended to msgs above, and taking that as the request silently disabled this whole
            # guarantee on every prefetched turn (list_dir, whoami, wayback, http_json, download_url).
            newest = str(user or "")
            want = named_tool(newest)
            if want and not any(t.get("name") == want for t in traces):
                # The operator asked for a limb BY NAME and the turn came back without calling it —
                # measured 2026-09-18, sometimes with an invented result ("agent_gauntlet.html
                # downloaded"). Ask once more with only that limb's card, run whatever it emits, and
                # if it still will not call, say so rather than let a guessed result stand.
                card = {"role": "user", "content": tool_card(want)}
                pf = {"model": model, "messages": list(msgs) + [card], "max_tokens": max_tokens, "stream": False, "tools": tool_schema}
                if use_cloud:
                    _, bodyf, _ = cloud_chat(pf)
                else:
                    with ENGINE_LOCK:
                        _, bodyf, _ = llama_chat(api_key=LLAMA_KEY, payload=pf, port=brain_port())
                try:
                    parsed_f = json.loads(bodyf.decode("utf-8"))
                except Exception:
                    parsed_f = {}
                note_timings(parsed_f)
                msgf = ((parsed_f.get("choices") or [{}])[0].get("message") or {})
                textf = str(msgf.get("content") or "")
                forced = run_tools_round(textf, msgf)
                got_named = [t for t in forced if t.get("name") == want]
                if got_named:
                    traces.extend(forced)
                    follow_f = list(msgs) + [
                        card,
                        {"role": "assistant", "content": textf, "tool_calls": msgf.get("tool_calls")},
                        {
                            "role": "user",
                            "content": "Tool results (RESOURCE, not CANON):\n"
                            + json.dumps(forced, default=str)[:8000]
                            + "\n\nNow answer the operator's newest message in plain prose using these results."
                            " Do not emit another tool call, and do not repeat the call JSON.",
                        },
                    ]
                    p_f = {"model": model, "messages": follow_f, "max_tokens": max_tokens, "stream": False}
                    if use_cloud:
                        _, body_f, _ = cloud_chat(p_f)
                    else:
                        with ENGINE_LOCK:
                            _, body_f, _ = llama_chat(api_key=LLAMA_KEY, payload=p_f, port=brain_port())
                    try:
                        parsed_ff = json.loads(body_f.decode("utf-8"))
                    except Exception:
                        parsed_ff = {}
                    note_timings(parsed_ff)
                    try:
                        t_f = str(((parsed_ff.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
                    except Exception:
                        t_f = ""
                    if t_f.strip():
                        assistant = t_f
                else:
                    auto = auto_limb(want, newest)
                    if auto is not None:
                        # The operator named the limb and the model would not call it. The HOST runs it
                        # (read-only limbs only — never a shell command, a python snippet or a file write)
                        # and hands back the readout, labelled as host-run.
                        res = __import__("tools").dispatch(want, auto)
                        tr = {"name": want, "arguments": auto, "result": res, "host": True}
                        traces.append(tr)
                        assistant = "Host ran the " + want + " limb you named: " + (tool_prose([tr]) or "no readout")
                    else:
                        honest_pending = want
        if use_tools and traces and not str(assistant or "").strip():
            # A limb ran and the turn still has no words for the operator. The engine can answer the
            # "now answer in plain prose, do not emit another tool call" instruction with a second tool
            # call, and the loop has no step left to narrate it - so the bubble arrived empty while the
            # console was holding the readout. Measured 2026-09-19 on the plainest possible ask ("what
            # time is it right now?"): finish=tool_calls, content '', call now({}), then a 25-token
            # follow-up call. Say what the limbs returned instead of saying nothing.
            own = [t for t in traces if not t.get("host")] or traces
            assistant = tool_prose(own) or ""
        if use_tools and traces and is_tool_call_echo(assistant, cur_msg):
            # The model emitted a call and then echoed it as its answer instead of narrating the
            # result: hand the operator the host readout rather than the raw call JSON.
            own = [t for t in traces if not t.get("host")] or traces
            echoed_prose = tool_prose(own)
            if echoed_prose:
                assistant = echoed_prose
        if use_tools and traces and re.search(
            r"\bunknown\b|\bcannot\b|\bcan't\b|^\s*(?:no result|nothing|n/a)\s*$", str(assistant or ""), re.I
        ) and len(str(assistant or "").strip()) < 40:
            # A limb DID run and the model still shrugged ("UNKNOWN"). Give the operator the readout
            # instead of a shrug — measured on skill_read, where the call and its text were fine.
            shrug_prose = tool_prose(traces)
            if shrug_prose:
                assistant = shrug_prose
        if not str(assistant or "").strip():
            # An empty bubble is the symptom that has cost the most time here, and the console keeps no
            # record of a turn's internals - only HTTP access lines - so every guess had to be inferred.
            # Leave a receipt: what came back, what ran, and what the model's message actually held.
            # Wrapped, and every name read through locals(): this runs on the failing path, which is
            # exactly where a name may be missing. A receipt may never become the failure itself - a
            # bare NameError here reached an operator as HTTP 500 handler_failed while printing nothing.
            try:
                print(
                    "[turn] blank answer: use_tools=%s host_did_tools=%s tools_ran=%s first_msg_keys=%s "
                    "cur_text=%d chars follow_msg_keys=%s"
                    % (
                        locals().get("use_tools"),
                        locals().get("host_did_tools"),
                        [t.get("name") for t in (locals().get("traces") or [])],
                        sorted(locals().get("msg_obj") or {}),
                        len(str(locals().get("cur_text") or "")),
                        sorted(locals().get("cur_msg") or {}),
                    ),
                    flush=True,
                )
            except Exception:  # noqa: BLE001 - logging may never take the console down
                pass
        assistant = sanitize_assistant(assistant, traces) or assistant
        prev_answer = ""
        for m in reversed(messages):
            if m.get("role") == "assistant" and isinstance(m.get("content"), str) and m["content"].strip():
                prev_answer = m["content"]
                break
        if prev_answer and assistant and same_answer(prev_answer, assistant):
            # The operator asked something new and got the old answer back — small models happily echo
            # whatever is in the session. One nudge; whatever comes back is kept.
            nudge = list(msgs) + [
                {"role": "assistant", "content": assistant},
                {
                    "role": "user",
                    "content": (
                        "That was your previous answer repeated. Answer only the newest operator message, in "
                        "different words, with different content. If nothing new applies, say what changed in "
                        "one line."
                    ),
                },
            ]
            p3 = {"model": model, "messages": nudge, "max_tokens": max_tokens, "stream": False}
            if use_cloud:
                _, body3, _ = cloud_chat(p3)
            else:
                with ENGINE_LOCK:
                    _, body3, _ = llama_chat(api_key=LLAMA_KEY, payload=p3, port=brain_port())
            try:
                p3j = json.loads(body3.decode("utf-8"))
            except json.JSONDecodeError:
                p3j = {}
            note_timings(p3j)
            try:
                fresh = (((p3j.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
            except Exception:
                fresh = ""
            if fresh and not same_answer(prev_answer, fresh):
                assistant = sanitize_assistant(fresh, traces) or fresh
        if honest_pending:
            # Last word: a limb was named, never called, and is not one the host may run for the
            # operator — so say that plainly instead of letting a guessed answer stand.
            assistant = (
                "I was asked for the " + honest_pending + " limb and did not issue the call, so I have no "
                "result to report — nothing was invented to fill the gap. Ask again with \"use the "
                + honest_pending + " limb\", or tell me to answer without it."
            )
        active = "cloud" if use_cloud else "local"
        if handoff and assistant and active == "local" and not assistant.startswith("\u26a0"):
            assistant = brain_router.banner(handoff["why"], handoff.get("api") or "", str(model)) + "\n\n" + assistant
        if active == "local" and has_image(messages) and not __import__("registry").selected_vision():
            # Never silently ignore a picture: the operator attached it and is owed one honest sentence
            # instead of an answer that reads as though the photo had been considered.
            assistant = VISION_BLIND_NOTE.format(model=str(model)) + "\n\n" + assistant
        if not handoff:
            # a clean turn clears the last-handoff note on the health bar
            STATE["fallback"] = None
        STATE["last_brain"] = active
        _perf = perf_summary()
        if _perf:
            STATE["last_perf"] = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), **_perf}
        rec = write_receipt(
            prompt=user,
            output=assistant,
            model=str(model),
            gate=gate,
            extra={"has_image": has_image(messages), "active_brain": active, "api_handoff": handoff},
        )
        try:
            save_session(list(messages) + [{"role": "assistant", "content": assistant}])
        except Exception:
            pass
        # The record of truth: the engine's window may have dropped older turns, this journal has not.
        safe_record("assistant", assistant, {"receipt": rec.get("id")})
        _comp = safe_status(_ctx, list(messages) + [{"role": "assistant", "content": assistant}])
        if want_stream:
            emit_sse({"type": "token", "delta": assistant, "verdict": gate.get("verdict")})
            emit_sse(
                {
                    "type": "done",
                    "traces": traces,
                    "receipt": rec["id"],
                    "active": active,
                    "brain": brain,
                    "fallback": handoff,
                    "perf": perf_summary(),
                    "compaction": _comp,
                }
            )
            return
        self._json(
            200,
            {
                "text": assistant,
                "gate": gate,
                "brain": brain,
                "active": active,
                "fallback": handoff,
                "receipt": rec["id"],
                "traces": traces,
                "perf": perf_summary(),
                "compaction": _comp,
                "history": {"kept": len(kept), "dropped": dropped, "of": len(messages),
                            "budget_tokens": trim_info["budget"]["history_tokens"],
                            "used_tokens": trim_info["used_tokens"], "pre": pre_note},
            },
        )

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


class _StickContainment(ThreadingHTTPServer):
    """Console server that contains a failure instead of dying on it.

    socketserver's default handle_error prints the traceback to stderr; on a stick console
    whose stream is cp437 that print can itself raise, which ends the whole console. Logging
    here can never raise, so one bad request costs one response, not the session.
    """

    def handle_error(self, ref: object, ca: object) -> None:  # noqa: N802
        try:
            import traceback  # noqa: PLC0415

            tb = "".join(traceback.format_exception(*_sys.exc_info()))[-4000:]
            _sys.stderr.write(f"[stick] request from {ca} failed:\n{tb}\n")
            _sys.stderr.flush()
        except Exception:  # noqa: BLE001 - logging must never raise
            pass


class _Tee:
    """Write to the window AND to a file, so a console that dies leaves a reason behind.

    This console has exited on its own twice with nothing on disk to explain it: stdout lived only in
    the launcher window, and when the window closed the reason closed with it. Everything printed now
    also lands in save/logs/console-<date>.log. A write failure here is never allowed to break a turn.
    """

    def __init__(self, stream, handle) -> None:
        self._stream = stream
        self._handle = handle

    def write(self, data: str) -> int:
        # The file side is flushed on every write on purpose: this log exists to explain a death, and a
        # buffered handle loses exactly the last lines that would - which is what happened when the
        # primer's own "prefix primed" line sat in the buffer while the engine log showed it had run.
        for target in (self._stream, self._handle):
            try:
                target.write(data)
                target.flush()
            except Exception:  # noqa: BLE001 - logging may never take the console down
                pass
        return len(data)

    def flush(self) -> None:
        for target in (self._stream, self._handle):
            try:
                target.flush()
            except Exception:  # noqa: BLE001
                pass

    def __getattr__(self, name: str):
        return getattr(self._stream, name)


def install_console_log() -> str:
    """Tee stdout/stderr into save/logs/console-<date>.log. Returns the path, or '' if it could not."""
    try:
        from paths import LOGS

        LOGS.mkdir(parents=True, exist_ok=True)
        path = LOGS / f"console-{time.strftime('%Y%m%d')}.log"
        handle = open(path, "a", encoding="utf-8", errors="replace")
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        handle.write(f"\n===== console start {stamp} pid={os.getpid()} =====\n")
        handle.flush()
        sys.stdout = _Tee(sys.stdout, handle)
        sys.stderr = _Tee(sys.stderr, handle)
        return str(path)
    except Exception:  # noqa: BLE001 - a read-only stick still has to run
        return ""


def main() -> int:
    _log = install_console_log()
    global TOKEN, LLAMA_KEY, BIND, AUTH_REQUIRED, MOCK_ONLY
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="serve")
    # None means "whoever knows": console.json may declare the port for this copy of the kit.
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--lan", action="store_true")
    ap.add_argument("--i-consent", action="store_true", dest="i_consent")
    ap.add_argument("--gguf", default="")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    ensure_dirs()
    # Retention is a boot-time concern: receipts/events/todo stores grow forever and every
    # turn used to pay a re-read of the whole history. Bounded, and it must never stop the
    # console from coming up, so a failure here is reported and swallowed.
    try:
        _ret = prune_at_startup()
        print(f"[stick] retention: receipts={_ret.get('receipts')} "
              f"events={_ret.get('events')} todos={_ret.get('todos')}", file=sys.stderr)
    except Exception as _ret_e:  # noqa: BLE001 - retention must not block boot
        print(f"[stick] retention prune skipped: {_ret_e}", file=sys.stderr)
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
    # console.json used to be dead config for the two keys that matter most for running a second
    # copy of this kit (its port pair and its bind). Honour them - and refuse a config that tries
    # to expose the console on the network without the explicit --lan --i-consent handshake.
    if args.port is None:
        try:
            args.port = int(cfg.get("port") or DEFAULT_PORT)
        except (TypeError, ValueError):
            print(f"console.json port is not a number, using {DEFAULT_PORT}", file=sys.stderr)
            args.port = DEFAULT_PORT
    if not args.lan:
        want_bind = str(cfg.get("bind") or "").strip()
        if want_bind and want_bind.lower() not in ("127.0.0.1", "localhost", "::1"):
            print(
                f"console.json asks to bind {want_bind}; refusing without --lan --i-consent",
                file=sys.stderr,
            )
            return 2
    if args.cmd != "serve":
        print("unknown cmd", args.cmd)
        return 2
    class _ConsoleServer(_StickContainment):
        # Windows maps SO_REUSEADDR (which http.server sets by default) to a *permissive* bind:
        # two consoles can share 9641 and the browser then talks to whichever one wins, while
        # their boots fight over 11441 — that is exactly "models vanished / boot hangs".
        # Exclusive-address makes the second start fail loudly instead of double-binding.
        allow_reuse_address = False

    def _port_owner_hint(port: int) -> str:
        try:
            out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=15).stdout or ""
        except Exception as e:  # pragma: no cover
            return f"unknown ({e})"
        rows = [ln.split() for ln in out.splitlines()]
        # netstat -ano columns: [Proto, Local, Foreign, State, PID]
        pids = sorted({r[4] for r in rows if len(r) >= 5 and f":{port}" in r[1] and r[3].upper() == "LISTENING"})
        names = []
        for pid in pids:
            nm = "?"
            try:
                t = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=15).stdout or ""
                if t.strip():
                    nm = t.split(",")[0].strip().strip('"')
            except Exception:
                pass
            names.append(f"PID {pid} ({nm})")
        return ", ".join(names) or "free"

    # The portal is spliced into one HTML document per request; a missing asset used to surface
    # as a 500 on every visit. Fail loudly here instead, before the port is taken.
    missing_assets = [n for n in ("index.html", "style.css", "app.js") if not (PORTAL / n).is_file()]
    if missing_assets:
        print(f"portal assets missing in {PORTAL}: {', '.join(missing_assets)}", file=sys.stderr)
        return 4
    try:
        httpd = _ConsoleServer((BIND, args.port), Handler)
    except OSError as e:
        print("", file=sys.stderr)
        print(f"port {args.port} is already in use — {e}", file=sys.stderr)
        print("another LYGO console is still running (or its engine):", file=sys.stderr)
        for _p in (args.port, LLAMA_PORT, EMBED_PORT):
            print(f"  {_p} -> {_port_owner_hint(_p)}", file=sys.stderr)
        print("close that window, or run LYGO_LLM_CONSOLE_STOP.bat, then start again.", file=sys.stderr)
        return 3
    # The token matters only when auth is on; printing it otherwise puts a useless secret on screen.
    url = f"http://127.0.0.1:{args.port}/?v={BUILD}" + (f"&t={TOKEN}" if AUTH_REQUIRED else "")
    print(f"LYGO LLM Console {BUILD}  {url}")
    print(f"kit {KIT_ROOT}")
    if _log:
        print(f"console log {_log}")
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
            from registry import pick_default, prefer_by_ram

            sel = data.get("selected")
            rec = next((m for m in (data.get("models") or []) if m.get("id") == sel), None)
            if not rec or not rec.get("runnable") or rec.get("kind") not in (None, "chat"):
                want_ram = prefer_by_ram()
                data["selected"] = pick_default(data.get("models") or [], prefer_ram=want_ram)
                data["selected_source"] = "ram" if want_ram else "auto"
                from registry import save as reg_save

                reg_save(data)
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
