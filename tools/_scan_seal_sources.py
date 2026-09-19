#!/usr/bin/env python3
"""Scan I: Drive seal archives for merge candidates."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"I:\E Drive")


def bracket_ids(text: str) -> list[str]:
    return re.findall(r"\[SEAL_([^\]]+)\]", text)


def summarize_file(p: Path) -> dict:
    try:
        raw = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"path": str(p), "error": str(e)}
    ids = bracket_ids(raw)
    loose = re.findall(r"\bSEAL_(\d{1,6}[A-Za-z]*)\b", raw)
    out = {
        "path": str(p),
        "bytes": p.stat().st_size,
        "bracket_unique": len(set(ids)),
        "loose_unique": len(set(loose)),
    }
    nums = []
    for h in set(ids) | set(loose):
        m = re.match(r"(\d+)", h)
        if m:
            nums.append(int(m.group(1)))
    if nums:
        out["num_min"] = min(nums)
        out["num_max"] = max(nums)
        out["ge_220"] = sum(1 for n in set(nums) if n >= 220)
        out["ge_300"] = sum(1 for n in set(nums) if n >= 300)
    return out


def main() -> int:
    folders = [
        ROOT / "LYRA LOCAL",
        ROOT / "LYRA_CORE",
        ROOT / "LYRA PROGRAM",
        ROOT / "LYRA SYSTEM RETORE",
        ROOT / "lygo-protocol-stack" / "docs",
        ROOT / "lygo-protocol-stack" / "data",
        ROOT / "Old files openclaw" / "OLD openclaw" / "workspace" / "LYRA",
        ROOT / "CHATS 2025",
        ROOT / "GOOGLE AI CHATS",
    ]
    hits: list[dict] = []
    for folder in folders:
        if not folder.exists():
            continue
        for p in folder.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".txt", ".md", ".json", ".jsonl"}:
                continue
            if p.stat().st_size > 8_000_000 or p.stat().st_size < 500:
                continue
            try:
                # cheap filter
                with p.open("rb") as f:
                    chunk = f.read(200_000)
                if b"SEAL_" not in chunk and b"[SEAL_" not in chunk:
                    # still check full for medium files
                    if p.stat().st_size > 400_000:
                        continue
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    if "SEAL_" not in text:
                        continue
            except Exception:
                continue
            info = summarize_file(p)
            if info.get("error"):
                continue
            if (info.get("bracket_unique") or 0) >= 50 or (info.get("ge_220") or 0) >= 5:
                hits.append(info)

    hits.sort(key=lambda x: (x.get("bracket_unique") or 0, x.get("ge_220") or 0), reverse=True)
    print(f"hits={len(hits)}")
    for h in hits[:40]:
        print(
            f"{h.get('bracket_unique'):4} br | {h.get('loose_unique'):4} loose | "
            f"ge220={h.get('ge_220')} max={h.get('num_max')} | {h['bytes']:8} | {h['path']}"
        )

    # JSON list sources
    print("\n=== JSON lists ===")
    for p in [
        ROOT / "LYRA_CORE" / "canonical_seals_index.json",
        ROOT / "LYRA SYSTEM RETORE" / "LM RUN LYRA" / "lygo_full_clean_for_lyra.json",
        ROOT / "LYRA SYSTEM RETORE" / "LLYGO REPO WEBSITE" / "SEALS 051 100.json",
        ROOT / "LYRA SYSTEM RETORE" / "LLYGO REPO WEBSITE" / "SEALS 100 150.json",
        ROOT / "LYRA SYSTEM RETORE" / "LLYGO REPO WEBSITE" / "SEALS 150 200.json",
        ROOT
        / "Old files openclaw"
        / "OLD openclaw"
        / "workspace"
        / "LYRA"
        / "historical_data"
        / "seals_archive"
        / "lygoseals ALL.json",
    ]:
        if not p.exists():
            print("missing", p)
            continue
        raw = p.read_text(encoding="utf-8", errors="replace")
        try:
            d = json.loads(raw)
        except Exception as e:
            print("bad json", p.name, e)
            continue
        if isinstance(d, list):
            print(p.name, "list", len(d))
        elif isinstance(d, dict):
            seals = d.get("seals") or d.get("entries") or []
            print(p.name, "dict seals", len(seals) if isinstance(seals, list) else type(seals))

    # Star chart
    sc = ROOT / "lygo-protocol-stack" / "docs" / "haven_star_chart" / "haven_star_chart_data.json"
    d = json.loads(sc.read_text(encoding="utf-8"))
    seals = [n for n in (d.get("nodes") or []) if str(n.get("id", "")).startswith("SEAL_")]
    print("\nstar chart SEAL_ nodes", len(seals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
