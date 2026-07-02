#!/usr/bin/env python3
"""
Stream-safe Content-Defined Chunking (CDC) + CAS.

Canonical implementation: tools/scalable_registry/chunking.py
Biophase7: The raw physics of the Content-Addr — 8 KiB disk stream, dedupe vault.
"""

from __future__ import annotations

from pathlib import Path

from scalable_registry.chunking import (  # noqa: F401
    DEFAULT_AVG_CHUNK,
    DEFAULT_MAX_CHUNK,
    DEFAULT_MIN_CHUNK,
    cas_path,
    chunk_file_to_cas,
    chunk_hash,
    content_defined_chunks,
    iter_content_defined_chunks,
    read_chunk_from_cas,
    read_json_from_cas,
    stream_chunks_ordered,
    write_chunk_to_cas,
    write_json_to_cas,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAS_DIR = str(ROOT / "data" / "cas")


def content_defined_chunks_from_path(
    file_path: str,
    min_size: int = DEFAULT_MIN_CHUNK,
    avg_size: int = DEFAULT_AVG_CHUNK,
    max_size: int = DEFAULT_MAX_CHUNK,
):
    """Alias for Biophase7 blueprint API (iterator from path string)."""
    return iter_content_defined_chunks(file_path, min_size=min_size, avg_size=avg_size, max_size=max_size)


def write_chunk_to_cas_dir(chunk: bytes, cas_dir: str = DEFAULT_CAS_DIR) -> str:
    return write_chunk_to_cas(chunk, cas_dir)