#!/usr/bin/env python3
"""
Build interactive Excavationpro Music Catalog website + gap report vs DistroKid restore list.
Outputs to Excavationpro/ + lygo-protocol-stack/docs/ for Pages + lattice.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT_DIR = STACK / "data" / "music_catalog"
RESTORE = Path(r"I:\Distrokid music restore ALL MUSIC\All music Restore.txt")
EXCAV = STACK.parent / "Excavationpro"
DOCS = STACK / "docs"

SPOTIFY_ARTIST = "https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S"
FFM = "https://ffm.to/eovnvo9"
ETERNAL = "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html"
RUMBLE_RADIO = (
    "https://rumble.com/v7c37aq-content-you-can-digoriginal-music-radiocoffee-room-chat-lurk-friendly247-st.html"
)
LATTICE_STACK = "https://deepseekoracle.github.io/lygo-protocol-stack/"
PUBLIC_ARCHIVE = "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/LYGO_PUBLIC_LINK_ARCHIVE.json"


def norm(t: str) -> str:
    t = (t or "").lower().strip()
    t = re.sub(r"\(feat\.?[^)]*\)", "", t)
    t = re.sub(r"\(with[^)]*\)", "", t)
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_restore(path: Path) -> list[dict]:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    releases = []
    i = 0
    while i < len(lines):
        title = lines[i]
        artist = lines[i + 1] if i + 1 < len(lines) else "Excavationpro"
        date = lines[i + 2] if i + 2 < len(lines) else ""
        if re.match(r"^\d{1,2}/", artist):
            date = artist
            artist = "Excavationpro"
            i += 2
        else:
            i += 3
        releases.append({"title": title, "artist": artist, "date": date})
    uniq: OrderedDict[str, dict] = OrderedDict()
    for r in releases:
        k = norm(r["title"])
        if k and k not in uniq:
            uniq[k] = r
        elif k in uniq and r.get("date") and not uniq[k].get("date"):
            uniq[k]["date"] = r["date"]
    return list(uniq.values())


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def build() -> dict:
    restore = parse_restore(RESTORE)
    cat = json.loads((CAT_DIR / "excavationpro_catalog.json").read_text(encoding="utf-8"))
    tracks = cat.get("tracks") or []
    albums = cat.get("albums") or []

    # indexes
    by_title: dict[str, list] = {}
    for t in tracks:
        k = norm(t.get("title") or "")
        if k:
            by_title.setdefault(k, []).append(t)
        # also index filename stem
        fn = t.get("filename") or ""
        fk = norm(Path(fn).stem if fn else "")
        if fk and fk != k:
            by_title.setdefault(fk, []).append(t)

    for a in albums:
        k = norm(a.get("title") or "")
        if k:
            by_title.setdefault(k, []).append(
                {
                    "title": a.get("title"),
                    "album": a.get("title"),
                    "spotify_url": a.get("spotify_url"),
                    "spotify_album_id": a.get("spotify_album_id"),
                    "date_published": a.get("date_published"),
                    "track_count": a.get("track_count"),
                    "isrc": None,
                    "sources": ["spotify_album"],
                }
            )

    # ISRC registry
    isrc_rows = []
    seen_isrc = set()
    for t in tracks:
        isrc = t.get("isrc")
        if not isrc or isrc in seen_isrc:
            continue
        seen_isrc.add(isrc)
        isrc_rows.append(
            {
                "title": t.get("title"),
                "isrc": isrc,
                "upc": t.get("upc"),
                "album": t.get("album"),
                "local_path": t.get("local_path"),
                "filename": t.get("filename"),
                "spotify_url": t.get("spotify_url"),
            }
        )

    matched = []
    missing = []
    for r in restore:
        k = norm(r["title"])
        entries = by_title.get(k) or []
        status = "missing"
        fuzzy = None
        if entries:
            status = "have"
        else:
            best, score = None, 0.0
            for ck, ents in by_title.items():
                s = SequenceMatcher(None, k, ck).ratio()
                if s > score:
                    score, best = s, ck
            if best and score >= 0.82:
                status = "fuzzy"
                fuzzy = {"score": round(score, 3), "matched_as": by_title[best][0].get("title"), "key": best}
                entries = by_title[best]

        has_isrc = any(e.get("isrc") for e in entries)
        has_local = any(e.get("local_path") for e in entries)
        has_spotify = any(e.get("spotify_url") or e.get("spotify_track_id") or e.get("spotify_album_id") for e in entries)
        spotify_url = next(
            (e.get("spotify_url") for e in entries if e.get("spotify_url")),
            None,
        )
        isrcs = list({e.get("isrc") for e in entries if e.get("isrc")})
        local_files = list({e.get("filename") for e in entries if e.get("filename")})[:5]

        row = {
            **r,
            "status": status,
            "fuzzy": fuzzy,
            "has_isrc": has_isrc,
            "has_local": has_local,
            "has_spotify": has_spotify,
            "isrcs": isrcs,
            "spotify_url": spotify_url,
            "local_files": local_files,
            "entry_count": len(entries),
        }
        if status == "missing":
            missing.append(row)
        else:
            matched.append(row)

    # merkle-ish ledger of catalog snapshot
    payload = {
        "signature": "Δ9Φ963-EXCAVATIONPRO-MUSIC-LEDGER-v1",
        "artist": "Excavationpro",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "steward": "Justin Helmer / Lightfather / Excavationpro",
        "live_links": {
            "spotify_artist": SPOTIFY_ARTIST,
            "feature_fm": FFM,
            "eternal_haven": ETERNAL,
            "rumble_live_radio": RUMBLE_RADIO,
            "lygo_stack_pages": LATTICE_STACK,
            "public_link_archive": PUBLIC_ARCHIVE,
            "music_catalog_page": "https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html",
        },
        "stats": {
            "restore_unique_titles": len(restore),
            "matched_titles": len(matched),
            "missing_titles": len(missing),
            "unique_isrcs_local": len(isrc_rows),
            "spotify_albums": len(albums),
            "catalog_track_rows": len(tracks),
        },
        "restore_matched": matched,
        "restore_missing": missing,
        "isrc_registry": isrc_rows,
        "spotify_albums": [
            {
                "title": a.get("title"),
                "spotify_album_id": a.get("spotify_album_id"),
                "spotify_url": a.get("spotify_url"),
                "date_published": a.get("date_published"),
                "track_count": a.get("track_count"),
                "upc": a.get("upc"),
            }
            for a in albums
        ],
    }

    # content hash of core lists for immutable ledger
    core = json.dumps(
        {
            "restore_titles": sorted(r["title"] for r in restore),
            "isrcs": sorted(r["isrc"] for r in isrc_rows),
            "spotify_albums": sorted(a.get("spotify_album_id") or "" for a in albums),
        },
        sort_keys=True,
    ).encode("utf-8")
    payload["ledger"] = {
        "content_sha256": hashlib.sha256(core).hexdigest(),
        "note": "SHA-256 of sorted restore titles + ISRCs + Spotify album IDs. Recompute after each catalog growth.",
        "lattice_role": "music-catalog-anchor",
        "anchor_paths": [
            "Excavationpro/excavationpro-music-catalog.html",
            "Excavationpro/data/excavationpro_music_ledger.json",
            "lygo-protocol-stack/data/music_catalog/",
        ],
    }

    return payload


def write_html(payload: dict, out_html: Path) -> None:
    data_json = json.dumps(payload, ensure_ascii=False)
    # avoid </script> break
    data_json = data_json.replace("</", "<\\/")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Excavationpro Music Catalog — Live Immutable Ledger</title>
<meta name="description" content="Public Excavationpro music catalog: searchable releases, ISRC codes, Spotify albums, live radio feed, and SHA-256 immutable ledger on the LYGO / Eternal Haven lattice.">
<link rel="canonical" href="https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html">
<meta property="og:title" content="Excavationpro Music Catalog — Live Immutable Ledger">
<meta property="og:description" content="Stream Excavationpro · explore ISRCs · live radio · lattice-anchored music ledger.">
<meta property="og:url" content="https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --void:#0a0a12; --panel:#12121f; --cyan:#00f0ff; --mag:#7d00ff; --gold:#d4af37;
  --ok:#3dd68c; --live:#00f0ff; --text:#e8e8f0; --muted:#9a9ab0;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; font-family:Inter,system-ui,sans-serif; background:radial-gradient(1200px 600px at 10% -10%,#1a1030 0%,var(--void) 50%);
  color:var(--text); min-height:100vh;
}}
a {{ color:var(--cyan); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
header {{
  padding:28px 20px 12px; max-width:1200px; margin:0 auto;
  border-bottom:1px solid rgba(0,240,255,.15);
}}
h1 {{ font-family:Cinzel,serif; font-size:1.75rem; margin:0 0 8px; color:var(--gold); }}
.sub {{ color:var(--muted); font-size:.95rem; line-height:1.5; }}
.nav {{ display:flex; flex-wrap:wrap; gap:10px 16px; margin-top:14px; font-size:.9rem; }}
.stats {{
  display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px;
  max-width:1200px; margin:20px auto; padding:0 20px;
}}
.card {{
  background:rgba(18,18,31,.85); border:1px solid rgba(125,0,255,.25); border-radius:12px;
  padding:14px 16px;
}}
.card b {{ display:block; font-size:1.5rem; color:var(--cyan); }}
.card span {{ font-size:.8rem; color:var(--muted); }}
.toolbar {{
  max-width:1200px; margin:0 auto 12px; padding:0 20px; display:flex; flex-wrap:wrap; gap:10px; align-items:center;
}}
input, select, button {{
  background:#0e0e18; border:1px solid rgba(0,240,255,.3); color:var(--text);
  border-radius:8px; padding:10px 12px; font-size:.9rem;
}}
input {{ flex:1; min-width:200px; }}
button {{ cursor:pointer; background:linear-gradient(135deg,rgba(0,240,255,.15),rgba(125,0,255,.2)); }}
button:hover {{ border-color:var(--cyan); }}
.tabs {{ max-width:1200px; margin:0 auto; padding:0 20px; display:flex; gap:8px; flex-wrap:wrap; }}
.tabs button.active {{ border-color:var(--gold); color:var(--gold); }}
main {{ max-width:1200px; margin:12px auto 40px; padding:0 20px; }}
table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
th, td {{ text-align:left; padding:8px 10px; border-bottom:1px solid rgba(255,255,255,.06); vertical-align:top; }}
th {{ color:var(--muted); font-weight:600; position:sticky; top:0; background:#0e0e18; }}
.badge {{
  display:inline-block; padding:2px 8px; border-radius:999px; font-size:.72rem; font-weight:600;
}}
.badge.live {{ background:rgba(0,240,255,.12); color:var(--live); }}
.badge.isrc {{ background:rgba(61,214,140,.15); color:var(--ok); }}
.badge.catalog {{ background:rgba(125,0,255,.15); color:#c9a0ff; }}
.ledger {{
  font-family:ui-monospace,Consolas,monospace; font-size:.75rem; word-break:break-all;
  background:#0a0a14; padding:12px; border-radius:8px; border:1px solid rgba(212,175,55,.25); color:var(--gold);
}}
.live-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; margin:16px 0; }}
.live-grid .card h3 {{ margin:0 0 8px; font-size:.95rem; color:var(--mag); }}
.embed-wrap {{
  position:relative; width:100%; border-radius:12px; overflow:hidden;
  border:1px solid rgba(0,240,255,.2); background:#000; aspect-ratio:16/9; max-height:420px;
}}
.embed-wrap iframe {{ position:absolute; inset:0; width:100%; height:100%; border:0; }}
footer {{ max-width:1200px; margin:0 auto; padding:20px; color:var(--muted); font-size:.8rem; }}
#panel-catalog table tr:hover, #panel-isrc table tr:hover, #panel-spotify table tr:hover {{ background:rgba(0,240,255,.04); }}
.hidden {{ display:none; }}
</style>
</head>
<body>
<header>
  <h1>Excavationpro Music Catalog</h1>
  <p class="sub">Public live catalog &amp; immutable music ledger — searchable releases, ISRC codes, Spotify albums, and 24/7 radio. Anchored on the LYGO / Eternal Haven lattice. Expandable as the collection grows.</p>
  <div class="nav">
    <a href="eternalhaven.html">← Eternal Haven</a>
    <a href="eternalhaven.html#music-hub">Music Hub</a>
    <a href="eternalhaven.html#lattice">Immutable Lattice</a>
    <a href="https://deepseekoracle.github.io/lygo-protocol-stack/" target="_blank" rel="noopener">LYGO Stack</a>
    <a href="{SPOTIFY_ARTIST}" target="_blank" rel="noopener">Spotify</a>
    <a href="{FFM}" target="_blank" rel="noopener">Feature.fm</a>
    <a href="{RUMBLE_RADIO}" target="_blank" rel="noopener">Live Radio</a>
  </div>
</header>

<section class="stats" id="stats"></section>

<section class="toolbar">
  <input id="q" type="search" placeholder="Search title, ISRC, album…" autocomplete="off">
  <select id="filter">
    <option value="all">All releases</option>
    <option value="live">On Spotify</option>
    <option value="isrc">With ISRC</option>
    <option value="catalog">Catalogued</option>
  </select>
  <button type="button" id="btn-export">Export CSV</button>
</section>

<div class="tabs">
  <button type="button" class="active" data-tab="overview">Live Feed</button>
  <button type="button" data-tab="catalog">Release Index</button>
  <button type="button" data-tab="isrc">ISRC Ledger</button>
  <button type="button" data-tab="spotify">Spotify Albums</button>
  <button type="button" data-tab="ledger">Immutable Ledger</button>
</div>

<main>
  <div id="panel-overview">
    <div class="live-grid">
      <div class="card"><h3>🎧 Live Radio</h3><p class="sub">24/7 Excavationpro &amp; LYGO originals.</p>
        <p><a href="{RUMBLE_RADIO}" target="_blank" rel="noopener">Open live stream on Rumble →</a></p></div>
      <div class="card"><h3>Spotify</h3><p class="sub">Full artist discography.</p>
        <p><a href="{SPOTIFY_ARTIST}" target="_blank" rel="noopener">Listen on Spotify →</a></p></div>
      <div class="card"><h3>Smart Link</h3><p class="sub">Multi-store feature link.</p>
        <p><a href="{FFM}" target="_blank" rel="noopener">ffm.to/eovnvo9 →</a></p></div>
      <div class="card"><h3>Eternal Haven</h3><p class="sub">Music hub + lattice anchors.</p>
        <p><a href="eternalhaven.html#music-hub">Open hub →</a></p></div>
    </div>
    <div class="card" style="margin-bottom:16px;">
      <h3 style="margin:0 0 10px;color:var(--gold);">Live stream</h3>
      <div class="embed-wrap">
        <iframe src="https://rumble.com/embed/v7c37aq/?pub=4" title="Excavationpro Live Radio" allowfullscreen allow="autoplay" loading="lazy"></iframe>
      </div>
      <p class="sub" style="margin-top:10px;">If the embed is blocked by your browser, use the <a href="{RUMBLE_RADIO}" target="_blank" rel="noopener">direct Rumble link</a>.</p>
    </div>
    <div class="card">
      <h3 style="margin:0 0 8px;color:var(--gold);">About this ledger</h3>
      <ul class="sub" style="margin:0;padding-left:18px;line-height:1.7;">
        <li><b>Release Index</b> — full public title list with date stamps.</li>
        <li><b>ISRC Ledger</b> — international standard recording codes for catalogued masters.</li>
        <li><b>Spotify Albums</b> — currently live album/EP pages with track counts.</li>
        <li><b>Immutable Ledger</b> — SHA-256 content hash; grows as new releases are added.</li>
      </ul>
    </div>
  </div>

  <div id="panel-catalog" class="hidden"><div class="card" style="overflow:auto;max-height:70vh;"><table><thead><tr>
    <th>Title</th><th>Date</th><th>Flags</th><th>ISRC</th><th>Listen</th>
  </tr></thead><tbody id="tb-catalog"></tbody></table></div></div>

  <div id="panel-isrc" class="hidden"><div class="card" style="overflow:auto;max-height:70vh;"><table><thead><tr>
    <th>ISRC</th><th>Title</th><th>Album / folder</th>
  </tr></thead><tbody id="tb-isrc"></tbody></table></div></div>

  <div id="panel-spotify" class="hidden"><div class="card" style="overflow:auto;max-height:70vh;"><table><thead><tr>
    <th>Album</th><th>Tracks</th><th>Date</th><th>Link</th>
  </tr></thead><tbody id="tb-spotify"></tbody></table></div></div>

  <div id="panel-ledger" class="hidden">
    <div class="card">
      <h3 style="color:var(--gold);margin-top:0;">Immutable content hash</h3>
      <p class="sub">SHA-256 over the sorted release index + ISRC set + Spotify album IDs. Updated when the catalog grows.</p>
      <div class="ledger" id="ledger-hash"></div>
      <p class="sub" style="margin-top:12px;">Public JSON: <a href="data/excavationpro_music_ledger.json">data/excavationpro_music_ledger.json</a></p>
      <p class="sub">Lattice signature: <span id="ledger-sig"></span></p>
    </div>
  </div>
</main>

<footer>
  Excavationpro / Justin Helmer · Lightfather · Signature Δ9Φ963-EXCAVATIONPRO-MUSIC-LEDGER-v1 ·
  Part of the <a href="eternalhaven.html">Eternal Haven</a> &amp; <a href="https://deepseekoracle.github.io/lygo-protocol-stack/" target="_blank" rel="noopener">LYGO</a> public lattice.
</footer>

<script id="LEDGER_DATA" type="application/json">{data_json}</script>
<script>
/* Expandable: prefers live JSON ledger (update without redesigning HTML). Fallback = embedded snapshot. */
let DATA = null;
const $ = (s) => document.querySelector(s);
const LEDGER_URLS = [
  'data/excavationpro_music_ledger.json',
  './data/excavationpro_music_ledger.json',
];

async function loadData() {{
  for (const u of LEDGER_URLS) {{
    try {{
      const r = await fetch(u + '?v=' + Date.now(), {{ cache: 'no-store' }});
      if (r.ok) {{
        DATA = await r.json();
        DATA._loaded_from = u;
        return DATA;
      }}
    }} catch (e) {{ /* file:// or offline */ }}
  }}
  DATA = JSON.parse(document.getElementById('LEDGER_DATA').textContent);
  DATA._loaded_from = 'embedded';
  return DATA;
}}

function allReleases() {{
  const a = (DATA.restore_matched || []).map(r => ({{...r, _cat: true}}));
  const b = (DATA.restore_missing || []).map(r => ({{...r, _cat: false, status: 'index'}}));
  return a.concat(b);
}}

function renderStats() {{
  const s = DATA.stats || {{}};
  const total = (s.restore_unique_titles || 0);
  const isrcs = s.unique_isrcs_local || (DATA.isrc_registry || []).length;
  const live = allReleases().filter(r => r.has_spotify || r.spotify_url).length;
  $('#stats').innerHTML = [
    ['Releases', total],
    ['ISRCs on ledger', isrcs],
    ['Spotify albums', s.spotify_albums || 0],
    ['Live-linked titles', live],
    ['Catalog rows', s.catalog_track_rows || 0],
  ].map(([l,v]) => `<div class="card"><b>${{v}}</b><span>${{l}}</span></div>`).join('');
}}

function q() {{ return ($('#q').value || '').toLowerCase().trim(); }}
function rowMatch(text) {{
  const qq = q();
  if (!qq) return true;
  return (text || '').toLowerCase().includes(qq);
}}

function flags(r) {{
  const bits = [];
  if (r.has_spotify || r.spotify_url) bits.push('<span class="badge live">spotify</span>');
  if (r.has_isrc || (r.isrcs && r.isrcs.length)) bits.push('<span class="badge isrc">isrc</span>');
  if (r._cat || r.status === 'have' || r.status === 'fuzzy') bits.push('<span class="badge catalog">catalogued</span>');
  return bits.join(' ') || '—';
}}

function renderCatalog() {{
  const f = $('#filter').value;
  let rows = allReleases();
  if (f === 'live') rows = rows.filter(r => r.has_spotify || r.spotify_url);
  if (f === 'isrc') rows = rows.filter(r => r.has_isrc || (r.isrcs && r.isrcs.length));
  if (f === 'catalog') rows = rows.filter(r => r._cat || r.status === 'have' || r.status === 'fuzzy');
  rows = rows.filter(r => rowMatch([r.title, r.date, ...(r.isrcs||[])].join(' ')));
  rows.sort((a,b) => (a.title||'').localeCompare(b.title||''));
  $('#tb-catalog').innerHTML = rows.map(r => `
    <tr>
      <td>${{esc(r.title)}}</td>
      <td>${{esc(r.date||'')}}</td>
      <td>${{flags(r)}}</td>
      <td>${{(r.isrcs||[]).map(i=>`<span class="badge isrc">${{esc(i)}}</span>`).join(' ') || '—'}}</td>
      <td>${{r.spotify_url ? `<a href="${{r.spotify_url}}" target="_blank" rel="noopener">Spotify</a>` : (DATA.live_links && DATA.live_links.spotify_artist ? `<a href="${{DATA.live_links.spotify_artist}}" target="_blank" rel="noopener">artist</a>` : '—')}}</td>
    </tr>`).join('') || '<tr><td colspan="5">No rows</td></tr>';
}}

function renderIsrc() {{
  const rows = (DATA.isrc_registry||[]).filter(r => rowMatch([r.isrc,r.title,r.album,r.filename].join(' ')));
  $('#tb-isrc').innerHTML = rows.map(r => `
    <tr>
      <td><span class="badge isrc">${{esc(r.isrc)}}</span></td>
      <td>${{esc(r.title||'')}}</td>
      <td>${{esc(r.album||'')}}</td>
    </tr>`).join('') || '<tr><td colspan="3">No ISRCs</td></tr>';
}}

function renderSpotify() {{
  const rows = (DATA.spotify_albums||[]).filter(a => rowMatch([a.title,a.upc,a.date_published].join(' ')));
  $('#tb-spotify').innerHTML = rows.map(a => `
    <tr>
      <td>${{esc(a.title||'')}}</td>
      <td>${{a.track_count||0}}</td>
      <td>${{esc(a.date_published||'')}}</td>
      <td>${{a.spotify_url ? `<a href="${{a.spotify_url}}" target="_blank" rel="noopener">Open album</a>` : '—'}}</td>
    </tr>`).join('');
}}

function renderLedger() {{
  $('#ledger-hash').textContent = (DATA.ledger && DATA.ledger.content_sha256) || '';
  $('#ledger-sig').textContent = (DATA.signature || '') + ' · ' + (DATA.generated_at || '');
}}

function esc(s) {{
  return String(s||'').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}

function showTab(name) {{
  document.querySelectorAll('.tabs button').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  ['overview','catalog','isrc','spotify','ledger'].forEach(n => {{
    const el = document.getElementById('panel-' + n);
    if (el) el.classList.toggle('hidden', n !== name);
  }});
  if (name === 'catalog') renderCatalog();
  if (name === 'isrc') renderIsrc();
  if (name === 'spotify') renderSpotify();
  if (name === 'ledger') renderLedger();
}}

function exportCsv() {{
  const f = $('#filter').value;
  let rows = [];
  if (f === 'isrc' || (document.querySelector('.tabs button.active')||{{}}).dataset.tab === 'isrc') {{
    rows = (DATA.isrc_registry||[]).map(r => [r.isrc, r.title, r.album]);
  }} else {{
    rows = allReleases().filter(r => {{
      if (f === 'live' && !(r.has_spotify || r.spotify_url)) return false;
      if (f === 'isrc' && !(r.has_isrc || (r.isrcs||[]).length)) return false;
      if (f === 'catalog' && !(r._cat || r.status === 'have' || r.status === 'fuzzy')) return false;
      return rowMatch(r.title);
    }}).map(r => [r.title, r.date, (r.isrcs||[]).join(';'), r.spotify_url||'']);
  }}
  const csv = rows.map(r => r.map(c => '"' + String(c??'').replace(/"/g,'""') + '"').join(',')).join('\\n');
  const blob = new Blob([csv], {{type:'text/csv'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'excavationpro_catalog.csv';
  a.click();
}}

function wireUi() {{
  $('#q').addEventListener('input', () => {{
    const t = document.querySelector('.tabs button.active')?.dataset.tab || 'catalog';
    if (t === 'overview') showTab('catalog');
    else showTab(t);
  }});
  $('#filter').addEventListener('change', () => showTab('catalog'));
  document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => showTab(b.dataset.tab)));
  $('#btn-export').addEventListener('click', exportCsv);
}}

loadData().then(() => {{
  wireUi();
  renderStats();
  showTab('overview');
}}).catch(err => {{
  console.error(err);
  DATA = JSON.parse(document.getElementById('LEDGER_DATA').textContent);
  wireUi();
  renderStats();
  showTab('overview');
}});
</script>
</body>
</html>
"""
    out_html.write_text(html, encoding="utf-8")
    print("wrote", out_html)


