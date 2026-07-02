"""Content-defined chunking (CDC) and content-addressable storage (CAS)."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import BinaryIO, Iterator

from . import CAS_SUBDIR_DEPTH

# Rabin-style CDC (deterministic, no external deps)
_CDC_PRIME = 1_000_003
_CDC_BASE = 257


def chunk_hash(chunk: bytes) -> str:
    return hashlib.sha256(chunk).hexdigest()


def _rolling_break(data: bytes, start: int, min_size: int, avg_size: int, max_size: int) -> int:
    """Return end offset (exclusive) for next chunk starting at start."""
    n = len(data)
    if start >= n:
        return n
    end_limit = min(n, start + max_size)
    if end_limit - start <= min_size:
        return end_limit
    mask = max(avg_size - 1, 1)
    if mask & (mask - 1):
        mask = 1 << (avg_size.bit_length() - 1)
    h = 0
    pos = start
    while pos < end_limit:
        h = (h * _CDC_BASE + data[pos]) % _CDC_PRIME
        pos += 1
        if pos - start >= min_size and (h & mask) == 0:
            return pos
    return end_limit


def content_defined_chunks(
    data: bytes,
    *,
    min_size: int = 256 * 1024,
    avg_size: int = 1024 * 1024,
    max_size: int = 4 * 1024 * 1024,
) -> list[bytes]:
    chunks: list[bytes] = []
    i = 0
    while i < len(data):
        j = _rolling_break(data, i, min_size, avg_size, max_size)
        chunks.append(data[i:j])
        i = j
    return chunks


def cas_path(cas_root: Path, digest: str) -> Path:
    if len(digest) < CAS_SUBDIR_DEPTH * 2:
        raise ValueError("invalid digest")
    parts = [digest[i : i + 2] for i in range(0, CAS_SUBDIR_DEPTH * 2, 2)]
    return cas_root.joinpath(*parts, digest)


def write_chunk_to_cas(chunk: bytes, cas_root: Path, *, touch_access: bool = True) -> str:
    digest = chunk_hash(chunk)
    path = cas_path(cas_root, digest)
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(chunk)
    if touch_access:
        now = time.time()
        os.utime(path, (now, now))
    return digest


def read_chunk_from_cas(digest: str, cas_root: Path) -> bytes:
    path = cas_path(cas_root, digest)
    if not path.is_file():
        raise FileNotFoundError(f"CAS miss: {digest}")
    now = time.time()
    os.utime(path, (now, now))
    return path.read_bytes()


def chunk_file_to_cas(
    file_path: Path,
    cas_root: Path,
    *,
    min_size: int = 256 * 1024,
    avg_size: int = 1024 * 1024,
    max_size: int = 4 * 1024 * 1024,
    read_size: int = 1024 * 1024,
) -> list[str]:
    """Stream file from disk; dedupe via CAS. Returns ordered chunk hashes."""
    hashes: list[str] = []
    buf = bytearray()
    with file_path.open("rb") as f:
        while True:
            block = f.read(read_size)
            if not block and not buf:
                break
            if block:
                buf.extend(block)
            while len(buf) >= min_size:
                view = bytes(buf)
                end = _rolling_break(view, 0, min_size, avg_size, max_size)
                if end == 0:
                    break
                chunk = view[:end]
                hashes.append(write_chunk_to_cas(chunk, cas_root))
                del buf[:end]
            if not block:
                if buf:
                    hashes.append(write_chunk_to_cas(bytes(buf), cas_root))
                    buf.clear()
                break
    if not hashes and file_path.stat().st_size == 0:
        hashes.append(write_chunk_to_cas(b"", cas_root))
    return hashes


def stream_chunks_ordered(hashes: list[str], cas_root: Path) -> Iterator[bytes]:
    for h in hashes:
        yield read_chunk_from_cas(h, cas_root)