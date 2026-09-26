#!/usr/bin/env python3
"""The map: what this skill is, where its parts live, and how to check them.

No network. No subprocess. No writes. Prints only.

    python scripts/lygo_llm_console_map.py plain   # human readable
    python scripts/lygo_llm_console_map.py map     # JSON, full
    python scripts/lygo_llm_console_map.py urls    # links only
    python scripts/lygo_llm_console_map.py demo    # what to type to see it work
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KIT = ROOT / "kit"

URLS = {
    "page": "https://chatagent.ca/lygo-llm-console.html",
    "clawhub": "https://clawhub.ai/deepseekoracle/skills/lygo-llm-console",
    "source": "https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/clawhub/mirrors/lygo-llm-console",
    "sparse_checkout": "git clone --depth 1 --filter=blob:none --sparse https://github.com/DeepSeekOracle/lygo-protocol-stack.git",
    "donate": "https://www.paypal.com/paypalme/ExcavationPro",
}

STEPS = {
    "install": "npx --yes clawhub@0.23.3 install deepseekoracle/lygo-llm-console",
    "verify": "python scripts/verify_kit.py",
    "self_check": "python scripts/self_check.py",
    "seed_identity": "cd kit && python src/install.py",
    "run_windows": "kit/INSTALL.bat then kit/LYGO_LLM_CONSOLE.bat (unprivileged user)",
    "portal": "http://127.0.0.1:9641/",
    "stop_windows": "kit/LYGO_LLM_CONSOLE_STOP.bat",
    "engine": "place ggml-org CPU llama-server.exe (tag b11074) in kit/engine/",
}


def load(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def kit_facts() -> dict:
    sums = KIT / "KIT_SHA256SUMS.txt"
    man = load(KIT / "PUBLIC_KIT.json")
    facts = {
        "ship_form": "unpacked tree (no archive)",
        "release": (KIT / "VERSION").read_text(encoding="utf-8").splitlines()[0].strip()
        if (KIT / "VERSION").is_file()
        else "unknown",
        "manifest": "kit/PUBLIC_KIT.json",
        "file_count": man.get("file_count"),
        "left_out": list(man.get("not_shipped", {}).keys()) if man else [],
    }
    if sums.is_file():
        facts["checksum_lines"] = len([ln for ln in sums.read_text(encoding="utf-8").splitlines() if ln.strip()])
        facts["kit_sha256sums"] = hashlib.sha256(sums.read_bytes()).hexdigest()
    facts["top_level"] = sorted(p.name for p in KIT.iterdir()) if KIT.is_dir() else []
    return facts


def payload() -> dict:
    claw = load(ROOT / "claw.json")
    return {
        "skill": "lygo-llm-console",
        "version": claw.get("version"),
        "console_release": claw.get("console_release"),
        "signature": claw.get("signature"),
        "publisher": claw.get("publisher"),
        "steward": claw.get("steward"),
        "layers": {
            "map": "scripts/ - no network, no subprocess, no writes",
            "operator_runtime": "kit/ - loopback HTTP, HTTPS GET, kit-local writes, optional shell/Python (not a sandbox)",
        },
        "permissions": claw.get("permissions", {}),
        "kit": kit_facts(),
        "urls": URLS,
        "steps": STEPS,
        "canon": "dual ledgers / Haven Star Chart = CANON; this package = RESOURCE",
    }


def plain(d: dict) -> str:
    lines = [
        "LYGO LLM Console - skill %s (ships console %s)" % (d["version"], d["console_release"]),
        "",
        "map layer      : scripts/ - prints only; no network, no subprocess, no writes",
        "runtime layer  : kit/ - the public console tree, unpacked, %s files" % d["kit"].get("file_count"),
        "kit release    : %s" % d["kit"].get("release"),
        "checksums      : kit/KIT_SHA256SUMS.txt (%s lines)" % d["kit"].get("checksum_lines"),
        "left out       : weights, engine binaries, tests, steward admin files (see kit/PUBLIC_KIT.json)",
        "",
        "verify         : python scripts/verify_kit.py",
        "install        : %s" % STEPS["install"],
        "run            : %s" % STEPS["run_windows"],
        "portal         : %s" % STEPS["portal"],
        "",
        "Not Ollama. Not a sandbox. No steward vaults, keys or weights.",
        "Steward: %s" % d["steward"],
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    cmd = (argv[0] if argv else "plain").lower()
    d = payload()
    if cmd in ("map", "json"):
        print(json.dumps(d, indent=2))
    elif cmd == "urls":
        print(json.dumps(d["urls"], indent=2))
    elif cmd == "demo":
        print(json.dumps({"steps": STEPS, "urls": d["urls"]}, indent=2))
    else:
        print(plain(d))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
