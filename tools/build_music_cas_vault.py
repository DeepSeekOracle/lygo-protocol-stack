#!/usr/bin/env python3
"""
Sovereign Music CAS Vault — Excavationpro

Hash real masters (names don't need to match commercial releases).
Build content-addressed vault + Merkle manifest for lattice retrieval.
Optional hardlink/copy ingest into I:\\E Drive\\MUSIC_VAULT\\cas\\

Usage:
  python tools/build_music_cas_vault.py --scan
  python tools/build_music_cas_vault.py --scan --ingest
  python tools/build_music_cas_vault.py --hub
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
EXCAV = STACK.parent / "Excavationpro"
DOCS = STACK / "docs"

DEFAULT_VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
DEFAULT_ROOTS = [
    # Full Excavationpro production trees (own music only — never IPOD/iTunes)
    Path(r"J:\ALL SOUND FILES\. KICK STREAM FOLDER"),
    Path(r"J:\ALL SOUND FILES\2026 NEW MUSIC"),
    Path(r"I:\Actors"),
    # Haven / Eternal Haven book narration + Lightfather seals audio
    Path(r"J:\FULL ADUIO BOOKS"),
    Path(r"J:\LIGHTFATHER"),
    # Additional own libraries
    Path(r"J:\Music 2024"),
    Path(r"J:\FINISHED BEAT STARS MUSIC"),
    Path(r"J:\STREAM STUFF"),
    Path(r"I:\Distrokid music restore ALL MUSIC"),
    # I:\ album project folders (singles/masters outside Actors)
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

AUDIO_EXT = {".mp3", ".wav", ".flac", ".m4a", ".aiff", ".aif", ".ogg", ".aac", ".wma", ".opus", ".m4b"}
SKIP_DIR = (
    "apache-openoffice",
    "\\windows\\",
    "\\$recycle",
    "\\node_modules",
    "\\.git\\",
    "\\steam\\",
    "\\program files",
    # Third-party / copyright libraries — never ingest
    "\\ipod\\",
    "\\itunes\\",
    "\\amazon music\\",
    "\\google play music\\",
)
ISRC_IN_NAME = re.compile(
    r"(?i)(?:QZ[A-Z0-9]{10}|QM42K\d{7}|QT[A-Z0-9]{10})"
)
ISRC_DASHED = re.compile(r"(?i)QZ-?[A-Z0-9]{3}-?\d{2}-?\d{5}")

SIGNATURE = "Δ9Φ963-SOVEREIGN-MUSIC-VAULT-v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm_title(t: str) -> str:
    t = (t or "").lower().strip()
    t = re.sub(r"\(feat\.?[^)]*\)", "", t)
    t = re.sub(r"\b(feat|ft|featuring)\.?\s*", " ", t)
    t = re.sub(r"\bjustin helmer\b", " ", t)
    t = re.sub(r"\b(hd|mastered|master|explicit|lyrics)\b", " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_isrcs(fn: str) -> list[str]:
    compact = fn.replace("-", "").replace("_", "").replace(" ", "")
    found = [m.group(0).upper() for m in ISRC_IN_NAME.finditer(compact)]
    for m in ISRC_DASHED.finditer(fn):
        found.append(re.sub(r"[^A-Za-z0-9]", "", m.group(0)).upper())
    out, seen = [], set()
    for x in found:
        if len(x) == 12 and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def title_from_fn(fn: str) -> str:
    stem = Path(fn).stem
    stem = re.sub(r"(?i)^hd[_ ]+", "", stem)
    for code in extract_isrcs(fn):
        stem = re.sub(re.escape(code), "", stem, flags=re.I)
        if len(code) == 12:
            dashed = f"{code[0:2]}-{code[2:5]}-{code[5:7]}-{code[7:12]}"
            stem = re.sub(re.escape(dashed), "", stem, flags=re.I)
    stem = re.sub(r"(?i)\b(feat|ft)\.?\s*justin\s*helmer\b", "", stem)
    stem = re.sub(r"[_\-]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip(" -_.")
    return stem


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def cas_relpath(digest: str, ext: str) -> Path:
    ext = ext.lower() if ext.startswith(".") else f".{ext.lower()}"
    return Path(digest[:2]) / f"{digest}{ext}"


def _is_blocked_root(root: Path) -> bool:
    """Refuse iPod / third-party libraries — own music + Haven only."""
    low = str(root).lower().replace("/", "\\")
    blocked = ("\\ipod", "ipod\\", "\\itunes", "\\amazon music", "\\google play music")
    return any(b in low for b in blocked) or low.rstrip("\\").endswith("ipod")


def iter_audio(roots: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if _is_blocked_root(root):
            print(f"[skip] blocked third-party root (own music only): {root}", flush=True)
            continue
        if not root.exists():
            print(f"[warn] missing root {root}", flush=True)
            continue
        print(f"[scan] {root}", flush=True)
        for dirpath, dirnames, filenames in os.walk(root):
            low = dirpath.lower()
            if any(s in low for s in SKIP_DIR):
                dirnames[:] = []
                continue
            dirnames[:] = [
                d
                for d in dirnames
                if "apache-openoffice" not in d.lower()
                and d.lower() not in ("ipod", "itunes")
            ]
            for fn in filenames:
                if Path(fn).suffix.lower() in AUDIO_EXT:
                    files.append(Path(dirpath) / fn)
    return files


def load_commercial_maps() -> tuple[dict[str, str], dict[str, dict]]:
    """isrc_compact -> commercial title; norm_title -> restore row."""
    isrc_map: dict[str, str] = {}
    title_map: dict[str, dict] = {}
    vault_csv = CAT / "excavationpro_vault_isrcs.csv"
    if vault_csv.exists():
        for i, line in enumerate(vault_csv.read_text(encoding="utf-8", errors="replace").splitlines()):
            if i == 0 or not line.strip():
                continue
            # "title",isrc,source
            m = re.match(r'^"(.*)",([A-Z0-9]+),', line)
            if m:
                isrc_map[m.group(2).upper()] = m.group(1).replace('""', '"')
    restore = CAT / "All_music_Restore.txt"
    # also ledger
    led = CAT / "excavationpro_music_ledger.json"
    if led.exists():
        data = json.loads(led.read_text(encoding="utf-8"))
        for row in (data.get("restore_matched") or []) + (data.get("restore_missing") or []):
            t = row.get("title") or ""
            k = norm_title(t)
            if k:
                title_map[k] = row
            isrc = (row.get("isrc") or "").upper().replace("-", "")
            if isrc:
                isrc_map[isrc] = t
    # streaming albums tracks
    stream = CAT / "streaming_discography_full.json"
    if stream.exists():
        data = json.loads(stream.read_text(encoding="utf-8"))
        for alb in data.get("albums") or []:
            for tr in alb.get("tracks") or []:
                t = tr.get("title") or ""
                k = norm_title(t)
                if k and k not in title_map:
                    title_map[k] = {"title": t, "album": alb.get("title"), "source": "streaming"}
    return isrc_map, title_map


def merkle_root(hex_hashes: list[str]) -> str:
    """Simple binary Merkle over sorted leaf hex digests."""
    if not hex_hashes:
        return hashlib.sha256(b"").hexdigest()
    level = [bytes.fromhex(h) if len(h) == 64 else hashlib.sha256(h.encode()).digest() for h in sorted(hex_hashes)]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else a
            nxt.append(hashlib.sha256(a + b).digest())
        level = nxt
    return level[0].hex()


def ingest_to_cas(src: Path, digest: str, vault_root: Path, mode: str = "hardlink") -> str | None:
    """Place file in CAS. Returns relative cas path or None."""
    rel = cas_relpath(digest, src.suffix)
    dest = vault_root / "cas" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return str(rel).replace("\\", "/")
    try:
        if mode == "hardlink":
            try:
                os.link(src, dest)
                return str(rel).replace("\\", "/")
            except OSError:
                # cross-device → copy
                shutil.copy2(src, dest)
                return str(rel).replace("\\", "/")
        if mode == "copy":
            shutil.copy2(src, dest)
            return str(rel).replace("\\", "/")
        if mode == "symlink":
            try:
                dest.symlink_to(src)
                return str(rel).replace("\\", "/")
            except OSError:
                shutil.copy2(src, dest)
                return str(rel).replace("\\", "/")
    except Exception as e:
        print(f"[ingest fail] {src}: {e}", flush=True)
        return None
    return None


def scan_and_build(
    roots: list[Path],
    vault_root: Path,
    do_ingest: bool = False,
    ingest_mode: str = "hardlink",
    max_files: int = 0,
    merge_existing: bool = True,
) -> dict[str, Any]:
    isrc_map, title_map = load_commercial_maps()
    files = iter_audio(roots)
    if max_files and max_files > 0:
        files = files[:max_files]
    print(f"[scan] audio files: {len(files)}", flush=True)

    by_hash: dict[str, dict[str, Any]] = {}
    prior_roots: list[str] = []
    if merge_existing:
        for prior in (
            vault_root / "manifest" / "vault_index.json",
            CAT / "music_vault_index_full.json",
        ):
            if prior.exists():
                try:
                    old = json.loads(prior.read_text(encoding="utf-8"))
                    for o in old.get("objects") or []:
                        d = o.get("sha256")
                        if d:
                            by_hash[d] = o
                    prior_roots = list(old.get("scan_roots") or [])
                    print(f"[merge] loaded {len(by_hash)} existing from {prior}", flush=True)
                    break
                except Exception as e:
                    print(f"[merge] skip {prior}: {e}", flush=True)

    errors = 0
    new_count = 0

    for i, path in enumerate(files):
        try:
            st = path.stat()
            digest = sha256_file(path)
            fn = path.name
            isrcs = extract_isrcs(fn)
            guess = title_from_fn(fn)
            commercial = None
            for code in isrcs:
                if code in isrc_map:
                    commercial = isrc_map[code]
                    break
            if not commercial:
                k = norm_title(guess)
                if k in title_map:
                    commercial = title_map[k].get("title")
            aliases = list(dict.fromkeys([a for a in [guess, commercial] if a]))

            if digest in by_hash:
                row = by_hash[digest]
                paths = list(row.get("paths") or [])
                if str(path) not in paths:
                    paths.append(str(path))
                row["paths"] = paths
                fns = list(row.get("filenames") or [])
                if fn not in fns:
                    fns.append(fn)
                row["filenames"] = fns
                al = list(row.get("aliases") or [])
                for a in aliases:
                    if a not in al:
                        al.append(a)
                row["aliases"] = al
                ir = list(row.get("isrcs") or [])
                for c in isrcs:
                    if c not in ir:
                        ir.append(c)
                row["isrcs"] = ir
                if commercial and not row.get("commercial_title"):
                    row["commercial_title"] = commercial
            else:
                cas_path = None
                if do_ingest:
                    cas_path = ingest_to_cas(path, digest, vault_root, mode=ingest_mode)
                by_hash[digest] = {
                    "sha256": digest,
                    "size": st.st_size,
                    "ext": path.suffix.lower(),
                    "title_guess": guess,
                    "commercial_title": commercial,
                    "aliases": aliases,
                    "isrcs": isrcs,
                    "paths": [str(path)],
                    "filenames": [fn],
                    "cas_path": cas_path,
                    "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                }
                new_count += 1
        except Exception as e:
            errors += 1
            print(f"[err] {path}: {e}", flush=True)
        if (i + 1) % 50 == 0 or i == 0:
            print(f"  hashed {i+1}/{len(files)} unique={len(by_hash)} new={new_count}", flush=True)

    objects = sorted(
        by_hash.values(),
        key=lambda r: (r.get("commercial_title") or r.get("title_guess") or "").lower(),
    )
    leaves = [o["sha256"] for o in objects]
    root = merkle_root(leaves)
    all_bytes = sum(int(o.get("size") or 0) for o in objects)
    scan_roots = list(dict.fromkeys(prior_roots + [str(r) for r in roots]))

    manifest = {
        "signature": SIGNATURE,
        "artist": "Excavationpro",
        "steward": "Justin Helmer / Lightfather",
        "generated_at": utc_now(),
        "vault_root": str(vault_root),
        "scan_roots": scan_roots,
        "stats": {
            "files_seen": len(files),
            "files_seen_this_scan": len(files),
            "unique_objects": len(objects),
            "new_objects_this_scan": new_count,
            "total_bytes": all_bytes,
            "total_gb": round(all_bytes / (1024**3), 3),
            "with_isrc": sum(1 for o in objects if o.get("isrcs")),
            "with_commercial_title": sum(1 for o in objects if o.get("commercial_title")),
            "ingested_to_cas": sum(1 for o in objects if o.get("cas_path")),
            "errors": errors,
        },
        "merkle_root": root,
        "retrieval": {
            "by_hash": "cas/{first2}/{sha256}{ext}",
            "local_gateway": "http://127.0.0.1:8765/sha256/{sha256}",
            "note": "Platform titles may differ from filenames; hash is the identity.",
        },
        "lattice": {
            "role": "sovereign-music-vault",
            "hub_page": "excavationpro-sovereign-music-hub.html",
            "manifest_paths": [
                "data/music_catalog/music_vault_manifest.json",
                "Excavationpro/data/music_vault_manifest.json",
            ],
        },
        "objects": objects,
    }
    return manifest


def write_manifest(manifest: dict[str, Any], vault_root: Path) -> None:
    vault_root.mkdir(parents=True, exist_ok=True)
    (vault_root / "manifest").mkdir(exist_ok=True)
    (vault_root / "cas").mkdir(exist_ok=True)

    full_path = vault_root / "manifest" / "vault_index.json"
    full_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (vault_root / "manifest" / "merkle_root.txt").write_text(
        manifest["merkle_root"] + "\n", encoding="utf-8"
    )

    # slim public index (no full path list spam — keep first path only)
    public_objects = []
    for o in manifest["objects"]:
        public_objects.append(
            {
                "sha256": o["sha256"],
                "size": o["size"],
                "ext": o["ext"],
                "title": o.get("commercial_title") or o.get("title_guess") or o["filenames"][0],
                "aliases": o.get("aliases") or [],
                "isrcs": o.get("isrcs") or [],
                "cas_path": o.get("cas_path"),
                "sources_count": len(o.get("paths") or []),
            }
        )
    public = {
        "signature": SIGNATURE,
        "artist": "Excavationpro",
        "generated_at": manifest["generated_at"],
        "merkle_root": manifest["merkle_root"],
        "stats": manifest["stats"],
        "retrieval": manifest["retrieval"],
        "youtube_music": "https://music.youtube.com/@Excavationpro",
        "spotify": "https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S",
        "deezer": "https://www.deezer.com/artist/146004952",
        "catalog_page": "https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html",
        "objects": public_objects,
    }

    CAT.mkdir(parents=True, exist_ok=True)
    (CAT / "music_vault_manifest.json").write_text(
        json.dumps(public, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (CAT / "music_vault_merkle_root.txt").write_text(manifest["merkle_root"] + "\n", encoding="utf-8")
    # full private-ish copy stays under vault + CAT for rebuild
    (CAT / "music_vault_index_full.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if EXCAV.exists():
        (EXCAV / "data").mkdir(exist_ok=True)
        (EXCAV / "data" / "music_vault_manifest.json").write_text(
            json.dumps(public, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(f"wrote {full_path}", flush=True)
    print(f"merkle {manifest['merkle_root']}", flush=True)
    print(f"stats {manifest['stats']}", flush=True)


def write_hub_html(public_manifest_path: Path, out_html: Path) -> None:
    data = public_manifest_path.read_text(encoding="utf-8")
    # escape for script
    data_js = data.replace("</", "<\\/")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Excavationpro Sovereign Music Hub — Independent Vault</title>
<meta name="description" content="Independent Excavationpro music vault: content-addressed masters, SHA-256 identity, Merkle lattice manifest. Platform-independent discovery and retrieval.">
<meta name="keywords" content="Excavationpro, sovereign music, independent artist, music vault, CAS, SHA-256, LYGO lattice, DistroKid alternative">
<link rel="canonical" href="https://deepseekoracle.github.io/Excavationpro/excavationpro-sovereign-music-hub.html">
<meta property="og:title" content="Excavationpro Sovereign Music Hub">
<meta property="og:description" content="Your music, hashed and mapped — not owned by a distributor.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://deepseekoracle.github.io/Excavationpro/excavationpro-sovereign-music-hub.html">
<meta name="twitter:card" content="summary_large_image">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{ --void:#07070f; --panel:#12121f; --cyan:#00f0ff; --mag:#9b5cff; --gold:#d4af37; --ok:#3dd68c; --text:#e8e8f0; --muted:#9a9ab0; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Inter,system-ui,sans-serif; background:radial-gradient(1000px 500px at 20% -10%,#1a1040 0%,var(--void) 55%); color:var(--text); min-height:100vh; }}
a {{ color:var(--cyan); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
header {{ max-width:1100px; margin:0 auto; padding:28px 20px 12px; border-bottom:1px solid rgba(0,240,255,.15); }}
h1 {{ font-family:Cinzel,serif; color:var(--gold); margin:0 0 8px; font-size:1.7rem; }}
.sub {{ color:var(--muted); line-height:1.55; max-width:70ch; }}
.nav {{ display:flex; flex-wrap:wrap; gap:12px 16px; margin-top:14px; font-size:.9rem; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; max-width:1100px; margin:20px auto; padding:0 20px; }}
.card {{ background:rgba(18,18,31,.9); border:1px solid rgba(155,92,255,.3); border-radius:12px; padding:14px 16px; }}
.card b {{ display:block; font-size:1.45rem; color:var(--cyan); }}
.card span {{ font-size:.78rem; color:var(--muted); }}
.panel {{ max-width:1100px; margin:0 auto 28px; padding:0 20px; }}
.panel h2 {{ font-family:Cinzel,serif; color:var(--mag); font-size:1.15rem; }}
.ledger {{ font-family:ui-monospace,Consolas,monospace; font-size:.78rem; word-break:break-all; background:#0a0a14; border:1px solid rgba(212,175,55,.3); color:var(--gold); padding:12px; border-radius:8px; }}
input {{ width:100%; background:#0e0e18; border:1px solid rgba(0,240,255,.3); color:var(--text); border-radius:8px; padding:12px; margin:10px 0 14px; }}
table {{ width:100%; border-collapse:collapse; font-size:.84rem; }}
th,td {{ text-align:left; padding:8px 10px; border-bottom:1px solid rgba(255,255,255,.06); vertical-align:top; }}
th {{ color:var(--muted); position:sticky; top:0; background:#0e0e18; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:.7rem; background:rgba(61,214,140,.15); color:var(--ok); }}
.hash {{ font-family:ui-monospace,Consolas,monospace; font-size:.72rem; color:var(--muted); word-break:break-all; }}
.note {{ background:rgba(0,240,255,.06); border-left:3px solid var(--cyan); padding:12px 14px; border-radius:0 8px 8px 0; color:var(--muted); font-size:.9rem; line-height:1.5; }}
footer {{ max-width:1100px; margin:0 auto; padding:20px; color:var(--muted); font-size:.8rem; }}
</style>
</head>
<body>
<header>
  <h1>Sovereign Music Hub</h1>
  <p class="sub">Excavationpro — independent of DistroKid, Spotify, and YouTube Music.
  Every master is identified by <b style="color:var(--gold)">SHA-256</b>, not a platform ID.
  If commercial stores delist a song, the vault still knows the bytes.</p>
  <div class="nav">
    <a href="excavationpro-music-catalog.html">Public Catalog</a>
    <a href="eternalhaven.html">Eternal Haven</a>
    <a href="https://music.youtube.com/@Excavationpro" target="_blank" rel="noopener">YouTube Music</a>
    <a href="https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S" target="_blank" rel="noopener">Spotify</a>
    <a href="https://www.deezer.com/artist/146004952" target="_blank" rel="noopener">Deezer</a>
    <a href="https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/SOVEREIGN_MUSIC_VAULT.md" target="_blank" rel="noopener">Vault Spec</a>
  </div>
</header>

<section class="stats" id="stats"></section>

<div class="panel">
  <h2>Lattice Merkle root</h2>
  <div class="ledger" id="merkle">…</div>
  <p class="sub" style="margin-top:8px">This root is the vault’s fingerprint on the LYGO lattice. Recompute after every ingest.</p>
</div>

<div class="panel">
  <h2>How retrieval works</h2>
  <div class="note">
    <b>1. Discover</b> — search this page (titles, ISRCs, hashes).<br>
    <b>2. Identify</b> — copy the SHA-256 (true identity of the master).<br>
    <b>3. Retrieve</b> — from the steward vault <code>MUSIC_VAULT/cas/…</code> or local gateway
    <code>http://127.0.0.1:8765/sha256/&lt;hash&gt;</code> when the steward is online.<br>
    <b>4. Verify</b> — re-hash the file; it must match. Platforms can rename or vanish; the hash cannot lie.
  </div>
</div>

<div class="panel">
  <h2>Vault objects</h2>
  <input id="q" type="search" placeholder="Search title, ISRC, hash…" autocomplete="off">
  <div style="overflow:auto; max-height:70vh;">
    <table>
      <thead><tr><th>Title</th><th>ISRC</th><th>Size</th><th>SHA-256</th></tr></thead>
      <tbody id="tb"></tbody>
    </table>
  </div>
</div>

<footer>
  Δ9Φ963 Sovereign Music Vault · Not a distributor · Not DRM · Steward: Justin Helmer / Excavationpro / Lightfather
</footer>

<script id="vault-data" type="application/json">{data_js}</script>
<script>
const DATA = JSON.parse(document.getElementById('vault-data').textContent);
function esc(s) {{ return String(s||'').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function fmt(n) {{
  if (n > 1e9) return (n/1e9).toFixed(2)+' GB';
  if (n > 1e6) return (n/1e6).toFixed(1)+' MB';
  return (n/1e3).toFixed(0)+' KB';
}}
const s = DATA.stats || {{}};
document.getElementById('stats').innerHTML = [
  ['Unique masters', s.unique_objects||0],
  ['Source files', s.files_seen||0],
  ['Vault size', (s.total_gb||0)+' GB'],
  ['With ISRC', s.with_isrc||0],
  ['Commercial title', s.with_commercial_title||0],
  ['CAS ingested', s.ingested_to_cas||0],
].map(([l,v]) => `<div class="card"><b>${{v}}</b><span>${{l}}</span></div>`).join('');
document.getElementById('merkle').textContent = DATA.merkle_root || '';

function render() {{
  const q = (document.getElementById('q').value||'').toLowerCase().trim();
  let rows = DATA.objects || [];
  if (q) {{
    rows = rows.filter(o => [o.title, ...(o.aliases||[]), ...(o.isrcs||[]), o.sha256].join(' ').toLowerCase().includes(q));
  }}
  rows = rows.slice().sort((a,b) => (a.title||'').localeCompare(b.title||''));
  document.getElementById('tb').innerHTML = rows.map(o => `
    <tr>
      <td>${{esc(o.title)}}</td>
      <td>${{(o.isrcs||[]).map(i=>`<span class="badge">${{esc(i)}}</span>`).join(' ') || '—'}}</td>
      <td>${{fmt(o.size||0)}}</td>
      <td class="hash" title="Copy this hash to retrieve">${{esc(o.sha256)}}</td>
    </tr>`).join('') || '<tr><td colspan="4">No matches</td></tr>';
}}
document.getElementById('q').addEventListener('input', render);
render();
</script>
</body>
</html>
"""
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    print(f"wrote hub {out_html}", flush=True)


