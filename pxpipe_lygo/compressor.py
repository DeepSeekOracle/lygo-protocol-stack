"""Core LYGO pxpipe compression pipeline."""

from __future__ import annotations

import base64
import hashlib
import time
from typing import Any

from pxpipe_lygo import __signature__
from pxpipe_lygo.manifest_store import persist_manifest
from pxpipe_lygo.p0_gate import should_compress_payload
from pxpipe_lygo.png_renderer import render_text_to_png
from pxpipe_lygo.router import select_provider
from pxpipe_lygo.verbatim_guard import extract_exact_identifiers


class LYGOCompressor:
    def compress(self, text: str, *, provider: str | None = None) -> dict[str, Any]:
        provider = select_provider(provider)
        ok_pre, diag_pre = should_compress_payload(text)
        if not ok_pre:
            return {
                "action": "pass_through",
                "signature": __signature__,
                "provider": provider,
                "diagnostics": diag_pre,
                "text": text,
            }

        exact_ids = extract_exact_identifiers(text)
        png_bytes, width, height = render_text_to_png(text)
        ok_post, diag_post = should_compress_payload(text, png_width=width, png_height=height)
        if not ok_post:
            return {
                "action": "pass_through",
                "signature": __signature__,
                "provider": provider,
                "diagnostics": diag_post,
                "text": text,
            }

        original_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        png_hash = hashlib.sha256(png_bytes).hexdigest()
        manifest_id = original_hash[:16]
        text_tokens = diag_post.get("estimated_text_tokens", len(text) // 4)
        vision_tokens = diag_post.get("estimated_vision_tokens", 0)
        tokens_saved = max(0, text_tokens - vision_tokens)

        manifest: dict[str, Any] = {
            "manifest_id": manifest_id,
            "signature": __signature__,
            "original_sha256": original_hash,
            "png_sha256": png_hash,
            "provider": provider,
            "tokens_saved_estimate": tokens_saved,
            "estimated_text_tokens": text_tokens,
            "estimated_vision_tokens": vision_tokens,
            "exact_identifiers": exact_ids,
            "png": {"width": width, "height": height, "bytes": len(png_bytes)},
            "timestamp": time.time(),
            "p0": diag_post.get("p0"),
        }
        store_meta = persist_manifest(manifest)

        return {
            "action": "compress",
            "signature": __signature__,
            "manifest_id": manifest_id,
            "provider": provider,
            "tokens_saved_estimate": tokens_saved,
            "exact_identifiers": exact_ids,
            "png_base64": base64.b64encode(png_bytes).decode("ascii"),
            "png_width": width,
            "png_height": height,
            "storage": store_meta,
            "diagnostics": diag_post,
        }


def should_compress_text(text: str) -> bool:
    ok, _ = should_compress_payload(text)
    return ok


def compress_text(text: str, *, provider: str | None = None) -> dict[str, Any]:
    return LYGOCompressor().compress(text, provider=provider)