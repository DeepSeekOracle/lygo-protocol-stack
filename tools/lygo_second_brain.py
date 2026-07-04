#!/usr/bin/env python3
"""LYGO Second Brain — stack CLI wrapper (ingest, index, search, consensus, wiki)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "lygo_second_brain" / "scripts"
DEFAULT_VAULT = ROOT / "lygo_second_brain" / "vault"


def vault_root() -> Path:
    env = os.environ.get("LYGO_VAULT_ROOT")
    return Path(env).resolve() if env else DEFAULT_VAULT.resolve()


def run_script(script: str, extra: list[str]) -> int:
    py = SCRIPTS / script
    if not py.is_file():
        print(f"Missing {py}", file=sys.stderr)
        return 1
    cmd = [sys.executable, str(py), *extra, "--vault", str(vault_root())]
    return subprocess.call(cmd)


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: lygo_second_brain.py {ingest|index|search|consensus|wiki} ...\n"
            f"Vault: {vault_root()} (override: LYGO_VAULT_ROOT)",
            file=sys.stderr,
        )
        return 1
    cmd = sys.argv[1].lower()
    rest = sys.argv[2:]
    if cmd == "ingest":
        if not rest:
            print("ingest requires a source path under vault/raw/", file=sys.stderr)
            return 1
        return run_script("ingest.py", rest)
    if cmd == "index":
        return run_script("embed_index.py", rest)
    if cmd == "search":
        if not rest:
            print("search requires a query string", file=sys.stderr)
            return 1
        return run_script("search.py", rest)
    if cmd == "consensus":
        if not rest:
            print("consensus requires a question string", file=sys.stderr)
            return 1
        return run_script("consensus.py", rest)
    if cmd == "wiki":
        if not rest:
            print("wiki requires a topic string", file=sys.stderr)
            return 1
        return run_script("wiki_build.py", rest)
    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())