"""Phase 6 hardware-attested provenance for manifest merkle roots."""

from __future__ import annotations

import hashlib
import hmac
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


class ProvenanceError(RuntimeError):
    pass


def _ensure_p6_path() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def sign_merkle_root(merkle_root: str, *, node_id: str = "LYGO_REGISTRY_NODE") -> dict[str, Any]:
    """P6-attested HMAC over merkle_root (TPM/PUF-derived key material)."""
    _ensure_p6_path()
    from protocol6_quantum_attest.measurement import (  # noqa: E402
        MeasurementCollector,
        verify_p0_hash_against_golden,
    )
    from protocol6_quantum_attest.attestation import _signing_key  # noqa: E402
    from protocol6_quantum_attest.puf_arbiter import puf_fingerprint  # noqa: E402

    coll = MeasurementCollector(node_id=node_id)
    m = coll.collect()
    p0 = str(m.get("p0_hash") or "")
    if not verify_p0_hash_against_golden(p0):
        raise ProvenanceError("P0 golden check failed — cannot sign manifest (no verified hardware badge path)")
    digest = str(m.get("measurement_digest") or "")
    if not digest:
        raise ProvenanceError("missing measurement_digest")
    puf_fp = str(m.get("puf_fingerprint") or puf_fingerprint())
    key = _signing_key(digest, node_id, puf_fp)
    sig = hmac.new(key, merkle_root.encode("utf-8"), hashlib.sha256).hexdigest()
    return {
        "generator_node_id": node_id,
        "measurement_digest": digest,
        "p0_hash": p0,
        "puf_fingerprint": puf_fp,
        "merkle_root_signature": sig,
        "signature_scheme": "P6-HMAC-SHA256-v1",
    }


def verify_manifest_provenance(manifest: dict[str, Any]) -> tuple[bool, str]:
    prov = manifest.get("provenance") or {}
    if not prov.get("merkle_root_signature"):
        return False, "missing merkle_root_signature"
    merkle_root = str(manifest.get("merkle_root") or "")
    if not merkle_root:
        return False, "missing merkle_root"
    _ensure_p6_path()
    from protocol6_quantum_attest.measurement import verify_p0_hash_against_golden  # noqa: E402
    from protocol6_quantum_attest.attestation import _signing_key  # noqa: E402

    p0 = str(prov.get("p0_hash") or "")
    if not verify_p0_hash_against_golden(p0):
        return False, "generator p0_hash not aligned with golden"
    node_id = str(prov.get("generator_node_id") or "LYGO_REGISTRY_NODE")
    digest = str(prov.get("measurement_digest") or "")
    puf_fp = str(prov.get("puf_fingerprint") or "")
    if not puf_fp:
        return False, "missing puf_fingerprint in provenance"
    key = _signing_key(digest, node_id, puf_fp)
    expected = hmac.new(key, merkle_root.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(str(prov.get("merkle_root_signature")), expected):
        return False, "merkle_root_signature mismatch"
    return True, "ok"