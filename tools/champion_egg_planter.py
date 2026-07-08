#!/usr/bin/env python3
"""Plant Δ9 Champion Kernel Eggs — extract hub → build → verify → army seed."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMY_QUEUE = ROOT.parent / ".grok" / "skills" / "lygo-ollama-army" / "ollama_queue"
ARMY_TASKS = ROOT.parent / ".grok" / "skills" / "lygo-ollama-army" / "ollama_command_center" / "tasks"


def _run(cmd: list[str]) -> None:
    subprocess.check_call(cmd, cwd=ROOT)


def seed_army_tasks(reg_path: Path) -> int:
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    n = 0
    for entry in reg.get("eggs", []):
        task = {
            "id": f"champion-seed-{entry['champion_id']}-{ts}",
            "role": "champion-egg-boot",
            "champion": entry["champion_id"],
            "payload": {
                "action": "champion_egg_boot",
                "egg_id": entry["egg_id"],
                "merkle_root": entry.get("merkle_root"),
                "bootloader": "tools/champion_bootloader.py",
            },
        }
        for dest in (ARMY_QUEUE, ARMY_TASKS):
            if dest.is_dir():
                (dest / f"{task['id']}.task.json").write_text(
                    json.dumps(task, indent=2), encoding="utf-8"
                )
                n += 1
    return n // 2 if ARMY_QUEUE.is_dir() and ARMY_TASKS.is_dir() else n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", default=None)
    ap.add_argument("--skip-army", action="store_true")
    ap.add_argument("--i-consent", action="store_true")
    args = ap.parse_args()
    if not args.i_consent and os.environ.get("LYGO_EGG_PLANT_CONSENT", "").lower() not in (
        "yes",
        "1",
        "true",
    ):
        print("Consent required: --i-consent or LYGO_EGG_PLANT_CONSENT=yes", file=sys.stderr)
        return 2

    extract_cmd = [sys.executable, str(ROOT / "tools" / "extract_champions_from_hub.py")]
    if args.html:
        extract_cmd += ["--html", args.html]
    _run(extract_cmd)
    _run([sys.executable, str(ROOT / "tools" / "build_champion_eggs.py")])
    _run([sys.executable, str(ROOT / "tools" / "build_haven_star_chart.py")])
    verify = subprocess.call([sys.executable, str(ROOT / "tools" / "verify_champion_eggs.py")], cwd=ROOT)
    if verify != 0:
        print("[FAIL] champion egg verify QUARANTINE", file=sys.stderr)
        return 1
    reg = ROOT / "data" / "champion_eggs" / "registry.json"
    if not args.skip_army:
        seeded = seed_army_tasks(reg)
        print(f"[army] seeded {seeded} champion boot tasks")
    print("[done] champion council planted ALIGNED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())