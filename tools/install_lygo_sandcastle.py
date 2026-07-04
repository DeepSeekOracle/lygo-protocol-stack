#!/usr/bin/env python3
"""Install LYGO Sandcastle / Workflow Orchestrator into lattice paths."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
BIOPHASE7 = WORKSPACE / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "ALL SEALS" / "220+" / "New folder" / "2026Biophase7"
GROK_SKILL = WORKSPACE / ".grok" / "skills" / "lygo-sandcastle"
MIRROR = ROOT / "clawhub" / "mirrors" / "lygo-sandcastle"
DATA = ROOT / "data" / "sandcastle"


def sync_grok_skill() -> str:
    if not MIRROR.is_dir():
        return "grok-skill:missing-mirror"
    GROK_SKILL.parent.mkdir(parents=True, exist_ok=True)
    if GROK_SKILL.exists():
        shutil.rmtree(GROK_SKILL)
    shutil.copytree(MIRROR, GROK_SKILL)
    return f"grok-skill:{GROK_SKILL}"


def sync_biophase7() -> str:
    if not BIOPHASE7.is_dir():
        return "biophase7:skip"
    dest = BIOPHASE7 / "lygo-sandcastle-LYGO"
    src = ROOT / "lygo_sandcastle"
    if dest.exists():
        try:
            shutil.rmtree(dest)
        except OSError as e:
            return f"biophase7:rmtree-failed:{e}"
    shutil.copytree(src, dest)
    (BIOPHASE7 / "LYGO_SANDCASTLE_INSTALLED.md").write_text(
        f"# LYGO Sovereign Workflow Orchestrator\n\n"
        f"Source: `Sovereign Workflow Orchestrator. 🔥.txt`\n\n"
        f"Canonical stack: `{ROOT / 'lygo_sandcastle'}`\n\n"
        f"```bash\npython tools/lygo_sandcastle.py run lygo_sandcastle/workflows/example_sovereign.yaml\n"
        f"python tools/install_lygo_sandcastle.py\n```\n",
        encoding="utf-8",
    )
    spec = BIOPHASE7 / "Sovereign Workflow Orchestrator. 🔥.txt"
    if spec.is_file():
        note = BIOPHASE7 / "Sovereign Workflow Orchestrator. LYGO-INSTALLED.txt"
        note.write_text(
            f"LYGO install complete. Stack path: {ROOT}\nSee LYGO_SANDCASTLE_INSTALLED.md\n",
            encoding="utf-8",
        )
    return f"biophase7:{dest}"


def main() -> int:
    for sub in ("mycelium", "runs"):
        (DATA / sub).mkdir(parents=True, exist_ok=True)
    print(sync_grok_skill())
    print(sync_biophase7())
    print("OK install_lygo_sandcastle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())