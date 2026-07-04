"""In-process API for agents, CLI tools, and other LYGO scripts (no proxy required)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TextIO

from pxpipe_lygo.compressor import LYGOCompressor, compress_text
from pxpipe_lygo.message_adapters import compress_result_to_blocks, normalize_target


def compress_file_for_tool(
    path: str | Path,
    *,
    target: str = "auto",
    keep_png_path: str | Path | None = None,
) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return compress_text_for_tool(text, target=target, keep_png_path=keep_png_path, source=str(path))


def compress_text_for_tool(
    text: str,
    *,
    target: str = "auto",
    keep_png_path: str | Path | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    tgt = normalize_target(None if target == "auto" else target)
    result = compress_text(text, provider=tgt if tgt != "raw" else "grok")
    payload: dict[str, Any] = {
        "source": source,
        "action": result.get("action"),
        "target": tgt,
    }
    if result.get("action") == "compress" and keep_png_path:
        import base64

        Path(keep_png_path).write_bytes(base64.b64decode(result["png_base64"]))
        payload["png_path"] = str(Path(keep_png_path).resolve())

    blocks = compress_result_to_blocks(result, target=tgt)
    payload.update(blocks)
    if result.get("action") == "pass_through":
        payload["text"] = result.get("text", text)
    payload["usage_hint"] = _usage_hint(tgt)
    return payload


def _usage_hint(target: str) -> str:
    hints = {
        "anthropic": "Paste `content` array into a message; or point ANTHROPIC_BASE_URL at pxpipe proxy.",
        "openai": "Paste `content` parts into chat message; or OPENAI_BASE_URL=http://127.0.0.1:47821/v1",
        "grok": "Same as openai; XAI_BASE_URL=http://127.0.0.1:47821/v1 for chat/completions shim.",
        "gemini": "Use `parts` in generateContent request.",
        "raw": "Use png_base64 for custom clients.",
    }
    return hints.get(target, hints["openai"])


def write_tool_json(payload: dict[str, Any], stream: TextIO | None = None) -> None:
    out = stream
    if out is None:
        import sys

        out = sys.stdout
    # Never dump full base64 in default agent JSON if blocks already present
    slim = {k: v for k, v in payload.items() if k != "png_base64"}
    json.dump(slim, out, indent=2)
    out.write("\n")
    out.flush()


def maybe_compress_context(text: str, *, target: str = "auto", min_chars: int | None = None) -> str:
    """Agent helper: return original text or a short pointer + save manifest when compressed."""
    from pxpipe_lygo.config import MIN_CHARS_TO_COMPRESS

    floor = min_chars if min_chars is not None else MIN_CHARS_TO_COMPRESS
    if len(text) < floor:
        return text
    payload = compress_text_for_tool(text, target=target)
    if payload.get("action") != "compress":
        return text
    mid = payload.get("manifest_id", "?")
    saved = payload.get("tokens_saved_estimate", 0)
    png = payload.get("png_path")
    lines = [
        f"[LYGO pxpipe-LYGO compressed ~{saved} est. tokens | manifest {mid}]",
        "Vision context was rendered to PNG; use tools/pxpipe_lygo_for_agent.py or proxy /v1/transform to attach.",
    ]
    if png:
        lines.append(f"PNG: {png}")
    exact = payload.get("exact_identifiers") or []
    if exact:
        lines.append("EXACT identifiers (do not paraphrase):")
        lines.extend(f"  {x}" for x in exact[:24])
    return "\n".join(lines)