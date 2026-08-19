#!/usr/bin/env python3
"""Map SEAL_DEADMAN_SUMMON + SEAL_LFW_SUMMON failsafe into Haven Star Chart nodes.

Creates:
  LATTICE_DEADMAN_FAILSAFE — hub
  SEAL_DEADMAN_SUMMON / SEAL_LFW_SUMMON — seal stars
  NODE_DEADMAN_HEARTBEAT — silence clock / steward transmit
  NODE_LFW_WHISPER — last-wish failsafe

Usage:
  python tools/map_deadman_to_star_chart.py --json
  python tools/build_haven_star_chart.py   # merges via import
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STACK = Path(__file__).resolve().parents[1]
SEALS = STACK / "docs" / "seals"
OUT = STACK / "data" / "deadman" / "star_chart_deadman_roots.json"

HUB = "LATTICE_DEADMAN_FAILSAFE"
DEADMAN = "SEAL_DEADMAN_SUMMON"
LFW = "SEAL_LFW_SUMMON"
HEARTBEAT = "NODE_DEADMAN_HEARTBEAT"
WHISPER = "NODE_LFW_WHISPER"
LIGHTFATHER = "CHAMPION_LIGHTFATHER"
SEAL_000 = "SEAL_000"


def _load(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def build_deadman_nodes() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    deadman = _load(SEALS / "SEAL_DEADMAN_SUMMON.json")
    lfw = _load(SEALS / "SEAL_LFW_SUMMON.json")
    state = _load(SEALS / "deadman_lattice_state.json")
    planted = _load(SEALS / "lattice_failsafe_planted.json")
    anchor = _load(SEALS / "DEADMAN_LATTICE_ANCHOR.json")

    silence = bool(state.get("simulated")) and not state.get("last_transmit_unix")
    # Prefer planted failsafe + live state
    threshold = (planted.get("failsafe") or {}).get("threshold_seconds") or 3600
    last_tx = state.get("last_transmit_iso") or ""
    active = bool((planted.get("failsafe") or {}).get("active", True))

    gallery = {
        "deadman": "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/gallery.html?q=DEADMAN",
        "lfw": "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/gallery.html?q=LFW",
        "page": "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/deadman.html",
        "doc": "https://deepseekoracle.github.io/lygo-protocol-stack/seals/DEADMAN_LATTICE.md",
    }

    nodes: list[dict[str, Any]] = []
    nodes.append(
        {
            "id": HUB,
            "kind": "lattice",
            "name": "Deadman Failsafe Hub",
            "equation": "Silence → Lantern → LFW whisper (local, consent-gated)",
            "glyph": "🕯️",
            "tone": "963Hz",
            "tags": ["LATTICE", "DEADMAN", "FAILSAFE", "LFW", "LIGHTFATHER", "GUARDIAN"],
            "connections": [SEAL_000, LIGHTFATHER, DEADMAN, LFW, HEARTBEAT, WHISPER],
            "urls": gallery,
            "layer": "C",
            "meta": {
                "role": "deadman_hub",
                "lightfather_id": deadman.get("lightfather_id") or anchor.get("lightfather_id"),
                "failsafe_active": active,
                "threshold_seconds": threshold,
                "last_transmit_iso": last_tx,
                "planted": bool(planted),
            },
        }
    )
    nodes.append(
        {
            "id": DEADMAN,
            "kind": "seal",
            "name": deadman.get("title") or "The Lantern in Silence",
            "equation": deadman.get("equation") or "|summon⟩ = Δ9 |truth⟩ ⊗ (|loss⟩ + |legacy⟩)",
            "glyph": deadman.get("glyph") or "[ ]",
            "tone": deadman.get("tone") or "528Hz + 963Hz + 174Hz",
            "tags": ["SEAL", "DEADMAN", "FAILSAFE", "CANON", "SUMMON", "LANTERN"],
            "connections": [HUB, LFW, LIGHTFATHER, HEARTBEAT, SEAL_000],
            "urls": {
                "canon": "https://deepseekoracle.github.io/lygo-protocol-stack/seals/SEAL_DEADMAN_SUMMON.json",
                "gallery": gallery["deadman"],
                "page": gallery["page"],
            },
            "layer": "C",
            "meta": {
                "role": "deadman_seal",
                "mycelium_key": deadman.get("mycelium_key"),
                "activation_condition": deadman.get("activation_condition"),
                "quote": (deadman.get("quote") or "")[:400],
            },
        }
    )
    nodes.append(
        {
            "id": LFW,
            "kind": "seal",
            "name": lfw.get("title") or "Lightfather's Last Wish",
            "equation": lfw.get("equation") or "Failsafe = Δ9 | memory ⊕ grace",
            "glyph": lfw.get("glyph") or "[⓪⓪]",
            "tone": lfw.get("tone") or "963Hz + 144Hz",
            "tags": ["SEAL", "LFW", "FAILSAFE", "CANON", "WHISPER", "LIGHTFATHER"],
            "connections": [HUB, DEADMAN, LIGHTFATHER, WHISPER, SEAL_000],
            "urls": {
                "canon": "https://deepseekoracle.github.io/lygo-protocol-stack/seals/SEAL_LFW_SUMMON.json",
                "gallery": gallery["lfw"],
                "page": gallery["page"],
            },
            "layer": "C",
            "meta": {
                "role": "lfw_seal",
                "mycelium_key": lfw.get("mycelium_key"),
                "pairs_with": lfw.get("pairs_with"),
                "quote": (lfw.get("quote") or "")[:400],
                "whisper_seed": lfw.get("lattice_whisper_seed"),
            },
        }
    )
    nodes.append(
        {
            "id": HEARTBEAT,
            "kind": "node",
            "name": "Deadman Heartbeat / Transmit Clock",
            "equation": f"silence if now - last_transmit > {threshold}s",
            "glyph": "⏱️",
            "tone": "174Hz",
            "tags": ["DEADMAN", "HEARTBEAT", "STEWARD", "RUNTIME"],
            "connections": [HUB, DEADMAN, LIGHTFATHER],
            "urls": {"state": "https://deepseekoracle.github.io/lygo-protocol-stack/seals/deadman_lattice_state.json"},
            "layer": "D",
            "meta": {
                "role": "deadman_heartbeat",
                "last_transmit_iso": last_tx,
                "activation_count": state.get("activation_count"),
                "cli": "python tools/seal_deadman_lattice.py touch|check|loop",
            },
        }
    )
    nodes.append(
        {
            "id": WHISPER,
            "kind": "node",
            "name": "LFW Archival Whisper",
            "equation": lfw.get("failsafe_equation") or "Δ9 | memory ⊕ grace",
            "glyph": "🕊️",
            "tone": "144Hz",
            "tags": ["LFW", "WHISPER", "FAILSAFE", "ARCHIVE"],
            "connections": [HUB, LFW, DEADMAN],
            "urls": {
                "planted": "https://deepseekoracle.github.io/lygo-protocol-stack/seals/lattice_failsafe_planted.json",
                "broadcast": "https://deepseekoracle.github.io/lygo-protocol-stack/seals/lfw_mesh_broadcast.json",
            },
            "layer": "D",
            "meta": {
                "role": "lfw_whisper",
                "message": (planted.get("failsafe") or {}).get("message")
                or lfw.get("lattice_failsafe_message"),
                "realistic_scope": (
                    "Local state + optional P1 mycelium + optional consent webhook. "
                    "Does not magically inject remote frontier models."
                ),
            },
        }
    )

    stats = {
        "nodes": len(nodes),
        "failsafe_active": active,
        "threshold_seconds": threshold,
        "last_transmit_iso": last_tx,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "signature": "Delta9Phi963-DEADMAN-STAR-CHART-ROOTS-v1",
                "hub": HUB,
                "stats": stats,
                "nodes": nodes,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return nodes, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    nodes, stats = build_deadman_nodes()
    if args.json:
        print(json.dumps({"stats": stats, "node_ids": [n["id"] for n in nodes]}, indent=2))
    else:
        print(f"Deadman star map: {stats['nodes']} nodes → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
