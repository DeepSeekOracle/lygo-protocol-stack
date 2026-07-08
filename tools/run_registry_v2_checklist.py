#!/usr/bin/env python3
"""v2 verification checklist (Lightfather hardened blueprint)."""

from __future__ import annotations

import copy
import json
import secrets
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from scalable_registry import MAX_MANIFEST_JSON_BYTES, SUB_MANIFEST_MAX_HASHES  # noqa: E402
from scalable_registry.chunking import write_chunk_to_cas  # noqa: E402
from scalable_registry.manifest_builder import (  # noqa: E402
    _json_len,
    build_manifest_from_hashes,
    manifest_content_sha256,
)
from scalable_registry.registry_manager import (  # noqa: E402
    CAS_ROOT,
    add_manifest_entry,
    collect_protected_chunk_hashes,
    load_registry,
    persist_manifest,
    prune_cas,
)
from scalable_registry.retrieve import verify_and_stream_to_file  # noqa: E402
from scalable_registry.verify import verify_manifest_file  # noqa: E402

OUT = ROOT / "tests" / "scalable_registry_v2_checklist_last_run.json"


def main() -> int:
    checks: list[dict] = []
    t0 = time.time()

    hashes = []
    for _ in range(1500):
        hashes.append(write_chunk_to_cas(secrets.token_bytes(400), CAS_ROOT))
    manifest = build_manifest_from_hashes(
        hashes,
        {"name": "checklist-hier", "version": "2"},
        size_bytes=1500 * 400,
        node_id="CHECKLIST_NODE",
        require_p6=False,
    )
    ok_hier = manifest.get("type") == "super_manifest" and len(manifest.get("sub_manifests") or []) >= 2
    checks.append(
        {
            "id": "V2-01-hierarchical-split",
            "pass": ok_hier,
            "note": f"subs={len(manifest.get('sub_manifests') or [])} chunks={manifest.get('chunk_count')}",
        }
    )
    ok_size = _json_len(manifest) <= MAX_MANIFEST_JSON_BYTES
    checks.append(
        {
            "id": "V2-02-super-under-85kib",
            "pass": ok_size,
            "note": f"bytes={_json_len(manifest)} limit={MAX_MANIFEST_JSON_BYTES}",
        }
    )

    prov = manifest.get("provenance") or {}
    checks.append(
        {
            "id": "V2-03-provenance-present",
            "pass": bool(prov.get("generator_node_id")),
            "note": "signed when require_p6; dev unsigned allowed",
        }
    )

    bad = copy.deepcopy(manifest)
    bad["provenance"] = {
        "generator_node_id": "ROGUE",
        "measurement_digest": "deadbeef",
        "p0_hash": prov.get("p0_hash") or "00" * 32,
        "puf_fingerprint": "aa" * 16,
        "merkle_root_signature": "0" * 64,
        "signature_scheme": "P6-HMAC-SHA256-v1",
    }
    ok_bad, _ = verify_manifest_file(bad)
    checks.append({"id": "V2-04-reject-bad-signature", "pass": not ok_bad, "note": "tampered sig quarantined"})

    payload = secrets.token_bytes(2_000_000)
    from scalable_registry.manifest_builder import build_manifest_from_bytes

    m2 = build_manifest_from_bytes(payload, {"name": "mem-test"}, CAS_ROOT, require_p6=False)
    dest = ROOT / "tests" / "_registry_checklist_out.bin"
    tracemalloc.start()
    verify_and_stream_to_file(m2, dest)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    dest.unlink(missing_ok=True)
    checks.append(
        {
            "id": "V2-05-stream-retrieve-ram",
            "pass": peak < 100 * 1024 * 1024,
            "note": f"peak_bytes={peak}",
        }
    )

    mid = manifest["manifest_id"]
    manifest["content_sha256"] = manifest_content_sha256(manifest)
    persist_manifest(manifest)
    add_manifest_entry(mid, manifest["merkle_root"], content_sha256=manifest["content_sha256"], metadata={})
    reg_before = load_registry()
    protected = collect_protected_chunk_hashes()
    prune_cas(0.000001, protect_hashes=protected)
    reg_after = load_registry()
    checks.append(
        {
            "id": "V2-06-prune-preserves-registry",
            "pass": reg_before.get("global_merkle_root") == reg_after.get("global_merkle_root"),
            "note": "immutable registry index",
        }
    )

    checks.append(
        {
            "id": "V2-07-sub-batch-cap",
            "pass": SUB_MANIFEST_MAX_HASHES == 1000,
            "note": "directive chunk size",
        }
    )

    all_pass = all(c["pass"] for c in checks)
    report = {
        "signature": "Δ9Φ963-SCALABLE-REGISTRY-v2-CHECKLIST",
        "all_pass": all_pass,
        "checks": checks,
        "duration_ms": int((time.time() - t0) * 1000),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())