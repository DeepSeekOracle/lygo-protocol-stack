#!/usr/bin/env python3
"""Push repos to GitHub using Git Credential Manager (Windows). No secrets printed."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CRYPTO = STACK.parent / "lyra-crypto-operator"


def gcm_password(host: str, path: str) -> str | None:
    payload = f"protocol=https\nhost={host}\npath={path}\n\n"
    for cmd in (["git", "credential-manager", "get"], ["git", "credential", "fill"]):
        try:
            cp = subprocess.run(
                cmd,
                input=payload if cmd[-1] == "get" else "protocol=https\nhost=github.com\n\n",
                capture_output=True,
                text=True,
                timeout=60,
            )
        except FileNotFoundError:
            continue
        if cp.returncode != 0:
            continue
        for line in cp.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    return None


def push_repo(repo: Path, github_path: str) -> int:
    token = gcm_password("github.com", github_path)
    if not token:
        print(f"SKIP {repo}: no GCM credential for /{github_path}", file=sys.stderr)
        return 2
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    subprocess.run(["gh", "auth", "setup-git"], cwd=repo, env=env, capture_output=True)
    cp = subprocess.run(
        ["git", "push", "origin", "HEAD"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if cp.stdout:
        print(cp.stdout.strip())
    if cp.stderr:
        print(cp.stderr.strip())
    if cp.returncode == 0:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
        print(f"OK {github_path} -> {head}")
    return cp.returncode


def main() -> int:
    jobs = [
        (STACK, "DeepSeekOracle/lygo-protocol-stack"),
        (CRYPTO, "DeepSeekOracle/lyra-crypto-operator"),
    ]
    rc = 0
    for repo, path in jobs:
        if not (repo / ".git").is_dir():
            print(f"SKIP missing {repo}", file=sys.stderr)
            continue
        if push_repo(repo, path) != 0:
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())