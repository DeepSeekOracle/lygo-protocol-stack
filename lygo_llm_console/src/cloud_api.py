"""Cloud API brain for the admin console. Keys stay in gitignored config/api.json. Never echo secrets."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from paths import CONFIG, ensure_dirs
from atomicio import atomic_write_text

from brain_router import API as API_MODE
from brain_router import LOCAL as LOCAL_MODE
from brain_router import mode_of

API_PATH = CONFIG / "api.json"

# After a failed API turn the console stops trying for this long and lets the local
# engine answer; an explicit re-activation (or clear_error) lifts it immediately.
COOLDOWN_S = 300.0

PROVIDERS: dict[str, dict[str, Any]] = {
    "deepseek": {
        "label": "DeepSeek",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner", "deepseek-flash"],
        "help": "platform.deepseek.com — keys. Model deepseek-chat or deepseek-flash.",
    },
    "groq": {
        "label": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "openai/gpt-oss-20b",
        "models": ["openai/gpt-oss-20b", "openai/gpt-oss-120b"],
        "help": "console.groq.com/keys",
    },
    "openai": {
        "label": "OpenAI",
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "gpt-4o"],
        "help": "platform.openai.com",
    },
    "xai": {
        "label": "xAI Grok",
        "url": "https://api.x.ai/v1/chat/completions",
        "model": "grok-2-latest",
        "models": ["grok-2-latest", "grok-3"],
        "help": "console.x.ai",
    },
    "gemini": {
        "label": "Google Gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-flash-latest",
        "models": ["gemini-flash-latest", "gemini-pro-latest", "gemini-2.0-flash", "gemini-2.0-flash-001"],
        "help": "aistudio.google.com/apikey — OpenAI-compatible Gemini. Use the -latest ids: the 1.5/2.5 pins are retired.",
    },
    "openrouter": {
        "label": "OpenRouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openrouter/auto",
        "models": ["openrouter/auto"],
        "help": "openrouter.ai/keys",
    },
    "custom": {
        "label": "OpenAI-compatible URL",
        "url": "",
        "model": "",
        "models": [],
        "help": "Full chat/completions URL + key + model id",
    },
}

# --- house policy: DeepSeek is the default API and the standing backup -----------------------
# One rule, one place: with nothing wired — or with a provider name we do not ship — the API side
# of this brain IS DeepSeek, and DeepSeek also leads the fallback order behind any other primary.
DEFAULT_PROVIDER = "deepseek"
DEFAULT_MODEL = "deepseek-chat"


# ---- two-key failover (admin stick upgrade) -------------------------------------------
# The primary brain is `provider` + `key`. Every provider named in `fallbacks` that also holds
# a key in the `keys` map is tried, in order, when the primary answers with an auth, quota or
# server error. The local engine stays the last resort, so a dead cloud chain still answers.
FAIL_CODES = (401, 402, 403, 408, 409, 429, 500, 502, 503, 504)


def sanitize_key(k: str) -> str:
    k = (k or "").replace("\ufeff", "")
    k = k.replace("\u200b", "").replace("\u00a0", "")
    k = k.strip().replace("Bearer ", "").replace("bearer ", "")
    k = k.strip("\"'`")
    k = "".join(ch for ch in k if 33 <= ord(ch) <= 126)
    return k


def _blank() -> dict[str, Any]:
    return {
        "enabled": False,
        "provider": DEFAULT_PROVIDER,
        "model": DEFAULT_MODEL,
        "url": "",
        "key": "",
        "keys": {},
        "fallbacks": [],
        "last_provider": "",
        "chain_tried": [],
        "degraded": False,
        "last_error": "",
        "last_code": 0,
        "last_at": 0.0,
        "handoffs": 0,
    }


def _load() -> dict[str, Any]:
    if not API_PATH.is_file():
        return _blank()
    try:
        obj = json.loads(API_PATH.read_text(encoding="utf-8"))
    except Exception:
        obj = {}
    if not isinstance(obj, dict):
        obj = {}
    obj.setdefault("enabled", False)
    # A config that names a provider we do not ship (hand-edited, retired, or a typo) must never
    # become a chain entry posting to an empty URL: fall back to the house default instead.
    if str(obj.get("provider") or "").strip() not in PROVIDERS:
        obj["provider"] = DEFAULT_PROVIDER
    if not str(obj.get("model") or "").strip():
        obj["model"] = DEFAULT_MODEL
    obj.setdefault("url", "")
    obj.setdefault("key", "")
    obj.setdefault("degraded", False)
    obj.setdefault("last_error", "")
    obj.setdefault("last_code", 0)
    obj.setdefault("last_at", 0.0)
    obj.setdefault("handoffs", 0)
    obj.setdefault("last_provider", "")
    obj["key"] = sanitize_key(str(obj.get("key") or ""))
    raw_keys = obj.get("keys")
    clean: dict[str, str] = {}
    if isinstance(raw_keys, dict):
        for name, val in raw_keys.items():
            v = sanitize_key(str(val or ""))
            if v:
                clean[str(name)] = v
    obj["keys"] = clean
    raw_fb = obj.get("fallbacks")
    seen: list[str] = []
    if isinstance(raw_fb, list):
        for name in raw_fb:
            n = str(name or "").strip()
            if n and n not in seen:
                seen.append(n)
    obj["fallbacks"] = seen
    tried = obj.get("chain_tried")
    obj["chain_tried"] = [str(x) for x in tried][-8:] if isinstance(tried, list) else []
    return obj


def save(obj: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    CONFIG.mkdir(parents=True, exist_ok=True)
    cur = _load()
    if "key" in obj:
        k = sanitize_key(str(obj.get("key") or ""))
        if k:
            cur["key"] = k
        elif obj.get("key") == "":
            cur["key"] = ""
    if isinstance(obj.get("keys"), dict):
        # merge, per provider: a non-empty value wires that provider up, "" unwires just it
        for name, val in obj["keys"].items():
            n = str(name or "").strip()
            if not n:
                continue
            v = sanitize_key(str(val or ""))
            if v:
                cur["keys"][n] = v
            elif val == "":
                cur["keys"].pop(n, None)
    if isinstance(obj.get("fallbacks"), list):
        cur["fallbacks"] = [str(x or "").strip() for x in obj["fallbacks"] if str(x or "").strip()]
    if "provider" in obj:
        cur["provider"] = str(obj.get("provider") or "deepseek")
    if "model" in obj:
        cur["model"] = str(obj.get("model") or "")
    if "url" in obj:
        cur["url"] = str(obj.get("url") or "").strip()
    if "enabled" in obj:
        cur["enabled"] = bool(obj.get("enabled"))
    if cur.get("enabled") or obj.get("clear_error"):
        # switching the API on (or an explicit clear) ends the previous handoff
        cur["degraded"] = False
        cur["last_error"] = ""
        cur["last_code"] = 0
    p = PROVIDERS.get(cur["provider"]) or PROVIDERS["deepseek"]
    if cur["provider"] != "custom":
        cur["url"] = p.get("url") or cur.get("url") or ""
    if not cur.get("model"):
        cur["model"] = p.get("model") or "deepseek-chat"
    atomic_write_text(API_PATH, json.dumps(cur, indent=2))
    return public_status()


def public_status() -> dict[str, Any]:
    cur = _load()
    p = PROVIDERS.get(cur.get("provider") or "") or {}
    chain = chain_for(cur)
    st: dict[str, Any] = {
        "ok": True,
        "enabled": bool(cur.get("enabled") and chain),
        "has_key": bool(chain),
        "key_count": len(chain),
        "keys_wired": [str(c.get("provider")) for c in chain],
        "chain": [str(c.get("label")) for c in chain],
        "last_provider": str(cur.get("last_provider") or ""),
        "chain_tried": list(cur.get("chain_tried") or []),
        "fallbacks": list(cur.get("fallbacks") or []),
        "failover": True,
        "default_provider": DEFAULT_PROVIDER,
        "is_default": str(cur.get("provider") or DEFAULT_PROVIDER) == DEFAULT_PROVIDER,
        "provider": cur.get("provider") or DEFAULT_PROVIDER,
        "label": p.get("label") or cur.get("provider"),
        "model": cur.get("model") or p.get("model"),
        "url": (cur.get("url") or p.get("url") or "")[:80],
        "help": p.get("help") or "",
        "providers": {k: {"label": v["label"], "model": v["model"], "help": v["help"], "models": v.get("models") or []} for k, v in PROVIDERS.items()},
        "path": str(API_PATH),
        "secret": "never_echoed",
        "degraded": bool(cur.get("degraded")),
        "last_error": str(cur.get("last_error") or ""),
        "last_code": int(cur.get("last_code") or 0),
        "last_at": float(cur.get("last_at") or 0.0),
        "handoffs": int(cur.get("handoffs") or 0),
        "cooldown_s": COOLDOWN_S,
    }
    st["mode"] = mode_of(st)
    st["active"] = st["mode"] == API_MODE
    return st


def chain_for(cur: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Ordered candidates: the primary (provider + key) first, then every keyed fallback.

    A provider is only ever a candidate if it actually holds a key, so a half-wired stick
    simply runs a shorter chain. Returns [] when nothing is keyed (caller treats as no key).
    """
    cur = _load() if cur is None else cur
    primary = str(cur.get("provider") or DEFAULT_PROVIDER)
    if primary not in PROVIDERS:
        primary = DEFAULT_PROVIDER
    keys = cur.get("keys") if isinstance(cur.get("keys"), dict) else {}
    order: list[str] = [primary]
    # DeepSeek also leads the BACKUP order: an operator who wired several keys and set no order
    # still fails over to the house default first. An explicit primary always outranks it.
    for name in [DEFAULT_PROVIDER] + list(cur.get("fallbacks") or []) + list(keys):
        n = str(name or "").strip()
        if n and n not in order:
            order.append(n)
    out: list[dict[str, Any]] = []
    for name in order:
        p = PROVIDERS.get(name) or {}
        key = sanitize_key(str(keys.get(name) or (cur.get("key") if name == primary else "")))
        if not key:
            continue
        url = str(((cur.get("url") if name == primary else "") or p.get("url") or "")).strip()
        model = str(((cur.get("model") if name == primary else "") or p.get("model") or ""))
        out.append(
            {
                "provider": name,
                "label": str(p.get("label") or name),
                "key": key,
                "url": url,
                "model": model,
                "extra": p.get("extra") or {},
            }
        )
    return out


