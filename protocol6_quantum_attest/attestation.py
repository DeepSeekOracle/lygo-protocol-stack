"""Badge generation and peer verification."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from .keylime_bridge import KeylimeAttestation
from .measurement import MeasurementCollector, P6_VERSION, get_p0_hash, verify_p0_hash_against_golden

PHI_MIN = 0.618
PHI_MAX = 1.618
FRESHNESS_MAX_AGE_SEC = 300
P6_POLISH_SIGNATURE = "Δ9Φ963-P6-POLISH-v1.0"
from .puf_arbiter import puf_fingerprint


def _signing_key(measurement_digest: str, node_id: str, puf_fp: str) -> bytes:
    """Derived key from measurement + node + PUF fingerprint (no repo secrets)."""
    material = f"{measurement_digest}|{node_id}|{puf_fp}|{get_p0_hash()}"
    return hashlib.sha256(material.encode("utf-8")).digest()


class AttestationService:
    def __init__(self, collector: MeasurementCollector | None = None, *, node_id: str = "LYGO_NODE"):
        self.node_id = node_id
        self.collector = collector or MeasurementCollector(node_id=node_id)

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
        return self.verify_badge_detailed(badge).get("valid", False)

    def _parse_badge_age_sec(self, badge: dict[str, Any]) -> float | None:
        ts = badge.get("timestamp")
        if ts is None:
            return None
        if isinstance(ts, (int, float)):
            return max(0.0, datetime.now(timezone.utc).timestamp() - float(ts))
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds())
        except (ValueError, TypeError):
            return None

    def _check_ethical_gate(self, badge: dict[str, Any]) -> bool:
        """Φ-band gate: P0 golden OK + measurement integrity markers."""
        measurement = badge.get("measurement") or {}
        p0 = str(badge.get("p0_hash") or measurement.get("p0_hash") or "")
        if not verify_p0_hash_against_golden(p0):
            return False
        if not measurement.get("p0_golden_ok", True):
            return False
        tpm = measurement.get("tpm") or {}
        if tpm.get("mode") == "stub" and not measurement.get("puf_fingerprint"):
            return False
        quote = measurement.get("tpm_quote")
        if quote is not None and not KeylimeAttestation.verify_quote(quote if isinstance(quote, dict) else None):
            return False
        return True

    def _check_freshness(self, badge: dict[str, Any], max_age: float = FRESHNESS_MAX_AGE_SEC) -> bool:
        age = self._parse_badge_age_sec(badge)
        if age is None:
            return True
        return age <= max_age

    def verify_badge_detailed(self, badge: dict[str, Any]) -> dict[str, Any]:
        reasons: list[str] = []
        if not isinstance(badge, dict):
            return {
                "valid": False,
                "alignment": "MISALIGNED",
                "ethical_gate": False,
                "p0_match": False,
                "fresh": False,
                "reasons": ["invalid badge object"],
                "signature": P6_POLISH_SIGNATURE,
            }

        measurement = badge.get("measurement") or {}
        p0 = str(badge.get("p0_hash") or measurement.get("p0_hash") or "")
        p0_match = verify_p0_hash_against_golden(p0)
        if not p0_match:
            reasons.append("P0 hash mismatch")

        sig = badge.get("badge_signature")
        signature_valid = False
        if not sig:
            reasons.append("missing badge_signature")
        else:
            node_id = str(badge.get("node_id", "LYGO_NODE"))
            digest = str(badge.get("measurement_digest") or measurement.get("measurement_digest") or "")
            puf_fp = str(measurement.get("puf_fingerprint") or "")
            if not digest or not puf_fp:
                reasons.append("missing measurement digest or PUF fingerprint")
            else:
                signable = {k: v for k, v in badge.items() if k not in ("signature", "badge_signature", "signed")}
                body = json.dumps(signable, sort_keys=True, default=str).encode("utf-8")
                key = _signing_key(digest, node_id, puf_fp)
                expected = hmac.new(key, body, hashlib.sha256).hexdigest()
                signature_valid = hmac.compare_digest(str(sig), expected)
                if not signature_valid:
                    reasons.append("invalid HMAC signature")

        ethical_gate_passed = self._check_ethical_gate(badge)
        if not ethical_gate_passed:
            reasons.append("ethical gate failed")

        fresh = self._check_freshness(badge)
        if not fresh:
            reasons.append("measurement stale")

        valid = p0_match and signature_valid and ethical_gate_passed and fresh
        return {
            "valid": valid,
            "alignment": "ALIGNED" if valid else "MISALIGNED",
            "ethical_gate": ethical_gate_passed,
            "p0_match": p0_match,
            "signature_valid": signature_valid,
            "fresh": fresh,
            "reasons": reasons,
            "p0_hash": get_p0_hash(),
            "signature": P6_POLISH_SIGNATURE,
        }