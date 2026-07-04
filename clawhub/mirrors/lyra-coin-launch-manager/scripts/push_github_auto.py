#!/usr/bin/env python3
"""Create DeepSeekOracle/lyra-crypto-operator (if missing) and push main."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

OPERATOR = Path(__file__).resolve().parents[1]
STACK_ENV = Path(r"I:\E Drive\lygo-protocol-stack\.env")
ORG_REPO = "DeepSeekOracle/lyra-crypto-operator"


def load_token() -> str | None:
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT"):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    if STACK_ENV.is_file():
        for line in STACK_ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT") and v:
                return v
    try:
        cp = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True,
            text=True,
            timeout=30,
        )
        if cp.returncode == 0:
            for line in cp.stdout.splitlines():
                if line.startswith("password="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def api(method: str, url: str, token: str, body: dict | None = None) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {"message": str(e)}
        except json.JSONDecodeError:
            payload = {"message": raw[:500]}
        return e.code, payload


def ensure_repo(token: str) -> bool:
    code, _ = api("GET", f"https://api.github.com/repos/{ORG_REPO}", token)
    if code == 200:
        print("repo_exists: true")
        return True
    code, body = api(
        "POST",
        "https://api.github.com/user/repos",
        token,
        {
            "name": "lyra-crypto-operator",
            "description": "LYRA Clawnch crypto tools — lattice-separated from lygo-protocol-stack",
            "private": False,
        },
    )
    if code == 201:
        print("repo_created: true")
        return True
    if code == 422 and "already exists" in json.dumps(body).lower():
        print("repo_exists: true")
        return True
    print("repo_create_failed:", json.dumps(body)[:400], file=sys.stderr)
    return False


def git_push(token: str) -> int:
    cp = subprocess.run(
        [
            "git",
            "-c",
            f"http.extraHeader=Authorization: Bearer {token}",
            "push",
            "-u",
            "origin",
            "main",
        ],
        cwd=OPERATOR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if cp.stdout:
        print(cp.stdout[-1500:])
    if cp.stderr:
        print(cp.stderr[-1500:])
    return cp.returncode


def main() -> int:
    scan = subprocess.run(
        [sys.executable, str(OPERATOR / "scripts" / "scan_for_secrets.py"), "--all"],
        cwd=OPERATOR,
        timeout=120,
    )
    if scan.returncode != 0:
        print("BLOCKED: scan_for_secrets failed — fix before push", file=sys.stderr)
        return 4
    token = load_token()
    if not token:
        print("NO_GITHUB_TOKEN", file=sys.stderr)
        return 2
    if not ensure_repo(token):
        return 3
    rc = git_push(token)
    if rc == 0:
        print(f"OK https://github.com/{ORG_REPO}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())