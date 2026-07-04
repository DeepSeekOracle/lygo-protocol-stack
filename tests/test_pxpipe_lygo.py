"""Tests for pxpipe-lygo (P0 gate, renderer, compressor)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pxpipe_lygo.p0_gate import should_compress_payload  # noqa: E402
from pxpipe_lygo.png_renderer import render_text_to_png  # noqa: E402
from pxpipe_lygo.compressor import compress_text  # noqa: E402
from pxpipe_lygo.message_adapters import compress_result_to_blocks  # noqa: E402
from pxpipe_lygo.agent_helper import maybe_compress_context  # noqa: E402


def test_should_not_compress_short_text():
    ok, diag = should_compress_payload("hello")
    assert ok is False
    assert diag.get("reason") == "below_min_chars"


def test_render_png_roundtrip():
    text = "LYGO pxpipe test\nline two\n" + ("x" * 200)
    png, w, h = render_text_to_png(text)
    assert len(png) > 100
    assert w > 0 and h > 0


def test_compress_long_prose_or_pass():
    text = ("# System prompt\n" + "Explain the LYGO lattice. " * 120).strip()
    result = compress_text(text, provider="grok")
    assert result["action"] in ("compress", "pass_through")
    assert "signature" in result
    if result["action"] == "compress":
        assert result["manifest_id"]
        assert "storage" in result
        blocks = compress_result_to_blocks(result, target="grok")
        assert blocks["action"] == "compress"
        assert isinstance(blocks["content"], list)


def test_maybe_compress_short_unchanged():
    assert maybe_compress_context("tiny") == "tiny"