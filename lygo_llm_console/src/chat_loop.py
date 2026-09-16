from __future__ import annotations

import json
import re
from typing import Any

from align import load_align
from p0_hook import gate_output_window
from tools import dispatch, parse_fence_tool

SYSTEM = load_align()


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


def _args(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            v = json.loads(raw)
            return v if isinstance(v, dict) else {"value": raw}
        except json.JSONDecodeError:
            return {"value": raw}
    return {}


def extract_tool_calls(message: dict[str, Any], content: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tc in message.get("tool_calls") or []:
        fn = tc.get("function") or tc
        name = (fn.get("name") if isinstance(fn, dict) else None) or tc.get("name")
        if not name:
            continue
        args = _args(fn.get("arguments") if isinstance(fn, dict) else tc.get("arguments"))
        out.append({"name": str(name), "arguments": args})
    fence = parse_fence_tool(content or "")
    if fence:
        out.append(fence)
    for m in re.finditer(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", content or "", re.S):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        name = obj.get("name") or obj.get("tool")
        if name:
            out.append({"name": str(name), "arguments": _args(obj.get("arguments") or obj.get("parameters") or obj)})
    # dedupe
    seen = set()
    uniq = []
    for c in out:
        key = (c["name"], json.dumps(c.get("arguments") or {}, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    return uniq


def run_tools_round(assistant_text: str, message: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    calls = extract_tool_calls(message or {}, assistant_text or "")
    traces = []
    for spec in calls[:4]:
        result = dispatch(spec["name"], spec.get("arguments") or {})
        traces.append({"name": spec["name"], "arguments": spec.get("arguments"), "result": result})
    return traces
