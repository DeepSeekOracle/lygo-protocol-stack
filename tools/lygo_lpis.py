#!/usr/bin/env python3
"""CLI — LYGO Prompt Implant System (LPIS)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lygo_lpis import LYGPromptImplantSystem  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO LPIS")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ing = sub.add_parser("ingest")
    ing.add_argument("--source", required=True)
    ing.add_argument("--file")
    ing.add_argument("--url")

    ana = sub.add_parser("analyze")
    ana.add_argument("--prompt-id", required=True)

    gen = sub.add_parser("generate")
    gen.add_argument("--prompt-id", required=True)
    gen.add_argument("--target", default="grok")
    gen.add_argument("--layers", default="P0,P1,P3,P5")

    imp = sub.add_parser("implant")
    imp.add_argument("--variant-id", required=True)
    imp.add_argument("--target", required=True)

    anc = sub.add_parser("anchor")
    anc.add_argument("--prompt-id", required=True)

    lst = sub.add_parser("list")

    args = ap.parse_args()
    lpis = LYGPromptImplantSystem()

    if args.cmd == "ingest":
        fp = Path(args.file) if args.file else None
        out = lpis.ingest(args.source, file_path=fp, url=args.url)
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 2

    if args.cmd == "analyze":
        print(json.dumps(lpis.analyze_id(args.prompt_id), indent=2))
        return 0

    if args.cmd == "generate":
        layers = [x.strip() for x in args.layers.split(",") if x.strip()]
        out = lpis.generate(args.prompt_id, target=args.target, layers=layers)
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 2

    if args.cmd == "implant":
        out = lpis.implant(args.variant_id, args.target)
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 2

    if args.cmd == "anchor":
        out = lpis.anchor_prompt(args.prompt_id)
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 2

    if args.cmd == "list":
        print(json.dumps(lpis.vault.list_ids(), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())