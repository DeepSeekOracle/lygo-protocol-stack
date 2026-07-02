"""Stream-safe manifest reassembly (chunk verify + disk write)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .chunking import cas_path, chunk_hash
from .manifest_builder import expand_chunk_hashes
from .registry_manager import CAS_ROOT, load_manifest


def verify_and_stream_to_file(
    manifest: dict,
    dest: Path,
    *,
    cas_root: Path | None = None,
) -> dict:
    cas = cas_root or CAS_ROOT
    hashes = expand_chunk_hashes(manifest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    if dest.exists():
        dest.unlink()
    with dest.open("ab") as out:
        for h in hashes:
            path = cas_path(cas, h)
            if not path.is_file():
                raise FileNotFoundError(f"missing CAS chunk {h}")
            hasher = hashlib.sha256()
            with path.open("rb") as src:
                while True:
                    block = src.read(1024 * 1024)
                    if not block:
                        break
                    hasher.update(block)
                    out.write(block)
                    written += len(block)
            if hasher.hexdigest() != h:
                raise ValueError(f"TAMPER_DETECTED chunk expected={h} actual={hasher.hexdigest()}")
    expected_size = int(manifest.get("size_bytes") or 0)
    if expected_size and written != expected_size:
        raise ValueError(f"size mismatch wrote={written} expected={expected_size}")
    return {"ok": True, "bytes_written": written, "chunks": len(hashes)}


def retrieve_by_id(manifest_id: str, dest: Path, *, cas_root: Path | None = None) -> dict:
    manifest = load_manifest(manifest_id)
    if manifest is None:
        raise FileNotFoundError(manifest_id)
    return verify_and_stream_to_file(manifest, dest, cas_root=cas_root)