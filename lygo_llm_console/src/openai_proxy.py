from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Iterator

from paths import LLAMA_PORT

# A thinking model given this console's own prompt will spend the whole budget in its reasoning channel
# and hand back empty content - which reaches the operator as an answer that never arrives, and the
# portal stops it as "engine not responding". llama-server renders chat_template_kwargs into the chat
# template, so this asks the template to skip that channel and answer. Templates that do not use the
# flag simply ignore it. LYGO_THINKING=1 turns the reasoning channel back on for anyone who wants it.
THINKING_OFF = {"enable_thinking": False}


def for_local_engine(payload: dict[str, Any]) -> dict[str, Any]:
    """The payload as our own engine should receive it."""
    out = dict(payload)
    if str(os.environ.get("LYGO_THINKING") or "").lower() in ("1", "true", "yes", "on"):
        return out
    kwargs = dict(out.get("chat_template_kwargs") or {})
    kwargs.setdefault("enable_thinking", False)
    out["chat_template_kwargs"] = kwargs
    return out


def llama_chat(
    *,
    api_key: str,
    payload: dict[str, Any],
    port: int = LLAMA_PORT,
    timeout: float = 600.0,
) -> tuple[int, bytes, str]:
    data = json.dumps(for_local_engine(payload)).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            ctype = resp.headers.get("Content-Type") or "application/json"
            return resp.status, body, ctype
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b"{}", "application/json"


def llama_chat_stream(*, api_key: str, payload: dict[str, Any], port: int = LLAMA_PORT) -> Iterator[bytes]:
    data = json.dumps(for_local_engine(payload)).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        while True:
            line = resp.readline()
            if not line:
                break
            yield line
