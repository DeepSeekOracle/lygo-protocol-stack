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
    try:
        src_size = src.stat().st_size
    except OSError as e:
        return False, str(e)
    if src.suffix.lower() == ".mp3" and src_size < 15_000_000:
        shutil.copy2(src, dest)
        return True, "copy-mp3"
    # Full-book multi-GB masters: allow long encode (≈ hours for 5–7GB WAV)
    # ~1GB WAV ≈ 1–3 min at 160k; use generous cap
    timeout = 600
    if src_size > 500_000_000:
        timeout = max(3600, int(src_size / 1_000_000) * 4)  # ~4s per MB upper bound
    if src_size > 8_000_000_000:
        # skip monstrous >8GB sources for public stream; vault still holds masters
        return False, f"skip-too-large:{src_size}"
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
            timeout=timeout,
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
        "rumble_live": "https://rumble.com/user/excavationpro/live",
        "rumble_live_radio": (
            "https://rumble.com/v7cuiw2-content-you-can-digoriginal-music-radiocoffee-room-chat-lurk-friendly247-st.html"
            "?mref=1th29y&mc=2p3fp"
        ),
        "rumble_embed": "https://rumble.com/embed/v7anxls/?pub=1th29y",
        "kick_live": "https://kick.com/excavationpro",
        "twitch_live": "https://twitch.tv/excavationpro",
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
    n_tracks = len(slim_tracks)
    n_play = playable or n_tracks
    desc = (
        f"Free Excavationpro music portal: {n_play}+ playable streams, sovereign SHA-256 vault, "
        "immutable ledger, Kick/Rumble/Twitch live portals, Eternal Haven lattice. "
        "Independent of DistroKid. Listen free in your browser — Justin Helmer / Lightfather."
    )
    # JSON-LD sample tracks (first 40 for crawlers without huge payload)
    sample_tracks = [
        {
            "@type": "MusicRecording",
            "name": t.get("title") or "Track",
            "url": t.get("stream_url") or "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
            "byArtist": {"@type": "MusicGroup", "name": "Excavationpro"},
        }
        for t in slim_tracks[:40]
        if t.get("title")
    ]
    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": "https://deepseekoracle.github.io/Excavationpro/#website",
                "name": "Excavationpro / Eternal Haven",
                "url": "https://deepseekoracle.github.io/Excavationpro/",
                "publisher": {"@id": "https://deepseekoracle.github.io/Excavationpro/#org"},
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html?q={search_term_string}",
                    "query-input": "required name=search_term_string",
                },
            },
            {
                "@type": "WebPage",
                "@id": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html#webpage",
                "url": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
                "name": "Excavationpro Listen Free — Sovereign Music Portal",
                "description": desc,
                "isPartOf": {"@id": "https://deepseekoracle.github.io/Excavationpro/#website"},
                "about": {"@id": "https://deepseekoracle.github.io/Excavationpro/#artist"},
                "primaryImageOfPage": {"@type": "ImageObject", "url": og},
                "inLanguage": "en",
            },
            {
                "@type": "MusicPlaylist",
                "@id": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html#playlist",
                "name": "Excavationpro Sovereign Stream Pack",
                "numTracks": n_tracks,
                "description": desc,
                "url": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
                "author": {"@id": "https://deepseekoracle.github.io/Excavationpro/#artist"},
                "track": sample_tracks,
            },
            {
                "@type": "MusicGroup",
                "@id": "https://deepseekoracle.github.io/Excavationpro/#artist",
                "name": "Excavationpro",
                "alternateName": ["Justin Helmer", "Lightfather"],
                "url": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
                "sameAs": [
                    "https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S",
                    "https://music.youtube.com/@Excavationpro",
                    "https://www.deezer.com/artist/146004952",
                    "https://kick.com/excavationpro",
                    "https://twitch.tv/excavationpro",
                    "https://rumble.com/user/Excavationpro",
                    "https://twitter.com/Excavationpro",
                    "https://instagram.com/Excavationpro",
                    "https://excavationpro.ca/",
                    "https://ffm.to/eovnvo9",
                ],
                "genre": ["Hip Hop", "Experimental", "Electronic"],
            },
            {
                "@type": "Organization",
                "@id": "https://deepseekoracle.github.io/Excavationpro/#org",
                "name": "Excavationpro / LYGO / Eternal Haven",
                "url": "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html",
                "logo": og,
                "sameAs": [
                    "https://github.com/DeepSeekOracle/Excavationpro",
                    "https://github.com/DeepSeekOracle/lygo-protocol-stack",
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Eternal Haven",
                        "item": "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Listen Free",
                        "item": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
                    },
                ],
            },
            {
                "@type": "DonateAction",
                "name": "Support Excavationpro via PayPal",
                "recipient": {"@id": "https://deepseekoracle.github.io/Excavationpro/#artist"},
                "target": "https://www.paypal.com/paypalme/ExcavationPro",
            },
        ],
    }
    json_ld_s = json.dumps(json_ld, ensure_ascii=False).replace("</", "<\\/")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Excavationpro Listen Free — {n_play}+ Songs · Sovereign Music Portal · Lattice Ledger</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="Excavationpro, free music stream, listen free, independent artist, Justin Helmer, Lightfather, sovereign music vault, LYGO lattice, Eternal Haven, Kick live, Twitch, Rumble, hip hop, experimental, donate PayPal">
