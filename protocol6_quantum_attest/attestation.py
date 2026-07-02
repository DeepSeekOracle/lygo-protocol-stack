"""Badge generation and peer verification."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from .measurement import MeasurementCollector, P6_VERSION, get_p0_hash, verify_p0_hash_against_golden
from .puf_arbiter import puf_fingerprint


def _signing_key(measurement_digest: str, node_id: str, puf_fp: str) -> bytes:
    """Derived key from measurement + node + PUF fingerprint (no repo secrets)."""
    material = f"{measurement_digest}|{node_id}|{puf_fp}|{get_p0_hash()}"
    return hashlib.sha256(material.encode("utf-8")).digest()


class AttestationService:
    def __init__(self, collector: MeasurementCollector | None = None, *, node_id: str = "LYGO_NODE"):
        self.collector = collector or MeasurementCollector()
        self.node_id = node_id

    def generate_badge(self) -> dict[str, Any]:
        m = self.collector.collect()
        digest = str(m.get("measurement_digest", ""))
        payload = {
            "signature": P6_VERSION,
            "node_id": self.node_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "measurement": m,
            "p0_hash": m.get("p0_hash"),
            "measurement_digest": digest,
        }
        signable = {k: v for k, v in payload.items() if k not in ("signature", "badge_signature", "signed")}
        body = json.dumps(signable, sort_keys=True, default=str).encode("utf-8")
        puf_fp = str(m.get("puf_fingerprint") or puf_fingerprint())
        key = _signing_key(digest, self.node_id, puf_fp)
        sig = hmac.new(key, body, hashlib.sha256).hexdigest()
        payload["badge_signature"] = sig
        payload["signed"] = True
        return payload

    def verify_badge(self, badge: dict[str, Any]) -> bool:
        if not isinstance(badge, dict):
            return False
        sig = badge.get("badge_signature")
        if not sig:
            return False
        node_id = str(badge.get("node_id", "LYGO_NODE"))
        measurement = badge.get("measurement") or {}
        digest = str(badge.get("measurement_digest") or measurement.get("measurement_digest") or "")
        if not digest:
            return False
        p0 = badge.get("p0_hash") or measurement.get("p0_hash")
        if not verify_p0_hash_against_golden(str(p0 or "")):
            return False
        signable = {k: v for k, v in badge.items() if k not in ("signature", "badge_signature", "signed")}
        body = json.dumps(signable, sort_keys=True, default=str).encode("utf-8")
        puf_fp = str(measurement.get("puf_fingerprint") or "")
        if not puf_fp:
            return False
        key = _signing_key(digest, node_id, puf_fp)
        expected = hmac.new(key, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(str(sig), expected):
            return False
        return bool(measurement.get("p0_golden_ok", verify_p0_hash_against_golden(str(p0 or ""))))