def write_gateway_script(vault_root: Path) -> None:
    """Small local HTTP gateway — written once."""
    gw = STACK / "tools" / "music_vault_gateway.py"
    if gw.exists():
        return
    # always write/update
    pass


def main() -> int:
    ap = argparse.ArgumentParser(description="Sovereign Music CAS Vault")
    ap.add_argument("--scan", action="store_true", help="Hash scan masters")
    ap.add_argument("--ingest", action="store_true", help="Hardlink/copy into CAS while scanning")
    ap.add_argument("--ingest-mode", default="hardlink", choices=["hardlink", "copy", "symlink"])
    ap.add_argument("--hub", action="store_true", help="Rebuild public hub HTML from existing manifest")
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--root", action="append", type=Path, help="Extra/override scan root (repeatable)")
    ap.add_argument("--max-files", type=int, default=0, help="Cap for testing")
    ap.add_argument("--no-merge", action="store_true", help="Do not merge prior vault objects")
    args = ap.parse_args()

    if not args.scan and not args.hub:
        args.scan = True
        args.hub = True

    roots = args.root if args.root else DEFAULT_ROOTS

    if args.scan:
        manifest = scan_and_build(
            roots=roots,
            vault_root=args.vault,
            do_ingest=args.ingest,
            ingest_mode=args.ingest_mode,
            max_files=args.max_files,
            merge_existing=not args.no_merge,
        )
        write_manifest(manifest, args.vault)
        # egg-ready core (stats + merkle only, small)
        egg = {
            "signature": SIGNATURE,
            "egg_id": "excavationpro-music-vault-v1",
            "merkle_root": manifest["merkle_root"],
            "stats": manifest["stats"],
            "generated_at": manifest["generated_at"],
            "hub": "excavationpro-sovereign-music-hub.html",
        }
        (CAT / "egg_payload" / "music_vault_egg_core.json").parent.mkdir(parents=True, exist_ok=True)
        (CAT / "egg_payload" / "music_vault_egg_core.json").write_text(
            json.dumps(egg, indent=2), encoding="utf-8"
        )

    if args.hub or args.scan:
        pub = CAT / "music_vault_manifest.json"
        if not pub.exists():
            print("[hub] no manifest yet — run --scan first", flush=True)
            return 1
        write_hub_html(pub, EXCAV / "excavationpro-sovereign-music-hub.html")
        write_hub_html(pub, DOCS / "excavationpro-sovereign-music-hub.html")
        # also store vault copy of hub
        args.vault.mkdir(parents=True, exist_ok=True)
        write_hub_html(pub, args.vault / "sovereign-music-hub.html")

    # always ensure gateway tool exists
    write_gateway_file()
    return 0


