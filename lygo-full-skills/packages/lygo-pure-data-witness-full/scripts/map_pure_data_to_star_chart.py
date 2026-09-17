#!/usr/bin/env python3
"""Map Pure-Data Witness ledger into Haven Star Chart nodes.

Creates:
  LATTICE_PURE_DATA_WITNESS — hub
  SEAL-style root via NODE_PDW_ROOT (lattice node; gate ID-safe)
  NODE_PDW_<hash12> — one star per witness (fork/archive log)

Usage:
  python tools/map_pure_data_to_star_chart.py --json
  python tools/build_haven_star_chart.py   # merges via import
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STACK = Path(__file__).resolve().parents[1]
LEDGER = STACK / "docs" / "pure-data" / "ledger.json"
OUT = STACK / "data" / "pure_data" / "star_chart_pdw_roots.json"

HUB = "LATTICE_PURE_DATA_WITNESS"
ROOT_NODE = "NODE_PDW_ROOT"
LIGHTFATHER = "CHAMPION_LIGHTFATHER"
SEAL_000 = "SEAL_000"


def _node_id_from_witness(wid: str) -> str:
    # NODE_PDW_5A5E3C3C0E77 from PDW-5A5E3C3C0E77
    hexpart = re.sub(r"^PDW-", "", wid or "", flags=re.I)
    hexpart = re.sub(r"[^A-F0-9]", "", hexpart.upper())[:16] or "0"
    return f"NODE_PDW_{hexpart}"


def build_pdw_nodes(ledger_path: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = ledger_path or LEDGER
    witnesses: list[dict] = []
    root = None
    if path.is_file():
        led = json.loads(path.read_text(encoding="utf-8"))
        witnesses = led.get("witnesses") or []
        root = led.get("merkle_style_root")

    nodes: list[dict[str, Any]] = []
    nodes.append(
        {
            "id": HUB,
            "kind": "lattice",
            "name": "Pure-Data Witness Hub",
            "equation": "Pure = SHA256(bytes_at_T) ∧ ¬rewrite",
            "glyph": "📜",
            "tone": "963Hz",
            "tags": ["LATTICE", "PURE_DATA", "PDW", "ARCHIVE", "DIGEST", "GROWTH"],
            "connections": [SEAL_000, ROOT_NODE, LIGHTFATHER],
            "urls": {
                "design": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_PURE_DATA_WITNESS.md",
                "ui": "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/pure-data.html",
                "register": "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/register.html",
                "ledger": "https://deepseekoracle.github.io/lygo-protocol-stack/pure-data/ledger.json",
            },
            "layer": "C",
            "meta": {
                "role": "pure_data_hub",
                "ledger_root": root,
                "witness_count": len(witnesses),
            },
        }
    )
    nodes.append(
        {
            "id": ROOT_NODE,
            "kind": "node",
            "name": "PDW Archive Root",
            "equation": "WitnessRoot = Merkle(content_sha256_i)",
            "glyph": "🔗",
            "tone": "528Hz",
            "tags": ["PURE_DATA", "PDW", "ARCHIVE_ROOT", "FORK_LOG", "DIGEST"],
            "connections": [HUB, SEAL_000],
            "urls": {
                "ledger": "https://deepseekoracle.github.io/lygo-protocol-stack/pure-data/ledger.json",
            },
            "layer": "C",
            "meta": {"role": "pdw_root", "ledger_root": root},
        }
    )

    fork_log: list[dict] = []
    prev = ROOT_NODE
    for w in witnesses:
        wid = w.get("witness_id") or ""
        nid = _node_id_from_witness(wid)
        sha = (w.get("content_sha256") or "")[:16]
        nodes.append(
            {
                "id": nid,
                "kind": "node",
                "name": f"Witness {wid}",
                "equation": f"H = {sha}…",
                "glyph": "◆",
                "tone": "741Hz",
                "tags": ["PURE_DATA", "PDW", "WITNESS", "ARCHIVE", "FORK_LOG", "DIGEST"],
                "connections": [HUB, ROOT_NODE, prev],
                "urls": {
                    "source": w.get("source_url") or "",
                    "ledger": "https://deepseekoracle.github.io/lygo-protocol-stack/pure-data/ledger.json",
                },
                "layer": "C",
                "meta": {
                    "role": "pdw_witness",
                    "witness_id": wid,
                    "content_sha256": w.get("content_sha256"),
                    "captured_utc": w.get("captured_utc"),
                    "egg_id": w.get("egg_id"),
                    "bytes": w.get("bytes"),
                    "parent_node": prev,
                },
            }
        )
        fork_log.append({"node_id": nid, "witness_id": wid, "parent": prev, "sha256": w.get("content_sha256")})
        prev = nid

    stats = {
        "witnesses": len(witnesses),
        "nodes": len(nodes),
        "ledger_root": root,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "signature": "Delta9Phi963-PDW-STAR-CHART-ROOTS-v1",
                "hub": HUB,
                "root": ROOT_NODE,
                "fork_log": fork_log,
                "stats": stats,
                "nodes": nodes,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return nodes, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ledger", type=Path, default=None)
    args = ap.parse_args()
    nodes, stats = build_pdw_nodes(args.ledger)
    if args.json:
        print(json.dumps({"stats": stats, "node_ids": [n["id"] for n in nodes]}, indent=2))
    else:
        print(f"PDW star map: {stats['nodes']} nodes, {stats['witnesses']} witnesses → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
