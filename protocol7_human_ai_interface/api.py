"""HAIP REST helpers (stdlib + optional FastAPI)."""

from __future__ import annotations

from typing import Any

from .haip_service import HAIPService

_service: HAIPService | None = None


def get_haip() -> HAIPService:
    global _service
    if _service is None:
        _service = HAIPService()
    return _service


def handle_register(body: dict[str, Any]) -> dict[str, Any]:
    device_type = str(body.get("device_type", ""))
    device_id = str(body.get("device_id", ""))
    connection_type = str(body.get("connection_type", "simulated"))
    if not device_type or not device_id:
        return {"error": "device_type and device_id required", "status": "error"}
    try:
        return get_haip().register_device(device_type, device_id, connection_type)
    except ValueError as exc:
        return {"error": str(exc), "status": "error"}


def handle_biometric_state() -> dict[str, Any]:
    state = get_haip().get_biometric_state()
    if state.get("status") in ("no_devices", "no_data"):
        return {
            "timestamp": __import__("time").time(),
            "readings": {},
            "ethical_vector": [0.0, 0.0, 0.0],
            "frequency": 528,
            "light_code": None,
            "status": state.get("status"),
            "signature": "Δ9Φ963-PHASE7-v1.0",
        }
    return {
        "timestamp": state["timestamp"],
        "readings": state.get("readings", {}),
        "ethical_vector": state["ethical_vector"],
        "frequency": state["frequency"],
        "light_code": state.get("light_code"),
        "entropy": state.get("entropy"),
        "signature": state.get("signature"),
    }


def handle_biometric_history(query_seconds: int = 60) -> list[dict[str, Any]]:
    return get_haip().history(query_seconds)


def build_fastapi_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
    except ImportError:
        return None

    app = FastAPI(title="LYGO HAIP API", version="1.0")

    class DeviceRegister(BaseModel):
        device_type: str
        device_id: str
        connection_type: str = "simulated"

    @app.post("/device/register")
    async def register_device(device: DeviceRegister):
        out = handle_register(device.model_dump())
        if out.get("status") == "error":
            raise HTTPException(status_code=400, detail=out.get("error"))
        return out

    @app.get("/biometric/state")
    async def biometric_state():
        return handle_biometric_state()

    @app.get("/biometric/history")
    async def biometric_history(seconds: int = 60):
        return handle_biometric_history(seconds)

    return app


app = build_fastapi_app()