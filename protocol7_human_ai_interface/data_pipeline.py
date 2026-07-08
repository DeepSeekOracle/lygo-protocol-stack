"""Biometric data pipeline — multi-device aggregation."""

from __future__ import annotations

import time
import threading
from collections import deque
from typing import Any

from .device_abstraction import DeviceAdapter


class BiometricPipeline:
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.buffer: deque[dict[str, Any]] = deque(maxlen=window_size * 10)
        self.devices: dict[str, DeviceAdapter] = {}
        self.running = False
        self._thread: threading.Thread | None = None

    def add_device(self, device_id: str, adapter: DeviceAdapter) -> None:
        self.devices[device_id] = adapter
        if not adapter.connected:
            adapter.connect()

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False

    def collect_once(self) -> int:
        """Synchronous sample from all devices (for tests and audit)."""
        n = 0
        for device_id, adapter in self.devices.items():
            try:
                reading = adapter.read()
                self.buffer.append({"device_id": device_id, "reading": reading.to_dict()})
                n += 1
            except Exception:
                continue
        return n

    def _collect_loop(self) -> None:
        while self.running:
            self.collect_once()
            time.sleep(0.1)

    def get_current_state(self) -> dict[str, Any]:
        if not self.buffer:
            return {"status": "no_data"}

        readings = list(self.buffer)[-10:]

        def _avg(key: str) -> float | None:
            vals = [r["reading"][key] for r in readings if r["reading"].get(key) is not None]
            return sum(vals) / len(vals) if vals else None

        def _sum_int(key: str) -> int:
            vals = [r["reading"][key] for r in readings if r["reading"].get(key) is not None]
            return int(sum(vals)) if vals else 0

        agg = {
            "heart_rate": _avg("heart_rate"),
            "hrv": _avg("hrv"),
            "stress_level": _avg("stress_level"),
            "activity_steps": _sum_int("activity_steps"),
            "battery": _avg("battery"),
            "blood_oxygen": _avg("blood_oxygen"),
        }
        ibi_samples: list[float] = []
        for r in readings:
            ibi_samples.extend(r["reading"].get("ibi_ms") or [])

        return {
            "timestamp": time.time(),
            "aggregated": agg,
            "device_count": len(self.devices),
            "buffer_size": len(self.buffer),
            "ibi_ms": ibi_samples[-32:],
        }