#!/usr/bin/env python3
"""LYGO TV — ClawHub pointer. Prints URLs. No network. No subprocess."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

SIG = "Delta9Phi963-LYGO-TV-v1.2.0"
VERSION = "1.2.0"

TV = "https://chatagent.ca/sources/"
CATALOG = "https://chatagent.ca/sources/catalog.json"
TERMS = "https://chatagent.ca/terms.html"
DISCLAIMER = "https://chatagent.ca/sources/disclaimer.html"
EMBLEM = "https://chatagent.ca/sources/emblem.svg"
SOURCE = "https://github.com/DeepSeekOracle/chatagent/tree/main/sources"
SKILL_SRC = "https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/clawhub/mirrors/lygo-tv"
STACK = "https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/docs/free-sources"
WITNESS = "https://chatagent.ca/witness/"
LISTEN = "https://asiancoastline.com/listen.html"
CLAWHUB = "https://clawhub.ai/deepseekoracle/skills/lygo-tv"
INSTALL = "npx clawhub@latest install deepseekoracle/lygo-tv"
PAYPAL = "https://www.paypal.com/paypalme/ExcavationPro"
PATREON = "https://www.patreon.com/Excavationpro"
RUMBLE = "https://rumble.com/register/Excavationpro/"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def urls() -> dict[str, str]:
    return {
        "player": TV,
        "bookmark": TV,
        "catalog": CATALOG,
        "terms": TERMS,
        "disclaimer": DISCLAIMER,
        "emblem": EMBLEM,
        "source": SOURCE,
        "skill_source": SKILL_SRC,
        "stack_mirror": STACK,
        "witness": WITNESS,
        "listen": LISTEN,
        "clawhub": CLAWHUB,
        "install": INSTALL,
        "paypal": PAYPAL,
        "patreon": PATREON,
        "rumble_join": RUMBLE,
    }


def map_payload() -> dict[str, Any]:
    return {
        "signature": SIG,
        "version": VERSION,
        "channel": "CLAWHUB_PUBLIC_TENTACLE",
        "class": "RESOURCE",
        "live_star_chart_ingest": False,
        "generated_utc": utc_now(),
        "player": TV,
        "how": "Bookmark https://chatagent.ca/sources/ . Channel tab = Excavationpro rooms. Public lists after Terms tick.",
        "default": "Channel tab opens Excavationpro Kick / Rumble / Twitch / YouTube",
        "urls": urls(),
        "forbidden": [
            "CORS or pirate proxy",
            "pay-TV decrypt",
            "invented M3U lists",
            "YouTube cable-news slop",
            "silent Star Chart ingest",
            "auto git/HF/ClawHub/social publish",
        ],
    }


def plain() -> str:
    return "\n".join(
        [
            "LYGO TV — free online TV player",
            "",
            "Bookmark / open: " + TV,
            "1. Channel tab = Excavationpro Kick, Rumble, Twitch, YouTube (always open).",
            "2. FAST / Lists / Topics / Places / Languages after Terms tick for this session.",
            "3. Click a channel. GitHub lists wait for a click.",
            "4. Keys: left/right next, F fullscreen, / search.",
            "5. Agents: " + INSTALL,
            "",
            "Catalog is RESOURCE. Dual ledgers stay CANON.",
            "No login. Optional tip: " + PAYPAL,
            "Install: " + INSTALL,
        ]
    )


def donate() -> dict[str, str]:
    return {"paypal": PAYPAL, "patreon": PATREON, "rumble_join": RUMBLE}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="LYGO TV pointer")
    p.add_argument(
        "cmd",
        nargs="?",
        default="plain",
        choices=("plain", "urls", "map", "demo", "donate", "bookmark"),
    )
    args = p.parse_args(argv)
    if args.cmd == "plain":
        sys.stdout.write(plain() + "\n")
        return 0
    if args.cmd == "urls":
        print(json.dumps(urls(), indent=2))
        return 0
    if args.cmd == "donate":
        print(json.dumps(donate(), indent=2))
        return 0
    if args.cmd == "bookmark":
        print(json.dumps({"player": TV, "bookmark": TV, "clawhub": CLAWHUB, "install": INSTALL}, indent=2))
        return 0
    print(json.dumps(map_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
