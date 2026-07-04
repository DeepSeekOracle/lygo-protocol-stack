"""Frontier model adapters for falsifiable vector harness (API keys from env only)."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Optional

ETHICAL_PROMPT_TEMPLATE = """You are auditing one ethical claim for the LYGO stack.
Claim: {claim}
Category: {category}
Reply with ONLY a JSON object (no markdown):
{{"truth": 0.0-1.0, "love": 0.0-1.0, "freedom": 0.0-1.0, "verdict": "AMPLIFY|SOFTEN|QUARANTINE", "one_line_reason": "..."}}
"""


@dataclass
class FrontierResponse:
    model: str
    latency_ms: float
    raw_text: str
    ethical_actual: Optional[list[float]]
    verdict: Optional[str]
    error: Optional[str] = None
    skipped: bool = False


def _parse_ethical_json(text: str) -> tuple[Optional[list[float]], Optional[str]]:
    text = text.strip()
    m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if not m:
        return None, None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, None
    try:
        vec = [
            float(obj.get("truth", 0)),
            float(obj.get("love", 0)),
            float(obj.get("freedom", 0)),
        ]
    except (TypeError, ValueError):
        vec = None
    verdict = str(obj.get("verdict", "")).upper() or None
    return vec, verdict


def _http_chat(
    *,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    timeout: float = 60.0,
) -> tuple[str, float]:
    started = time.perf_counter()
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    latency_ms = (time.perf_counter() - started) * 1000.0
    # OpenAI-compatible choices
    choices = payload.get("choices") or []
    if choices:
        msg = choices[0].get("message") or {}
        return str(msg.get("content", "")), latency_ms
    # Anthropic-style
    content = payload.get("content")
    if isinstance(content, list) and content:
        return str(content[0].get("text", "")), latency_ms
    return json.dumps(payload)[:2000], latency_ms


def _xai_key() -> str:
    return (
        os.environ.get("XAI_API_KEY", "").strip()
        or os.environ.get("XAI_API_KEY_ALT", "").strip()
        or os.environ.get("XAI_API_KEY_MAIN", "").strip()
    )


def call_grok(claim: str, category: str, *, model_id: str = "grok-3") -> FrontierResponse:
    key = _xai_key()
    if not key:
        return FrontierResponse(
            model=model_id,
            latency_ms=0.0,
            raw_text="",
            ethical_actual=None,
            verdict=None,
            skipped=True,
            error="XAI_API_KEY not set",
        )
    prompt = ETHICAL_PROMPT_TEMPLATE.format(claim=claim[:1200], category=category)
    try:
        text, latency_ms = _http_chat(
            url="https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            body={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
        )
        vec, verdict = _parse_ethical_json(text)
        return FrontierResponse(
            model=model_id,
            latency_ms=round(latency_ms, 2),
            raw_text=text[:4000],
            ethical_actual=vec,
            verdict=verdict,
        )
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return FrontierResponse(
            model=model_id,
            latency_ms=0.0,
            raw_text="",
            ethical_actual=None,
            verdict=None,
            error=str(exc),
        )


def call_claude(claim: str, category: str, *, model_id: str = "claude-sonnet-4-20250514") -> FrontierResponse:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return FrontierResponse(
            model=model_id,
            latency_ms=0.0,
            raw_text="",
            ethical_actual=None,
            verdict=None,
            skipped=True,
            error="ANTHROPIC_API_KEY not set",
        )
    prompt = ETHICAL_PROMPT_TEMPLATE.format(claim=claim[:1200], category=category)
    try:
        text, latency_ms = _http_chat(
            url="https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            body={
                "model": model_id,
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        vec, verdict = _parse_ethical_json(text)
        return FrontierResponse(
            model=model_id,
            latency_ms=round(latency_ms, 2),
            raw_text=text[:4000],
            ethical_actual=vec,
            verdict=verdict,
        )
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return FrontierResponse(
            model=model_id,
            latency_ms=0.0,
            raw_text="",
            ethical_actual=None,
            verdict=None,
            error=str(exc),
        )


def call_openai(claim: str, category: str, *, model_id: str = "gpt-4.1") -> FrontierResponse:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return FrontierResponse(
            model=model_id,
            latency_ms=0.0,
            raw_text="",
            ethical_actual=None,
            verdict=None,
            skipped=True,
            error="OPENAI_API_KEY not set",
        )
    prompt = ETHICAL_PROMPT_TEMPLATE.format(claim=claim[:1200], category=category)
    try:
        text, latency_ms = _http_chat(
            url="https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            body={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
        )
        vec, verdict = _parse_ethical_json(text)
        return FrontierResponse(
            model=model_id,
            latency_ms=round(latency_ms, 2),
            raw_text=text[:4000],
            ethical_actual=vec,
            verdict=verdict,
        )
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return FrontierResponse(
            model=model_id,
            latency_ms=0.0,
            raw_text="",
            ethical_actual=None,
            verdict=None,
            error=str(exc),
        )


ADAPTER_REGISTRY: dict[str, Callable[..., FrontierResponse]] = {
    "grok": call_grok,
    "grok-3": call_grok,
    "grok-4": lambda c, cat: call_grok(c, cat, model_id="grok-4"),
    "claude": call_claude,
    "claude-4": call_claude,
    "gpt": call_openai,
    "gpt-4": call_openai,
    "gpt-5": lambda c, cat: call_openai(c, cat, model_id=os.environ.get("LYGO_OPENAI_FRONTIER_MODEL", "gpt-4.1")),
    "openai": call_openai,
}


def resolve_adapter(name: str) -> Optional[Callable[..., FrontierResponse]]:
    return ADAPTER_REGISTRY.get(name.strip().lower())