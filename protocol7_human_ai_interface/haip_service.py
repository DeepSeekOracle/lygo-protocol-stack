"""HAIP orchestration — devices, pipeline, ethical + entropy outputs."""

from __future__ import annotations

import time
from typing import Any

from .data_pipeline import BiometricPipeline
from .device_abstraction import ADAPTER_TYPES, DeviceAdapter, create_adapter
from .entropy_extraction import BiometricEntropyHarness
from .ethical_mapping import EthicalVectorMapper

P7_VERSION = "Δ9Φ963-PHASE7-v1.0"


class HAIPService:
    def __init__(self) -> None:
        self.pipeline = BiometricPipeline()
        self.mapper = EthicalVectorMapper()
        self.entropy = BiometricEntropyHarness()
        self.devices: dict[str, DeviceAdapter] = {}

    def register_device(self, device_type: str, device_id: str, connection_type: str = "simulated") -> dict[str, Any]:
        adapter = create_adapter(device_type, device_id, connection_type)
        self.pipeline.add_device(device_id, adapter)
        self.pipeline.start()
        self.devices[device_id] = adapter
        return {"status": "registered", "device_id": device_id, "device_type": device_type}

    def get_biometric_state(self) -> dict[str, Any]:
        if not self.devices:
            return {"status": "no_devices", "signature": P7_VERSION}
        if self.pipeline.buffer:
            state = self.pipeline.get_current_state()
        else:
            self.pipeline.collect_once()
            state = self.pipeline.get_current_state()

        if state.get("status") == "no_data":
            return {"status": "no_data", "signature": P7_VERSION}

        ethical_vector = self.mapper.map_to_ethical_vector(state)
        frequency = self.mapper.map_to_frequency(ethical_vector)
        light_code = self.mapper.light_code_from_state(state, ethical_vector)
        seed_pack = self.entropy.from_biometric_state(state)

        return {
            "signature": P7_VERSION,
            "timestamp": state.get("timestamp", time.time()),
            "biometric": state,
            "readings": state,
            "ethical_vector": ethical_vector,
            "frequency": frequency,
            "light_code": light_code,
            "entropy": seed_pack,
        }

    def history(self, seconds: int = 60) -> list[dict[str, Any]]:
        n = min(len(self.pipeline.buffer), max(1, seconds * 10))
        return list(self.pipeline.buffer)[-n:]