<meta name="author" content="Justin Helmer / Excavationpro / Lightfather">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="googlebot" content="index, follow">
<meta name="bingbot" content="index, follow">
<meta name="theme-color" content="#0a0a12">
<meta name="google-adsense-account" content="ca-pub-0646320966060599">
<link rel="canonical" href="https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html">
<link rel="alternate" type="application/json" href="data/public_stream_playlist.json" title="Stream playlist JSON">
<meta property="og:site_name" content="Excavationpro / Eternal Haven">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="Excavationpro Listen Free — {n_play}+ Sovereign Streams">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="music.playlist">
<meta property="og:url" content="https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html">
<meta property="og:image" content="{og}">
<meta property="og:image:alt" content="Excavationpro Eternal Haven music portal">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@Excavationpro">
<meta name="twitter:creator" content="@Excavationpro">
<meta name="twitter:title" content="Excavationpro Listen Free — {n_play}+ Streams">
<meta name="twitter:description" content="Free sovereign player · ledger · Kick/Rumble/Twitch live · support via PayPal.">
<meta name="twitter:image" content="{og}">
<link rel="sitemap" type="application/xml" href="sitemap.xml">
<script type="application/ld+json">{json_ld_s}</script>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --void:#06060e; --panel:#12121f; --cyan:#00f0ff; --mag:#b06bff; --gold:#d4af37;
  --ok:#3dd68c; --text:#eeeef6; --muted:#9a9ab0; --live:#ff4d6d; --paypal:#0070ba;
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{
  margin:0; font-family:Inter,system-ui,sans-serif; color:var(--text);
  background:radial-gradient(1100px 560px at 12% -8%,#2a1450 0%,var(--void) 48%);
  min-height:100vh; padding-bottom:120px;
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
.nav-main a.donate {{ border-color:rgba(0,112,186,.6); background:rgba(0,112,186,.2); color:#7ec8ff; }}
.donate-strip {{
  margin:14px 0 0; padding:14px 16px; border-radius:12px;
  border:1px solid rgba(0,112,186,.45); background:linear-gradient(135deg,rgba(0,112,186,.18),rgba(176,107,255,.12));
  display:flex; flex-wrap:wrap; gap:12px; align-items:center; justify-content:space-between;
}}
.donate-strip p {{ margin:0; color:var(--muted); font-size:.88rem; line-height:1.45; max-width:60ch; }}
.paypal-btn {{
  display:inline-flex; align-items:center; gap:8px; padding:12px 18px; border-radius:10px;
  background:var(--paypal); color:#fff !important; font-weight:700; font-size:.92rem;
  border:none; text-decoration:none !important; box-shadow:0 4px 18px rgba(0,112,186,.35);
}}
.paypal-btn:hover {{ filter:brightness(1.12); color:#fff !important; }}
.live-pills {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
.live-pills a {{
  font-size:.8rem; font-weight:600; padding:8px 12px; border-radius:8px;
  border:1px solid rgba(255,77,109,.4); background:rgba(255,77,109,.12); color:#ffb3c1;
}}
.live-pills a:hover {{ border-color:var(--gold); color:var(--gold); text-decoration:none; }}
.ad-region {{
  display:none; margin:14px 0; padding:10px 12px; border-radius:12px;
  border:1px dashed rgba(255,255,255,.12); background:rgba(0,0,0,.25); text-align:center;
}}
.ad-region.ads-consent {{ display:block; }}
.ad-label {{ font-size:.68rem; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; margin-bottom:6px; }}
.ad-box {{ min-height:90px; overflow:hidden; }}
.cookie-banner {{
  position:fixed; left:12px; right:12px; bottom:108px; z-index:60; max-width:560px; margin:0 auto;
  background:rgba(12,12,22,.97); border:1px solid rgba(0,240,255,.3); border-radius:12px;
  padding:14px 16px; box-shadow:0 8px 32px rgba(0,0,0,.5); font-size:.84rem; color:var(--muted);
}}
.cookie-banner strong {{ color:var(--text); }}
.cookie-actions {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }}
.cookie-actions button {{
  cursor:pointer; border-radius:8px; padding:8px 14px; font-weight:600; font-size:.82rem;
  border:1px solid rgba(0,240,255,.35); background:rgba(0,240,255,.12); color:var(--text);
}}
.cookie-actions button.accept {{ border-color:rgba(0,112,186,.6); background:var(--paypal); color:#fff; }}
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
.controls button.radio-btn.on {{ border-color:#ff6b9d; color:#ff6b9d; box-shadow:0 0 12px rgba(255,107,157,.35); }}
.controls button:hover {{ border-color:var(--cyan); }}
.mode-pill {{ font-size:.72rem; color:var(--muted); margin-left:4px; letter-spacing:.03em; }}
.mode-pill.on {{ color:var(--gold); }}
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
  <p class="sub">Epic sovereign music portal — free browser player, immutable ledger, SHA-256 vault, and live portals.
  Independent of DistroKid and Spotify. Support keeps hosting &amp; tools free for everyone.</p>
  <nav class="nav-main" id="nav-main" aria-label="All sites"></nav>
  <div class="live-pills" aria-label="Live streaming portals">
    <a href="https://kick.com/excavationpro" target="_blank" rel="noopener">● Kick Live</a>
    <a href="https://rumble.com/user/excavationpro/live" target="_blank" rel="noopener">● Rumble Live</a>
    <a href="https://twitch.tv/excavationpro" target="_blank" rel="noopener">● Twitch Live</a>
  </div>
  <div class="donate-strip" id="donate">
    <p><strong style="color:var(--text)">Support Excavationpro / LYGO / Eternal Haven</strong><br>
    Donations are appreciated, never expected — they help cover hosting, streams, and lattice tools.
    PayPal: <a href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener">paypal.me/ExcavationPro</a></p>
    <a class="paypal-btn" href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener noreferrer">Donate via PayPal</a>
  </div>
</header>

<div class="wrap">
  <div class="ad-region" id="ad-top" aria-label="Advertisement">
    <div class="ad-label">Advertisement</div>
    <div class="ad-box"><ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-0646320966060599" data-ad-format="auto" data-full-width-responsive="true"></ins></div>
  </div>

  <div class="tabs" role="tablist">
    <button type="button" class="active" data-tab="player">Player</button>
    <button type="button" data-tab="ledger">Immutable Ledger</button>
    <button type="button" data-tab="lattice">Lattice &amp; Links</button>
    <button type="button" data-tab="radio">Live Portals</button>
    <button type="button" data-tab="support">Support</button>
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
    <p class="kb">Keys: <b>Space</b> play/pause · <b>N</b> next · <b>P</b> prev · <b>S</b> shuffle · <b>R</b> radio · <b>/</b> search · continuous auto-next always on</p>
    <div class="list" id="list"></div>
    <div class="ad-region" id="ad-mid" aria-label="Advertisement" style="margin-top:16px">
      <div class="ad-label">Advertisement</div>
      <div class="ad-box"><ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-0646320966060599" data-ad-format="auto" data-full-width-responsive="true"></ins></div>
    </div>
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
    <h2>Live portals</h2>
    <div class="grid2 link-grid" style="margin-bottom:14px">
      <div>
        <h3 style="color:var(--gold);font-size:.95rem;margin:0 0 8px">Watch live</h3>
        <a id="kick-open" href="https://kick.com/excavationpro" target="_blank" rel="noopener">Kick — kick.com/excavationpro<small>Primary live stream portal</small></a>
        <a id="rumble-open" href="https://rumble.com/user/excavationpro/live" target="_blank" rel="noopener">Rumble Live — rumble.com/user/excavationpro/live<small>Live room</small></a>
        <a id="twitch-open" href="https://twitch.tv/excavationpro" target="_blank" rel="noopener">Twitch — twitch.tv/excavationpro<small>Live portal</small></a>
      </div>
      <div>
        <h3 style="color:var(--gold);font-size:.95rem;margin:0 0 8px">24/7 radio embed</h3>
        <p class="sub" style="margin:0 0 8px">Always-on coffee-room radio (Rumble embed).</p>
      </div>
    </div>
    <div class="embed-wrap">
      <iframe src="{rumble_embed}" title="Excavationpro Live Radio" allowfullscreen allow="autoplay"></iframe>
    </div>
    <p class="sub" style="margin-top:10px"><a id="rumble-radio-open" href="#" target="_blank" rel="noopener">Open 24/7 radio on Rumble ↗</a></p>
  </div>

  <div id="panel-support" class="panel hidden">
    <h2>Support the portal</h2>
    <div class="note">
      This listen hub, stream hosting, and lattice docs stay free for the public.
      If the music or tools help you, a PayPal tip keeps the lights on.
    </div>
    <div class="donate-strip">
      <p><strong style="color:var(--text)">PayPal.me/ExcavationPro</strong><br>
      Official donate link for Justin Helmer / Excavationpro / LYGO Systems / Eternal Haven.
      Donations appreciated, never expected.</p>
      <a class="paypal-btn" href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener noreferrer">Donate via PayPal</a>
    </div>
    <div class="grid2" style="margin-top:16px">
      <div class="card">
        <b style="font-size:1rem;color:var(--gold)">What support funds</b>
        <span style="display:block;margin-top:8px;line-height:1.5">Public stream hosting · GitHub Pages · Rumble/Kick presence · catalog &amp; ledger rebuilds · Eternal Haven lattice tools</span>
      </div>
      <div class="card">
        <b style="font-size:1rem;color:var(--gold)">Also free forever</b>
        <span style="display:block;margin-top:8px;line-height:1.5">Search &amp; play · immutable ledger verification · open lattice links · no account required to listen</span>
      </div>
    </div>
    <p class="sub" style="margin-top:14px">Privacy: Advertising cookies load only after you accept the banner. See Eternal Haven for full cookie policy.
    AdSense publisher: <code>ca-pub-0646320966060599</code> · <a href="ads.txt">ads.txt</a></p>
  </div>
</div>

<div id="cookieBanner" class="cookie-banner" role="dialog" aria-label="Cookie consent" style="display:none">
  <strong>Cookies &amp; ads</strong>
  <p style="margin:6px 0 0">We use cookies for optional Google AdSense ads that help support free hosting.
  Streams and the player work without accepting ads. <a href="eternalhaven.html#privacy" style="color:var(--gold)">Privacy notes</a></p>
  <div class="cookie-actions">
    <button type="button" class="accept" id="cookieAccept">Accept ads &amp; cookies</button>
    <button type="button" id="cookieDecline">Essential only</button>
  </div>
</div>

<footer class="wrap">
  Δ9Φ963 Sovereign Listen Hub · Steward: Justin Helmer / Lightfather / Excavationpro ·
  Free to listen · Streams on Hugging Face · Ledger on LYGO lattice ·
  <a href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener">Donate PayPal</a> ·
  <a href="https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/SOVEREIGN_MUSIC_VAULT.md">Vault spec</a> ·
  <a href="sitemap.xml">Sitemap</a> · <a href="robots.txt">robots.txt</a>
</footer>

<div class="dock">
  <div class="dock-inner">
    <div class="now" id="now"><span>Select a track…</span><div class="sub2" id="now-meta"></div></div>
    <div class="controls">
      <button type="button" id="btn-prev" title="Previous (P)">⏮ Prev</button>
      <button type="button" id="btn-play" title="Play/Pause (Space)">▶ Play</button>
      <button type="button" id="btn-next" title="Next (N)">Next ⏭</button>
      <button type="button" id="btn-shuffle" title="Shuffle queue (S)">Shuffle</button>
      <button type="button" id="btn-radio" title="Radio — random forever (R)" class="radio-btn">📡 Radio</button>
      <button type="button" id="btn-repeat" title="Repeat one track">Repeat 1</button>
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
let repeatOne = false;
let radio = false;
let filteredIdx = order.slice();
let shuffleBag = [];
let advancing = false;

// --- nav ---
const NAV = [
  ['▶ Listen', SITES.listen, 'pri'],
  ['Catalog', SITES.catalog, ''],
  ['Hash Vault', SITES.sovereign_vault, ''],
  ['Eternal Haven', SITES.eternal_haven, ''],
  ['Haven Star Chart', SITES.haven_star_chart, ''],
  ['LYGO Resonance', SITES.lygo_resonance, ''],
  ['LYGO Stack', SITES.lygo_stack, ''],
  ['Kick Live', SITES.kick_live, ''],
  ['Rumble Live', SITES.rumble_live, ''],
  ['Twitch Live', SITES.twitch_live, ''],
  ['Spotify', SITES.spotify, ''],
  ['YouTube Music', SITES.youtube_music, ''],
  ['Deezer', SITES.deezer, ''],
  ['Feature.fm', SITES.feature_fm, ''],
  ['HF Streams', SITES.hf_streams, ''],
  ['GitHub', SITES.github_excavationpro, ''],
  ['excavationpro.ca', SITES.website, ''],
  ['Donate PayPal', 'https://www.paypal.com/paypalme/ExcavationPro', 'donate'],
  ['X', SITES.twitter, ''],
  ['Instagram', SITES.instagram, ''],
];
document.getElementById('nav-main').innerHTML = NAV.map(([label, href, cls]) =>
  href ? `<a href="${{href}}" class="${{cls || ''}}" ${{href.startsWith('http') && !href.includes('deepseekoracle.github.io/Excavationpro') ? 'target="_blank" rel="noopener"' : ''}}>${{label}}</a>` : ''
).join('');

// Cookie consent + AdSense (load script only after accept — policy aligned with Eternal Haven)
const ADSENSE_SRC = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-0646320966060599';
function showAdRegions() {{
  document.querySelectorAll('.ad-region').forEach(el => el.classList.add('ads-consent'));
}}
function pushAdUnits() {{
  document.querySelectorAll('ins.adsbygoogle').forEach(el => {{
    if (el.getAttribute('data-adsbygoogle-status')) return;
    try {{
      (window.adsbygoogle = window.adsbygoogle || []).push({{}});
      el.setAttribute('data-adsbygoogle-status', 'done');
    }} catch (e) {{ console.warn('AdSense', e); }}
  }});
}}
function loadAdSenseScript() {{
  showAdRegions();
  if (window.adsbygoogle) {{ pushAdUnits(); return; }}
  if (document.querySelector('script[data-lygo-adsense]')) {{ pushAdUnits(); return; }}
  const s = document.createElement('script');
  s.async = true;
  s.src = ADSENSE_SRC;
  s.crossOrigin = 'anonymous';
  s.setAttribute('data-lygo-adsense', '1');
  s.onload = () => pushAdUnits();
  document.head.appendChild(s);
}}
(function cookieConsent() {{
  const banner = document.getElementById('cookieBanner');
  const consent = localStorage.getItem('cookiesAccepted');
  if (consent === 'true') {{ loadAdSenseScript(); return; }}
  if (consent === 'false') {{ if (banner) banner.style.display = 'none'; return; }}
  if (banner) banner.style.display = 'block';
  const acc = document.getElementById('cookieAccept');
  const dec = document.getElementById('cookieDecline');
  if (acc) acc.onclick = () => {{
    localStorage.setItem('cookiesAccepted', 'true');
    if (banner) banner.style.display = 'none';
    loadAdSenseScript();
  }};
  if (dec) dec.onclick = () => {{
    localStorage.setItem('cookiesAccepted', 'false');
    if (banner) banner.style.display = 'none';
  }};
}})();

// ?q= search from URL (SEO SearchAction)
try {{
  const uq = new URLSearchParams(location.search).get('q');
  if (uq) {{
    const qi = document.getElementById('q');
    if (qi) {{ qi.value = uq; }}
  }}
}} catch (e) {{}}

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
  ['Live portals', [
    ['Kick Live', SITES.kick_live],
    ['Rumble Live', SITES.rumble_live],
    ['Twitch Live', SITES.twitch_live],
    ['Rumble channel', SITES.rumble_channel],
    ['Rumble 24/7 radio room', SITES.rumble_live_radio],
  ]],
  ['Streaming & social', [
    ['Spotify artist', SITES.spotify],
    ['YouTube Music', SITES.youtube_music],
    ['Deezer', SITES.deezer],
    ['Feature.fm', SITES.feature_fm],
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
const kickA = document.getElementById('kick-open');
const rumbleA = document.getElementById('rumble-open');
const twitchA = document.getElementById('twitch-open');
const rumbleRadioA = document.getElementById('rumble-radio-open');
if (kickA && SITES.kick_live) kickA.href = SITES.kick_live;
if (rumbleA && SITES.rumble_live) rumbleA.href = SITES.rumble_live;
if (twitchA && SITES.twitch_live) twitchA.href = SITES.twitch_live;
if (rumbleRadioA && (SITES.rumble_live_radio || SITES.rumble_live)) rumbleRadioA.href = SITES.rumble_live_radio || SITES.rumble_live;

// --- tabs ---
document.querySelectorAll('.tabs button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tabs button').forEach(b => b.classList.toggle('active', b === btn));
    ['player','ledger','lattice','radio','support'].forEach(n => {{
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

function playablePool() {{
  return filteredIdx.filter(i => tracks[i] && tracks[i].stream_url);
}}

function shuffleArray(arr) {{
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    const t = a[i]; a[i] = a[j]; a[j] = t;
  }}
  return a;
}}

function refillBag(exclude) {{
  let pool = playablePool();
  if (exclude != null && exclude >= 0 && pool.length > 1) {{
    pool = pool.filter(i => i !== exclude);
  }}
  shuffleBag = shuffleArray(pool);
}}

function updateModeUI() {{
  const sh = document.getElementById('btn-shuffle');
  const rp = document.getElementById('btn-repeat');
  const rd = document.getElementById('btn-radio');
  if (sh) {{
    sh.classList.toggle('on', shuffle && !radio);
    sh.textContent = shuffle && !radio ? 'Shuffle ✓' : 'Shuffle';
  }}
  if (rp) {{
    rp.classList.toggle('on', repeatOne);
    rp.textContent = repeatOne ? 'Repeat 1 ✓' : 'Repeat 1';
  }}
  if (rd) {{
    rd.classList.toggle('on', radio);
    rd.textContent = radio ? '📡 Radio ON' : '📡 Radio';
  }}
  const pill = document.getElementById('mode-pill');
  if (pill) {{
    let label = 'Continuous · auto-next';
    if (radio) label = '📡 RADIO · random forever';
    else if (shuffle) label = 'Shuffle · continuous';
    if (repeatOne) label += ' · loop track';
    pill.textContent = label;
    pill.classList.toggle('on', radio || shuffle || repeatOne);
  }}
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
  if (radio || shuffle) refillBag(current);
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
  const mode = radio ? ' · 📡 RADIO' : (shuffle ? ' · shuffle' : '');
  document.getElementById('now').innerHTML = t
    ? `<span>▶ ${{esc(t.title)}}${{mode}}</span><div class="sub2">${{esc((t.isrcs||[])[0]||'')}} · ${{t.sha256 ? t.sha256.slice(0,16)+'…' : ''}}</div>`
    : '<span>Select a track… or hit 📡 Radio</span><div class="sub2"></div>';
}}
function updatePlayBtn() {{
  document.getElementById('btn-play').textContent = (!audio.paused && current >= 0) ? '⏸ Pause' : '▶ Play';
}}

function playIndex(i) {{
  const t = tracks[i];
  if (!t || !t.stream_url) return false;
  current = i;
  try {{ audio.pause(); }} catch (e) {{}}
  audio.src = t.stream_url;
  audio.load();
  const p = audio.play();
  if (p && p.catch) p.catch(() => {{}});
  updateNow();
  updatePlayBtn();
  renderList();
  try {{ history.replaceState(null, '', '#' + (t.sha256 || i)); }} catch (e) {{}}
  return true;
}}

/** Pick next index. dir: +1 next, -1 prev. Continuous wrap always. */
function pickNext(dir) {{
  const pool = playablePool();
  if (!pool.length) return -1;

  // Repeat-one only on natural advance
  if (repeatOne && dir > 0 && current >= 0 && tracks[current] && tracks[current].stream_url) {{
    return current;
  }}

  // Radio or Shuffle: random from bag (no immediate full-catalog repeats)
  if ((radio || shuffle) && dir > 0) {{
    if (!shuffleBag.length) refillBag(current);
    if (!shuffleBag.length) return pool[Math.floor(Math.random() * pool.length)];
    return shuffleBag.pop();
  }}

  // Sequential through playable filtered list (wraps forever)
  let pos = pool.indexOf(current);
  if (pos < 0) pos = dir > 0 ? -1 : 0;
  let npos = pos + dir;
  if (npos >= pool.length) npos = 0;
  if (npos < 0) npos = pool.length - 1;
  return pool[npos];
}}

function nextTrack(dir) {{
  if (advancing) return;
  advancing = true;
  try {{
    const pool = playablePool();
    const maxTry = Math.min(25, Math.max(1, pool.length));
    for (let t = 0; t < maxTry; t++) {{
      const i = pickNext(dir);
      if (i < 0) break;
      if (playIndex(i)) break;
      shuffleBag = shuffleBag.filter(x => x !== i);
      current = i;
    }}
  }} finally {{
    advancing = false;
  }}
}}

function setShuffle(on) {{
  shuffle = !!on;
  if (shuffle) {{
    radio = false;
    refillBag(current);
  }} else {{
    shuffleBag = [];
  }}
  updateModeUI();
  renderList();
}}

function toggleShuffle() {{
  setShuffle(!shuffle);
}}

function toggleRadio() {{
  radio = !radio;
  if (radio) {{
    shuffle = false;
    repeatOne = false;
    refillBag(-1);
    updateModeUI();
    nextTrack(1); // 1-click: start random forever
  }} else {{
    shuffleBag = [];
    updateModeUI();
  }}
}}

function toggleRepeatOne() {{
  repeatOne = !repeatOne;
  updateModeUI();
}}

document.getElementById('btn-prev').onclick = () => nextTrack(-1);
document.getElementById('btn-next').onclick = () => nextTrack(1);
document.getElementById('btn-play').onclick = () => {{
  if (current < 0) {{ nextTrack(1); return; }}
  if (audio.paused) audio.play().catch(()=>{{}}); else audio.pause();
  updatePlayBtn(); renderList();
}};
document.getElementById('btn-shuffle').onclick = toggleShuffle;
const btnRadio = document.getElementById('btn-radio');
if (btnRadio) btnRadio.onclick = toggleRadio;
document.getElementById('btn-repeat').onclick = toggleRepeatOne;
document.getElementById('btn-copy').onclick = async () => {{
  const t = current >= 0 ? tracks[current] : null;
  const url = t && t.stream_url ? t.stream_url : location.href;
  try {{ await navigator.clipboard.writeText(url); document.getElementById('btn-copy').textContent = 'Copied'; setTimeout(() => document.getElementById('btn-copy').textContent = 'Copy link', 1200); }}
  catch (e) {{ prompt('Copy URL', url); }}
}};

// Continuous listening: always auto-advance on end (Repeat 1 handled in pickNext)
audio.addEventListener('play', () => {{ updatePlayBtn(); renderList(); }});
audio.addEventListener('pause', () => {{ updatePlayBtn(); renderList(); }});
audio.addEventListener('ended', () => {{ nextTrack(1); }});
// Skip dead streams so radio/continuous never stalls
audio.addEventListener('error', () => {{
  if (current < 0) return;
  console.warn('stream error, skipping', current);
  setTimeout(() => nextTrack(1), 250);
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
  if (e.key === 's' || e.key === 'S') toggleShuffle();
  if (e.key === 'r' || e.key === 'R') toggleRadio();
  if (e.key === '/') {{ e.preventDefault(); document.getElementById('q').focus(); }}
}});

(function injectModePill() {{
  const dock = document.querySelector('.dock-inner .controls');
  if (dock && !document.getElementById('mode-pill')) {{
    const span = document.createElement('span');
    span.id = 'mode-pill';
    span.className = 'mode-pill';
    span.textContent = 'Continuous · auto-next';
    dock.appendChild(span);
  }}
  updateModeUI();
}})();

// deep link #sha256
rebuildFilter();
(function bootHash() {{
  const h = (location.hash || '').replace(/^#/, '');
  if (!h) return;
  const i = tracks.findIndex(t => t.sha256 === h || (t.sha256 && t.sha256.startsWith(h)));
  if (i >= 0) playIndex(i);
  else if (/^\d+$/.test(h)) {{
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
