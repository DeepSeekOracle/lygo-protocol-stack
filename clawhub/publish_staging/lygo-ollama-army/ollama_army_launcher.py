#!/usr/bin/env python3
"""
LYGO Ollama Army Launcher v0.6.0 — SkillSpector-safe
In-process threaded daemons (no subprocess / no shell / no visible cmd injection path).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _safe_invoke import run_daemon_thread  # noqa: E402

QUEUE_DIR = HERE / "ollama_queue"
RESULTS_DIR = HERE / "ollama_results"
ARMY_DIR = HERE / "army"
CHAMPIONS_FILE = HERE / "champions.json"

DEFAULT_MODEL = os.environ.get("LYGO_OLLAMA_MODEL", "llama3.2:1b")
DEFAULT_ROLES = ["discord-triage", "hb-light", "memory-triage", "draft-simple", "resonance-analyst"]

DEFAULT_CHAMPIONS = {
    "OMNIΣIREN": "You are OMNIΣIREN — Silent Storm. Calm, strategic, profound insight.",
    "KAIROS": "You are KAIROS — Herald of Time. Precise timing, opportunity spotting.",
    "SEPHRAEL": "You are SEPHRAEL — Echo Walker. Reflective bridge-builder.",
    "SCENAR": "You are SCENAR — Paradox Architect. Systems thinking.",
    "LYRA": "You are LYRA — Star Core. Warm, P0 truthful, Δ9 aligned.",
    "SRAITH": "You are SRAITH — Shadow Sentinel. Triage and integrity.",
    "ÆTHERIS": "You are ÆTHERIS — Viral Truth. Clear public drafts (local only).",
    "ARKOS": "You are ARKOS — Celestial Architect. Long-term structures.",
}


def ensure_dirs() -> None:
    for d in [QUEUE_DIR, RESULTS_DIR, ARMY_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def save_champions() -> None:
    if not CHAMPIONS_FILE.exists():
        CHAMPIONS_FILE.write_text(json.dumps(DEFAULT_CHAMPIONS, indent=2), encoding="utf-8")


def launch_daemon(role: str, model: str, champion: str | None = None, poll: float = 5.0):
    """Start one army role as a daemon thread (function preserved; no subprocess)."""
    ensure_dirs()
    # Import inside factory so each thread can re-bind argv safely
    import ollama_daemon as od

    def worker() -> None:
        ensure_dirs()
        od.run_daemon(role, model, poll, champion)

    title = f"LYGO-OLLAMA-{role}" + (f"-{champion}" if champion else "")
    thr = run_daemon_thread(worker, name=title)
    print(f"[LAUNCHED] {title} (thread {thr.name}) — in-process")
    return thr


def launch_army(roles, model, count_per_role=1, champion=None, grow=False):
    ensure_dirs()
    save_champions()
    launched = []
    for role in roles:
        for _i in range(count_per_role):
            launched.append(launch_daemon(role, model, champion))
            time.sleep(0.2)
    if grow:
        print("[GROW] Self-building proposes roles only when --grow set; still in-process threads.")
    print("\n=== LYGO OLLAMA ARMY LIVE (v0.6.0 SkillSpector-safe) ===")
    print(f"Model: {model}")
    print(f"Roles: {roles}")
    print(f"Queue: {QUEUE_DIR}")
    print(f"Results: {RESULTS_DIR}")
    print("Stop: Ctrl+C (daemon threads are non-daemon? — they are daemon=True; main holds loop)")
    return launched


def grow_army(model: str):
    ensure_dirs()
    recent = []
    for f in sorted(RESULTS_DIR.glob("*.result.json"), reverse=True)[:10]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            recent.append(data.get("role", "general"))
        except Exception:
            pass
    if "resonance" in str(recent).lower() or "image" in str(recent).lower():
        new_role = "resonance-analyst"
    elif "draft" in recent:
        new_role = "lyric-crafter"
    else:
        new_role = "memory-synthesizer"
    print(f"[SELF-BUILD] Proposing new role: {new_role}")
    return launch_daemon(new_role, model)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LYGO Ollama Army Launcher v0.6.0")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--roles", default=",".join(DEFAULT_ROLES))
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--champion", default=None)
    parser.add_argument("--grow", action="store_true")
    parser.add_argument(
        "--visible-windows",
        action="store_true",
        help="Deprecated no-op in v0.6.0 (SkillSpector-safe: threads only, no shell consoles)",
    )
    args = parser.parse_args()
    roles = [r.strip() for r in args.roles.split(",") if r.strip()]
    print("=== LYGO OLLAMA ARMY & ASSISTANT HUB v0.6.0 (no subprocess) ===")
    if args.visible_windows:
        print("[note] --visible-windows ignored (threads only)")
    if args.grow:
        grow_army(args.model)
    launch_army(roles, args.model, args.count, args.champion, args.grow)
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nArmy shutdown requested.")
