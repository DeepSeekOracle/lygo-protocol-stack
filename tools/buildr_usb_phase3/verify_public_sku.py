#!/usr/bin/env python3
"""Scan a PUBLIC_SKU export tree for forbidden builder secrets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FORBIDDEN_NAMES = {
    ".env",
    "credentials.json",
    "core_signing.key",
    "id_rsa",
    "wallet.json",
}
FORBIDDEN_PARTS = ("_builder_vault", ".git", "GROK_BUILDR_BOOT.md")
SECRET_PATTERNS = (
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{20,}"),
    re.compile(r"xai-[a-zA-Z0-9]{20,}"),
)


def scan(root: Path) -> dict:
    hits: list[str] = []
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root).as_posix()
        if any(p in rel for p in FORBIDDEN_PARTS):
            hits.append(f"forbidden_path:{rel}")
        if f.name in FORBIDDEN_NAMES:
            hits.append(f"forbidden_name:{rel}")
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")[:50000]
        except OSError:
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                hits.append(f"secret_pattern:{rel}")
                break
    required = [
        root / "README.txt",
        root / "PUBLIC_MANIFEST.json",
        root / "core",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    ok = not hits and not missing
    return {"ok": ok, "root": str(root), "hits": hits[:50], "missing": missing}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("export_dir")
    args = ap.parse_args()
    report = scan(Path(args.export_dir))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())