"""Hierarchical manifests (≤90 KiB JSON) + optional anchor."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from . import MAX_MANIFEST_JSON_BYTES, SIGNATURE, SUB_MANIFEST_MAX_HASHES
from .chunking import chunk_file_to_cas, chunk_hash, content_defined_chunks, write_chunk_to_cas
from .merkle import merkle_root
from .provenance import ProvenanceError, sign_merkle_root

ROOT = Path(__file__).resolve().parents[2]


def _canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _json_len(obj: dict) -> int:
    return len(_canonical_json(obj))


def _leaf_manifest(
    chunk_hashes: list[str],
    metadata: dict[str, Any],
    *,
    size_bytes: int,
    manifest_type: str = "synthetic_data_manifest",
) -> dict[str, Any]:
    root = merkle_root(chunk_hashes)
    return {
        "signature": SIGNATURE,
        "type": manifest_type,
        "version": metadata.get("version", "1.0"),
        "timestamp": time.time(),
        "metadata": metadata,
        "chunk_hashes": chunk_hashes,
        "merkle_root": root,
        "chunk_count": len(chunk_hashes),
        "size_bytes": size_bytes,
    }


def _super_manifest(sub_refs: list[dict[str, Any]], metadata: dict[str, Any], *, size_bytes: int) -> dict[str, Any]:
    leaves = [str(r.get("merkle_root") or r.get("content_sha256") or "") for r in sub_refs]
    root = merkle_root(leaves)
    return {
        "signature": SIGNATURE,
        "type": "super_manifest",
        "version": metadata.get("version", "1.0"),
        "timestamp": time.time(),
        "metadata": metadata,
        "sub_manifests": sub_refs,
        "merkle_root": root,
        "chunk_count": sum(int(r.get("chunk_count") or 0) for r in sub_refs),
        "size_bytes": size_bytes,
    }


def _fit_chunk_batches(hashes: list[str], metadata: dict[str, Any], size_bytes: int) -> list[list[str]]:
    """Split hash list so each leaf manifest JSON stays under MAX_MANIFEST_JSON_BYTES."""
    if not hashes:
        return [[]]
    lo, hi = 1, len(hashes)
    best = 1
    while lo <= hi:
        mid = (lo + hi) // 2
        sample = _leaf_manifest(hashes[:mid], metadata, size_bytes=size_bytes)
        if _json_len(sample) <= MAX_MANIFEST_JSON_BYTES:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    batch_size = max(1, min(best, SUB_MANIFEST_MAX_HASHES))
    batches: list[list[str]] = []
    for i in range(0, len(hashes), batch_size):
        batches.append(hashes[i : i + batch_size])
    return batches


def attach_provenance(manifest: dict[str, Any], *, node_id: str, require_p6: bool = True) -> dict[str, Any]:
    root = str(manifest.get("merkle_root") or "")
    try:
        manifest["provenance"] = sign_merkle_root(root, node_id=node_id)
    except ProvenanceError:
        if require_p6:
            raise
        manifest["provenance"] = {"generator_node_id": node_id, "merkle_root_signature": "", "note": "unsigned_dev"}
    return manifest


def build_manifest_from_bytes(
    data: bytes,
    metadata: dict[str, Any],
    cas_root: Path,
    *,
    node_id: str = "LYGO_REGISTRY_NODE",
    require_p6: bool = True,
) -> dict[str, Any]:
    chunks = content_defined_chunks(data)
    hashes = [write_chunk_to_cas(c, cas_root) for c in chunks]
    return build_manifest_from_hashes(hashes, metadata, size_bytes=len(data), node_id=node_id, require_p6=require_p6)


def build_manifest_from_file(
    path: Path,
    metadata: dict[str, Any],
    cas_root: Path,
    *,
    node_id: str = "LYGO_REGISTRY_NODE",
    require_p6: bool = True,
) -> dict[str, Any]:
    size_bytes = path.stat().st_size
    hashes = chunk_file_to_cas(path, cas_root)
    return build_manifest_from_hashes(
        hashes, metadata, size_bytes=size_bytes, node_id=node_id, require_p6=require_p6
    )


def build_manifest_from_hashes(
    hashes: list[str],
    metadata: dict[str, Any],
    *,
    size_bytes: int,
    node_id: str = "LYGO_REGISTRY_NODE",
    require_p6: bool = True,
) -> dict[str, Any]:
    probe = _leaf_manifest(hashes, metadata, size_bytes=size_bytes)
    if _json_len(probe) <= MAX_MANIFEST_JSON_BYTES:
        attach_provenance(probe, node_id=node_id, require_p6=require_p6)
        probe["manifest_id"] = hashlib.sha256(_canonical_json(probe)).hexdigest()
        return probe

    from .registry_manager import persist_manifest

    batches = _fit_chunk_batches(hashes, metadata, size_bytes)
    sub_refs: list[dict[str, Any]] = []
    for idx, batch in enumerate(batches):
        sub = _leaf_manifest(batch, {**metadata, "sub_index": idx}, size_bytes=size_bytes)
        attach_provenance(sub, node_id=node_id, require_p6=require_p6)
        sub["manifest_id"] = hashlib.sha256(_canonical_json(sub)).hexdigest()
        persist_manifest(sub)
        sub_sha = manifest_content_sha256(sub)
        sub_refs.append(
            {
                "sub_index": idx,
                "manifest_id": sub["manifest_id"],
                "merkle_root": sub["merkle_root"],
                "chunk_count": sub["chunk_count"],
                "content_sha256": sub_sha,
            }
        )

    super_m = _super_manifest(sub_refs, metadata, size_bytes=size_bytes)
    attach_provenance(super_m, node_id=node_id, require_p6=require_p6)
    super_m["manifest_id"] = hashlib.sha256(_canonical_json(super_m)).hexdigest()
    return super_m


def manifest_content_sha256(manifest: dict[str, Any]) -> str:
    body = {k: v for k, v in manifest.items() if k != "content_sha256"}
    return hashlib.sha256(_canonical_json(body)).hexdigest()


def expand_chunk_hashes(manifest: dict[str, Any]) -> list[str]:
    if manifest.get("type") == "super_manifest":
        from .registry_manager import load_manifest

        out: list[str] = []
        for ref in manifest.get("sub_manifests") or []:
            sub = ref.get("inline")
            if sub is None:
                mid = str(ref.get("manifest_id") or "")
                sub = load_manifest(mid) if mid else None
            if not sub:
                raise FileNotFoundError(f"sub-manifest missing for ref {ref}")
            out.extend(list(sub.get("chunk_hashes") or []))
        return out
    return list(manifest.get("chunk_hashes") or [])


def anchor_manifest_local(manifest: dict[str, Any], *, label: str | None = None) -> dict[str, Any]:
    import sys

    tools = ROOT / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from lygo_anchor import LYGOAnchor  # noqa: E402

    payload = _canonical_json(manifest)
    if len(payload) > MAX_MANIFEST_JSON_BYTES:
        raise ValueError(f"manifest JSON {len(payload)} exceeds {MAX_MANIFEST_JSON_BYTES}")
    anchor = LYGOAnchor()
    name = label or str((manifest.get("metadata") or {}).get("name", "manifest"))
    result = anchor.anchor_bytes(payload, f"scalable_registry:{name}", description=name)
    anchor_meta = {
        "success": getattr(result, "success", True),
        "url": getattr(result, "url", None),
        "service": getattr(result, "service", "local"),
        "content_sha256": getattr(result, "content_sha256", None),
    }
    return {"manifest_sha256": hashlib.sha256(payload).hexdigest(), "anchor": anchor_meta}


def anchor_manifest_tree(manifest: dict[str, Any], *, anchor_subs: bool = True) -> dict[str, Any]:
    """Anchor sub-manifests first (v2), then super/leaf primary entry."""
    out: dict[str, Any] = {"primary": None, "sub_anchors": []}
    if manifest.get("type") == "super_manifest" and anchor_subs:
        for ref in manifest.get("sub_manifests") or []:
            mid = str(ref.get("manifest_id") or "")
            from .registry_manager import load_manifest

            sub = load_manifest(mid)
            if not sub:
                raise FileNotFoundError(f"sub-manifest {mid} missing for anchor")
            anchored = anchor_manifest_local(sub, label=f"sub-{ref.get('sub_index', 0)}")
            ref["anchor"] = anchored.get("anchor")
            ref["anchor_url"] = (anchored.get("anchor") or {}).get("url")
            ref["anchor_content_sha256"] = anchored.get("manifest_sha256")
            out["sub_anchors"].append({"manifest_id": mid, **anchored})
        from .registry_manager import persist_manifest

        persist_manifest(manifest)
    name = str((manifest.get("metadata") or {}).get("name", "manifest"))
    out["primary"] = anchor_manifest_local(manifest, label=name)
    return out