def main() -> int:
    payload = build()
    CAT_DIR.mkdir(parents=True, exist_ok=True)
    ledger_path = CAT_DIR / "excavationpro_music_ledger.json"
    ledger_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", ledger_path)
    print("stats", payload["stats"])
    print("ledger", payload["ledger"]["content_sha256"][:16] + "…")

    # public pages
    if EXCAV.exists():
        write_html(payload, EXCAV / "excavationpro-music-catalog.html")
        (EXCAV / "data").mkdir(exist_ok=True)
        (EXCAV / "data" / "excavationpro_music_ledger.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("wrote Excavationpro pages")

    write_html(payload, DOCS / "excavationpro-music-catalog.html")
    (DOCS / "excavationpro_music_ledger.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # missing titles plain text
    miss = CAT_DIR / "restore_MISSING_titles.txt"
    miss.write_text("\n".join(r["title"] for r in payload["restore_missing"]), encoding="utf-8")
    print("wrote", miss, "count", len(payload["restore_missing"]))

    # gap summary md
    md = CAT_DIR / "RESTORE_GAP_SUMMARY.md"
    s = payload["stats"]
    md.write_text(
        f"""# DistroKid Restore vs Local Catalog

Generated: {payload['generated_at']}

| Metric | Count |
|--------|------:|
| Unique titles in `All music Restore.txt` | {s['restore_unique_titles']} |
| Matched in our catalog (exact/fuzzy) | {s['matched_titles']} |
| **Missing from catalog** | **{s['missing_titles']}** |
| Unique ISRCs from J: filenames | {s['unique_isrcs_local']} |
| Spotify albums (public page) | {s['spotify_albums']} |

## Ledger
`{payload['ledger']['content_sha256']}`

## Site
- https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html
- Local: `Excavationpro/excavationpro-music-catalog.html`

## Rebuild
```bash
python tools/build_music_registry_site.py
```
""",
        encoding="utf-8",
    )
    print("wrote", md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
