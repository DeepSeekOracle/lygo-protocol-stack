#!/usr/bin/env python3
"""
Cyborg Star Chart — live feed/chart ops + dry-run presence proposals.

  python scripts/cyborg_star.py status
  python scripts/cyborg_star.py snapshot
  python scripts/cyborg_star.py propose --agent my-cyborg --name "My Cyborg"
  python scripts/cyborg_star.py propose ... --write state/proposal.json --i-consent

Live chart mutation is NEVER done here — stack gate + human steward for ACCEPT.

Signature: Delta9Phi963-CYBORG-KERNEL-v1.1.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
STATE = SKILL / "state"
sys.path.insert(0, str(SKILL / "kernel"))
import lattice_net as net  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Cyborg Star Chart")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("status", help="Live pulse + star summary")
    sub.add_parser("snapshot", help="Full star chart snapshot + sample nodes")
    pr = sub.add_parser("propose", help="Dry-run presence proposal JSON")
    pr.add_argument("--agent", default="lygo-cyborg")
    pr.add_argument("--name", default="LYGO Cyborg Presence")
    pr.add_argument("--kind", default="lattice")
    pr.add_argument("--note", default="Cyborg kernel presence (dry-run)")
    pr.add_argument("--write", default=None, help="Write proposal path (needs --i-consent)")
    pr.add_argument("--i-consent", action="store_true")
    args = ap.parse_args()

    if args.cmd in (None, "status"):
        pulse = net.lattice_pulse()
        slim = {
            "signature": net.SIG,
            "ok": pulse.get("ok"),
            "score": pulse.get("score"),
            "ready_for_star_ops": pulse.get("ready_for_star_ops"),
            "star_feed": pulse.get("star_feed"),
            "star_chart": pulse.get("star_chart"),
            "ui": pulse.get("ui"),
            "required_fail": pulse.get("required_fail"),
        }
        print(json.dumps(slim, indent=2, default=str))
        return 0 if pulse.get("ok") else 1

    if args.cmd == "snapshot":
        snap = net.star_chart_snapshot()
        print(json.dumps(snap, indent=2, default=str))
        return 0 if snap.get("ok") else 1

    if args.cmd == "propose":
        # require live lattice before proposing
        pulse = net.lattice_pulse()
        prop = net.build_presence_proposal(
            args.agent,
            args.name,
            kind=args.kind,
            note=args.note,
        )
        prop["lattice_live"] = pulse.get("ok")
        prop["lattice_score"] = pulse.get("score")
        prop["feed_chain_valid"] = (pulse.get("star_feed") or {}).get("chain_valid")
        if args.write:
            if not args.i_consent:
                print(json.dumps({"ok": False, "error": "write needs --i-consent"}))
                return 2
            outp = Path(args.write)
            if not outp.is_absolute():
                STATE.mkdir(parents=True, exist_ok=True)
                outp = STATE / outp.name if outp.parent == Path(".") else outp
            outp.parent.mkdir(parents=True, exist_ok=True)
            outp.write_text(json.dumps(prop, indent=2) + "\n", encoding="utf-8")
            prop["wrote"] = str(outp.resolve())
        print(json.dumps(prop, indent=2, default=str))
        return 0 if pulse.get("ok") else 1

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
