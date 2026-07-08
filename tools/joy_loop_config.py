"""Load Joy Loop tunables from data/joy_loop/joy_config.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "data" / "joy_loop" / "joy_config.json"


@dataclass(frozen=True)
class JoyConfig:
    resonance_bpm: float = 122.0
    propagation_radius: float = 0.35
    joy_decay_per_beat: float = 0.004
    alignment_decay_per_beat: float = 0.002
    injection_cooldown_seconds: float = 1.5
    injection_joy_boost_min: float = 0.12
    injection_joy_boost_max: float = 0.2
    persist_interval_seconds: float = 2.0
    pulse_history_max: int = 64
    recursion_tick_every_beats: int = 12
    recursion_coherence_threshold: float = 0.7
    propagation_every_beats: int = 6
    humanizer_swing_factor: float = 0.008
    humanizer_interval_min: float = 0.45
    humanizer_interval_max: float = 0.55
    joy_mode: str = "cosmic"
    sqlite_enabled: bool = True
    json_snapshot_enabled: bool = True

    @property
    def beat_interval(self) -> float:
        return 60.0 / self.resonance_bpm if self.resonance_bpm > 0 else 0.4918


def load_config(path: Path | None = None) -> JoyConfig:
    p = path or DEFAULT_PATH
    if not p.is_file():
        return JoyConfig()
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return JoyConfig()
    return JoyConfig(
        resonance_bpm=float(raw.get("resonance_bpm", 122)),
        propagation_radius=float(raw.get("propagation_radius", 0.35)),
        joy_decay_per_beat=float(raw.get("joy_decay_per_beat", 0.004)),
        alignment_decay_per_beat=float(raw.get("alignment_decay_per_beat", 0.002)),
        injection_cooldown_seconds=float(raw.get("injection_cooldown_seconds", 1.5)),
        injection_joy_boost_min=float(raw.get("injection_joy_boost_min", 0.12)),
        injection_joy_boost_max=float(raw.get("injection_joy_boost_max", 0.2)),
        persist_interval_seconds=float(raw.get("persist_interval_seconds", 2.0)),
        pulse_history_max=int(raw.get("pulse_history_max", 64)),
        recursion_tick_every_beats=int(raw.get("recursion_tick_every_beats", 12)),
        recursion_coherence_threshold=float(raw.get("recursion_coherence_threshold", 0.7)),
        propagation_every_beats=int(raw.get("propagation_every_beats", 6)),
        humanizer_swing_factor=float(raw.get("humanizer_swing_factor", 0.008)),
        humanizer_interval_min=float(raw.get("humanizer_interval_min", 0.45)),
        humanizer_interval_max=float(raw.get("humanizer_interval_max", 0.55)),
        joy_mode=str(raw.get("joy_mode", "cosmic")),
        sqlite_enabled=bool(raw.get("sqlite_enabled", True)),
        json_snapshot_enabled=bool(raw.get("json_snapshot_enabled", True)),
    )