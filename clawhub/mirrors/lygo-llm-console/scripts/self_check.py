#!/usr/bin/env python3
"""Self-check: what this skill package is, is not, and can be verified to be.

No network. No subprocess. No writes. Reads this package's own files.

    python scripts/self_check.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CLAW = ROOT / "claw.json"
KIT = ROOT / "kit"

IS = [
    "a map layer: scripts/ prints URLs, hashes and this check",
    "an operator runtime you run yourself: kit/ (unpacked public console tree)",
    "loopback HTTP (9641 portal, 11441 engine) unless you pass --lan --i-consent",
    "https GET to public hosts only; loopback/RFC1918/link-local/.internal refused",
    "writes inside the kit folder (workspace/, save/) unless you widen it in config",
    "a pinned llama-server subprocess plus optional local python/cmd snippets",
]

IS_NOT = [
    "a cloud service, an API key reseller, or a hosted endpoint",
    "Ollama: it never launches or requires ollama.exe (reading an existing CAS tree is optional)",
    "a sandbox: shell/python_exec/rust_exec run code as YOUR user",
    "a carrier of model weights, engine binaries, or the steward's vaults/keys/admin config",
    "LYGO CANON: dual ledgers and the Haven Star Chart are CANON, this package is RESOURCE",
    "a publisher: nothing here posts, uploads or updates by itself",
]


def main() -> int:
    out: dict = {"ok": True, "checks": [], "is": IS, "is_not": IS_NOT}
    meta = {}
    if CLAW.is_file():
        try:
            meta = json.loads(CLAW.read_text(encoding="utf-8"))
        except ValueError as exc:  # noqa: BLE001
            out["ok"] = False
            out["checks"].append(f"claw.json unreadable: {exc}")
    else:
        out["ok"] = False
        out["checks"].append("claw.json missing")

    sums = KIT / "KIT_SHA256SUMS.txt"
    manifest = KIT / "PUBLIC_KIT.json"
    out["checks"].append(f"map layer: {len(list((ROOT / 'scripts').glob('*.py')))} script(s), no network calls")
    out["checks"].append(f"kit present: {KIT.is_dir()}")
    out["checks"].append(f"kit ship form: {meta.get('kit_ship_form', 'unknown')}")
    out["checks"].append(f"checksum list present: {sums.is_file()}")

    if sums.is_file():
        lines = [ln for ln in sums.read_text(encoding="utf-8").splitlines() if ln.strip()]
        out["checks"].append(f"files pinned: {len(lines)}")
        digest = hashlib.sha256(sums.read_bytes()).hexdigest()
        pin = meta.get("kit_sha256sums")
        match = (digest == pin) if pin else None
        out["checks"].append(f"KIT_SHA256SUMS.txt sha256 {digest}")
        out["checks"].append(f"matches claw.json pin: {match}")
        if match is False:
            out["ok"] = False
    else:
        out["ok"] = False

    if manifest.is_file():
        try:
            man = json.loads(manifest.read_text(encoding="utf-8"))
            out["checks"].append(
                f"manifest: console {man.get('console_release')}, {man.get('file_count')} files, "
                f"patched {len(man.get('patched_in_the_copy_only', []))}, listed-as-left-out "
                f"{len(man.get('not_shipped', {}))}"
            )
        except ValueError as exc:  # noqa: BLE001
            out["ok"] = False
            out["checks"].append(f"PUBLIC_KIT.json unreadable: {exc}")
    else:
        out["ok"] = False
        out["checks"].append("kit/PUBLIC_KIT.json missing")

    if (KIT / "VERSION").is_file():
        out["checks"].append(f"kit release: {(KIT / 'VERSION').read_text(encoding='utf-8').splitlines()[0].strip()}")
    out["version"] = meta.get("version")
    out["console_release"] = meta.get("console_release")
    out["verify_with"] = "python scripts/verify_kit.py"
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
