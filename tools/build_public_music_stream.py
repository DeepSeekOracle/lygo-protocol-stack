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

    # If no public URL yet, still build player that works when playlist has stream_url
    # or falls back to relative (won't work on Pages without host)
    tracks = pl.get("tracks") or []
    playable = sum(1 for t in tracks if t.get("stream_url"))
    data_js = json.dumps(pl, ensure_ascii=False).replace("</", "<\\/")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Excavationpro — Listen Free (Sovereign Stream Hub)</title>
<meta name="description" content="Play Excavationpro music free — independent stream vault, not locked to DistroKid or Spotify. Search and listen in your browser.">
<meta name="keywords" content="Excavationpro, free music stream, independent artist, listen free, sovereign music, Justin Helmer">
<link rel="canonical" href="https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html">
<meta property="og:title" content="Excavationpro — Listen Free">
<meta property="og:description" content="Independent browser player for Excavationpro masters. Platform-independent.">
<meta property="og:type" content="music.playlist">
<meta property="og:url" content="https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html">
<meta name="twitter:card" content="summary_large_image">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{ --void:#06060e; --cyan:#00f0ff; --mag:#b06bff; --gold:#d4af37; --ok:#3dd68c; --text:#eeeef6; --muted:#9a9ab0; --panel:#12121f; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Inter,system-ui,sans-serif; background:radial-gradient(900px 480px at 15% -10%,#221045 0%,var(--void) 50%); color:var(--text); min-height:100vh; }}
a {{ color:var(--cyan); }}
header {{ max-width:1000px; margin:0 auto; padding:24px 18px 10px; }}
h1 {{ font-family:Cinzel,serif; color:var(--gold); margin:0 0 8px; font-size:1.65rem; }}
.sub {{ color:var(--muted); line-height:1.5; }}
.nav {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:12px; font-size:.9rem; }}
.player-bar {{
  position:sticky; top:0; z-index:20; background:rgba(8,8,16,.94); border-bottom:1px solid rgba(0,240,255,.2);
  backdrop-filter:blur(8px);
}}
.player-inner {{ max-width:1000px; margin:0 auto; padding:12px 18px; display:grid; gap:8px; }}
.now {{ font-size:.95rem; color:var(--gold); min-height:1.3em; }}
audio {{ width:100%; height:40px; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px; max-width:1000px; margin:16px auto; padding:0 18px; }}
.card {{ background:var(--panel); border:1px solid rgba(176,107,255,.3); border-radius:10px; padding:12px; }}
.card b {{ display:block; color:var(--cyan); font-size:1.3rem; }}
.card span {{ font-size:.75rem; color:var(--muted); }}
main {{ max-width:1000px; margin:0 auto 40px; padding:0 18px; }}
input {{ width:100%; padding:12px; border-radius:8px; border:1px solid rgba(0,240,255,.3); background:#0c0c16; color:var(--text); margin:10px 0; }}
.row {{
  display:grid; grid-template-columns:1fr auto auto; gap:10px; align-items:center;
  padding:10px 8px; border-bottom:1px solid rgba(255,255,255,.06);
}}
.row:hover {{ background:rgba(0,240,255,.04); }}
.row button {{
  background:linear-gradient(135deg,rgba(0,240,255,.2),rgba(176,107,255,.25));
  border:1px solid rgba(0,240,255,.4); color:var(--text); border-radius:8px; padding:8px 14px; cursor:pointer; font-weight:600;
}}
.row button:hover {{ border-color:var(--gold); color:var(--gold); }}
.title {{ font-weight:500; }}
.meta {{ font-size:.75rem; color:var(--muted); }}
.badge {{ display:inline-block; padding:2px 7px; border-radius:999px; background:rgba(61,214,140,.12); color:var(--ok); font-size:.7rem; margin-right:4px; }}
.warn {{ background:rgba(255,180,0,.08); border-left:3px solid var(--gold); padding:10px 12px; margin:12px 0; color:var(--muted); font-size:.88rem; }}
footer {{ max-width:1000px; margin:0 auto; padding:20px 18px; color:var(--muted); font-size:.78rem; }}
</style>
</head>
<body>
<header>
  <h1>Listen — Excavationpro</h1>
  <p class="sub">Independent stream hub. Not DistroKid. Not Spotify. Search and press play.
  If main platforms delist a track, this vault still serves it.</p>
  <div class="nav">
    <a href="excavationpro-music-catalog.html">Full Catalog</a>
    <a href="excavationpro-sovereign-music-hub.html">Hash Vault</a>
    <a href="eternalhaven.html">Eternal Haven</a>
    <a href="https://rumble.com/user/Excavationpro" target="_blank" rel="noopener">Live Radio</a>
  </div>
</header>

<div class="player-bar">
  <div class="player-inner">
    <div class="now" id="now">Select a track…</div>
    <audio id="audio" controls preload="none"></audio>
  </div>
</div>

<section class="stats" id="stats"></section>
<main>
  <div class="warn" id="warn" style="display:none"></div>
  <input id="q" type="search" placeholder="Search songs…" autocomplete="off">
  <div id="list"></div>
</main>
<footer>Δ9Φ963 Sovereign Stream · Steward: Justin Helmer / Excavationpro · Free to listen · Verify via SHA-256 vault</footer>

<script id="pl" type="application/json">{data_js}</script>
<script>
const PL = JSON.parse(document.getElementById('pl').textContent);
const tracks = PL.tracks || [];
const audio = document.getElementById('audio');
const now = document.getElementById('now');
let current = -1;

document.getElementById('stats').innerHTML = [
  ['Tracks online', tracks.filter(t => t.stream_url).length],
  ['In pack', tracks.length],
  ['Stream size', ((PL.stats||{{}}).total_stream_gb||0) + ' GB'],
  ['Bitrate', PL.bitrate || '160k'],
].map(([l,v]) => `<div class="card"><b>${{v}}</b><span>${{l}}</span></div>`).join('');

if (!tracks.some(t => t.stream_url)) {{
  document.getElementById('warn').style.display = 'block';
  document.getElementById('warn').textContent = 'Streams are encoding/publishing. Local steward can play via vault gateway; public HTTPS URLs appear after HF publish.';
}}

function esc(s) {{ return String(s||'').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}

function play(i) {{
  const t = tracks[i];
  if (!t || !t.stream_url) {{ now.textContent = 'No public stream URL yet for this track'; return; }}
  current = i;
  now.textContent = '▶ ' + (t.title || 'track');
  audio.src = t.stream_url;
  audio.play().catch(() => {{}});
  document.querySelectorAll('.row button').forEach((b, idx) => b.textContent = idx === i ? 'Playing' : 'Play');
}}

audio.addEventListener('ended', () => {{
  if (current >= 0 && current < tracks.length - 1) play(current + 1);
}});

function render() {{
  const q = (document.getElementById('q').value||'').toLowerCase().trim();
  let rows = tracks;
  if (q) rows = tracks.filter(t => [t.title, ...(t.aliases||[]), ...(t.isrcs||[])].join(' ').toLowerCase().includes(q));
  document.getElementById('list').innerHTML = rows.map((t) => {{
    const i = tracks.indexOf(t);
    const can = !!t.stream_url;
    return `<div class="row">
      <div>
        <div class="title">${{esc(t.title)}}</div>
        <div class="meta">${{(t.isrcs||[]).slice(0,2).map(x=>`<span class="badge">${{esc(x)}}</span>`).join('')}} ${{can ? '' : '· pending publish'}}</div>
      </div>
      <div class="meta">${{t.size ? (t.size/1e6).toFixed(1)+' MB' : ''}}</div>
      <button type="button" ${{can ? '' : 'disabled'}} onclick="play(${{i}})">${{can ? 'Play' : '…'}}</button>
    </div>`;
  }}).join('') || '<p class="sub">No matches</p>';
}}
document.getElementById('q').addEventListener('input', render);
render();
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

    # also drop playlist for Pages
    if EXCAV.exists():
        (EXCAV / "data").mkdir(exist_ok=True)
        (EXCAV / "data" / "public_stream_playlist.json").write_text(
            pl_path.read_text(encoding="utf-8"), encoding="utf-8"
        )
    print(f"[hub] playable_urls={playable}/{len(tracks)} base={pl.get('public_base_url')}", flush=True)


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
