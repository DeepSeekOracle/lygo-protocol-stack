from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Iterator

from paths import LLAMA_PORT


def llama_chat(
    *,
    api_key: str,
    payload: dict[str, Any],
    port: int = LLAMA_PORT,
    timeout: float = 600.0,
) -> tuple[int, bytes, str]:
    data = json.dumps(payload).encode("utf-8")
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
    data = json.dumps(payload).encode("utf-8")
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
