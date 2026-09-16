#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lygo_llm_console_map as m  # noqa: E402

PIN = "0df99aeb65593e336d33a8252101364fb7b4e595e888ed79280341aa7195e4ce"


def main() -> int:
    src = (HERE / "lygo_llm_console_map.py").read_text(encoding="utf-8")
    no_sub = not re.search(r"(?m)^\s*import\s+subprocess\b", src)
    no_net = "urllib" not in src and "requests" not in src and "http.client" not in src
    payload = m.map_payload()
    zip_ok = (HERE.parent / "kit" / "lygo-llm-console-public.zip").is_file()
    sha_file = HERE.parent / "kit" / "lygo-llm-console-public.zip.sha256"
    pin_ok = PIN in src and payload.get("kit_sha256") == PIN
    ok = (
        payload["admin"]["included"] is False
        and no_sub
        and no_net
        and m.VERSION == "1.2.0"
        and "clawhub@0.23.3" in src
        and "@latest" not in src
        and zip_ok
        and pin_ok
        and (HERE.parent / "README.md").is_file()
        and sha_file.is_file()
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "signature": m.SIG,
                "no_subprocess": no_sub,
                "no_network_imports": no_net,
                "kit_zip": zip_ok,
                "kit_sha256_pinned": pin_ok,
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
