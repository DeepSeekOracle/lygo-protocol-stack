from __future__ import annotations

import json
from typing import Any, Callable

from p0_hook import gate_output_window, gate_prompt
from receipts import write_receipt
from tools import TOOLS_SCHEMA, dispatch, parse_fence_tool

SYSTEM = (
    "You are LYGO LLM Console, a local aligned agent on the LYGO protocol stack. "
    "When you need a tool, emit a fenced block:\n```tool\n"
    '{"name":"list_dir","arguments":{"path":"."}}\n```\n'
    "Tools: list_dir, read_file, write_file, remember, kernel_status, search_corpus, p0_gate, stack_health. "
    "Never request OS wipe, format c:, diskpart, or a shell. Human remains the publisher."
)


def extract_user_text(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for m in messages:
        if m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for p in c:
                if isinstance(p, dict) and p.get("type") == "text":
                    parts.append(str(p.get("text") or ""))
    return "\n".join(parts)


def has_image(messages: list[dict[str, Any]]) -> bool:
    for m in messages:
        c = m.get("content")
        if isinstance(c, list):
            for p in c:
                if isinstance(p, dict) and p.get("type") in {"image_url", "image"}:
                    return True
    return False


def run_tools_round(assistant_text: str) -> tuple[str | None, dict[str, Any] | None]:
    spec = parse_fence_tool(assistant_text)
    if not spec:
        return None, None
    result = dispatch(spec["name"], spec.get("arguments") or {})
    return spec["name"], result
