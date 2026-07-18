#!/usr/bin/env python3
"""
Build PUBLIC listenable streams from vault masters + publish hub player.

1) Transcode WAV/masters → 160kbps MP3 under MUSIC_VAULT/public_stream/{sha256}.mp3
2) Build stream playlist JSON with public URLs
3) Optional: upload to Hugging Face dataset for free public HTTPS streaming
4) Rebuild sovereign hub with real HTML5 <audio> players

Usage:
  python tools/build_public_music_stream.py --encode
  python tools/build_public_music_stream.py --encode --limit 50
  python tools/build_public_music_stream.py --publish-hf
  python tools/build_public_music_stream.py --hub
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
EXCAV = STACK.parent / "Excavationpro"
DOCS = STACK / "docs"
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
STREAM_DIR = VAULT / "public_stream"
FFMPEG_CANDIDATES = [
    Path(r"I:\E Drive\tools\ffmpeg\ffmpeg.exe"),
    Path(r"I:\E Drive\tools\ffmpeg\bin\ffmpeg.exe"),
    Path("ffmpeg"),
]
HF_REPO_DEFAULT = "DeepSeekOracle/excavationpro-music-stream"
BITRATE = "160k"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_ffmpeg() -> str:
    for p in FFMPEG_CANDIDATES:
        if p.name == "ffmpeg":
            if shutil.which("ffmpeg"):
                return "ffmpeg"
            continue
        if p.is_file():
            return str(p)
    # search portable tree
    root = Path(r"I:\E Drive\tools\ffmpeg")
    if root.exists():
        for hit in root.rglob("ffmpeg.exe"):
            return str(hit)
    raise SystemExit("ffmpeg not found — install or place at I:\\E Drive\\tools\\ffmpeg\\ffmpeg.exe")


def load_full_index() -> dict:
    p = CAT / "music_vault_index_full.json"
    if not p.exists():
        p = VAULT / "manifest" / "vault_index.json"
    return json.loads(p.read_text(encoding="utf-8"))


def source_path(obj: dict) -> Path | None:
    for p in obj.get("paths") or []:
        pp = Path(p)
        if pp.is_file():
            return pp
    return None


def encode_one(ffmpeg: str, src: Path, dest: Path) -> tuple[bool, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        return True, "skip"
    # if source already small mp3, copy
    if src.suffix.lower() == ".mp3" and src.stat().st_size < 15_000_000:
        shutil.copy2(src, dest)
        return True, "copy-mp3"
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-b:a",
        BITRATE,
        "-ar",
        "44100",
        "-ac",
        "2",
        "-map_metadata",
        "-1",
        str(dest),
    ]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if r.returncode != 0 or not dest.exists():
            return False, (r.stderr or r.stdout or "encode fail")[-400:]
        return True, "encoded"
    except Exception as e:
        return False, str(e)


def encode_streams(limit: int = 0, workers: int = 2) -> dict:
    ffmpeg = find_ffmpeg()
    print(f"[ffmpeg] {ffmpeg}", flush=True)
    idx = load_full_index()
    objects = idx.get("objects") or []
    STREAM_DIR.mkdir(parents=True, exist_ok=True)

    jobs = []
    for o in objects:
        digest = o["sha256"]
        src = source_path(o)
        if not src:
            continue
        dest = STREAM_DIR / f"{digest}.mp3"
        jobs.append((o, src, dest))
    if limit > 0:
        jobs = jobs[:limit]
    print(f"[encode] jobs={len(jobs)} → {STREAM_DIR}", flush=True)

    ok = skip = fail = 0
    results = []

    def work(item):
        o, src, dest = item
        success, msg = encode_one(ffmpeg, src, dest)
        return o, dest, success, msg

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = [ex.submit(work, j) for j in jobs]
        for i, fut in enumerate(as_completed(futs), 1):
            o, dest, success, msg = fut.result()
            if success:
                if msg == "skip":
                    skip += 1
                else:
                    ok += 1
                results.append(
                    {
                        "sha256": o["sha256"],
                        "title": o.get("commercial_title") or o.get("title_guess") or (o.get("filenames") or ["?"])[0],
                        "aliases": o.get("aliases") or [],
                        "isrcs": o.get("isrcs") or [],
                        "size": dest.stat().st_size if dest.exists() else 0,
                        "stream_file": dest.name,
                        "local_stream": str(dest),
                    }
                )
            else:
                fail += 1
                if fail <= 8:
                    print(f"[fail] {o.get('title_guess')}: {msg}", flush=True)
            if i % 25 == 0 or i == len(futs):
                print(f"  progress {i}/{len(futs)} ok={ok} skip={skip} fail={fail}", flush=True)

    playlist = {
        "signature": "Δ9Φ963-PUBLIC-MUSIC-STREAM-v1",
        "artist": "Excavationpro",
        "generated_at": utc_now(),
        "bitrate": BITRATE,
        "stream_dir": str(STREAM_DIR),
        "stats": {
            "encoded_or_ready": len(results),
            "new_encoded": ok,
            "skipped_existing": skip,
            "failed": fail,
            "total_stream_bytes": sum(r["size"] for r in results),
            "total_stream_gb": round(sum(r["size"] for r in results) / (1024**3), 3),
        },
        "public_base_url": None,  # filled by --publish-hf or --base-url
        "tracks": sorted(results, key=lambda x: (x.get("title") or "").lower()),
    }
    out = CAT / "public_stream_playlist.json"
    out.write_text(json.dumps(playlist, indent=2, ensure_ascii=False), encoding="utf-8")
    (VAULT / "manifest" / "public_stream_playlist.json").parent.mkdir(parents=True, exist_ok=True)
    (VAULT / "manifest" / "public_stream_playlist.json").write_text(
        json.dumps(playlist, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[encode] wrote {out} tracks={len(results)} gb={playlist['stats']['total_stream_gb']}", flush=True)
    return playlist


def publish_hf(repo_id: str = HF_REPO_DEFAULT, private: bool = False) -> str:
    """Upload public_stream/*.mp3 + playlist to HF dataset for public HTTPS streaming."""
    token_path = Path.home() / ".cache" / "huggingface" / "token"
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not token and token_path.exists():
        token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        raise SystemExit("No HF token — set HF_TOKEN or login")

    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub"])
        from huggingface_hub import HfApi, create_repo

    api = HfApi(token=token)
    print(f"[hf] ensure repo {repo_id}", flush=True)
    try:
        create_repo(repo_id, repo_type="dataset", private=private, exist_ok=True, token=token)
    except Exception as e:
        print(f"[hf] create_repo note: {e}", flush=True)

    # upload folder
    print(f"[hf] upload {STREAM_DIR} → datasets/{repo_id}/stream/", flush=True)
    api.upload_folder(
        folder_path=str(STREAM_DIR),
        path_in_repo="stream",
        repo_id=repo_id,
        repo_type="dataset",
        token=token,
        commit_message="Excavationpro public stream pack (160kbps MP3)",
    )
    # playlist
    pl_path = CAT / "public_stream_playlist.json"
    if pl_path.exists():
        api.upload_file(
            path_or_fileobj=str(pl_path),
            path_in_repo="public_stream_playlist.json",
            repo_id=repo_id,
            repo_type="dataset",
            token=token,
            commit_message="playlist index",
        )

    base = f"https://huggingface.co/datasets/{repo_id}/resolve/main/stream"
    # rewrite playlist with public URLs
    pl = json.loads(pl_path.read_text(encoding="utf-8"))
    pl["public_base_url"] = base
    pl["hf_dataset"] = f"https://huggingface.co/datasets/{repo_id}"
    pl["published_at"] = utc_now()
    for t in pl.get("tracks") or []:
        t["stream_url"] = f"{base}/{t['stream_file']}"
    pl_path.write_text(json.dumps(pl, indent=2, ensure_ascii=False), encoding="utf-8")
    (VAULT / "manifest" / "public_stream_playlist.json").write_text(
        json.dumps(pl, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if EXCAV.exists():
        (EXCAV / "data").mkdir(exist_ok=True)
        (EXCAV / "data" / "public_stream_playlist.json").write_text(
            json.dumps(pl, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    print(f"[hf] public base: {base}", flush=True)
    return base


def _load_lattice_payload() -> dict:
    """Bundle ledger + vault merkle + live links for the listen page."""
    out: dict = {
        "signature": "Δ9Φ963-SOVEREIGN-LISTEN-HUB-v1",
        "steward": "Justin Helmer / Lightfather / Excavationpro",
        "generated_at": utc_now(),
    }
    led_path = CAT / "excavationpro_music_ledger.json"
    vault_path = CAT / "music_vault_manifest.json"
    if led_path.exists():
        led = json.loads(led_path.read_text(encoding="utf-8"))
        out["music_ledger"] = {
            "signature": led.get("signature"),
            "generated_at": led.get("generated_at"),
            "steward": led.get("steward"),
            "content_sha256": (led.get("ledger") or {}).get("content_sha256"),
            "lattice_role": (led.get("ledger") or {}).get("lattice_role"),
            "note": (led.get("ledger") or {}).get("note"),
            "stats": led.get("stats") or {},
            "live_links": led.get("live_links") or {},
        }
    if vault_path.exists():
        v = json.loads(vault_path.read_text(encoding="utf-8"))
        out["vault"] = {
            "signature": v.get("signature"),
            "merkle_root": v.get("merkle_root"),
            "stats": v.get("stats") or {},
            "generated_at": v.get("generated_at"),
        }
    # canonical lattice / web links (always present)
    out["sites"] = {
        "listen": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
        "catalog": "https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html",
        "sovereign_vault": "https://deepseekoracle.github.io/Excavationpro/excavationpro-sovereign-music-hub.html",
        "eternal_haven": "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html",
        "haven_star_chart": "https://deepseekoracle.github.io/Excavationpro/HavenStarChart.html",
        "lygo_resonance": "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html",
        "lygo_stack": "https://deepseekoracle.github.io/lygo-protocol-stack/",
        "github_excavationpro": "https://github.com/DeepSeekOracle/Excavationpro",
        "github_stack": "https://github.com/DeepSeekOracle/lygo-protocol-stack",
        "spotify": "https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S",
        "youtube_music": "https://music.youtube.com/@Excavationpro",
        "deezer": "https://www.deezer.com/artist/146004952",
        "feature_fm": "https://ffm.to/eovnvo9",
        "rumble_channel": "https://rumble.com/user/Excavationpro",
        "rumble_live": (
            "https://rumble.com/v7cuiw2-content-you-can-digoriginal-music-radiocoffee-room-chat-lurk-friendly247-st.html"
            "?mref=1th29y&mc=2p3fp"
        ),
        "rumble_embed": "https://rumble.com/embed/v7anxls/?pub=1th29y",
        "hf_streams": f"https://huggingface.co/datasets/{HF_REPO_DEFAULT}",
        "twitter": "https://twitter.com/Excavationpro",
        "instagram": "https://instagram.com/Excavationpro",
        "website": "https://excavationpro.ca/",
        "public_link_archive": (
            "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/LYGO_PUBLIC_LINK_ARCHIVE.json"
        ),
        "sovereign_vault_spec": (
            "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/SOVEREIGN_MUSIC_VAULT.md"
        ),
    }
    return out


def write_public_player_hub(base_url: str | None = None) -> None:
    pl_path = CAT / "public_stream_playlist.json"
    if not pl_path.exists():
        raise SystemExit("no playlist — run --encode first")
    pl = json.loads(pl_path.read_text(encoding="utf-8"))
    if base_url:
        pl["public_base_url"] = base_url.rstrip("/")
        for t in pl.get("tracks") or []:
            t["stream_url"] = f"{pl['public_base_url']}/{t['stream_file']}"
        pl_path.write_text(json.dumps(pl, indent=2, ensure_ascii=False), encoding="utf-8")

    lattice = _load_lattice_payload()
    # slim tracks for page size: keep fields player needs
    slim_tracks = []
    for t in pl.get("tracks") or []:
        slim_tracks.append(
            {
                "title": t.get("title"),
                "sha256": t.get("sha256"),
                "isrcs": (t.get("isrcs") or [])[:3],
                "aliases": (t.get("aliases") or [])[:2],
                "size": t.get("size"),
                "stream_url": t.get("stream_url"),
            }
        )
    page_data = {
        "playlist": {
            "signature": pl.get("signature"),
            "bitrate": pl.get("bitrate"),
            "public_base_url": pl.get("public_base_url"),
            "hf_dataset": pl.get("hf_dataset") or f"https://huggingface.co/datasets/{HF_REPO_DEFAULT}",
            "stats": pl.get("stats") or {},
            "generated_at": pl.get("generated_at") or pl.get("published_at"),
            "tracks": slim_tracks,
        },
        "lattice": lattice,
    }
    playable = sum(1 for t in slim_tracks if t.get("stream_url"))
    data_js = json.dumps(page_data, ensure_ascii=False).replace("</", "<\\/")
    og = "https://deepseekoracle.github.io/Excavationpro/assets/og-haven-star-chart.jpg"
    rumble_embed = lattice["sites"]["rumble_embed"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Excavationpro Listen — Free Sovereign Music Player + Lattice Ledger</title>
<meta name="description" content="Fully interactive free player for Excavationpro: 1700+ streams, SHA-256 vault, immutable music ledger, Eternal Haven lattice links, 24/7 Rumble radio. Independent of DistroKid and Spotify.">
<meta name="keywords" content="Excavationpro, free music player, sovereign stream, immutable ledger, LYGO lattice, Eternal Haven, Justin Helmer, independent artist">
<link rel="canonical" href="https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html">
<meta property="og:title" content="Excavationpro — Listen Free + Lattice Ledger">
<meta property="og:description" content="Interactive sovereign music hub: play free streams, verify immutable ledger, explore the lattice.">
<meta property="og:type" content="music.playlist">
<meta property="og:url" content="https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Excavationpro Listen Free">
<meta name="twitter:description" content="Sovereign player + immutable ledger + full lattice links.">
<meta name="twitter:image" content="{og}">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --void:#06060e; --panel:#12121f; --cyan:#00f0ff; --mag:#b06bff; --gold:#d4af37;
  --ok:#3dd68c; --text:#eeeef6; --muted:#9a9ab0; --live:#ff4d6d;
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{
  margin:0; font-family:Inter,system-ui,sans-serif; color:var(--text);
  background:radial-gradient(1100px 560px at 12% -8%,#2a1450 0%,var(--void) 48%);
  min-height:100vh; padding-bottom:110px;
}}
a {{ color:var(--cyan); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.wrap {{ max-width:1120px; margin:0 auto; padding:0 16px; }}
header.hero {{ padding:22px 0 10px; border-bottom:1px solid rgba(0,240,255,.12); }}
h1 {{ font-family:Cinzel,serif; color:var(--gold); margin:0 0 8px; font-size:clamp(1.4rem,3vw,1.9rem); }}
.sub {{ color:var(--muted); line-height:1.55; max-width:70ch; font-size:.95rem; }}
.nav-main {{ display:flex; flex-wrap:wrap; gap:8px 10px; margin-top:14px; }}
.nav-main a {{
  font-size:.78rem; padding:6px 10px; border-radius:999px;
  border:1px solid rgba(0,240,255,.25); background:rgba(0,240,255,.06); color:var(--text);
}}
.nav-main a:hover {{ border-color:var(--gold); color:var(--gold); text-decoration:none; }}
.nav-main a.pri {{ border-color:rgba(212,175,55,.5); background:rgba(212,175,55,.12); color:var(--gold); }}
.tabs {{ display:flex; flex-wrap:wrap; gap:8px; margin:16px 0 10px; }}
.tabs button {{
  cursor:pointer; border-radius:8px; border:1px solid rgba(176,107,255,.35);
  background:rgba(18,18,31,.9); color:var(--text); padding:9px 14px; font-size:.85rem;
}}
.tabs button.active {{ border-color:var(--gold); color:var(--gold); }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px; margin:12px 0 18px; }}
.card {{
  background:rgba(18,18,31,.92); border:1px solid rgba(176,107,255,.28); border-radius:12px; padding:12px 14px;
}}
.card b {{ display:block; color:var(--cyan); font-size:1.25rem; }}
.card span {{ font-size:.72rem; color:var(--muted); }}
.toolbar {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:10px; }}
.toolbar input, .toolbar select {{
  flex:1; min-width:160px; padding:11px 12px; border-radius:8px;
  border:1px solid rgba(0,240,255,.3); background:#0c0c16; color:var(--text); font-size:.9rem;
}}
.list {{ max-height:min(62vh,720px); overflow:auto; border:1px solid rgba(255,255,255,.06); border-radius:12px; background:rgba(8,8,16,.55); }}
.row {{
  display:grid; grid-template-columns:44px 1fr auto auto; gap:10px; align-items:center;
  padding:10px 12px; border-bottom:1px solid rgba(255,255,255,.05);
}}
.row:hover, .row.on {{ background:rgba(0,240,255,.06); }}
.row .n {{ color:var(--muted); font-size:.8rem; font-variant-numeric:tabular-nums; }}
.row .title {{ font-weight:500; font-size:.92rem; }}
.row .meta {{ font-size:.72rem; color:var(--muted); margin-top:2px; }}
.badge {{
  display:inline-block; padding:2px 7px; border-radius:999px; font-size:.68rem;
  background:rgba(61,214,140,.12); color:var(--ok); margin-right:4px;
}}
.row button.play {{
  cursor:pointer; border-radius:8px; border:1px solid rgba(0,240,255,.4);
  background:linear-gradient(135deg,rgba(0,240,255,.18),rgba(176,107,255,.22));
  color:var(--text); padding:8px 12px; font-weight:600; font-size:.82rem;
}}
.row button.play:hover {{ border-color:var(--gold); color:var(--gold); }}
.hidden {{ display:none !important; }}
.panel h2 {{ font-family:Cinzel,serif; color:var(--mag); font-size:1.1rem; margin:8px 0 10px; }}
.ledger {{
  font-family:ui-monospace,Consolas,monospace; font-size:.74rem; word-break:break-all;
  background:#0a0a14; border:1px solid rgba(212,175,55,.35); color:var(--gold);
  padding:12px; border-radius:8px; margin:8px 0 14px;
}}
.grid2 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px; }}
.link-grid a {{
  display:block; padding:10px 12px; border-radius:10px; margin-bottom:8px;
  border:1px solid rgba(0,240,255,.2); background:rgba(0,240,255,.05); color:var(--text); font-size:.86rem;
}}
.link-grid a:hover {{ border-color:var(--gold); text-decoration:none; }}
.link-grid a small {{ display:block; color:var(--muted); font-size:.72rem; margin-top:3px; }}
.embed-wrap {{
  position:relative; width:100%; border-radius:12px; overflow:hidden;
  border:1px solid rgba(0,240,255,.2); background:#000; aspect-ratio:16/9; max-height:380px;
}}
.embed-wrap iframe {{ position:absolute; inset:0; width:100%; height:100%; border:0; }}
.note {{
  background:rgba(0,240,255,.06); border-left:3px solid var(--cyan);
  padding:10px 12px; border-radius:0 8px 8px 0; color:var(--muted); font-size:.86rem; line-height:1.5; margin:10px 0;
}}
/* sticky player dock */
.dock {{
  position:fixed; left:0; right:0; bottom:0; z-index:50;
  background:rgba(6,6,14,.96); border-top:1px solid rgba(0,240,255,.25);
  backdrop-filter:blur(10px); box-shadow:0 -8px 30px rgba(0,0,0,.45);
}}
.dock-inner {{ max-width:1120px; margin:0 auto; padding:10px 16px 12px; }}
.now {{ color:var(--gold); font-size:.92rem; min-height:1.25em; margin-bottom:6px; }}
.now .sub2 {{ color:var(--muted); font-size:.75rem; }}
.controls {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:6px; }}
.controls button {{
  cursor:pointer; border-radius:8px; border:1px solid rgba(176,107,255,.4);
  background:rgba(18,18,31,.95); color:var(--text); padding:8px 12px; font-size:.82rem; font-weight:600;
}}
.controls button.on {{ border-color:var(--gold); color:var(--gold); }}
.controls button:hover {{ border-color:var(--cyan); }}
audio {{ width:100%; height:36px; }}
footer {{ max-width:1120px; margin:24px auto 0; padding:16px; color:var(--muted); font-size:.76rem; }}
.kb {{ font-size:.72rem; color:var(--muted); margin-top:6px; }}
@media (max-width:640px) {{
  .row {{ grid-template-columns:32px 1fr auto; }}
  .row .sz {{ display:none; }}
}}
</style>
</head>
<body>
<header class="hero wrap">
  <h1>Excavationpro — Listen Free</h1>
  <p class="sub">Fully interactive sovereign player. Streams host outside DistroKid/Spotify.
  Immutable music ledger + vault Merkle root live on this page. Linked to the full Eternal Haven / LYGO lattice.</p>
  <nav class="nav-main" id="nav-main" aria-label="All sites"></nav>
