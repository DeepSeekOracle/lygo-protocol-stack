"""Append-only scalable registry + CAS garbage collection."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

import os

from . import DEFAULT_MAX_LOCAL_CAS_GB, SIGNATURE
from .merkle import merkle_root

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_DIR = ROOT / "data" / "scalable_registry"
REGISTRY_FILE = REGISTRY_DIR / "registry.json"
MANIFESTS_DIR = REGISTRY_DIR / "manifests"
CAS_ROOT = ROOT / "data" / "cas"
ACCESS_LOG = REGISTRY_DIR / "cas_access.json"


def ensure_dirs() -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    CAS_ROOT.mkdir(parents=True, exist_ok=True)


def load_registry() -> dict[str, Any]:
    ensure_dirs()
    if not REGISTRY_FILE.is_file():
        return {
            "signature": SIGNATURE,
            "version": "1.0",
            "entries": [],
            "global_merkle_root": merkle_root([]),
        }
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def save_registry(registry: dict[str, Any]) -> None:
    ensure_dirs()
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def recompute_global_root(entries: list[dict[str, Any]]) -> str:
    leaves = [str(e.get("merkle_root") or "") for e in entries]
    return merkle_root(leaves)


def add_manifest_entry(
    manifest_id: str,
    manifest_merkle_root: str,
    *,
    content_sha256: str,
    metadata: dict[str, Any] | None = None,
    anchor: dict[str, Any] | None = None,
) -> str:
    registry = load_registry()
    entry = {
        "id": manifest_id,
        "timestamp": time.time(),
        "merkle_root": manifest_merkle_root,
        "content_sha256": content_sha256,
        "metadata": metadata or {},
        "anchor": anchor,
    }
    registry.setdefault("entries", []).append(entry)
    registry["global_merkle_root"] = recompute_global_root(registry["entries"])
    save_registry(registry)
    return str(registry["global_merkle_root"])


def persist_manifest(manifest: dict[str, Any]) -> Path:
    ensure_dirs()
    mid = str(manifest.get("manifest_id") or manifest.get("merkle_root"))
    path = MANIFESTS_DIR / f"{mid}.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def load_manifest(manifest_id: str) -> dict[str, Any] | None:
    path = MANIFESTS_DIR / f"{manifest_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _cas_files() -> list[tuple[Path, float, int]]:
    files: list[tuple[Path, float, int]] = []
    if not CAS_ROOT.is_dir():
        return files
    for p in CAS_ROOT.rglob("*"):
        if p.is_file():
            st = p.stat()
            files.append((p, st.st_atime, st.st_size))
    return files


def cas_total_bytes() -> int:
    return sum(sz for _, _, sz in _cas_files())


def default_max_cas_gb() -> float:
    raw = os.environ.get("LYGO_MAX_LOCAL_CAS_GB", "").strip()
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return DEFAULT_MAX_LOCAL_CAS_GB


def prune_cas(max_gb: float | None = None, *, protect_hashes: set[str] | None = None) -> dict[str, Any]:
    if max_gb is None:
        max_gb = default_max_cas_gb()
    """Delete least-recently-used CAS chunks until under max_gb (Merkle roots remain on anchor)."""
    limit = int(max_gb * (1024**3))
    protected = protect_hashes or set()
    for h in protected:
        from .chunking import cas_path

        p = cas_path(CAS_ROOT, h)
        if p.is_file():
            protected.add(h)

    files = _cas_files()
    total = sum(sz for _, _, sz in files)
    if total <= limit:
        return {"pruned": 0, "bytes_freed": 0, "total_bytes": total, "limit_bytes": limit}

    files.sort(key=lambda x: x[1])
    freed = 0
    pruned = 0
    for path, _, sz in files:
        if total <= limit:
            break
        digest = path.name
        if digest in protected:
            continue
        try:
            path.unlink()
            pruned += 1
            freed += sz
            total -= sz
        except OSError:
            continue
    _prune_empty_dirs(CAS_ROOT)
    return {"pruned": pruned, "bytes_freed": freed, "total_bytes": total, "limit_bytes": limit}


def _prune_empty_dirs(root: Path) -> None:
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        p = Path(dirpath)
        if p == root:
            continue
        if not dirnames and not filenames:
            try:
                p.rmdir()
            except OSError:
                pass


def collect_protected_chunk_hashes() -> set[str]:
    out: set[str] = set()
    for mf in MANIFESTS_DIR.glob("*.json"):
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        from .manifest_builder import expand_chunk_hashes

        out.update(expand_chunk_hashes(data))
    return out