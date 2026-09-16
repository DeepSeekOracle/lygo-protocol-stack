#!/usr/bin/env python3
"""LYGO LLM Console — public ClawHub tentacle. No network. No subprocess."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

SIG = "Δ9Φ963-LYGO-LLM-CONSOLE-SKILL-v1.1.0"
VERSION = "1.1.0"
PAGE = "https://chatagent.ca/lygo-llm-console.html"
ZIP_NAME = "lygo-llm-console-public.zip"
ZIP_URL = "https://chatagent.ca/data/lygo-full-skills/dist/lygo-llm-console-public.zip"
CLAWHUB = "https://clawhub.ai/deepseekoracle/skills/lygo-llm-console"
INSTALL = "npx clawhub@latest install deepseekoracle/lygo-llm-console"
DONATE_PP = "https://www.paypal.com/paypalme/ExcavationPro"
DONATE_PAT = "https://www.patreon.com/Excavationpro"
ARCADE = "https://chatagent.ca/games/"
CRYPT = "https://chatagent.ca/games/lattice-crypt/"
WHITEPAPER = "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/whitepapers/LYGO_LLM_CONSOLE_v1.md"
STEWARD = "Justin Helmer (Excavationpro / Lightfather)"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def map_payload() -> dict[str, Any]:
    return {
        "signature": SIG,
        "version": VERSION,
        "channel": "CLAWHUB_PUBLIC_TENTACLE",
        "generated_utc": utc_now(),
        "mark": "LYGO",
        "steward": STEWARD,
        "credits": {
            "author": STEWARD,
            "lygo_ai_agents": "LYGO protocol stack agents assembled the public kit; they do not own the mark.",
            "inference": "ggml-org llama.cpp (separate project, operator-supplied binary)",
            "canon": "Dual ledgers and Haven Star Chart remain CANON. This skill and page are RESOURCE.",
        },
        "message": "This skill maps the public LYGO LLM Console. Admin/steward trees are not included.",
        "product": {
            "name": "LYGO LLM Console",
            "not": ["Ollama", "ollama.exe", "cloud LLM API"],
            "does": [
                "Scan GGUF and read-only Ollama CAS",
                "Spawn ggml-org llama-server on loopback (in the zip, not this skill)",
                "Agent portal text/tools/images",
                "P0 Φ-gate on generations",
                "OpenAI-shaped /v1 proxy without executing Console tools",
            ],
        },
        "public": {
            "page": PAGE,
            "zip": ZIP_NAME,
            "zip_url": ZIP_URL,
            "clawhub": CLAWHUB,
            "install": INSTALL,
        },
        "admin": {
            "included": False,
            "note": "lygo_llm_console/ on the steward stack is a separate tree. Vaults never ship in the zip.",
        },
        "donate": {"paypal": DONATE_PP, "patreon": DONATE_PAT},
        "play": {"arcade": ARCADE, "crypt": CRYPT},
        "whitepaper": WHITEPAPER,
    }


def plain() -> str:
    m = map_payload()
    return "\n".join(
        [
            "LYGO LLM Console — public map",
            f"Steward: {STEWARD}",
            f"Page: {PAGE}",
            f"Zip: {ZIP_URL}",
            f"ClawHub: {INSTALL}",
            "Admin tree is NOT in this skill.",
            "Ollama is not required.",
            f"Donate: {DONATE_PP}",
            f"Signature: {SIG}",
        ]
    )


def urls() -> dict[str, str]:
    return {
        "page": PAGE,
        "zip": ZIP_URL,
        "clawhub": CLAWHUB,
        "whitepaper": WHITEPAPER,
        "paypal": DONATE_PP,
        "patreon": DONATE_PAT,
        "arcade": ARCADE,
    }


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