</header>

<div class="wrap">
  <div class="tabs" role="tablist">
    <button type="button" class="active" data-tab="player">Player</button>
    <button type="button" data-tab="ledger">Immutable Ledger</button>
    <button type="button" data-tab="lattice">Lattice &amp; Links</button>
    <button type="button" data-tab="radio">Live Radio</button>
  </div>

  <section class="stats" id="stats"></section>

  <div id="panel-player">
    <div class="toolbar">
      <input id="q" type="search" placeholder="Search title, ISRC, hash…" autocomplete="off">
      <select id="sort" aria-label="Sort">
        <option value="title">Sort: Title A–Z</option>
        <option value="title-desc">Sort: Title Z–A</option>
        <option value="size">Sort: Size</option>
        <option value="isrc">Sort: Has ISRC first</option>
      </select>
      <select id="filter" aria-label="Filter">
        <option value="all">All tracks</option>
        <option value="isrc">With ISRC</option>
        <option value="playable">Playable only</option>
      </select>
    </div>
    <p class="kb">Keys: <b>Space</b> play/pause · <b>N</b> next · <b>P</b> prev · <b>S</b> shuffle · <b>/</b> focus search</p>
    <div class="list" id="list"></div>
  </div>

  <div id="panel-ledger" class="panel hidden">
    <h2>Immutable Music Ledger</h2>
    <div class="note">SHA-256 content hash of the public catalog snapshot (restore titles + ISRCs + streaming album set). Recomputed when the catalog grows. Platform delists do not rewrite this root.</div>
    <p class="sub">Music ledger signature</p>
    <div class="ledger" id="led-sig">—</div>
    <p class="sub">Ledger content SHA-256</p>
    <div class="ledger" id="led-hash">—</div>
    <p class="sub">Sovereign vault Merkle root (masters)</p>
    <div class="ledger" id="vault-merkle">—</div>
    <div class="grid2" id="led-stats"></div>
    <div class="note" id="led-note" style="margin-top:14px"></div>
  </div>

  <div id="panel-lattice" class="panel hidden">
    <h2>Lattice · Websites · Discovery</h2>
    <div class="note">Everything public for Excavationpro / LYGO — music, haven, stack, social, streams. No distributor lock-in for <em>discovery</em>.</div>
    <div class="grid2 link-grid" id="link-grid"></div>
  </div>

  <div id="panel-radio" class="panel hidden">
    <h2>24/7 Live Radio (Rumble)</h2>
    <div class="embed-wrap">
      <iframe src="{rumble_embed}" title="Excavationpro Live Radio" allowfullscreen allow="autoplay"></iframe>
    </div>
    <p class="sub" style="margin-top:10px"><a id="rumble-open" href="#" target="_blank" rel="noopener">Open live on Rumble ↗</a></p>
  </div>
