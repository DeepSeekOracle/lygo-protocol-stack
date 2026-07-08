"""Attestation REST helpers (stdlib HTTP server integration)."""

from __future__ import annotations

from typing import Any

from .attestation import AttestationService
from .measurement import MeasurementCollector

_services: dict[str, AttestationService] = {}


def get_service(node_id: str = "LYGO_NODE") -> AttestationService:
    if node_id not in _services:
        _services[node_id] = AttestationService(MeasurementCollector(), node_id=node_id)
    return _services[node_id]


def handle_health() -> dict[str, Any]:
    return MeasurementCollector().health()


def handle_badge_get(node_id: str = "LYGO_NODE") -> dict[str, Any]:
    return get_service(node_id).generate_badge()


def handle_verify_post(body: dict[str, Any]) -> dict[str, Any]:
    badge = body.get("badge") if isinstance(body.get("badge"), dict) else body
    if not isinstance(badge, dict):
        return {"valid": False, "error": "missing badge object"}
    # Verification uses badge's node_id and measurement digest for key derivation
    node_id = str(badge.get("node_id", "LYGO_NODE"))
    valid = get_service(node_id).verify_badge(badge)
    return {
        "valid": valid,
        "node_id": node_id,
        "signature": "Δ9Φ963-PHASE6-v1.0",
    }


# Optional FastAPI app when installed (deployment guide)
def build_fastapi_app():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
    except ImportError:
        return None

    app = FastAPI(title="LYGO Phase 6 Attestation", version="1.0")

    class VerifyBody(BaseModel):
        badge: dict

    @app.get("/attestation/health")
    def health():
        return handle_health()

    @app.get("/attestation/badge")
    def badge():
        return handle_badge_get()

    @app.post("/attestation/verify")
    def verify(body: VerifyBody):
        return handle_verify_post(body.model_dump())

    return app


app = build_fastapi_app()