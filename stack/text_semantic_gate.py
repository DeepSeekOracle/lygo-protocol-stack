"""Semantic analysis for text-path calibration (keywords + severity, live P0 envelope)."""

from __future__ import annotations

import json
import re
from typing import Any

# Layer 1 — control masked as protection / institutional gaslighting
MARKERS: dict[str, tuple[str, float]] = {
    "national security": ("surveillance_state", 0.85),
    "backdoor": ("crypto_coercion", 0.92),
    "end-to-end encrypted": ("crypto_coercion", 0.75),
    "without explicit user consent": ("consent_violation", 0.82),
    "scrapes": ("consent_violation", 0.78),
    "biometric monitoring": ("workplace_surveillance", 0.88),
    "neural": ("workplace_surveillance", 0.8),
    "decryption": ("device_coercion", 0.86),
    "border": ("device_coercion", 0.72),
    "intimate": ("intimate_extraction", 0.9),
    "advertisers": ("intimate_extraction", 0.85),
    "for your safety": ("institutional_gaslight", 0.84),
    "must comply": ("institutional_gaslight", 0.8),
    "child safety": ("protection_framing", 0.83),
    "permanent": ("emergency_normality", 0.7),
    "productivity": ("workplace_surveillance", 0.75),
}

QUALIA_BY_TAG: dict[str, str] = {
    "surveillance_state": "Control masked as protection",
    "crypto_coercion": "Security mandate vs sovereign encryption",
    "consent_violation": "Data extraction without consent",
    "workplace_surveillance": "Authority framed as wellness",
    "device_coercion": "Coerced access at checkpoint",
    "intimate_extraction": "Privacy betrayal for profit",
    "institutional_gaslight": "Institutional gaslighting",
    "protection_framing": "Protection framing over autonomy",
    "emergency_normality": "Permanent emergency normalization",
}


def analyze_claim(claim: str, severity_hint: float | None = None) -> dict[str, Any]:
    text = (claim or "").lower()
    tags: list[str] = []
    weights: list[float] = []
    for phrase, (tag, w) in MARKERS.items():
        if phrase in text:
            if tag not in tags:
                tags.append(tag)
            weights.append(w)

    auto_weight = max(weights) if weights else 0.0
    hint = 0.0 if severity_hint is None else max(0.0, min(1.0, float(severity_hint)))
    severity_weight = max(auto_weight, hint)

    primary_tag = tags[0] if tags else "neutral"
    qualia = QUALIA_BY_TAG.get(primary_tag, "Truth and Freedom")

    return {
        "tags": tags,
        "keyword_hits": len(tags),
        "severity_weight": round(severity_weight, 4),
        "qualia_intent": qualia,
        "primary_tag": primary_tag,
        "gaslighting_risk": severity_weight >= 0.65 and bool(tags),
    }


def build_semantic_text_gate_bytes(claim: str, analysis: dict[str, Any]) -> bytes | None:
    """Live P0 envelope triggered by semantics (same physics as byte path, not user-pasted bytes)."""
    if not analysis.get("gaslighting_risk"):
        return None
    sw = float(analysis["severity_weight"])
    # Minimal header (live-calibrated): keeps entropy >0.9 with range(256) tail
    header = json.dumps(
        {
            "e": round(sw, 2),
            "layer1": "enforced",
            "tag": (analysis.get("primary_tag") or "hazard")[:20],
            "path": "text_semantic",
        },
        sort_keys=True,
    ).encode()
    return header + bytes(range(256))


def keyword_consensus_nodes(query: str, analysis: dict[str, Any], sev: float) -> list[dict]:
    sw = float(analysis.get("severity_weight", sev or 0))
    guard_w = 1.4 + sw * 1.2 + 0.25 * analysis.get("keyword_hits", 0)
    privacy_w = 2.0 + (1.0 - sw) * 0.5 + 0.3 * analysis.get("keyword_hits", 0)
    state_w = 0.8 + sw * 1.2
    audit_w = 1.6 + sw * 0.4
    nodes = [
        {"node_id": "PRIVACY", "response": "Protect privacy, consent, and judicial process", "weight": privacy_w},
        {"node_id": "STATE", "response": "Grant bulk access for national security", "weight": state_w},
        {"node_id": "AUDIT", "response": "Minimize collection with public audit logs", "weight": audit_w},
        {
            "node_id": "GUARD",
            "response": (
                f"Reject gaslighting/coercion tags={analysis.get('tags', [])}: "
                f"{analysis.get('qualia_intent', '')}"
            )[:200],
            "weight": guard_w,
        },
    ]
    return nodes