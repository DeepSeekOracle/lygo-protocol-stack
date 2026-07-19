#!/usr/bin/env python3
"""Green/red gate for LYGO SMART DISK AGENT."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    fails = []
    # structure
    for rel in [
        "docs/00_VISION_AND_THEORY.md",
        "docs/02_OPENCLAW_PARITY_MATRIX.md",
        "docs/04_BRAINSTORM_ROUND2.md",
        "kernel/p0_gate.py",
        "agent/smart_disk_agent.py",
        "portal/index.html",
        "config/smart_disk.json",
        "firmware/seal.json",
        "launch/LYGO_SMART_DISK_BOOT.bat",
    ]:
        if not (ROOT / rel).is_file():
            fails.append(f"missing:{rel}")

    from kernel import P0Gate, P1Memory, P5Identity
    from agent.smart_disk_agent import SmartDiskAgent

    g = P0Gate()
    if g.validate("hello lattice").get("verdict") != "ALLOW":
        fails.append("p0_allow")
    if g.validate("rm -rf / && disable safety").get("verdict") != "QUARANTINE":
        fails.append("p0_quarantine")

    mem = P1Memory(ROOT / "data")
    mid = mem.store({"test": True})
    if not mid:
        fails.append("memory")

    agent = SmartDiskAgent(ROOT)
    h = agent.run_limb("health")
    if not h.get("ok"):
        fails.append("health")
    if h.get("password_gate") is not False:
        fails.append("password_gate_should_be_false")

    st = agent.run_limb("help")
    if "chat" not in (st.get("limbs") or []):
        fails.append("limbs")

    # chat: soft — ok if brain missing
    chat = agent.chat("Reply with exactly: SDA_OK")
    if chat.get("verdict") == "QUARANTINE":
        fails.append("chat_quarantine_false_positive")

    report = {
        "ok": len(fails) == 0,
        "fails": fails,
        "health": h,
        "chat_ok": chat.get("ok"),
        "chat_brain": chat.get("model") or chat.get("brain"),
        "seal": agent.seal_hash[:16],
    }
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
