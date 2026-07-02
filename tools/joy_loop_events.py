"""Simple pub-sub for Joy Loop (v3 foundation)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

Listener = Callable[[dict[str, Any]], None]


class JoyEventBus:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Listener]] = defaultdict(list)

    def on(self, event: str, fn: Listener) -> None:
        self._listeners[event].append(fn)

    def emit(self, event: str, payload: dict[str, Any] | None = None) -> None:
        data = payload or {}
        for fn in list(self._listeners.get(event, [])):
            try:
                fn(data)
            except Exception:
                pass


# Standard events: on_beat, on_injection, on_joy_threshold, on_champion_activate, on_champion_retire