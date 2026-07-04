"""Provider-specific vision message blocks (multi-tool)."""

from __future__ import annotations

from typing import Any, Literal

Target = Literal["anthropic", "openai", "grok", "gemini", "raw"]

MIME = "image/png"


def anthropic_image_block(png_base64: str) -> dict[str, Any]:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": MIME, "data": png_base64},
    }


def anthropic_text_block(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def openai_image_part(png_base64: str) -> dict[str, Any]:
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{MIME};base64,{png_base64}"},
    }


def openai_text_part(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def gemini_inline_part(png_base64: str) -> dict[str, Any]:
    return {"inline_data": {"mime_type": MIME, "data": png_base64}}


def gemini_text_part(text: str) -> dict[str, Any]:
    return {"text": text}


def compress_result_to_blocks(
    result: dict[str, Any],
    *,
    target: Target = "openai",
    preamble: str | None = None,
) -> dict[str, Any]:
    """Turn compressor output into blocks any client/tool can paste into API payloads."""
    if result.get("action") != "compress":
        return {
            "action": "pass_through",
            "target": target,
            "text": result.get("text", ""),
            "diagnostics": result.get("diagnostics"),
        }

    b64 = result["png_base64"]
    exact = result.get("exact_identifiers") or []
    header = preamble or (
        "LYGO pxpipe-LYGO: bulky context rendered as image. "
        "Read all text in the image. Byte-exact values below must not be altered."
    )
    exact_lines = "\n".join(f"EXACT: {x}" for x in exact[:48])

    if target == "anthropic":
        content = [
            anthropic_text_block(header),
            anthropic_image_block(b64),
        ]
        if exact_lines:
            content.append(anthropic_text_block(exact_lines))
        return {
            "action": "compress",
            "target": target,
            "content": content,
            "manifest_id": result.get("manifest_id"),
            "tokens_saved_estimate": result.get("tokens_saved_estimate"),
        }

    if target in ("openai", "grok"):
        content = [
            openai_text_part(header),
            openai_image_part(b64),
        ]
        if exact_lines:
            content.append(openai_text_part(exact_lines))
        return {
            "action": "compress",
            "target": target,
            "content": content,
            "manifest_id": result.get("manifest_id"),
            "tokens_saved_estimate": result.get("tokens_saved_estimate"),
        }

    if target == "gemini":
        parts = [gemini_text_part(header), gemini_inline_part(b64)]
        if exact_lines:
            parts.append(gemini_text_part(exact_lines))
        return {
            "action": "compress",
            "target": target,
            "parts": parts,
            "manifest_id": result.get("manifest_id"),
            "tokens_saved_estimate": result.get("tokens_saved_estimate"),
        }

    return {
        "action": "compress",
        "target": "raw",
        "png_base64": b64,
        "manifest_id": result.get("manifest_id"),
        "exact_identifiers": exact,
        "tokens_saved_estimate": result.get("tokens_saved_estimate"),
    }


def normalize_target(name: str | None) -> Target:
    n = (name or "openai").strip().lower()
    if n in ("claude", "anthropic"):
        return "anthropic"
    if n in ("gpt", "openai", "chatgpt"):
        return "openai"
    if n in ("xai", "grok"):
        return "grok"
    if n in ("google", "gemini"):
        return "gemini"
    if n == "raw":
        return "raw"
    return "openai"