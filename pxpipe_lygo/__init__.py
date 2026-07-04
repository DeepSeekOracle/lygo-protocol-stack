"""LYGO pxpipe — sovereign vision-token compression (Biophase7 / lattice)."""

from __future__ import annotations

__version__ = "0.1.0"
__signature__ = "Δ9Φ963-PXPIPE-LYGO-v1"

from pxpipe_lygo.agent_helper import compress_text_for_tool, maybe_compress_context
from pxpipe_lygo.compressor import LYGOCompressor, compress_text, should_compress_text

__all__ = [
    "__version__",
    "__signature__",
    "LYGOCompressor",
    "compress_text",
    "should_compress_text",
    "compress_text_for_tool",
    "maybe_compress_context",
]