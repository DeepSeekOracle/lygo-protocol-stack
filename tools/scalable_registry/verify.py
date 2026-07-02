"""Registry + manifest verification (quarantine on tamper / bad provenance)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from . import SIGNATURE
from .manifest_builder import expand_chunk_hashes, manifest_content_sha256
from .merkle import merkle_root
from .provenance import verify_manifest_provenance
from .registry_manager import MANIFESTS_DIR, REGISTRY_FILE, load_manifest, load_registry, recompute_global_root

ROOT = Path(__file__).resolve().parents[2]
LAST_RUN = ROOT / "tests" / "scalable_registry_last_run.json"


def verify_registry_entries() -> tuple[bool, str]:
    reg = load_registry()
    entries = reg.get("entries") or []
    recomputed = recompute_global_root(entries)
    declared = str(reg.get("global_merkle_root") or "")
    if recomputed != declared:
        return False, f"global_merkle_root mismatch declared={declared[:16]}… recomputed={recomputed[:16]}…"
    return True, "ok"


def verify_manifest_file(manifest: dict[str, Any]) -> tuple[bool, str]:
    mtype = manifest.get("type")
    if mtype not in ("synthetic_data_manifest", "super_manifest", "sub_manifest"):
        return False, f"unknown manifest type {mtype}"
    prov = manifest.get("provenance") or {}
    if prov.get("note") == "unsigned_dev" and not prov.get("merkle_root_signature"):
        pass
    else:
        ok, msg = verify_manifest_provenance(manifest)
        if not ok:
            return False, f"provenance:{msg}"
    try:
        hashes = expand_chunk_hashes(manifest)
    except FileNotFoundError as exc:
        return False, str(exc)
    if mtype in ("synthetic_data_manifest", "sub_manifest"):
        expected_root = merkle_root(hashes)
        if expected_root != manifest.get("merkle_root"):
            return False, "leaf merkle_root mismatch"
    if mtype == "super_manifest":
        leaves = [str(r.get("merkle_root") or "") for r in manifest.get("sub_manifests") or []]
        if merkle_root(leaves) != manifest.get("merkle_root"):
            return False, "super merkle_root mismatch"
    actual_sha = manifest_content_sha256(manifest)
    declared_sha = manifest.get("content_sha256")
    if declared_sha and declared_sha != actual_sha:
        return False, "content_sha256 mismatch"
    return True, "ok"


def run_full_verify(*, write_artifact: bool = True) -> dict[str, Any]:
    t0 = time.time()
    checks: list[dict[str, Any]] = []
    all_pass = True

    ok, msg = verify_registry_entries()
    checks.append({"id": "REG-01-global-root", "pass": ok, "note": msg})
    all_pass &= ok

    reg = load_registry()
    for entry in reg.get("entries") or []:
        mid = str(entry.get("id") or "")
        manifest = load_manifest(mid)
        if manifest is None:
            checks.append({"id": f"REG-manifest-{mid[:12]}", "pass": False, "note": "missing file"})
            all_pass = False
            continue
        ok_m, note_m = verify_manifest_file(manifest)
        if ok_m and str(entry.get("merkle_root")) != str(manifest.get("merkle_root")):
            ok_m, note_m = False, "registry entry merkle_root != manifest"
        checks.append({"id": f"REG-entry-{mid[:12]}", "pass": ok_m, "note": note_m})
        all_pass &= ok_m

    for path in MANIFESTS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            checks.append({"id": f"REG-file-{path.name[:12]}", "pass": False, "note": "json corrupt"})
            all_pass = False
            continue
        ok_f, note_f = verify_manifest_file(data)
        checks.append({"id": f"REG-file-{path.stem[:12]}", "pass": ok_f, "note": note_f})
        all_pass &= ok_f

    verdict = "ALIGNED" if all_pass else "QUARANTINE"
    report = {
        "signature": SIGNATURE,
        "verdict": verdict,
        "all_pass": all_pass,
        "checks": checks,
        "global_merkle_root": reg.get("global_merkle_root"),
        "entry_count": len(reg.get("entries") or []),
        "duration_ms": int((time.time() - t0) * 1000),
    }
    if write_artifact:
        LAST_RUN.parent.mkdir(parents=True, exist_ok=True)
        LAST_RUN.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report