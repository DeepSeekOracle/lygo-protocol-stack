"""Forward rewritten requests to provider APIs (stdlib urllib)."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def provider_api_key(provider: str) -> str:
    keys = {
        "claude": ("ANTHROPIC_API_KEY",),
        "anthropic": ("ANTHROPIC_API_KEY",),
        "openai": ("OPENAI_API_KEY",),
        "grok": ("XAI_API_KEY", "GROK_API_KEY"),
        "gemini": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    }
    for env in keys.get(provider, ()):
        v = os.environ.get(env, "").strip()
        if v:
            return v
    return ""


def forward_request(
    provider: str,
    path: str,
    body: dict[str, Any],
    headers: dict[str, str],
    *,
    timeout: int = 180,
) -> tuple[int, bytes, dict[str, str]]:
    from pxpipe_lygo.router import upstream_base_url

    base = upstream_base_url(provider)
    if not base:
        return 502, json.dumps({"error": "unknown_provider", "provider": provider}).encode(), {}

    api_key = provider_api_key(provider)
    if not api_key:
        return 401, json.dumps({"error": "missing_api_key", "provider": provider}).encode(), {}

    url = f"{base}{path}"
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")

    if provider in ("claude", "anthropic"):
        req.add_header("x-api-key", api_key)
        req.add_header("anthropic-version", headers.get("anthropic-version", "2023-06-01"))
    elif provider in ("openai", "grok"):
        req.add_header("Authorization", f"Bearer {api_key}")
    elif provider == "gemini":
        url = f"{url}?key={api_key}"

    for k, v in headers.items():
        lk = k.lower()
        if lk in ("host", "content-length", "connection", "authorization", "x-api-key"):
            continue
        req.add_header(k, v)

    try:
        with urlopen(req, timeout=timeout) as resp:
            out_headers = {k: v for k, v in resp.headers.items()}
            return resp.status, resp.read(), out_headers
    except HTTPError as exc:
        return exc.code, exc.read(), {}
    except URLError as exc:
        return 502, json.dumps({"error": "upstream_failed", "detail": str(exc.reason)}).encode(), {}