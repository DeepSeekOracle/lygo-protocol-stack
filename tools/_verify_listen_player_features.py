#!/usr/bin/env python3
"""Verify listen portal player features are present and structurally sound."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PATHS = [
    Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html"),
    Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html"),
]

REQUIRED = [
    'id="btn-radio"',
    'id="btn-shuffle"',
    'id="btn-repeat"',
    "function toggleRadio",
    "function toggleShuffle",
    "function toggleRepeatOne",
    "function pickNext",
    "function nextTrack",
    "shuffleBag",
    "repeatOne",
    "playablePool",
    "audio.addEventListener('ended'",
    "audio.addEventListener('error'",
    "stream error, skipping",
    "Continuous · auto-next",
    "Radio ON",
]


def check(path: Path) -> list[str]:
    errs: list[str] = []
    if not path.exists():
        return [f"missing {path}"]
    t = path.read_text(encoding="utf-8")
    for s in REQUIRED:
        if s not in t:
            errs.append(f"{path.name}: missing {s!r}")
    # no old broken APIs
    if "function shuffleOrder" in t:
        errs.append(f"{path.name}: old shuffleOrder still present")
    if "let repeat = false" in t and "let repeatOne = false" not in t:
        errs.append(f"{path.name}: old repeat flag without repeatOne")
    m = re.search(r"<script>\s*(const DATA = JSON\.parse.*?)</script>\s*</body>", t, re.S)
    if not m:
        errs.append(f"{path.name}: main script not found")
    else:
        js = m.group(1)
        i = js.find("let order = tracks.map")
        body = js[i:] if i >= 0 else js
        if body.count("{") != body.count("}"):
            errs.append(
                f"{path.name}: brace mismatch {{ {body.count('{')} }} {body.count('}')}"
            )
    boot = re.search(
        r'<script id="boot" type="application/json">(.*?)</script>', t, re.S
    )
    if not boot:
        errs.append(f"{path.name}: boot JSON missing")
    else:
        try:
            data = json.loads(boot.group(1))
            tracks = (data.get("playlist") or {}).get("tracks") or []
            playable = sum(1 for x in tracks if x.get("stream_url"))
            if playable < 100:
                errs.append(f"{path.name}: only {playable} playable tracks")
            print(f"[ok] {path.name}: tracks={len(tracks)} playable={playable}")
        except json.JSONDecodeError as e:
            errs.append(f"{path.name}: boot JSON invalid: {e}")
    return errs


def main() -> int:
    all_errs: list[str] = []
    for p in PATHS:
        errs = check(p)
        all_errs.extend(errs)
        if not errs:
            print(f"[PASS] {p}")
        else:
            for e in errs:
                print(f"[FAIL] {e}")
    # generator template
    gen = Path(r"I:\E Drive\lygo-protocol-stack\tools\build_public_music_stream.py")
    gt = gen.read_text(encoding="utf-8")
    for s in ("btn-radio", "toggleRadio", "shuffleBag", "repeatOne"):
        if s not in gt:
            all_errs.append(f"generator missing {s}")
            print(f"[FAIL] generator missing {s}")
    if not any("generator missing" in e for e in all_errs):
        print(f"[PASS] {gen.name} has radio/shuffle template")
    if all_errs:
        print(f"\n{len(all_errs)} failure(s)")
        return 1
    print("\nALL PLAYER FEATURES VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