</div>

<footer class="wrap">
  Δ9Φ963 Sovereign Listen Hub · Steward: Justin Helmer / Lightfather / Excavationpro ·
  Free to listen · Streams on Hugging Face · Ledger on LYGO lattice ·
  <a href="https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/SOVEREIGN_MUSIC_VAULT.md">Vault spec</a>
</footer>

<div class="dock">
  <div class="dock-inner">
    <div class="now" id="now"><span>Select a track…</span><div class="sub2" id="now-meta"></div></div>
    <div class="controls">
      <button type="button" id="btn-prev" title="Previous (P)">⏮ Prev</button>
      <button type="button" id="btn-play" title="Play/Pause (Space)">▶ Play</button>
      <button type="button" id="btn-next" title="Next (N)">Next ⏭</button>
      <button type="button" id="btn-shuffle" title="Shuffle (S)">Shuffle</button>
      <button type="button" id="btn-repeat" title="Repeat one">Repeat</button>
      <button type="button" id="btn-copy" title="Copy stream URL">Copy link</button>
    </div>
    <audio id="audio" controls preload="none"></audio>
  </div>
</div>

<script id="boot" type="application/json">{data_js}</script>
<script>
const DATA = JSON.parse(document.getElementById('boot').textContent);
const PL = DATA.playlist || {{}};
const LATTICE = DATA.lattice || {{}};
const SITES = LATTICE.sites || {{}};
const tracks = PL.tracks || [];
const audio = document.getElementById('audio');
let order = tracks.map((_, i) => i);
let current = -1;
let shuffle = false;
let repeat = false;
let filteredIdx = order.slice();

