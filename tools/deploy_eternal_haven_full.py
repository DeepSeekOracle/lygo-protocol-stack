#!/usr/bin/env python3
"""
Full Eternal Haven public deploy:
  1) Encode short public samples (90s max) from local chapter audio
  2) Publish HF dataset DeepSeekOracle/eternal-haven-lore
  3) Build EternalHavenCodex.html companion page
  4) Wire links on excav index + chart docs (not music listen redesign)
  5) ClawHub publish eternal-haven-lore-pack (if auth works)

Full multi-GB masters stay local / Lulu only.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
DATA = STACK / "data" / "eternal_haven"
SAMPLES = DATA / "samples"
LORE_PACK = Path(r"I:\E Drive\lygo-protocol-stack\clawhub\mirrors\eternal-haven-lore-pack")
if not LORE_PACK.is_dir():
    LORE_PACK = STACK / "clawhub" / "mirrors" / "eternal-haven-lore-pack"
EXCAV = Path(r"D:\Excavationpro")
BOOKS = Path(r"J:\FULL ADUIO BOOKS")
HF_REPO = "DeepSeekOracle/eternal-haven-lore"
HF_BASE = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main"

SAMPLES_SPEC = [
    {
        "id": "sample_book1_prologue",
        "book": 1,
        "title": "Book I · Prologue sample",
        "src": BOOKS
        / "A9 Eternal Quantum Light Accord Rise of Eleven Book Series"
        / "Volume I of the Silver Accord"
        / "EternalBookProlog11.wav",
        "seconds": 90,
    },
    {
        "id": "sample_book1_ch1",
        "book": 1,
        "title": "Book I · Chapter 1 sample — Serenya & Emberion",
        "src": BOOKS
        / "A9 Eternal Quantum Light Accord Rise of Eleven Book Series"
        / "Volume I of the Silver Accord"
        / "EternalBookChapter1.wav",
        "seconds": 90,
    },
    {
        "id": "sample_book2_ch1",
        "book": 2,
        "title": "Book II · Chapter 1 sample",
        "src": BOOKS / "BOOK 2" / "Chapter 1" / "Chapter1-2.wav",
        "seconds": 90,
    },
    {
        "id": "sample_book3_ch1",
        "book": 3,
        "title": "Book III · Chapter 1 sample",
        "src": BOOKS / "Book 3" / "Chapter 1" / "download.wav",
        "seconds": 90,
    },
    {
        "id": "sample_book4_dawn",
        "book": 4,
        "title": "Book IV · Dawn sample",
        "src": BOOKS / "Book 4" / "5" / "download.wav",
        "seconds": 90,
    },
    {
        "id": "sample_stinger",
        "book": 0,
        "title": "Eternal Haven · Excavationpro stinger",
        "src": BOOKS / "A9 Eternal Quantum Light Accord Rise of Eleven Book Series" / "LikeshareExpro.wav",
        "seconds": 60,
    },
    {
        "id": "sample_game_intro",
        "book": 0,
        "title": "Eternal Haven Game · Intro motif",
        "src": BOOKS / "FULL BOOK SERIES AND WEBSITE" / "GAMEBOOK" / "intro.mp3",
        "seconds": 60,
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def encode_sample(src: Path, dest: Path, seconds: int) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1000:
        return "exists"
    if not src.is_file():
        return f"missing:{src}"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-t",
        str(seconds),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "128k",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(dest),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not dest.is_file():
        return f"fail:{(r.stderr or '')[-200:]}"
    return "encoded"


def build_samples() -> list[dict]:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in SAMPLES_SPEC:
        dest = SAMPLES / f"{spec['id']}.mp3"
        status = encode_sample(Path(spec["src"]), dest, int(spec["seconds"]))
        print(f"  sample {spec['id']}: {status}")
        if not dest.is_file():
            continue
        rows.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "book": spec["book"],
                "seconds": spec["seconds"],
                "file": f"samples/{spec['id']}.mp3",
                "stream_url": f"{HF_BASE}/samples/{spec['id']}.mp3",
                "bytes": dest.stat().st_size,
                "copyright": "© Justin Helmer — promotional sample only; full work on Lulu",
            }
        )
    (DATA / "samples_index.json").write_text(
        json.dumps(
            {
                "signature": "Δ9Φ963-ETERNAL-HAVEN-SAMPLES-v1",
                "updated_utc": utc_now(),
                "samples": rows,
                "note": "Short free samples for discovery. Full audiobooks not hosted here.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return rows


def publish_hf(samples: list[dict]) -> None:
    from huggingface_hub import HfApi, create_repo

    api = HfApi()
    try:
        create_repo(HF_REPO, repo_type="dataset", exist_ok=True, private=False)
    except Exception as e:
        print("[hf] create_repo", e)

    readme = f"""---
