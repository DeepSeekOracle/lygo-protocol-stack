#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lygo_llm_console_map as m  # noqa: E402


def main() -> int:
    src = (HERE / "lygo_llm_console_map.py").read_text(encoding="utf-8")
    no_sub = not re.search(r"(?m)^\s*import\s+subprocess\b", src)
    no_net = "urllib" not in src and "requests" not in src and "http.client" not in src
    payload = m.map_payload()
    skill = HERE.parent / "SKILL.md"
    ok = (
        payload["public"]["page"].startswith("https://chatagent.ca/")
        and payload["admin"]["included"] is False
        and "ollama.exe" in str(payload["product"]["not"])
        and no_sub
        and no_net
        and m.VERSION == "1.0.1"
        and (HERE.parent / "kit" / "src" / "server.py").is_file()
        and (HERE.parent / "README.md").is_file()
        and (HERE.parent / "skill-card.md").is_file()
        and "LYGO_SERVER_KEYS" not in src
        and "run_cmd" not in src
        and skill.is_file()
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "signature": m.SIG,
                "no_subprocess": no_sub,
                "no_network_imports": no_net,
                "admin_included": payload["admin"]["included"],
                "page": payload["public"]["page"],
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
