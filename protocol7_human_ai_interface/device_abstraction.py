"""Device abstraction layer — Apple Watch, Garmin, Oura, custom sensors."""

from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class BiometricReading:
    timestamp: float
    heart_rate: float | None = None
    hrv: float | None = None
    sleep_stage: str | None = None
    activity_steps: int | None = None
    blood_oxygen: float | None = None
    temperature: float | None = None
    stress_level: float | None = None
    battery: float | None = None
    ibi_ms: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "heart_rate": self.heart_rate,
            "hrv": self.hrv,
            "sleep_stage": self.sleep_stage,
            "activity_steps": self.activity_steps,
            "blood_oxygen": self.blood_oxygen,
            "temperature": self.temperature,
            "stress_level": self.stress_level,
            "battery": self.battery,
            "ibi_ms": self.ibi_ms,
        }


class DeviceAdapter(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def read(self) -> BiometricReading:
        pass

    @abstractmethod
    def get_device_info(self) -> dict[str, Any]:
        pass


def _simulated_reading(device_label: str, *, seed: int | None = None) -> BiometricReading:
    rng = random.Random(seed if seed is not None else time.time())
    hr = 60 + rng.randint(0, 40)
    ibi = [60000.0 / hr + rng.uniform(-40, 40) for _ in range(8)]
    return BiometricReading(
        timestamp=time.time(),
        heart_rate=float(hr),
        hrv=50.0 + rng.randint(0, 30),
        sleep_stage=rng.choice(["awake", "rem", "light", "deep"]),
        activity_steps=rng.randint(1000, 5000),
        blood_oxygen=95.0 + rng.randint(0, 4),
        temperature=36.5 + rng.uniform(0, 0.5),
        stress_level=rng.uniform(0, 1),
        battery=0.5 + rng.uniform(0, 0.5),
        ibi_ms=ibi,
    )


class AppleWatchAdapter(DeviceAdapter):
    def __init__(self, device_id: str, connection_type: str = "bluetooth"):
        self.device_id = device_id
        self.connection_type = connection_type
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def read(self) -> BiometricReading:
        if not self.connected:
            raise ConnectionError("Device not connected")
        return _simulated_reading("apple_watch")

    def get_device_info(self) -> dict[str, Any]:
        return {
            "type": "Apple Watch",
            "model": "Series 9 (simulated)",
            "device_id": self.device_id,
            "connection_type": self.connection_type,
            "connected": self.connected,
            "gatt_service": "0x180D",
        }


class GarminAdapter(DeviceAdapter):
    def __init__(self, device_id: str, connection_type: str = "bluetooth"):
        self.device_id = device_id
        self.connection_type = connection_type
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def read(self) -> BiometricReading:
        if not self.connected:
            raise ConnectionError("Device not connected")
        r = _simulated_reading("garmin")
        return BiometricReading(**{**r.to_dict(), "heart_rate": (r.heart_rate or 70) - 2})

    def get_device_info(self) -> dict[str, Any]:
        return {"type": "Garmin", "device_id": self.device_id, "connection_type": self.connection_type, "connected": self.connected}


class OuraAdapter(DeviceAdapter):
    def __init__(self, device_id: str, connection_type: str = "api"):
        self.device_id = device_id
        self.connection_type = connection_type
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def read(self) -> BiometricReading:
        if not self.connected:
            raise ConnectionError("Device not connected")
        r = _simulated_reading("oura")
        return BiometricReading(**{**r.to_dict(), "hrv": (r.hrv or 50) + 5})

    def get_device_info(self) -> dict[str, Any]:
        return {"type": "Oura Ring", "device_id": self.device_id, "connection_type": self.connection_type, "connected": self.connected}


class CustomSensorAdapter(DeviceAdapter):
    def __init__(self, device_id: str, connection_type: str = "wifi"):
        self.device_id = device_id
        self.connection_type = connection_type
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def read(self) -> BiometricReading:
        if not self.connected:
            raise ConnectionError("Device not connected")
        return _simulated_reading("custom")

    def get_device_info(self) -> dict[str, Any]:
        return {"type": "Custom Sensor", "device_id": self.device_id, "connection_type": self.connection_type, "connected": self.connected}


ADAPTER_TYPES = {
    "apple_watch": AppleWatchAdapter,
    "garmin": GarminAdapter,
    "oura": OuraAdapter,
    "custom": CustomSensorAdapter,
}


def create_adapter(device_type: str, device_id: str, connection_type: str = "simulated") -> DeviceAdapter:
    cls = ADAPTER_TYPES.get(device_type)
    if cls is None:
        raise ValueError(f"Unknown device type: {device_type}")
    return cls(device_id, connection_type)