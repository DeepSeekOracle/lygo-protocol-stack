"""Content-defined chunking (CDC) and content-addressable storage (CAS).

Biophase7 physics: stream from disk in 8 KiB blocks, rolling-hash boundaries,
dedupe on write — never load full dataset into RAM.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Iterator

from . import CAS_SUBDIR_DEPTH

# Rabin-style CDC (in-memory / secondary)
_CDC_PRIME = 1_000_003
_CDC_BASE = 257

# Biophase7 stream CDC defaults (The raw physics of the Content-Addr)
DEFAULT_MIN_CHUNK = 512 * 1024
DEFAULT_AVG_CHUNK = 1024 * 1024
DEFAULT_MAX_CHUNK = 4 * 1024 * 1024
STREAM_READ_SIZE = 8192


def chunk_hash(chunk: bytes) -> str:
    return hashlib.sha256(chunk).hexdigest()


def _rolling_break(data: bytes, start: int, min_size: int, avg_size: int, max_size: int) -> int:
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
    min_size: int = DEFAULT_MIN_CHUNK,
    avg_size: int = DEFAULT_AVG_CHUNK,
    max_size: int = DEFAULT_MAX_CHUNK,
) -> list[bytes]:
    chunks: list[bytes] = []
    i = 0
    while i < len(data):
        j = _rolling_break(data, i, min_size, avg_size, max_size)
        chunks.append(data[i:j])
        i = j
    return chunks


def iter_content_defined_chunks(
    file_path: str | Path,
    *,
    min_size: int = DEFAULT_MIN_CHUNK,
    avg_size: int = DEFAULT_AVG_CHUNK,
    max_size: int = DEFAULT_MAX_CHUNK,
) -> Iterator[bytes]:
    """
    Stream-safe CDC (Biophase7): yields chunks incrementally from disk.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    prime = 257
    mod = max(avg_size, 1)
    buffer = bytearray()
    rolling_hash = 0

    with path.open("rb") as f:
        while True:
            block = f.read(STREAM_READ_SIZE)
            if not block:
                if buffer:
                    yield bytes(buffer)
                break

            for byte in block:
                buffer.append(byte)
                rolling_hash = (rolling_hash * prime + byte) % mod
                current_len = len(buffer)
                if current_len >= min_size:
                    if rolling_hash == 0 or current_len >= max_size:
                        yield bytes(buffer)
                        buffer.clear()
                        rolling_hash = 0

            if len(buffer) >= max_size:
                yield bytes(buffer)
                buffer.clear()
                rolling_hash = 0


def cas_path(cas_root: Path, digest: str) -> Path:
    if len(digest) < CAS_SUBDIR_DEPTH * 2:
        raise ValueError("invalid digest")
    parts = [digest[i : i + 2] for i in range(0, CAS_SUBDIR_DEPTH * 2, 2)]
    return cas_root.joinpath(*parts, digest)


def write_chunk_to_cas(
    chunk: bytes,
    cas_root: Path | str = "data/cas",
    *,
    touch_access: bool = True,
) -> str:
    root = Path(cas_root)
    digest = chunk_hash(chunk)
    path = cas_path(root, digest)
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(chunk)
    if touch_access:
        now = time.time()
        os.utime(path, (now, now))
    return digest


def write_json_to_cas(obj: dict, cas_root: Path) -> str:
    """Store manifest/sub-manifest JSON in CAS (content-addressed blob)."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return write_chunk_to_cas(payload, cas_root)


def read_json_from_cas(content_id: str, cas_root: Path) -> dict:
    raw = read_chunk_from_cas(content_id, cas_root)
    return json.loads(raw.decode("utf-8"))


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
    min_size: int = DEFAULT_MIN_CHUNK,
    avg_size: int = DEFAULT_AVG_CHUNK,
    max_size: int = DEFAULT_MAX_CHUNK,
) -> list[str]:
    """Stream file → CAS; returns ordered chunk hashes (dedupe)."""
    hashes: list[str] = []
    empty = True
    for chunk in iter_content_defined_chunks(
        file_path, min_size=min_size, avg_size=avg_size, max_size=max_size
    ):
        empty = False
        hashes.append(write_chunk_to_cas(chunk, cas_root))
    if empty and file_path.stat().st_size == 0:
        hashes.append(write_chunk_to_cas(b"", cas_root))
    return hashes


def stream_chunks_ordered(hashes: list[str], cas_root: Path) -> Iterator[bytes]:
    for h in hashes:
        yield read_chunk_from_cas(h, cas_root)