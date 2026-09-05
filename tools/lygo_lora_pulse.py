#!/usr/bin/env python3
"""Stack hybrid: Layer D compact pulse via lygo-lora-mesh codec. No radio driver."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(os.environ.get("LYGO_STACK_ROOT") or Path(__file__).resolve().parents[1])
MIRROR = STACK / "clawhub" / "mirrors" / "lygo-lora-mesh" / "scripts"
GROK = Path(r"I:\E Drive\.grok\skills\lygo-lora-mesh\scripts")
for cand in (MIRROR, GROK):
    if (cand / "lygo_lora.py").is_file():
        sys.path.insert(0, str(cand))
        break
else:
    sys.stderr.write("lygo_lora.py missing — install lygo-lora-mesh or sync clawhub/mirrors/lygo-lora-mesh\n")
    raise SystemExit(2)

import lygo_lora as t  # noqa: E402

OUT = STACK / "data" / "living_mesh" / "lora_last.json"
DEFAULT_BADGE = STACK / "data" / "living_mesh" / "last_badge.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_badge(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="LYGO LoRa pulse on living-mesh")
    p.add_argument(
        "cmd",
        nargs="?",
        default="encode",
        choices=("encode", "decode", "probe", "compare", "ingest", "plain"),
    )
    p.add_argument("--badge", default="")
    p.add_argument("--pulse", default="")
    p.add_argument("--pulse-file", default="")
    p.add_argument("--i-consent", action="store_true")
    args = p.parse_args(argv)

    if args.cmd == "plain":
        sys.stdout.write(t.plain() + "\n")
        return 0

    badge_path = Path(args.badge) if args.badge else DEFAULT_BADGE
    pf = Path(args.pulse_file) if args.pulse_file else None

    if args.cmd == "probe":
        print(json.dumps(t.probe(pf), indent=2))
        return 0
    if args.cmd == "decode":
        print(json.dumps(t.decode_pulse(args.pulse), indent=2))
        return 0 if t.decode_pulse(args.pulse).get("ok") else 1

    if not badge_path.is_file():
        print(json.dumps({"ok": False, "yield": "NAMED_SHADOW", "reason": "no last_badge.json"}, indent=2))
        return 1
    try:
        badge = load_badge(badge_path)
        pulse = t.pulse_from_badge(badge)
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as e:
        print(json.dumps({"ok": False, "yield": "NAMED_SHADOW", "error": str(e)}, indent=2))
        return 1

    lm = badge.get("living_mesh") if isinstance(badge.get("living_mesh"), dict) else {}
    local_digest = str(lm.get("roots_digest") or "")

    if args.cmd == "encode":
        print(json.dumps({"ok": True, "pulse": pulse, "bytes": len(pulse.encode("ascii")), "badge": str(badge_path)}, indent=2))
        return 0

    remote = t.decode_pulse(args.pulse) if args.pulse else t.probe(pf)
    cmp = t.compare(local_digest, remote)
    if args.cmd == "compare":
        print(json.dumps(cmp, indent=2))
        return 0

    if args.cmd == "ingest":
        if not args.i_consent:
            print(json.dumps({"ok": False, "error": "ingest needs --i-consent"}, indent=2))
            return 2
        rec = {
            "signature": t.SIG,
            "written_utc": utc_now(),
            "pulse": args.pulse or (remote.get("pulse_file") if remote.get("board") else None),
            "compare": cmp,
            "live_star_chart_ingest": False,
            "note": "RF receipt only. Does not merge eggs or write the live Star Chart.",
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "wrote": str(OUT), "verdict": cmp.get("verdict")}, indent=2))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
