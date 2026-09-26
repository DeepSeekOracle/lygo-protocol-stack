#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import lygo_tv as t  # noqa: E402


def main() -> int:
    src = (HERE / "lygo_tv.py").read_text(encoding="utf-8")
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    no_sub = not re.search(r"(?m)^\s*import\s+subprocess\b", src)
    no_net = "urllib" not in src and "requests" not in src and "http.client" not in src
    m = t.map_payload()
    u = t.urls()
    embed = t.embed()
    # The declared version is the one in SKILL.md: the script and the signature follow it, so a
    # release needs the version written once. Hardcoding it here meant editing three files and
    # forgetting one still passed.
    found = re.search(r"(?m)^version:\s*([0-9][0-9.]*)\s*$", skill)
    declared = found.group(1) if found else ""
    ok = (
        no_sub
        and no_net
        and bool(declared)
        and t.VERSION == declared
        and t.SIG == "Delta9Phi963-LYGO-TV-v" + declared
        and u["player"] == "https://chatagent.ca/sources/"
        and u["catalog"].endswith("/sources/catalog.json")
        and u["terms"].endswith("/terms.html")
        and u["disclaimer"].endswith("/disclaimer.html")
        and u["emblem"].endswith("/emblem.svg")
        and (ROOT / "emblem.svg").is_file()
        and m["class"] == "RESOURCE"
        and m["live_star_chart_ingest"] is False
        and "CORS or pirate proxy" in m["forbidden"]
        and t.plain().startswith("LYGO TV")
        # the embed: the shipped snippet, the shipped files, and the fetch contract behind them
        and u["player_js"].endswith("/assets/lygo-tv-ninja.js")
        and u["player_css"].endswith("/assets/lygo-tv-ninja.css")
        and "<div data-lygo-tv></div>" in embed
        and "data-lygo-tv" in skill
        and (ROOT / "embed" / "lygo-tv-ninja.js").is_file()
        and (ROOT / "embed" / "lygo-tv-ninja.css").is_file()
        and (ROOT / "embed" / "lygo-tv-embed.html").is_file()
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "declared_in_skill_md": declared,
                "script_version": t.VERSION,
                "signature": t.SIG,
                "no_subprocess": no_sub,
                "no_network_imports": no_net,
                "player": u["player"],
                "embed_assets_present": (ROOT / "embed" / "lygo-tv-ninja.js").is_file(),
                "emblem_file": (ROOT / "emblem.svg").is_file(),
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