// --- nav ---
const NAV = [
  ['▶ Listen', SITES.listen, true],
  ['Catalog', SITES.catalog],
  ['Hash Vault', SITES.sovereign_vault],
  ['Eternal Haven', SITES.eternal_haven],
  ['Haven Star Chart', SITES.haven_star_chart],
  ['LYGO Resonance', SITES.lygo_resonance],
  ['LYGO Stack', SITES.lygo_stack],
  ['Spotify', SITES.spotify],
  ['YouTube Music', SITES.youtube_music],
  ['Deezer', SITES.deezer],
  ['Feature.fm', SITES.feature_fm],
  ['Rumble Live', SITES.rumble_live],
  ['HF Streams', SITES.hf_streams],
  ['GitHub', SITES.github_excavationpro],
  ['excavationpro.ca', SITES.website],
  ['X', SITES.twitter],
  ['Instagram', SITES.instagram],
];
document.getElementById('nav-main').innerHTML = NAV.map(([label, href, pri]) =>
  href ? `<a href="${{href}}" class="${{pri ? 'pri' : ''}}" ${{href.startsWith('http') && !href.includes('deepseekoracle.github.io/Excavationpro') ? 'target="_blank" rel="noopener"' : ''}}>${{label}}</a>` : ''
).join('');

// --- stats ---
const led = LATTICE.music_ledger || {{}};
const vault = LATTICE.vault || {{}};
const ls = led.stats || {{}};
document.getElementById('stats').innerHTML = [
  ['Playable streams', tracks.filter(t => t.stream_url).length],
  ['Stream pack', ((PL.stats||{{}}).total_stream_gb || 0) + ' GB'],
  ['Bitrate', PL.bitrate || '160k'],
  ['Catalog albums', ls.streaming_albums_total || ls.spotify_albums || '—'],
  ['ISRC ledger', ls.unique_isrcs_total || '—'],
  ['Vault masters', (vault.stats||{{}}).unique_objects || tracks.length],
].map(([l,v]) => `<div class="card"><b>${{v}}</b><span>${{l}}</span></div>`).join('');