def enabled() -> bool:
    cur = _load()
    return bool(cur.get("enabled") and chain_for(cur))


def _post(url: str, key: str, body: dict[str, Any], extra: dict[str, Any], timeout: float) -> tuple[int, bytes, str]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
        method="POST",
    )
    for hk, hv in (extra or {}).items():
        req.add_header(str(hk), str(hv))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type") or "application/json"
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b"{}", "application/json"
    except Exception as e:
        err = json.dumps({"error": str(e)[:400]}).encode("utf-8")
        return 502, err, "application/json"


def _note_chain(tried: list[str], last_provider: str = "") -> None:
    """Record which keys were attempted (codes only — never key material)."""
    try:
        ensure_dirs()
        CONFIG.mkdir(parents=True, exist_ok=True)
        cur = _load()
        cur["chain_tried"] = [str(x) for x in tried][-8:]
        if last_provider:
            cur["last_provider"] = last_provider
        atomic_write_text(API_PATH, json.dumps(cur, indent=2))
    except Exception:
        pass


def _note_success(provider: str) -> None:
    try:
        ensure_dirs()
        CONFIG.mkdir(parents=True, exist_ok=True)
        cur = _load()
        cur["last_provider"] = str(provider)
        atomic_write_text(API_PATH, json.dumps(cur, indent=2))
    except Exception:
        pass


