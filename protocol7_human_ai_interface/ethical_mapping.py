"""Map biometric aggregates to Truth / Love / Freedom and Solfeggio frequency."""

from __future__ import annotations

from typing import Any


class EthicalVectorMapper:
    def map_to_ethical_vector(self, biometric_state: dict[str, Any]) -> list[float]:
        agg = biometric_state.get("aggregated", {})
        hr = agg.get("heart_rate") or 70
        hrv = agg.get("hrv") or 50
        stress = agg.get("stress_level") if agg.get("stress_level") is not None else 0.5
        activity = agg.get("activity_steps") or 0
        battery = agg.get("battery") if agg.get("battery") is not None else 0.5

        truth_score = max(0.0, 1.0 - float(stress)) * (float(hrv) / 100.0) * 1.2
        truth_score = min(1.0, truth_score)

        love_score = (float(battery) + (float(hrv) / 100.0)) / 2.0
        love_score = min(1.0, love_score)

        freedom_score = (min(1.0, float(activity) / 10000.0) + (1.0 - float(stress))) / 2.0
        freedom_score = min(1.0, freedom_score)

        return [round(truth_score, 4), round(love_score, 4), round(freedom_score, 4)]

    def map_to_frequency(self, ethical_vector: list[float]) -> int:
        t, l, f = ethical_vector
        if t > 0.7 and l > 0.7 and f > 0.7:
            return 963
        if t > 0.7:
            return 852
        if l > 0.7:
            return 639
        if f > 0.7:
            return 417
        return 528

    def light_code_from_state(self, biometric_state: dict[str, Any], ethical_vector: list[float]) -> str:
        import hashlib

        ts = biometric_state.get("timestamp", 0)
        data_hash = hashlib.sha256(f"{ts}{ethical_vector}".encode()).hexdigest()[:8]
        return f"LF-Δ9-{data_hash}-963-528-174-Φ-∞"