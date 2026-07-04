#!/usr/bin/env python3
"""Install LYGO Second Brain into workspace lattice paths."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
BIOPHASE7 = WORKSPACE / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "ALL SEALS" / "220+" / "New folder" / "2026Biophase7"
GROK_SKILL = WORKSPACE / ".grok" / "skills" / "lygo-second-brain"
MIRROR = ROOT / "clawhub" / "mirrors" / "lygo-second-brain"
VAULT = ROOT / "lygo_second_brain" / "vault"


def init_vault_git(vault: Path) -> str:
    """Optional per-vault git — not nested inside stack repo (see .gitignore)."""
    if (vault / ".git").exists():
        return "vault-git:exists"
    subprocess.run(["git", "init"], cwd=vault, capture_output=True, check=False)
    subprocess.run(["git", "add", "-A"], cwd=vault, capture_output=True, check=False)
    r = subprocess.run(
        ["git", "commit", "-m", "LYGO second brain vault init"],
        cwd=vault,
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        return "vault-git:initialized"
    return "vault-git:commit-skipped"


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
        return "biophase7:skip (path missing)"
    dest = BIOPHASE7 / "lygo-second-brain-LYGO"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "lygo_second_brain", dest)
    prov = BIOPHASE7 / "LYGO_SECOND_BRAIN_INSTALLED.md"
    prov.write_text(
        f"# LYGO Second Brain installed from stack\n\n"
        f"Canonical: `{ROOT / 'lygo_second_brain'}`\n\n"
        f"Run: `python tools/install_lygo_second_brain.py` from lygo-protocol-stack.\n",
        encoding="utf-8",
    )
    return f"biophase7:{dest}"


def main() -> int:
    for d in ("raw", "permanent", "wiki", "archive"):
        (VAULT / d).mkdir(parents=True, exist_ok=True)
    print(init_vault_git(VAULT))
    print(sync_grok_skill())
    print(sync_biophase7())
    print(f"LYGO_VAULT_ROOT={VAULT}")
    print("OK install complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())