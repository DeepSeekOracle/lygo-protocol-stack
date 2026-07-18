#!/usr/bin/env python3
"""
Scan I:\\ and J:\\ for audio not yet in the sovereign music vault.
Also flag Haven / audiobook / book narration paths.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
AUDIO = {".mp3", ".wav", ".flac", ".m4a", ".aiff", ".aif", ".ogg", ".aac", ".wma", ".opus", ".m4b"}
SKIP_DIR_NAMES = {
    "windows",
    "$recycle.bin",
    "system volume information",
    "program files",
    "program files (x86)",
    "programdata",
    "appdata",
    "node_modules",
    ".git",
    "steam",
    "steamapps",
    "epic games",
    "battle.net",
    "microsoft",
    "packages",
    "windowsapps",
    "browser_profile",
    "yandex_cdp_profile",
    # Third-party / copyright device libraries — not Excavationpro music
    "ipod",
    "itunes",
}
HAVEN_KEYS = (
    "haven",
    "audiobook",
    "audio book",
    "eternal",
    "lightfather",
    "lore",
    "narrat",
    "chapter",
    "book-brain",
    "book_brain",
    "void atlas",
    "void-atlas",
    "hero",
    "codex",
)


def load_vault_hashes() -> set[str]:
    for p in (
        CAT / "music_vault_index_full.json",
        Path(r"I:\E Drive\MUSIC_VAULT\manifest\vault_index.json"),
        CAT / "music_vault_manifest.json",
    ):
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        objs = data.get("objects") or []
        # full index has sha256; public may too
        hs = {o.get("sha256") for o in objs if o.get("sha256")}
        if hs:
            print(f"[vault] loaded {len(hs)} hashes from {p}", flush=True)
            return hs
    return set()


def is_havenish(path: str, name: str) -> bool:
    low = (path + " " + name).lower()
    return any(k in low for k in HAVEN_KEYS)


def scan_drive(root: Path, by_top: dict, haven_dirs: dict) -> tuple[int, int]:
    total = 0
    tbytes = 0
    for dirpath, dirnames, filenames in os.walk(root):
        low = dirpath.lower()
        # prune
        dirnames[:] = [
            d
            for d in dirnames
            if d.lower() not in SKIP_DIR_NAMES and not d.startswith("$")
        ]
        if any(
            x in low
            for x in (
                "\\windows\\",
                "\\$recycle",
                "\\node_modules",
                "\\program files",
                "\\steam\\",
                "\\appdata\\",
                "\\browser_profile",
            )
        ):
            dirnames[:] = []
            continue
        parts = Path(dirpath).parts
        top = parts[1] if len(parts) > 1 else str(parts[0])
        for fn in filenames:
            ext = Path(fn).suffix.lower()
            if ext not in AUDIO:
                continue
            full = str(Path(dirpath) / fn)
            try:
                sz = os.path.getsize(full)
            except OSError:
                continue
            by_top[top]["n"] += 1
            by_top[top]["bytes"] += sz
            total += 1
            tbytes += sz
            if is_havenish(dirpath, fn):
                haven_dirs[dirpath]["n"] += 1
                haven_dirs[dirpath]["bytes"] += sz
    return total, tbytes


def main() -> int:
    known = load_vault_hashes()
    by_top: dict[str, dict] = defaultdict(lambda: {"n": 0, "bytes": 0})
    haven_dirs: dict[str, dict] = defaultdict(lambda: {"n": 0, "bytes": 0})
    drives = []
    for letter in ("I:/", "J:/"):
        p = Path(letter)
        if p.exists():
            drives.append(p)
            print(f"=== scanning {letter} ===", flush=True)
            n, b = scan_drive(p, by_top, haven_dirs)
            print(f"  audio files {n}  {b/1e9:.2f} GB", flush=True)

    # Haven ranking
    haven_ranked = sorted(haven_dirs.items(), key=lambda x: -x[1]["bytes"])
    print("\n=== TOP HAVEN/BOOK-ISH FOLDERS ===", flush=True)
    for d, s in haven_ranked[:40]:
        print(f"  {s['n']:5d}  {s['bytes']/1e9:6.2f} GB  {d}", flush=True)

    # Top volume folders overall
    print("\n=== TOP AUDIO FOLDERS (drive root children) ===", flush=True)
    for top, s in sorted(by_top.items(), key=lambda x: -x[1]["bytes"])[:40]:
        print(f"  {s['n']:6d}  {s['bytes']/1e9:7.2f} GB  {top}", flush=True)

    report = {
        "known_vault_hashes": len(known),
        "by_top": {k: v for k, v in sorted(by_top.items(), key=lambda x: -x[1]["bytes"])},
        "haven_dirs": [
            {"path": d, "files": s["n"], "bytes": s["bytes"], "gb": round(s["bytes"] / 1e9, 3)}
            for d, s in haven_ranked[:80]
        ],
    }
    out = CAT / "ij_audio_gap_scan.json"
    CAT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {out}", flush=True)

    # Recommend roots not already fully covered
    already = {
        r"J:\ALL SOUND FILES",
        r"I:\Actors",
        r"I:\E Drive\MUSIC_VAULT",
    }
    print("\n=== RECOMMENDED ADDITIONAL ROOTS ===", flush=True)
    for d, s in haven_ranked[:20]:
        if s["n"] < 3:
            continue
        if any(d.lower().startswith(a.lower()) for a in already):
            # still print if haven under known
            if is_havenish(d, ""):
                print(f"  (partially covered) {s['n']} files {s['bytes']/1e9:.2f}GB  {d}", flush=True)
            continue
        print(f"  ADD  {s['n']:5d}  {s['bytes']/1e9:6.2f} GB  {d}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