def write_gateway_file() -> None:
    path = STACK / "tools" / "music_vault_gateway.py"
    path.write_text(
        '''#!/usr/bin/env python3
"""Local-only gateway to serve CAS vault objects by SHA-256. Default bind 127.0.0.1."""
from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

DEFAULT_VAULT = Path(r"I:\\E Drive\\MUSIC_VAULT")
STACK_MANIFEST = Path(__file__).resolve().parents[1] / "data" / "music_catalog" / "music_vault_manifest.json"


def load_index(vault: Path) -> dict[str, dict]:
    # prefer full index for paths
    full = vault / "manifest" / "vault_index.json"
    pub = STACK_MANIFEST
    path = full if full.exists() else pub
    data = json.loads(path.read_text(encoding="utf-8"))
    by = {}
    for o in data.get("objects") or []:
        by[o["sha256"]] = o
    return by, data


class Handler(BaseHTTPRequestHandler):
    vault: Path = DEFAULT_VAULT
    by_hash: dict = {}
    manifest: dict = {}

    def log_message(self, fmt, *args):
        print("[gw]", fmt % args)

    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])
        if path in ("/", "/index", "/manifest"):
            body = json.dumps(
                {
                    "signature": self.manifest.get("signature"),
                    "merkle_root": self.manifest.get("merkle_root"),
                    "stats": self.manifest.get("stats"),
                    "objects": len(self.by_hash),
                    "usage": "/sha256/<hex> or /cas/<rel>",
                },
                indent=2,
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path.startswith("/sha256/"):
            digest = path[len("/sha256/") :].strip().lower()
            row = self.by_hash.get(digest)
            if not row:
                self.send_error(404, "unknown hash")
                return
            # try CAS then original paths
            candidates = []
            if row.get("cas_path"):
                candidates.append(self.vault / "cas" / row["cas_path"])
            # rebuild cas path from digest
            ext = row.get("ext") or ".wav"
            candidates.append(self.vault / "cas" / digest[:2] / f"{digest}{ext}")
            for p in row.get("paths") or []:
                candidates.append(Path(p))
            for c in candidates:
                if c and Path(c).is_file():
                    return self._file(Path(c))
            self.send_error(404, "file not on this machine")
            return
        if path.startswith("/cas/"):
            rel = path[len("/cas/") :]
            fp = self.vault / "cas" / rel
            if fp.is_file():
                return self._file(fp)
            self.send_error(404, "not found")
            return
        self.send_error(404, "try / or /sha256/<hash>")

    def _file(self, fp: Path):
        data = fp.read_bytes()
        ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-SHA256", fp.name.split(".")[0] if len(fp.stem) == 64 else "")
        self.end_headers()
        self.wfile.write(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--host", default="127.0.0.1", help="Use 127.0.0.1 only unless you intentionally expose")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    by, man = load_index(args.vault)
    Handler.vault = args.vault
    Handler.by_hash = by
    Handler.manifest = man
    print(f"Sovereign vault gateway on http://{args.host}:{args.port}/  objects={len(by)}")
    print("Ctrl+C to stop. Audio is served only if CAS or original paths exist.")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
