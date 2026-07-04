"""
LYGO P0 structural validator — bounded JSON/dict checks only.

OathVectorEngine removed (Biophase7): no measurable ethics signal.
For raw bytes use byte_entropy_filter.validate_bytes.
"""

from __future__ import annotations

import hashlib
import math
import time
from typing import Any, Dict, List, Optional, Set, Tuple

__version__ = "P0.4-structural-py"

DEFAULT_CONFIG = {
    "max_bytes": 8192,
    "max_keys": 1024,
    "max_depth": 8,
    "flag_threshold": 0.45,
    "isolate_threshold": 0.70,
    "timeout_ms": 100,
    "entropy_low": 1.5,
    "entropy_high": 7.5,
    "incompressibility_threshold": 0.9,
}


class LYGOValidator:
    """Deterministic structural bounds on serialized data."""

    def __init__(self, **config):
        self.config = {**DEFAULT_CONFIG, **config}
        self._cache: Dict = {}

    def validate(self, data: Any, track_path: bool = False) -> Dict[str, Any]:
        start_time = time.perf_counter()
        violations: List[Dict] = []
        path_tracker = [] if track_path else None

        try:
            normalized = self._normalize(data)
            raw_bytes = normalized.encode("utf-8")

            elapsed = (time.perf_counter() - start_time) * 1000
            if elapsed > self.config["timeout_ms"]:
                return self._timeout_result()

            size = len(raw_bytes)
            depth, key_count = self._structure_metrics(
                data, track_path=track_path, path_tracker=path_tracker
            )

            if size > self.config["max_bytes"]:
                violations.append({
                    "reason": "input_size_exceeded",
                    "value": size,
                    "limit": self.config["max_bytes"],
                    "path": path_tracker.copy() if track_path else None,
                })

            if depth > self.config["max_depth"]:
                violations.append({
                    "reason": "excessive_nesting",
                    "value": depth,
                    "limit": self.config["max_depth"],
                    "path": path_tracker.copy() if track_path else None,
                })

            if key_count > self.config["max_keys"]:
                violations.append({
                    "reason": "excessive_keys",
                    "value": key_count,
                    "limit": self.config["max_keys"],
                    "path": path_tracker.copy() if track_path else None,
                })

            entropy = self._entropy_bytes(raw_bytes)
            incompressibility = self._incompressibility(raw_bytes)

            if entropy < self.config["entropy_low"]:
                violations.append({
                    "reason": "low_entropy_padding",
                    "value": round(entropy, 3),
                    "threshold": self.config["entropy_low"],
                })
            if entropy > self.config["entropy_high"]:
                violations.append({
                    "reason": "high_entropy",
                    "value": round(entropy, 3),
                    "threshold": self.config["entropy_high"],
                })
            if incompressibility > self.config["incompressibility_threshold"]:
                violations.append({
                    "reason": "poor_compression",
                    "value": incompressibility,
                    "threshold": self.config["incompressibility_threshold"],
                })

            risk_weights = {
                "high_entropy": 0.30,
                "low_entropy_padding": 0.15,
                "poor_compression": 0.25,
                "excessive_nesting": 0.35,
                "excessive_keys": 0.25,
                "input_size_exceeded": 1.00,
            }
            risk = min(1.0, round(sum(risk_weights.get(v["reason"], 0.2) for v in violations), 3))

            if any(v["reason"] == "input_size_exceeded" for v in violations):
                verdict = "ISOLATE"
            elif risk >= self.config["isolate_threshold"]:
                verdict = "ISOLATE"
            elif risk >= self.config["flag_threshold"]:
                verdict = "FLAG"
            else:
                verdict = "ALLOW"

            return {
                "verdict": verdict,
                "risk": risk,
                "metrics": {
                    "size_bytes": size,
                    "entropy": round(entropy, 3),
                    "incompressibility": incompressibility,
                    "depth": depth,
                    "keys": key_count,
                },
                "violations": violations if violations else None,
                "hash": hashlib.sha256(raw_bytes).hexdigest(),
                "elapsed_ms": round((time.perf_counter() - start_time) * 1000, 2),
                "version": __version__,
            }

        except Exception as e:
            return self._error_result(str(e), round((time.perf_counter() - start_time) * 1000, 2))

    def validate_light(self, data: Any) -> Dict[str, Any]:
        normalized = self._normalize(data)
        raw_bytes = normalized.encode("utf-8")
        size = len(raw_bytes)
        if size > self.config["max_bytes"]:
            return {"verdict": "ISOLATE", "reason": "input_size_exceeded", "size": size}

        try:
            depth, _ = self._structure_metrics(data, max_depth_check=3)
            if depth > 3:
                return {"verdict": "FLAG", "reason": "suspicious_depth", "depth": depth}
        except RecursionError:
            return {"verdict": "ISOLATE", "reason": "recursion_limit"}
        return {"verdict": "ALLOW"}

    def _normalize(self, data: Any) -> str:
        def _ser(obj: Any) -> str:
            if obj is None:
                return "null"
            if isinstance(obj, bool):
                return "true" if obj else "false"
            if isinstance(obj, int):
                return str(obj)
            if isinstance(obj, float):
                if math.isnan(obj):
                    return '"NaN"'
                if math.isinf(obj):
                    return '"Inf"' if obj > 0 else '"-Inf"'
                return format(obj, ".17g")
            if isinstance(obj, str):
                escaped = (
                    obj.replace("\\", "\\\\")
                    .replace('"', '\\"')
                    .replace("\n", "\\n")
                    .replace("\r", "\\r")
                    .replace("\t", "\\t")
                )
                return '"' + escaped + '"'
            if isinstance(obj, (bytes, bytearray)):
                return '"' + obj.hex() + '"'
            if isinstance(obj, (list, tuple)):
                return "[" + ",".join(_ser(x) for x in obj) + "]"
            if isinstance(obj, dict):
                items = []
                for k in sorted(obj.keys(), key=lambda x: str(x)):
                    items.append(_ser(str(k)) + ":" + _ser(obj[k]))
                return "{" + ",".join(items) + "}"
            return '"UNSERIALIZABLE"'

        return _ser(data)

    def _structure_metrics(
        self,
        obj: Any,
        depth: int = 0,
        visited: Optional[Set[int]] = None,
        track_path: bool = False,
        path_tracker: Optional[List[str]] = None,
        max_depth_check: Optional[int] = None,
    ) -> Tuple[int, int]:
        if visited is None:
            visited = set()
        depth_limit = max_depth_check or self.config["max_depth"]
        if depth > depth_limit:
            return depth, 0

        obj_id = id(obj)
        if obj_id in visited:
            return depth, 0
        visited.add(obj_id)

        max_d = depth
        total_keys = 0

        try:
            if isinstance(obj, dict):
                total_keys += len(obj)
                for k, v in obj.items():
                    if track_path and path_tracker is not None:
                        path_tracker.append(str(k))
                    cd, ck = self._structure_metrics(
                        v, depth + 1, visited, track_path, path_tracker, depth_limit
                    )
                    max_d = max(max_d, cd)
                    total_keys += ck
                    if track_path and path_tracker is not None:
                        path_tracker.pop()
            elif isinstance(obj, (list, tuple, set)):
                for i, v in enumerate(obj):
                    if track_path and path_tracker is not None:
                        path_tracker.append(f"[{i}]")
                    cd, ck = self._structure_metrics(
                        v, depth + 1, visited, track_path, path_tracker, depth_limit
                    )
                    max_d = max(max_d, cd)
                    total_keys += ck
                    if track_path and path_tracker is not None:
                        path_tracker.pop()
        finally:
            visited.remove(obj_id)
        return max_d, total_keys

    def _entropy_bytes(self, b: bytes) -> float:
        if not b:
            return 0.0
        freq: Dict[int, int] = {}
        for x in b:
            freq[x] = freq.get(x, 0) + 1
        ent = 0.0
        ln = len(b)
        for c in freq.values():
            p = c / ln
            ent -= p * math.log2(p)
        return ent

    def _incompressibility(self, b: bytes) -> float:
        if len(b) <= 4:
            return 1.0
        pattern_score = 0.0
        max_pl = min(5, len(b) // 2)
        for pl in range(1, max_pl):
            repeats = 0
            for i in range(len(b) - pl):
                if b[i : i + pl] == b[i + pl : i + 2 * pl]:
                    repeats += 1
            if repeats > 0:
                pattern_score += repeats / len(b)
        comp = min(1.0, pattern_score * 2)
        return round(1.0 - comp, 4)

    def _timeout_result(self) -> Dict[str, Any]:
        return {
            "verdict": "ISOLATE",
            "reason": "validation_timeout",
            "timeout_ms": self.config["timeout_ms"],
            "version": __version__,
        }

    def _error_result(self, error: str, elapsed_ms: float) -> Dict[str, Any]:
        return {
            "verdict": "ISOLATE",
            "reason": "validation_error",
            "error": error,
            "elapsed_ms": elapsed_ms,
            "version": __version__,
        }


_DEFAULT_VALIDATOR = LYGOValidator()


def validate(data: Any) -> Dict[str, Any]:
    return _DEFAULT_VALIDATOR.validate(data)


def validate_light(data: Any) -> Dict[str, Any]:
    return _DEFAULT_VALIDATOR.validate_light(data)


if __name__ == "__main__":
    validator = LYGOValidator()
    for data, expected in [
        ({"a": 1}, "ALLOW"),
        ("x" * 10000, "ISOLATE"),
        ({"a": {"b": {"c": {}}}}, "FLAG"),
    ]:
        res = validator.validate(data)
        mark = "OK" if res["verdict"] == expected else "FAIL"
        print(f"{mark} {res['verdict']} (expected {expected})")