// --- ledger panel ---
document.getElementById('led-sig').textContent = led.signature || PL.signature || '—';
document.getElementById('led-hash').textContent = led.content_sha256 || '—';
document.getElementById('vault-merkle').textContent = vault.merkle_root || '—';
document.getElementById('led-note').textContent = led.note || 'Ledger anchors restore titles + ISRCs + streaming catalog.';
const ledCards = [
  ['Restore titles', ls.restore_unique_titles],
  ['Matched / known', ls.matched_titles],
  ['Local masters', ls.have_local_master],
  ['On streaming map', ls.have_spotify],
  ['Vault ISRCs', ls.restore_with_vault_isrc],
  ['Catalog rows', ls.catalog_track_rows],
  ['Ledger generated', (led.generated_at || '').slice(0,19).replace('T',' ') || '—'],
  ['Vault generated', (vault.generated_at || '').slice(0,19).replace('T',' ') || '—'],
];
document.getElementById('led-stats').innerHTML = ledCards.map(([l,v]) =>
  `<div class="card"><b>${{v ?? '—'}}</b><span>${{l}}</span></div>`
).join('');

// --- lattice links panel ---
const LINK_SECTIONS = [
  ['Music hub', [
    ['Listen (this page)', SITES.listen],
    ['Full catalog + ISRC ledger', SITES.catalog],
    ['Sovereign hash vault', SITES.sovereign_vault],
    ['Public stream dataset (HF)', SITES.hf_streams],
    ['Vault architecture doc', SITES.sovereign_vault_spec],
  ]],
  ['Lattice / LYGO', [
    ['Eternal Haven', SITES.eternal_haven],
    ['Haven Star Chart', SITES.haven_star_chart],
    ['LYGO Resonance', SITES.lygo_resonance],
    ['LYGO Protocol Stack Pages', SITES.lygo_stack],
    ['Public link archive', SITES.public_link_archive],
    ['Stack GitHub', SITES.github_stack],
  ]],
  ['Streaming & social', [
    ['Spotify artist', SITES.spotify],
    ['YouTube Music', SITES.youtube_music],
    ['Deezer', SITES.deezer],
    ['Feature.fm', SITES.feature_fm],
    ['Rumble channel', SITES.rumble_channel],
    ['Rumble 24/7 live', SITES.rumble_live],
    ['X / Twitter', SITES.twitter],
    ['Instagram', SITES.instagram],
    ['excavationpro.ca', SITES.website],
  ]],
];
document.getElementById('link-grid').innerHTML = LINK_SECTIONS.map(([h, items]) =>
  `<div><h3 style="color:var(--gold);font-size:.95rem;margin:0 0 8px">${{h}}</h3>${{
    items.map(([lab, href]) => href ? `<a href="${{href}}" target="_blank" rel="noopener">${{lab}}<small>${{href}}</small></a>` : ''
  ).join('')}}</div>`
).join('');
const rumbleA = document.getElementById('rumble-open');
if (rumbleA && SITES.rumble_live) rumbleA.href = SITES.rumble_live;

