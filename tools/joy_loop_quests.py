"""JoyQuests — achievements when champions hit coherence / recursion milestones."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from joy_loop_protocol import JoyLoopEngine

ROOT = Path(__file__).resolve().parents[1]
QUESTS_PATH = ROOT / "data" / "joy_loop" / "quests_unlocked.json"


@dataclass
class JoyQuest:
    quest_id: str
    title: str
    description: str
    check: Callable[[str, dict], bool]


def _quest_catalog() -> list[JoyQuest]:
    return [
        JoyQuest(
            "first_pulse",
            "First Pulse",
            "Champion registered on the lattice",
            lambda _cid, st: st.get("pulse_count", 0) >= 1,
        ),
        JoyQuest(
            "coherence_50",
            "Half Bright",
            "Joy coherence reaches 0.50",
            lambda _cid, st: float(st.get("joy_coherence", 0)) >= 0.5,
        ),
        JoyQuest(
            "coherence_80",
            "Groove Master",
            "Joy coherence reaches 0.80",
            lambda _cid, st: float(st.get("joy_coherence", 0)) >= 0.8,
        ),
        JoyQuest(
            "depth_10",
            "Deep Recursion",
            "Recursion depth reaches 10",
            lambda _cid, st: int(st.get("recursion_depth", 0)) >= 10,
        ),
        JoyQuest(
            "swarm_harmony",
            "Council Unity",
            "Alignment confidence above 0.70",
            lambda _cid, st: float(st.get("alignment_confidence", 0)) >= 0.7,
        ),
    ]


class JoyQuestEngine:
    def __init__(self) -> None:
        self._unlocked: dict[str, list[dict]] = {}
        self._load()

    def _load(self) -> None:
        if QUESTS_PATH.is_file():
            try:
                self._unlocked = json.loads(QUESTS_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._unlocked = {}

    def _save(self) -> None:
        QUESTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        QUESTS_PATH.write_text(json.dumps(self._unlocked, indent=2), encoding="utf-8")

    def evaluate(self, engine: "JoyLoopEngine") -> list[dict]:
        new_unlocks: list[dict] = []
        states = engine.get_state() or {}
        for cid, st in states.items():
            earned = {u["quest_id"] for u in self._unlocked.get(cid, [])}
            for q in _quest_catalog():
                if q.quest_id in earned:
                    continue
                if q.check(cid, st):
                    entry = {
                        "quest_id": q.quest_id,
                        "title": q.title,
                        "description": q.description,
                        "unlocked_utc": time.time(),
                    }
                    self._unlocked.setdefault(cid, []).append(entry)
                    new_unlocks.append({"champion_id": cid, **entry})
        if new_unlocks:
            self._save()
        return new_unlocks

    def summary(self) -> dict[str, Any]:
        total = sum(len(v) for v in self._unlocked.values())
        return {"champions_with_quests": len(self._unlocked), "total_badges": total, "by_champion": self._unlocked}