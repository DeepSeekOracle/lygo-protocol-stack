#!/usr/bin/env python3
"""
Scan ONLY Excavationpro / own-created music roots.
Exclude iPod, iTunes, games, system, third-party libraries.
Compare to vault by SHA-256; report gaps; optional --merge into vault.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")

AUDIO_EXT = {".mp3", ".wav", ".flac", ".m4a", ".aiff", ".aif", ".ogg", ".aac", ".wma", ".opus", ".m4b"}

# Explicit own-music roots (never IPOD)
OWN_ROOTS = [
    Path(r"J:\ALL SOUND FILES\. KICK STREAM FOLDER"),
    Path(r"J:\ALL SOUND FILES\2026 NEW MUSIC"),
    Path(r"J:\Music 2024"),
    Path(r"J:\FINISHED BEAT STARS MUSIC"),
    Path(r"J:\STREAM STUFF"),
    Path(r"J:\FULL ADUIO BOOKS"),  # Haven books (your narration)
    Path(r"J:\LIGHTFATHER"),
    Path(r"I:\Actors"),
    Path(r"I:\Distrokid music restore ALL MUSIC"),
    Path(r"I:\GLITCH BEATS VOL 1"),
    Path(r"I:\FeelMyPain"),
    Path(r"I:\Nightfall Therapist"),
    Path(r"I:\One Day at a Time"),
    Path(r"I:\Painless"),
    Path(r"I:\Perception Codex"),
    Path(r"I:\Quantum Tears"),
    Path(r"I:\Screams in the Void"),
    Path(r"I:\So What"),
    Path(r"I:\SOUL SPIKE STACCATO"),
    Path(r"I:\Street Wise"),
    Path(r"I:\Subsonic Whisper"),
    Path(r"I:\Trance Overdose"),
    Path(r"I:\Twighlight World"),
    Path(r"I:\Waking up"),
    Path(r"I:\Whiskey Secrets"),
    Path(r"I:\White Heat"),
    Path(r"I:\Sandstorm"),
    Path(r"I:\Robot Reboot"),
    Path(r"I:\Mutation"),
    Path(r"I:\Energy"),
    Path(r"I:\Prison Systems"),
    Path(r"I:\OUTROS CLIPS"),
    Path(r"I:\1DESKTOP\AI music"),
    Path(r"I:\Future"),
]

# Dir names / path fragments to prune (not own masters)
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
    "ipod",
    "itunes",
    "amazon music",
    "google play music",
    "musicbee",
    "browser_profile",
    "yandex_cdp_profile",
    # games / non-music tooling under sound trees
    "palworldcmd",
    "mine craft",
    "minecraft",
    "deepseek-r1-main",
    "hd movie maker",
    "ea desktop",
    "processmonitor",
    "public_stream",
    "music_vault",
    "cas",
}

SKIP_PATH_SUBSTR = (
    "\\ipod\\",
    "\\itunes\\",
    "\\steam\\",
    "\\node_modules\\",
    "\\windows\\",
    "\\$recycle",
    "\\program files",
    "\\music_vault\\",
    "\\public_stream\\",
    "\\deepseek-r1",
    "\\palworld",
    "\\mine craft\\",
)

ISRC_RE = re.compile(r"(?i)(?:QZ[A-Z0-9]{10}|QM42K\d{7}|QT[A-Z0-9]{10})")


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_vault_hashes() -> set[str]:
    for p in (
        VAULT / "manifest" / "vault_index.json",
        CAT / "music_vault_index_full.json",
    ):
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        hs = {o.get("sha256") for o in (data.get("objects") or []) if o.get("sha256")}
        if hs:
            print(f"[vault] {len(hs)} hashes from {p}", flush=True)
            return hs
    return set()


def should_skip_dir(dirpath: str, name: str) -> bool:
    low = name.lower()
    if low in SKIP_DIR_NAMES or low.startswith("$"):
        return True
    pl = dirpath.lower().replace("/", "\\")
    if any(s in pl for s in SKIP_PATH_SUBSTR):
        return True
    return False


def iter_own_audio(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            print(f"[miss] {root}", flush=True)
            continue
        low_root = str(root).lower()
        if "ipod" in low_root or "itunes" in low_root:
            print(f"[block] refusing third-party root {root}", flush=True)
            continue
        print(f"[scan] {root}", flush=True)
        n_before = len(files)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not should_skip_dir(dirpath, d)]
            low = dirpath.lower().replace("/", "\\")
            if any(s in low for s in SKIP_PATH_SUBSTR):
                dirnames[:] = []
                continue
            for fn in filenames:
                if Path(fn).suffix.lower() in AUDIO_EXT:
                    files.append(Path(dirpath) / fn)
        print(f"  +{len(files) - n_before} audio", flush=True)
    return files


def main() -> int:
    do_hash = "--hash" in sys.argv or "--merge" in sys.argv
    do_merge = "--merge" in sys.argv
    max_new = 0
    for a in sys.argv:
        if a.startswith("--max="):
            max_new = int(a.split("=", 1)[1])

    vault_hs = load_vault_hashes()
    files = iter_own_audio(OWN_ROOTS)
    print(f"\n[own] total audio files found: {len(files)}", flush=True)

    by_root: dict[str, dict] = defaultdict(lambda: {"n": 0, "bytes": 0})
    for f in files:
        try:
            sz = f.stat().st_size
        except OSError:
            continue
        # top under drive
        parts = f.parts
        key = str(f.parents[min(2, len(f.parents) - 1)]) if len(f.parts) > 2 else str(f.parent)
        # better: first 3 path parts
        key = "\\".join(parts[:3]) if len(parts) >= 3 else str(f.parent)
        by_root[key]["n"] += 1
        by_root[key]["bytes"] += sz

    print("\n=== OWN MUSIC BY PATH PREFIX ===", flush=True)
    for k, s in sorted(by_root.items(), key=lambda x: -x[1]["bytes"])[:50]:
        print(f"  {s['n']:6d}  {s['bytes']/1e9:7.2f} GB  {k}", flush=True)

    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "own_music_only_no_ipod",
        "vault_hashes": len(vault_hs),
        "files_found": len(files),
        "by_prefix": {
            k: {"n": v["n"], "bytes": v["bytes"], "gb": round(v["bytes"] / 1e9, 3)}
            for k, v in sorted(by_root.items(), key=lambda x: -x[1]["bytes"])
        },
        "roots_scanned": [str(r) for r in OWN_ROOTS if r.exists()],
    }

    if not do_hash:
        out = CAT / "own_music_inventory.json"
        CAT.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nwrote inventory (no hash) {out}", flush=True)
        print("Re-run with --hash to find vault gaps, or --merge to add missing.", flush=True)
        return 0

    # Hash and find missing
    missing: list[dict] = []
    known_hits = 0
    errors = 0
    total = len(files)
    print(f"\n[hash] {total} files…", flush=True)
    for i, path in enumerate(files, 1):
        try:
            st = path.stat()
            digest = sha256_file(path)
        except OSError as e:
            errors += 1
            if errors <= 5:
                print(f"[err] {path}: {e}", flush=True)
            continue
        if digest in vault_hs:
            known_hits += 1
        else:
            missing.append(
                {
                    "sha256": digest,
                    "path": str(path),
                    "size": st.st_size,
                    "name": path.name,
                    "isrcs": [m.group(0).upper() for m in ISRC_RE.finditer(path.name.replace("-", "").replace("_", "").replace(" ", ""))],
                }
            )
            vault_hs.add(digest)  # de-dupe within this scan
        if i % 200 == 0 or i == total:
            print(
                f"  {i}/{total} known={known_hits} new={len(missing)} err={errors}",
                flush=True,
            )
        if max_new and len(missing) >= max_new:
            print(f"[cap] --max={max_new} reached", flush=True)
            break

    report["known_in_vault"] = known_hits
    report["new_unique"] = len(missing)
    report["new_unique_bytes"] = sum(m["size"] for m in missing)
    report["new_unique_gb"] = round(report["new_unique_bytes"] / 1e9, 3)
    report["errors"] = errors
    report["missing_sample"] = missing[:40]
    report["missing_by_folder"] = {}
    fb: dict[str, dict] = defaultdict(lambda: {"n": 0, "bytes": 0})
    for m in missing:
        folder = str(Path(m["path"]).parent)
        # collapse to first meaningful segment under ALL SOUND / Actors
        p = m["path"]
        if "2026 NEW MUSIC" in p:
            key = "J:\\ALL SOUND FILES\\2026 NEW MUSIC\\…"
        elif ". KICK STREAM FOLDER" in p:
            key = "J:\\ALL SOUND FILES\\. KICK STREAM FOLDER\\…"
        elif "Music 2024" in p:
            key = "J:\\Music 2024\\…"
        elif "Actors" in p:
            key = "I:\\Actors\\…"
        else:
            key = str(Path(p).parts[:3]) if len(Path(p).parts) >= 3 else folder
        fb[key]["n"] += 1
        fb[key]["bytes"] += m["size"]
    report["missing_by_folder"] = {
        k: {"n": v["n"], "gb": round(v["bytes"] / 1e9, 3)}
        for k, v in sorted(fb.items(), key=lambda x: -x[1]["bytes"])
    }

    out = CAT / "own_music_gap_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    miss_txt = CAT / "own_music_MISSING_paths.txt"
    miss_txt.write_text(
        "\n".join(m["path"] for m in missing),
        encoding="utf-8",
    )
    print(f"\n=== OWN MUSIC GAP ===", flush=True)
    print(f"  in vault already (by hash): {known_hits}", flush=True)
    print(f"  NEW unique masters:         {len(missing)}  ({report['new_unique_gb']} GB)", flush=True)
    print(f"  wrote {out}", flush=True)
    print(f"  wrote {miss_txt}", flush=True)
    print("\n  missing by area:", flush=True)
    for k, v in list(report["missing_by_folder"].items())[:20]:
        print(f"    {v['n']:5d}  {v['gb']:6.2f} GB  {k}", flush=True)

    if do_merge and missing:
        # Call vault builder roots for the big missing trees
        print("\n[merge] invoking vault scan on broad own-music roots…", flush=True)
        import subprocess

        roots = [
            r"J:\ALL SOUND FILES\. KICK STREAM FOLDER",
            r"J:\ALL SOUND FILES\2026 NEW MUSIC",
            r"J:\Music 2024",
            r"J:\FINISHED BEAT STARS MUSIC",
            r"J:\STREAM STUFF",
            r"J:\FULL ADUIO BOOKS",
            r"J:\LIGHTFATHER",
            r"I:\Actors",
        ]
        cmd = [sys.executable, str(STACK / "tools" / "build_music_cas_vault.py"), "--scan"]
        for r in roots:
            cmd.extend(["--root", r])
        print(" ", " ".join(cmd[:6]), f"+ {len(roots)} roots", flush=True)
        r = subprocess.run(cmd, cwd=str(STACK))
        return r.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
