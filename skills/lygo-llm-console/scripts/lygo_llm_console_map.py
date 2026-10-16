#!/usr/bin/env python3
"""Map-only. No network. No subprocess."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

SIG = "LYGO-LLM-CONSOLE-SKILL-v1.2.0"
VERSION = "1.2.0"
PAGE = "https://chatagent.ca/lygo-llm-console.html"
ZIP_NAME = "lygo-llm-console-public.zip"
KIT_SHA = "b60ed6deae6f1dba7182fa386bd00b1e724001638e8f2f30936af0a240b4444e"
CLAWHUB = "https://clawhub.ai/deepseekoracle/skills/lygo-llm-console"
INSTALL = "npx --yes clawhub@0.23.3 install deepseekoracle/lygo-llm-console"
DONATE_PP = "https://www.paypal.com/paypalme/ExcavationPro"
LLAMA_TAG = "b10988"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def map_payload() -> dict[str, Any]:
    return {
        "signature": SIG,
        "version": VERSION,
        "channel": "CLAWHUB_PUBLIC_SKILL",
        "generated_utc": utc_now(),
        "layers": {
            "A_map": "scripts only; no network; no spawn",
            "B_runtime": "kit zip after SHA-256 verify; operator runs BAT as unprivileged user",
        },
        "kit_sha256": KIT_SHA,
        "kit_zip": ZIP_NAME,
        "llama_cpu_tag": LLAMA_TAG,
        "public": {"page": PAGE, "clawhub": CLAWHUB, "install": INSTALL},
        "admin": {"included": False},
        "donate": {"paypal": DONATE_PP},
    }


def plain() -> str:
    return "\n".join(
        [
            "LYGO LLM Console map v1.2.0",
            "Install: " + INSTALL,
            "Verify kit SHA-256: " + KIT_SHA,
            "Engine tag: " + LLAMA_TAG,
            "Page: " + PAGE,
            "Admin vaults: not included",
        ]
    )


def urls() -> dict[str, str]:
    return {"page": PAGE, "clawhub": CLAWHUB, "paypal": DONATE_PP, "install": INSTALL}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="map", choices=["map", "plain", "urls", "demo"])
    args = ap.parse_args()
    if args.cmd == "plain":
        sys.stdout.write(plain() + "\n")
        return 0
    if args.cmd == "urls":
        print(json.dumps(urls(), indent=2))
        return 0
    print(json.dumps(map_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
