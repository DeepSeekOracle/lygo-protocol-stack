#!/usr/bin/env python3
"""Register a URL/file into Pure-Data Witness + optional Star Chart pending node.

Safety-gated. Agents/humans:
  python tools/pure_data_register.py --url https://... --i-consent
  python tools/pure_data_register.py --file ./page.html --i-consent
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from map_pure_data_to_star_chart import HUB, ROOT_NODE, _node_id_from_witness, build_pdw_nodes  # noqa: E402
from pure_data_safety import check_url  # noqa: E402
from pure_data_witness import (  # noqa: E402
    continuum_claims,
    digest_file,
    fetch_url,
    make_egg,
    rebuild_ledger,
)


def _star_submission(card: dict) -> dict:
    wid = card["witness_id"]
    nid = _node_id_from_witness(wid)
    node = {
        "id": nid,
        "kind": "node",
        "name": f"Witness {wid}",
        "equation": f"H={str(card.get('content_sha256') or '')[:20]}…",
        "glyph": "◆",
        "tone": "741Hz",
        "tags": ["PURE_DATA", "PDW", "WITNESS", "ARCHIVE", "FORK_LOG", "DIGEST", "AGENT_SUBMIT"],
        "connections": [HUB, ROOT_NODE],
        "urls": {
            "source": card.get("source_url") or "",
            "ledger": "https://deepseekoracle.github.io/lygo-protocol-stack/pure-data/ledger.json",
        },
        "layer": "C",
        "meta": {
            "role": "pdw_witness",
            "witness_id": wid,
            "content_sha256": card.get("content_sha256"),
            "egg_id": card.get("egg_id"),
            "safety": card.get("safety"),
        },
    }
    return {
        "signature": "Δ9Φ963-HAVEN-STAR-SUBMISSION-v1",
        "scan_cue": "LYGO-HSC-ATTEST-v1",
        "node": node,
        "pdw_card": {
            "witness_id": wid,
            "content_sha256": card.get("content_sha256"),
            "source_url": card.get("source_url"),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="PDW register + star-chart proposal")
    ap.add_argument("--url")
    ap.add_argument("--file")
    ap.add_argument("--out", default="data/pure_data")
    ap.add_argument("--ledger", default="docs/pure-data/ledger.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--i-consent", action="store_true")
    ap.add_argument("--skip-star-chart", action="store_true")
    ap.add_argument("--agent-id", default="lygo-pure-data-witness")
    ap.add_argument("--skill-slug", default="lygo-pure-data-witness")
    args = ap.parse_args()

    if not args.i_consent:
        print(json.dumps({"ok": False, "error": "consent_required:--i-consent"}))
        return 2
    if not args.url and not args.file:
        print(json.dumps({"ok": False, "error": "need --url or --file"}))
        return 2

    out = Path(args.out)
    if args.url:
        pre = check_url(args.url)
        if not pre.get("ok"):
            print(json.dumps({"ok": False, "stage": "url_gate", "gate": pre}, indent=2))
            return 3
        if args.dry_run:
            print(json.dumps({"ok": True, "dry_run": True, "url_gate": pre}, indent=2))
            return 0
        card = fetch_url(args.url, out)
    else:
        if args.dry_run:
            print(json.dumps({"ok": True, "dry_run": True, "file": args.file}, indent=2))
            return 0
        card = digest_file(Path(args.file), out, None)

    card_path = out / f"{card['witness_id']}.json"
    egg = make_egg(card_path, out / "eggs")
    continuum_claims(card_path)
    led = rebuild_ledger(out, Path(args.ledger))
    build_pdw_nodes(Path(args.ledger))

    star = None
    if not args.skip_star_chart:
        sub = _star_submission(json.loads(card_path.read_text(encoding="utf-8")))
        pending_dir = ROOT / "data" / "haven_star_chart" / "submissions" / "pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        sub_path = out / f"{card['witness_id']}.star_submission.json"
        sub_path.write_text(json.dumps(sub, indent=2), encoding="utf-8")
        # Prefer official gate submit
        import subprocess

        cmd = [
            sys.executable,
            str(ROOT / "tools" / "haven_star_chart_submit.py"),
            str(sub_path),
            "--agent-id",
            args.agent_id,
            "--skill-slug",
            args.skill_slug,
            "--i-consent",
        ]
        cp = subprocess.run(cmd, capture_output=True, text=True)
        star = {"returncode": cp.returncode, "stdout": cp.stdout[-2000:], "stderr": cp.stderr[-500:]}

    print(
        json.dumps(
            {
                "ok": True,
                "witness_id": card["witness_id"],
                "egg_id": egg.get("egg_id"),
                "ledger_root": led.get("merkle_style_root"),
                "egg_root": led.get("egg_fragment_root"),
                "star_chart": star,
                "safety": card.get("safety"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
