#!/usr/bin/env python3
"""Sync public skill surface from lyra-crypto-operator into ClawHub mirror.

Excludes operator_tools/ (GitHub push/credentials) and private paths.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Canonical crypto lane (workspace layout: I:\E Drive\lyra-crypto-operator)
_CANDIDATES = [
    Path(r"I:\E Drive\lyra-crypto-operator"),
    ROOT.parent / "lyra-crypto-operator",
    Path.home() / "lyra-crypto-operator",
]
OPERATOR = next((p for p in _CANDIDATES if p.is_dir()), _CANDIDATES[0])
MIRROR = ROOT / "clawhub" / "mirrors" / "lyra-coin-launch-manager"

# Never ship these into the public skill package
SKIP_NAMES = {
    ".git",
    "operator_tools",
    "GITHUB_CREATE.md",
    "SOURCE_CANONICAL.txt",
}
SKIP_SCRIPT_NAMES = {
    "push_github_auto.py",
    "create_github_repo.ps1",
    "scan_for_secrets.py",
}
ALLOW_ROOT = {
    "SKILL.md",
    "LICENSE",
    "claw.json",
    "README.txt",
    "README.md",
    "CRYPTO_LATTICE_SEPARATION.md",
    "references",
    "scripts",
}


def main() -> int:
    if not OPERATOR.is_dir():
        print(f"MISSING canonical repo: {OPERATOR}", file=sys.stderr)
        return 2
    if MIRROR.exists():
        shutil.rmtree(MIRROR)
    MIRROR.mkdir(parents=True)

    for item in OPERATOR.iterdir():
        if item.name in SKIP_NAMES or item.name.startswith("."):
            continue
        if item.name not in ALLOW_ROOT and item.name not in {"scripts", "references"}:
            # only allow-listed roots
            if item.name not in ALLOW_ROOT:
                continue
        if item.is_dir() and item.name == "scripts":
            dest = MIRROR / "scripts"
            dest.mkdir(parents=True, exist_ok=True)
            for py in item.iterdir():
                if py.name in SKIP_SCRIPT_NAMES:
                    print("skip script", py.name)
                    continue
                if py.suffix.lower() in {".py", ".md", ".txt"} or py.is_file():
                    if py.is_file() and py.name not in SKIP_SCRIPT_NAMES:
                        shutil.copy2(py, dest / py.name)
            continue
        if item.is_dir():
            shutil.copytree(item, MIRROR / item.name, dirs_exist_ok=True)
        else:
            if item.name in ALLOW_ROOT or item.suffix in {".md", ".txt", ".json"}:
                shutil.copy2(item, MIRROR / item.name)

    # safety scrub
    for bad in SKIP_SCRIPT_NAMES:
        p = MIRROR / "scripts" / bad
        if p.exists():
            p.unlink()
            print("removed leaked", p)
    op_tools = MIRROR / "operator_tools"
    if op_tools.exists():
        shutil.rmtree(op_tools)
        print("removed operator_tools from mirror")

    (MIRROR / "SOURCE_CANONICAL.txt").write_text(
        "Public skill surface only.\n"
        f"Canonical: {OPERATOR}\n"
        "Excluded: operator_tools/ (GitHub publish/credentials)\n"
        "Sync: python tools/sync_from_lyra_crypto_operator.py\n",
        encoding="utf-8",
    )
    print(f'{{"ok": true, "mirror": "{MIRROR}", "operator": "{OPERATOR}"}}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