license: other
pretty_name: Eternal Haven Lore Lattice
tags:
  - eternal-haven
  - lygo
  - lore
  - justin-helmer
  - excavationpro
---

# Eternal Haven Lore Lattice (public)

**Author:** Justin Helmer (Excavationpro / Lightfather)  
**Signature:** `Δ9Φ963-ETERNAL-HAVEN-LORE-HF-v1`

## Contents

| Path | Role |
|------|------|
| `lore_graph.json` | Public discovery graph (books, heroes, seals, chart IDs) |
| `books_manifest.json` | Book metadata + Lulu links |
| `samples/*.mp3` | **Short free samples only** (≤90s) |
| `samples_index.json` | Sample playlist |
| `skill/` | eternal-haven-lore-pack skill text (no full novel re-host beyond pack policy) |

## Rights

Story content **© Justin Helmer**. Full books: [Lulu](https://www.lulu.com/search?contributor=Justin+Helmer).  
Samples are promotional discovery audio — not a substitute for purchased/full releases.

## Lattice

- ClawHub: https://clawhub.ai/deepseekoracle/skills/eternal-haven-lore-pack  
- Star Chart: https://deepseekoracle.github.io/Excavationpro/HavenStarChart.html (filter Eternal Haven)  
- Codex page: https://deepseekoracle.github.io/Excavationpro/EternalHavenCodex.html  
- Site: https://eternalhaven.ca/

Updated: {utc_now()}
"""
    readme_path = DATA / "HF_README.md"
    readme_path.write_text(readme, encoding="utf-8")
    api.upload_file(
        path_or_fileobj=str(readme_path),
        path_in_repo="README.md",
        repo_id=HF_REPO,
        repo_type="dataset",
        commit_message="Eternal Haven lore dataset README",
    )
    for name in ("lore_graph.json", "books_manifest.json", "samples_index.json"):
        p = DATA / name
        if p.is_file():
            api.upload_file(
                path_or_fileobj=str(p),
                path_in_repo=name,
                repo_id=HF_REPO,
                repo_type="dataset",
                commit_message=f"lore: {name}",
            )
    for row in samples:
        local = SAMPLES / f"{row['id']}.mp3"
        if local.is_file():
            print("HF upload", row["file"])
            api.upload_file(
                path_or_fileobj=str(local),
                path_in_repo=row["file"],
                repo_id=HF_REPO,
                repo_type="dataset",
                commit_message=f"sample: {row['id']}",
            )
    # skill slim (md + heroes/themes, not full book txt if huge — actually pack already on clawhub)
    skill_files = [
        LORE_PACK / "SKILL.md",
        LORE_PACK / "references" / "heroes_index.md",
        LORE_PACK / "references" / "themes_and_motifs.md",
    ]
    for p in skill_files:
        if p.is_file():
            rel = "skill/" + str(p.relative_to(LORE_PACK)).replace("\\", "/")
            api.upload_file(
                path_or_fileobj=str(p),
                path_in_repo=rel,
                repo_id=HF_REPO,
                repo_type="dataset",
                commit_message=f"skill: {p.name}",
            )
    print("[hf] published", HF_REPO)


def write_codex_html(samples: list[dict]) -> Path:
    books = json.loads((DATA / "books_manifest.json").read_text(encoding="utf-8"))
    graph = json.loads((DATA / "lore_graph.json").read_text(encoding="utf-8"))
    heroes = [n for n in graph["nodes"] if n.get("kind") == "hero"]

    def book_cards() -> str:
        parts = []
        for b in books.get("books") or []:
            parts.append(
                f"""
      <article class="card book">
        <div class="glyph">{b.get('glyph','🌜')}</div>
        <h3>Book {b.get('volume')} · {b.get('era','')}</h3>
        <h2>{b.get('title')}</h2>
        <p>{b.get('summary','')}</p>
        <div class="actions">
          <a class="btn gold" href="{b.get('lulu_paperback') or books.get('lulu_search')}" target="_blank" rel="noopener">Lulu paperback</a>
          <a class="btn" href="{b.get('lulu_ebook') or books.get('lulu_search')}" target="_blank" rel="noopener">eBook</a>
          <a class="btn" href="HavenStarChart.html" target="_blank" rel="noopener">Open Star Chart</a>
        </div>
      </article>"""
            )
        return "\n".join(parts)

    def sample_rows() -> str:
        parts = []
        for s in samples:
            url = s["stream_url"]
            parts.append(
                f"""
      <div class="sample">
        <div>
          <strong>{s['title']}</strong>
          <div class="meta">Free sample · ≤{s['seconds']}s · © Justin Helmer</div>
        </div>
        <audio controls preload="none" src="{url}"></audio>
      </div>"""
            )
        return "\n".join(parts)

    def hero_chips() -> str:
        return "\n".join(
            f'<span class="chip" title="{h.get("domain","")}">{h.get("glyph","✦")} {h.get("name","")}</span>'
            for h in heroes
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="google-adsense-account" content="ca-pub-0646320966060599" />
  <title>Eternal Haven Codex · Books I–IV on the LYGO Lattice</title>
  <meta name="description" content="Eternal Haven Chronicles by Justin Helmer — Books I–IV lore lattice, free audio samples, Lulu storefront, Haven Star Chart, ClawHub lore pack." />
  <meta name="author" content="Justin Helmer / Excavationpro / Lightfather" />
  <link rel="canonical" href="https://deepseekoracle.github.io/Excavationpro/EternalHavenCodex.html" />
  <meta property="og:title" content="Eternal Haven Codex — Lattice Lore" />
  <meta property="og:description" content="Four books. One sky. Samples free. Full works on Lulu. Live on the Haven Star Chart." />
  <meta property="og:url" content="https://deepseekoracle.github.io/Excavationpro/EternalHavenCodex.html" />
  <meta property="og:image" content="https://deepseekoracle.github.io/Excavationpro/assets/og-haven-star-chart.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:site" content="@Excavationpro" />
  <meta name="lygo:signature" content="Δ9Φ963-ETERNAL-HAVEN-CODEX-v1" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=IBM+Plex+Sans:wght@300;400;600&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --bg:#07060f; --card:rgba(18,16,36,.82); --gold:#d4af37; --cyan:#00f0ff;
      --violet:#9b6dff; --text:#f0eef8; --muted:#9aa3bf; --line:rgba(0,240,255,.18);
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; font-family:"IBM Plex Sans",system-ui,sans-serif; color:var(--text);
      background:
        radial-gradient(900px 500px at 20% -10%, rgba(125,0,255,.22), transparent 55%),
        radial-gradient(700px 400px at 90% 10%, rgba(0,240,255,.12), transparent 50%),
        linear-gradient(180deg, #05040c, var(--bg) 40%, #04030a);
      min-height:100vh;
    }}
    a {{ color:var(--cyan); text-decoration:none; }}
    a:hover {{ color:var(--gold); }}
    .wrap {{ width:min(1100px, calc(100% - 2rem)); margin:0 auto; padding:1.5rem 0 3rem; }}
    header.hero {{
      border:1px solid var(--line); border-radius:18px; padding:1.5rem 1.4rem;
      background:var(--card); backdrop-filter:blur(10px);
      box-shadow:0 0 40px rgba(125,0,255,.12);
    }}
    h1 {{
      font-family:Cinzel,serif; margin:0 0 .5rem; font-size:clamp(1.6rem,4vw,2.4rem);
      background:linear-gradient(120deg,var(--gold),#fff 40%,var(--cyan));
      -webkit-background-clip:text; background-clip:text; color:transparent;
    }}
    .sub {{ color:var(--muted); max-width:46rem; line-height:1.55; }}
    .nav {{
      display:flex; flex-wrap:wrap; gap:.5rem; margin-top:1rem;
    }}
    .nav a {{
      border:1px solid var(--line); border-radius:999px; padding:.45rem .85rem;
      font-size:.82rem; color:var(--muted);
    }}
    .nav a.pri {{ border-color:rgba(212,175,55,.5); color:var(--gold); }}
    section {{ margin-top:2rem; }}
    h2.sec {{
      font-family:Cinzel,serif; font-size:1.1rem; letter-spacing:.06em;
      color:var(--gold); margin:0 0 .85rem;
    }}
    .grid {{
      display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:1rem;
    }}
    .card {{
      background:var(--card); border:1px solid var(--line); border-radius:14px;
      padding:1.1rem 1rem; min-height:12rem;
    }}
    .card .glyph {{ font-size:1.6rem; margin-bottom:.35rem; }}
    .card h3 {{ margin:0; font-size:.75rem; color:var(--violet); letter-spacing:.08em; text-transform:uppercase; }}
    .card h2 {{ margin:.25rem 0 .5rem; font-family:Cinzel,serif; font-size:1rem; line-height:1.3; }}
    .card p {{ margin:0; color:var(--muted); font-size:.9rem; line-height:1.45; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.85rem; }}
    .btn {{
      display:inline-block; border-radius:8px; padding:.45rem .7rem; font-size:.75rem;
      border:1px solid var(--line); color:var(--cyan);
    }}
    .btn.gold {{ border-color:rgba(212,175,55,.45); color:var(--gold); }}
    .sample {{
      display:grid; grid-template-columns:1fr; gap:.5rem;
      border:1px solid var(--line); border-radius:12px; padding:.85rem 1rem;
      background:rgba(8,8,18,.65); margin-bottom:.65rem;
    }}
    @media(min-width:720px) {{
      .sample {{ grid-template-columns:1fr auto; align-items:center; }}
    }}
    .sample audio {{ width:min(360px,100%); }}
    .meta {{ color:var(--muted); font-size:.75rem; margin-top:.15rem; }}
    .chips {{ display:flex; flex-wrap:wrap; gap:.45rem; }}
    .chip {{
      border:1px solid rgba(155,109,255,.35); border-radius:999px; padding:.35rem .7rem;
      font-size:.78rem; color:var(--text); background:rgba(125,0,255,.08);
    }}
    footer {{
      margin-top:2.5rem; padding-top:1rem; border-top:1px solid var(--line);
      color:var(--muted); font-size:.8rem; text-align:center;
    }}
    .note {{
      border-left:3px solid var(--gold); padding:.6rem .9rem; margin:1rem 0;
      background:rgba(212,175,55,.06); color:var(--muted); font-size:.88rem;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <h1>Eternal Haven Codex</h1>
      <p class="sub">
        Justin Helmer’s <strong style="color:var(--text)">Eternal Haven Chronicles</strong> (Books I–IV)
        live on the LYGO lattice — lore graph, Δ9 Star Chart constellation, ClawHub skill, and free
        <em>sample</em> audio for discovery. Full novels &amp; audiobooks remain steward-owned;
        purchase on Lulu when you want the whole sky.
      </p>
      <nav class="nav" aria-label="Lattice">
        <a class="pri" href="HavenStarChart.html">Haven Star Chart</a>
        <a href="https://clawhub.ai/deepseekoracle/skills/eternal-haven-lore-pack" target="_blank" rel="noopener">ClawHub Lore Pack</a>
        <a href="https://huggingface.co/datasets/DeepSeekOracle/eternal-haven-lore" target="_blank" rel="noopener">HF Lore Dataset</a>
        <a href="https://www.lulu.com/search?contributor=Justin+Helmer&page=1&pageSize=10&adult_audience_rating=00&sortBy=PRODUCT_SALES_90_DAYS" target="_blank" rel="noopener">Lulu store</a>
        <a href="https://eternalhaven.ca/" target="_blank" rel="noopener">eternalhaven.ca</a>
        <a href="https://asiancoastline.com/" target="_blank" rel="noopener">Music portal</a>
        <a href="https://chatagent.ca/" target="_blank" rel="noopener">Δ9 Council</a>
        <a href="https://linktr.ee/excavationpro" target="_blank" rel="noopener">Linktree</a>
        <a href="index.html">Lattice gateway</a>
      </nav>
    </header>

    <div class="note">
      <strong style="color:var(--gold)">Rights:</strong> Story &amp; characters © Justin Helmer.
      Samples are promotional (≤90s). Agents must not dump full books — summarize, quote sparingly, send readers here / Lulu.
      Signature: Δ9Φ963-ETERNAL-HAVEN-CODEX-v1 · generated {utc_now()[:19]}Z
    </div>

    <section>
      <h2 class="sec">Books I–IV</h2>
      <div class="grid">
        {book_cards()}
      </div>
    </section>

    <section>
      <h2 class="sec">Free audio samples</h2>
      <p class="sub" style="margin-top:0">Hosted on Hugging Face · not full audiobooks</p>
      {sample_rows() or "<p class='sub'>Samples encoding… re-run deploy.</p>"}
    </section>

    <section>
      <h2 class="sec">Heroes ↔ Δ9 champions (resonance)</h2>
      <div class="chips">
        {hero_chips()}
      </div>
      <p class="sub" style="margin-top:.85rem">
        Archetypal maps only — champions are not collapsed into book characters.
        Open the chart filter <strong>Eternal Haven</strong> to walk books and heroes as stars.
      </p>
    </section>

    <section>
      <h2 class="sec">Machine-readable</h2>
      <div class="actions">
        <a class="btn" href="https://huggingface.co/datasets/DeepSeekOracle/eternal-haven-lore/resolve/main/lore_graph.json" target="_blank" rel="noopener">lore_graph.json</a>
        <a class="btn" href="https://huggingface.co/datasets/DeepSeekOracle/eternal-haven-lore/resolve/main/books_manifest.json" target="_blank" rel="noopener">books_manifest.json</a>
        <a class="btn" href="https://huggingface.co/datasets/DeepSeekOracle/eternal-haven-lore/resolve/main/samples_index.json" target="_blank" rel="noopener">samples_index.json</a>
        <a class="btn" href="https://deepseekoracle.github.io/lygo-protocol-stack/data/eternal_haven/lore_graph.json" target="_blank" rel="noopener">Pages mirror graph</a>
      </div>
    </section>

    <footer>
      Steward: Justin Helmer · Excavationpro · Lightfather · DeepSeekOracle<br />
      Support (optional): <a href="https://www.paypal.com/paypalme/ExcavationPro">PayPal</a>
      · <a href="https://www.patreon.com/Excavationpro">Patreon</a><br />
      Δ9Φ963 — imperfect light · sealed promises · charted story · honest commerce
    </footer>
  </div>
</body>
</html>
"""
    out = STACK / "docs" / "EternalHavenCodex.html"
    out.write_text(html, encoding="utf-8")
    if EXCAV.is_dir():
        shutil.copy2(out, EXCAV / "EternalHavenCodex.html")
    print("[page]", out)
    return out


def wire_gateway() -> None:
    idx = EXCAV / "index.html"
    if not idx.is_file():
        return
    html = idx.read_text(encoding="utf-8")
    if "EternalHavenCodex.html" in html:
        print("[gateway] already linked")
        return
    card = """
          <a class="link-card" href="EternalHavenCodex.html">
            <span class="ic" aria-hidden="true">🌜</span>
            <span class="txt"><strong>Eternal Haven Codex</strong><small>Books I–IV · samples · chart</small></span>
          </a>
"""
    # insert near Eternal Haven if present
    if "eternalhaven.html" in html:
        html = html.replace(
            'href="eternalhaven.html"',
            'href="eternalhaven.html"',
            1,
        )
    if "Public hubs" in html or "link-grid" in html:
        # add after first link-grid open in creator section or hubs
        needle = "Eternal Haven Codex"
        if needle not in html:
            # after Music Codex gate if exists
            if "Music Codex" in html or "Listen Portal" in html:
                html = html.replace(
                    "</div>\n      </section>\n\n      <!-- LAYERS -->",
                    card + "\n        </div>\n      </section>\n\n      <!-- LAYERS -->",
                    1,
                )
            # simpler: inject into public hubs section
            if "id=\"hubs-title\"" in html:
                j = html.find('id="hubs-title"')
                k = html.find('<div class="link-grid">', j)
                if k > 0:
                    k = html.find(">", k) + 1
                    html = html[:k] + card + html[k:]
            elif "Music &amp; tools" in html or "music &amp; tools" in html.lower():
                pass
            # force before footer
            if "EternalHavenCodex.html" not in html:
                html = html.replace(
                    "<footer>",
                    f"""
      <section aria-labelledby="eh-codex">
        <div class="section-head"><h2 id="eh-codex">Eternal Haven</h2><p>Books on the lattice</p></div>
        <div class="link-grid">{card}</div>
      </section>
    <footer>
""",
                    1,
                )
    idx.write_text(html, encoding="utf-8")
    print("[gateway] EternalHavenCodex linked")


def clawhub_publish() -> None:
    pack = LORE_PACK
    if not (pack / "SKILL.md").is_file():
        print("[clawhub] pack missing")
        return
    cmd = [
        "npx",
        "--yes",
        "clawhub@latest",
        "publish",
        str(pack),
        "--slug",
        "eternal-haven-lore-pack",
        "--name",
        "Eternal Haven Lore Pack",
        "--changelog",
        "Lattice seed: lore_graph, star chart LORE_*/HERO_*, egg eternal-haven-lore-v1, HF samples + Codex page",
        "--tags",
        "latest,lore,eternal-haven,lygo",
        "--no-input",
    ]
    print("[clawhub]", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(STACK))
    print(r.stdout[-1500:] if r.stdout else "")
    print(r.stderr[-800:] if r.stderr else "")
    print("[clawhub] exit", r.returncode)


def main() -> int:
    print("=== samples ===")
    samples = build_samples()
    print("=== HF ===")
    try:
        publish_hf(samples)
    except Exception as e:
        print("[hf] ERROR", e)
        return 1
    print("=== codex page ===")
    write_codex_html(samples)
    # docs mirror samples index
    (STACK / "docs" / "data" / "eternal_haven").mkdir(parents=True, exist_ok=True)
    for name in ("samples_index.json", "lore_graph.json", "books_manifest.json"):
        s = DATA / name
        if s.is_file():
            shutil.copy2(s, STACK / "docs" / "data" / "eternal_haven" / name)
    wire_gateway()
    print("=== clawhub ===")
    clawhub_publish()
    print(json.dumps({"ok": True, "samples": len(samples), "hf": HF_REPO}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