def chat(payload: dict[str, Any], timeout: float = 180.0) -> tuple[int, bytes, str]:
    """One API turn, walked down the wired key chain.

    The primary provider answers first; if it fails in a way another key could survive
    (auth / quota / rate limit / server error) the next keyed provider is tried. A request
    the provider merely rejected as malformed (4xx that is not in FAIL_CODES) stops the walk
    immediately — repeating it elsewhere would waste a second quota. When every key fails the
    LAST failure is returned untouched, so the console's existing handoff to the local engine
    (note_error -> cooldown -> local takeover) still fires with a truthful status code.
    """
    cur = _load()
    chain = chain_for(cur)
    if not chain:
        return 401, b'{"error":"no_api_key"}', "application/json"
    last: tuple[int, bytes, str] = (401, b'{"error":"no_api_key"}', "application/json")
    tried: list[str] = []
    for i, cand in enumerate(chain):
        url = str(cand.get("url") or "")
        if not url.startswith("https://") and not url.startswith("http://127.0.0.1"):
            tried.append("%s:bad_url" % cand.get("provider"))
            last = (400, b'{"error":"bad_url"}', "application/json")
            continue
        body = dict(payload)
        body["model"] = cand.get("model") or payload.get("model")
        body["stream"] = False
        code, data, ctype = _post(url, str(cand.get("key")), body, cand.get("extra") or {}, timeout)
        tried.append("%s:%s" % (cand.get("provider"), code))
        last = (code, data, ctype)
        if code < 400:
            _note_success(str(cand.get("provider") or ""))
            if len(tried) > 1:
                _note_chain(tried, str(cand.get("provider") or ""))
            return code, data, ctype
        if code not in FAIL_CODES:
            break
        if i + 1 < len(chain):
            _note_chain(tried, str(cand.get("provider") or ""))
    _note_chain(tried, str(tried[-1].split(":")[0]) if tried else "")
    return last


def active() -> bool:
    """API usable *right now*: key saved, switched on, and not in a handoff."""
    st = public_status()
    return bool(st["enabled"] and not st["degraded"])


def note_error(code: int | Any, message: str = "") -> dict[str, Any]:
    """Record that an API turn failed; the console hands the next turns to local until cleared."""
    ensure_dirs()
    CONFIG.mkdir(parents=True, exist_ok=True)
    cur = _load()
    cur["degraded"] = True
    cur["last_code"] = int(code or 0)
    cur["last_error"] = " ".join(str(message or "").split())[:300]
    cur["last_at"] = time.time()
    cur["handoffs"] = int(cur.get("handoffs") or 0) + 1
    atomic_write_text(API_PATH, json.dumps(cur, indent=2))
    return public_status()


def clear_error() -> dict[str, Any]:
    """Operator re-activation: forget the handoff so the API is tried again."""
    ensure_dirs()
    CONFIG.mkdir(parents=True, exist_ok=True)
    cur = _load()
    cur["degraded"] = False
    cur["last_error"] = ""
    cur["last_code"] = 0
    atomic_write_text(API_PATH, json.dumps(cur, indent=2))
    return public_status()


def cooldown_active(seconds: float | None = None) -> bool:
    """True while a recent handoff should keep the console from calling the API again."""
    cur = _load()
    if not cur.get("degraded"):
        return False
    span = COOLDOWN_S if seconds is None else float(seconds)
    try:
        last = float(cur.get("last_at") or 0.0)
    except (TypeError, ValueError):
        last = 0.0
    return (time.time() - last) < span