// --- tabs ---
document.querySelectorAll('.tabs button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tabs button').forEach(b => b.classList.toggle('active', b === btn));
    ['player','ledger','lattice','radio'].forEach(n => {{
      const el = document.getElementById('panel-' + n);
      if (el) el.classList.toggle('hidden', n !== btn.dataset.tab);
    }});
  }});
}});

function esc(s) {{
  return String(s||'').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}
function fmtSize(n) {{
  if (!n) return '';
  if (n > 1e6) return (n/1e6).toFixed(1) + ' MB';
  return (n/1e3).toFixed(0) + ' KB';
}}

function rebuildFilter() {{
  const q = (document.getElementById('q').value || '').toLowerCase().trim();
  const f = document.getElementById('filter').value;
  const sort = document.getElementById('sort').value;
  let idx = tracks.map((_, i) => i);
  if (f === 'isrc') idx = idx.filter(i => (tracks[i].isrcs||[]).length);
  if (f === 'playable') idx = idx.filter(i => tracks[i].stream_url);
  if (q) {{
    idx = idx.filter(i => {{
      const t = tracks[i];
      return [t.title, t.sha256, ...(t.isrcs||[]), ...(t.aliases||[])].join(' ').toLowerCase().includes(q);
    }});
  }}
  idx.sort((a,b) => {{
    const ta = tracks[a], tb = tracks[b];
    if (sort === 'title-desc') return (tb.title||'').localeCompare(ta.title||'');
    if (sort === 'size') return (tb.size||0) - (ta.size||0);
    if (sort === 'isrc') return ((tb.isrcs||[]).length?1:0) - ((ta.isrcs||[]).length?1:0) || (ta.title||'').localeCompare(tb.title||'');
    return (ta.title||'').localeCompare(tb.title||'');
  }});
  filteredIdx = idx;
  renderList();
}}

function renderList() {{
  const el = document.getElementById('list');
  el.innerHTML = filteredIdx.map((i, n) => {{
    const t = tracks[i];
    const on = i === current ? 'on' : '';
    const can = !!t.stream_url;
    return `<div class="row ${{on}}" data-i="${{i}}">
      <div class="n">${{n+1}}</div>
      <div>
        <div class="title">${{esc(t.title)}}</div>
        <div class="meta">${{(t.isrcs||[]).slice(0,2).map(x=>`<span class="badge">${{esc(x)}}</span>`).join('')}}${{t.sha256 ? esc(t.sha256.slice(0,12))+'…' : ''}}</div>
      </div>
      <div class="meta sz">${{fmtSize(t.size)}}</div>
      <button type="button" class="play" ${{can?'':'disabled'}} data-play="${{i}}">${{i===current && !audio.paused ? 'Pause' : 'Play'}}</button>
    </div>`;
  }}).join('') || '<p class="sub" style="padding:16px">No matches</p>';
  el.querySelectorAll('[data-play]').forEach(b => b.addEventListener('click', e => {{
    e.stopPropagation();
    const i = +b.getAttribute('data-play');
    if (i === current && !audio.paused) {{ audio.pause(); updatePlayBtn(); renderList(); return; }}
    playIndex(i);
  }}));
  el.querySelectorAll('.row').forEach(r => r.addEventListener('click', () => playIndex(+r.dataset.i)));
}}

function updateNow() {{
  const t = current >= 0 ? tracks[current] : null;
  document.getElementById('now').innerHTML = t
    ? `<span>▶ ${{esc(t.title)}}</span><div class="sub2">${{esc((t.isrcs||[])[0]||'')}} · ${{t.sha256 ? t.sha256.slice(0,16)+'…' : ''}}</div>`
    : '<span>Select a track…</span><div class="sub2"></div>';
}}
function updatePlayBtn() {{
  document.getElementById('btn-play').textContent = (!audio.paused && current >= 0) ? '⏸ Pause' : '▶ Play';
}}

function playIndex(i) {{
  const t = tracks[i];
  if (!t || !t.stream_url) return;
  current = i;
  audio.src = t.stream_url;
  audio.play().catch(() => {{}});
  updateNow();
  updatePlayBtn();
  renderList();
  // deep link
  try {{ history.replaceState(null, '', '#' + (t.sha256 || i)); }} catch (e) {{}}
}}

function nextTrack(dir) {{
  if (!filteredIdx.length) return;
  let pos = filteredIdx.indexOf(current);
  if (pos < 0) pos = dir > 0 ? -1 : 0;
  let npos = pos + dir;
  if (repeat && current >= 0 && dir === 0) {{ playIndex(current); return; }}
  if (npos >= filteredIdx.length) npos = 0;
  if (npos < 0) npos = filteredIdx.length - 1;
  playIndex(filteredIdx[npos]);
}}

function shuffleOrder() {{
  shuffle = !shuffle;
  document.getElementById('btn-shuffle').classList.toggle('on', shuffle);
  if (shuffle) {{
    filteredIdx = filteredIdx.slice().sort(() => Math.random() - 0.5);
  }} else {{
    rebuildFilter();
    return;
  }}
  renderList();
}}

document.getElementById('btn-prev').onclick = () => nextTrack(-1);
document.getElementById('btn-next').onclick = () => nextTrack(1);
document.getElementById('btn-play').onclick = () => {{
  if (current < 0) {{ nextTrack(1); return; }}
  if (audio.paused) audio.play().catch(()=>{{}}); else audio.pause();
  updatePlayBtn(); renderList();
}};
document.getElementById('btn-shuffle').onclick = shuffleOrder;
document.getElementById('btn-repeat').onclick = () => {{
  repeat = !repeat;
  document.getElementById('btn-repeat').classList.toggle('on', repeat);
}};
document.getElementById('btn-copy').onclick = async () => {{
  const t = current >= 0 ? tracks[current] : null;
  const url = t && t.stream_url ? t.stream_url : location.href;
  try {{ await navigator.clipboard.writeText(url); document.getElementById('btn-copy').textContent = 'Copied'; setTimeout(() => document.getElementById('btn-copy').textContent = 'Copy link', 1200); }}
  catch (e) {{ prompt('Copy URL', url); }}
}};
audio.addEventListener('play', () => {{ updatePlayBtn(); renderList(); }});
audio.addEventListener('pause', () => {{ updatePlayBtn(); renderList(); }});
audio.addEventListener('ended', () => {{
  if (repeat) {{ playIndex(current); return; }}
  nextTrack(1);
}});
document.getElementById('q').addEventListener('input', rebuildFilter);
document.getElementById('sort').addEventListener('change', rebuildFilter);
document.getElementById('filter').addEventListener('change', rebuildFilter);

document.addEventListener('keydown', e => {{
  if (e.target.matches('input,textarea,select')) {{
    if (e.key === 'Escape') e.target.blur();
    return;
  }}
  if (e.key === ' ') {{ e.preventDefault(); document.getElementById('btn-play').click(); }}
  if (e.key === 'n' || e.key === 'N') nextTrack(1);
  if (e.key === 'p' || e.key === 'P') nextTrack(-1);
  if (e.key === 's' || e.key === 'S') shuffleOrder();
  if (e.key === '/') {{ e.preventDefault(); document.getElementById('q').focus(); }}
}});

// deep link #sha256
rebuildFilter();
(function bootHash() {{
  const h = (location.hash || '').replace(/^#/, '');
  if (!h) return;
  const i = tracks.findIndex(t => t.sha256 === h || (t.sha256 && t.sha256.startsWith(h)));
  if (i >= 0) playIndex(i);
  else if (/^\\d+$/.test(h)) {{
    const n = +h;
    if (n >= 0 && n < tracks.length) playIndex(n);
  }}
}})();
</script>
</body>
</html>
"""
    for out in (
        EXCAV / "excavationpro-listen.html",
        DOCS / "excavationpro-listen.html",
        VAULT / "excavationpro-listen.html",
    ):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"wrote {out}", flush=True)

    if EXCAV.exists():
        (EXCAV / "data").mkdir(exist_ok=True)
        (EXCAV / "data" / "public_stream_playlist.json").write_text(
            json.dumps(pl, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        # also write lattice snapshot for optional fetch
        (EXCAV / "data" / "listen_hub_lattice.json").write_text(
            json.dumps(lattice, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    (CAT / "listen_hub_lattice.json").write_text(
        json.dumps(lattice, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[hub] playable_urls={playable}/{len(slim_tracks)} base={pl.get('public_base_url')}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--encode", action="store_true")
    ap.add_argument("--publish-hf", action="store_true")
    ap.add_argument("--hub", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--repo", default=HF_REPO_DEFAULT)
    ap.add_argument("--base-url", default=None, help="Set public stream base URL without re-upload")
    args = ap.parse_args()

    if not any([args.encode, args.publish_hf, args.hub, args.base_url]):
        args.encode = True
        args.hub = True

    if args.encode:
        encode_streams(limit=args.limit, workers=args.workers)
    if args.publish_hf:
        publish_hf(repo_id=args.repo)
    if args.base_url:
        write_public_player_hub(base_url=args.base_url)
    elif args.hub or args.publish_hf or args.encode:
        write_public_player_hub()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
