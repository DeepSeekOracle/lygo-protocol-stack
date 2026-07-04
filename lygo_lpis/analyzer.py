"""Prompt analyzer — cognitive pattern tags + P0 gate."""

from __future__ import annotations

import re
from typing import Any

from .gatekeeper import P0Gatekeeper

PATTERNS: list[tuple[str, str]] = [
    ("planning", r"\b(plan|planning|roadmap|strategy|decompose)\b"),
    ("delegation", r"\b(subagent|delegate|sub-agent|spawn|handoff)\b"),
    ("verification", r"\b(verify|validation|self-check|review diff|test)\b"),
    ("tool_use", r"\b(tool|function call|bash|sandbox|execute)\b"),
    ("safety", r"\b(safety|refusal|harm|policy|quarantine)\b"),
    ("context", r"\b(context window|token|compress|summariz)\b"),
]


class PromptAnalyzer:
    def __init__(self) -> None:
        self.gate = P0Gatekeeper()

    def analyze(self, content: str) -> dict[str, Any]:
        gate = self.gate.validate_text(content)
        tags: dict[str, int] = {}
        lower = content.lower()
        for name, rx in PATTERNS:
            tags[name] = len(re.findall(rx, lower, flags=re.I))
        lygo_layers = []
        if tags.get("planning") or tags.get("context"):
            lygo_layers.append("P1")
        if tags.get("delegation"):
            lygo_layers.append("P3")
        if tags.get("verification"):
            lygo_layers.append("P0")
        if tags.get("safety"):
            lygo_layers.append("P5")
        return {
            "p0": gate,
            "pattern_counts": tags,
            "lygo_layer_map": lygo_layers or ["P0", "P1"],
            "lines": content.count("\n") + 1,
            "chars": len(content),
        }