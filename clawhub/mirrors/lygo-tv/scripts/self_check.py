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
    ok = (
        no_sub
        and no_net
        and t.VERSION == "1.2.0"
        and t.SIG == "Delta9Phi963-LYGO-TV-v1.2.0"
        and "version: 1.2.0" in skill
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
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "signature": t.SIG,
                "version": t.VERSION,
                "no_subprocess": no_sub,
                "no_network_imports": no_net,
                "player": u["player"],
                "emblem_file": (ROOT / "emblem.svg").is_file(),
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
