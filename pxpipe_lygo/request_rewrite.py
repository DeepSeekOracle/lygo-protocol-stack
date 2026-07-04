"""Rewrite API request bodies: compress bulky text fields per provider."""

from __future__ import annotations

import copy
from typing import Any

from pxpipe_lygo.compressor import LYGOCompressor
from pxpipe_lygo.message_adapters import compress_result_to_blocks, normalize_target


def _min_compress_chars() -> int:
    from pxpipe_lygo.config import MIN_CHARS_TO_COMPRESS

    return MIN_CHARS_TO_COMPRESS


def _compress_system_field(
    compressor: LYGOCompressor,
    text: str,
    target: str,
) -> tuple[str | None, list[dict[str, Any]] | None, dict[str, Any] | None]:
    if len(text) < _min_compress_chars():
        return text, None, None
    result = compressor.compress(text, provider=target)
    if result.get("action") != "compress":
        return text, None, None
    blocks = compress_result_to_blocks(result, target=normalize_target(target))
    meta = {
        "manifest_id": result.get("manifest_id"),
        "tokens_saved_estimate": result.get("tokens_saved_estimate"),
    }
    return None, blocks.get("content") or blocks.get("parts"), meta


def rewrite_anthropic_messages(body: dict[str, Any], compressor: LYGOCompressor) -> dict[str, Any]:
    out = copy.deepcopy(body)
    metas: list[dict[str, Any]] = []
    target = "anthropic"

    system = out.get("system")
    if isinstance(system, str) and system.strip():
        new_sys, blocks, meta = _compress_system_field(compressor, system, "claude")
        if blocks:
            out.pop("system", None)
            msgs = list(out.get("messages") or [])
            msgs.insert(
                0,
                {
                    "role": "user",
                    "content": blocks,
                },
            )
            out["messages"] = msgs
            if meta:
                metas.append(meta)

    messages = out.get("messages")
    if isinstance(messages, list):
        new_messages = []
        for msg in messages:
            if not isinstance(msg, dict):
                new_messages.append(msg)
                continue
            content = msg.get("content")
            if isinstance(content, str) and len(content) >= _min_compress_chars():
                result = compressor.compress(content, provider="claude")
                if result.get("action") == "compress":
                    blocks = compress_result_to_blocks(result, target="anthropic")
                    new_messages.append({**msg, "content": blocks["content"]})
                    metas.append(
                        {
                            "manifest_id": result.get("manifest_id"),
                            "tokens_saved_estimate": result.get("tokens_saved_estimate"),
                        }
                    )
                    continue
            new_messages.append(msg)
        out["messages"] = new_messages

    if metas:
        out.setdefault("metadata", {})["lygo_pxpipe"] = metas
    return out


def rewrite_openai_chat(body: dict[str, Any], compressor: LYGOCompressor, *, provider: str) -> dict[str, Any]:
    out = copy.deepcopy(body)
    metas: list[dict[str, Any]] = []
    target = normalize_target(provider)

    messages = out.get("messages")
    if not isinstance(messages, list):
        return out

    new_messages = []
    for msg in messages:
        if not isinstance(msg, dict):
            new_messages.append(msg)
            continue
        role = msg.get("role")
        content = msg.get("content")
        if isinstance(content, str) and len(content) >= _min_compress_chars():
            if role in ("system", "user", "assistant", "tool"):
                result = compressor.compress(content, provider=provider)
                if result.get("action") == "compress":
                    blocks = compress_result_to_blocks(result, target=target)
                    new_messages.append({**msg, "content": blocks["content"]})
                    metas.append(
                        {
                            "manifest_id": result.get("manifest_id"),
                            "tokens_saved_estimate": result.get("tokens_saved_estimate"),
                        }
                    )
                    continue
        new_messages.append(msg)

    out["messages"] = new_messages
    if metas:
        out.setdefault("metadata", {})["lygo_pxpipe"] = metas
    return out