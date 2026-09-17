"""Cloud API brain for the admin console. Keys stay in gitignored config/api.json. Never echo secrets."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from paths import CONFIG, ensure_dirs

API_PATH = CONFIG / "api.json"

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


def sanitize_key(k: str) -> str:
    k = (k or "").replace("\ufeff", "")
    k = k.replace("\u200b", "").replace("\u00a0", "")
    k = k.strip().replace("Bearer ", "").replace("bearer ", "")
    k = k.strip("\"'`")
    k = "".join(ch for ch in k if 33 <= ord(ch) <= 126)
    return k


def _load() -> dict[str, Any]:
    if not API_PATH.is_file():
        return {"enabled": False, "provider": "deepseek", "model": "deepseek-chat", "url": "", "key": ""}
    try:
        obj = json.loads(API_PATH.read_text(encoding="utf-8"))
    except Exception:
        obj = {}
    if not isinstance(obj, dict):
        obj = {}
    obj.setdefault("enabled", False)
    obj.setdefault("provider", "deepseek")
    obj.setdefault("model", "deepseek-chat")
    obj.setdefault("url", "")
    obj.setdefault("key", "")
    obj["key"] = sanitize_key(str(obj.get("key") or ""))
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
    if "provider" in obj:
        cur["provider"] = str(obj.get("provider") or "deepseek")
    if "model" in obj:
        cur["model"] = str(obj.get("model") or "")
    if "url" in obj:
        cur["url"] = str(obj.get("url") or "").strip()
    if "enabled" in obj:
        cur["enabled"] = bool(obj.get("enabled"))
    p = PROVIDERS.get(cur["provider"]) or PROVIDERS["deepseek"]
    if cur["provider"] != "custom" and not cur.get("url"):
        cur["url"] = p["url"]
    if not cur.get("model"):
        cur["model"] = p.get("model") or "deepseek-chat"
    API_PATH.write_text(json.dumps(cur, indent=2), encoding="utf-8")
    return public_status()


def public_status() -> dict[str, Any]:
    cur = _load()
    p = PROVIDERS.get(cur.get("provider") or "") or {}
    return {
        "ok": True,
        "enabled": bool(cur.get("enabled") and cur.get("key")),
        "has_key": bool(cur.get("key")),
        "provider": cur.get("provider") or "deepseek",
        "label": p.get("label") or cur.get("provider"),
        "model": cur.get("model") or p.get("model"),
        "url": (cur.get("url") or p.get("url") or "")[:80],
        "help": p.get("help") or "",
        "providers": {k: {"label": v["label"], "model": v["model"], "help": v["help"], "models": v.get("models") or []} for k, v in PROVIDERS.items()},
        "path": str(API_PATH),
        "secret": "never_echoed",
    }


def enabled() -> bool:
    cur = _load()
    return bool(cur.get("enabled") and cur.get("key"))


def chat(payload: dict[str, Any], timeout: float = 180.0) -> tuple[int, bytes, str]:
    cur = _load()
    if not cur.get("key"):
        return 401, b'{"error":"no_api_key"}', "application/json"
    p = PROVIDERS.get(cur.get("provider") or "") or {}
    url = (cur.get("url") or p.get("url") or "").strip()
    if not url.startswith("https://") and not url.startswith("http://127.0.0.1"):
        return 400, b'{"error":"bad_url"}', "application/json"
    model = cur.get("model") or p.get("model") or payload.get("model")
    body = dict(payload)
    body["model"] = model
    body["stream"] = False
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cur["key"],
        },
        method="POST",
    )
    extra = p.get("extra") or {}
    for hk, hv in extra.items():
        req.add_header(str(hk), str(hv))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type") or "application/json"
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b"{}", "application/json"
    except Exception as e:
        err = json.dumps({"error": str(e)[:400]}).encode("utf-8")
        return 502, err, "application/json"
