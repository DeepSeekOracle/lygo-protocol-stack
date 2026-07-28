#!/usr/bin/env python3
"""
Add Linktree + Feature.fm (ffm.to) hubs to lattice data and main webpages.

Policy: asiancoastline first for listen page; Excavationpro index is separate gateway.
Does NOT redesign listen player — only NAV + lattice.sites + landing link cards.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
ASIAN = Path(r"D:\asiancoastline")
EXCAV = Path(r"D:\Excavationpro")

LINKTREE = "https://linktr.ee/excavationpro"
FFM = "https://ffm.to/eovnvo9"

# Canonical destinations resolved from hubs (2026-07-28)
HUB_LINKS = {
    "linktree": LINKTREE,
    "feature_fm": FFM,
    "feature_fm_smartlink": FFM,
    "spotify": "https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S",
    "apple_music": "https://music.apple.com/us/artist/excavationpro/1586588545",
    "tidal": "https://tidal.com/browse/artist/28494039",
    "deezer": "https://www.deezer.com/artist/146004952",
    "amazon_music": "https://music.amazon.ca/artists/B09GPD3K68/excavationpro",
    "youtube": "https://youtube.com/excavationpro",
    "youtube_music": "https://music.youtube.com/channel/UCnCf9gjhMEfUFPvGkdlUabQ",
    "beatstars": "https://www.beatstars.com/excavationpro",
    "beatstars_store": "https://excavationpro.beatstars.com",
    "audius": "https://audius.co/excavationpro",
    "instagram": "https://www.instagram.com/excavationpro/",
    "twitter": "https://twitter.com/ExcavationPro",
    "bluesky": "https://bsky.app/profile/excavationpro.bsky.social",
    "kick_live": "https://kick.com/excavationpro",
    "twitch_live": "https://twitch.tv/excavationpro",
    "rumble": "https://rumble.com/c/Excavationpro",
    "bpm_finder": "https://bpmfinder.ca/",
    "chatagent": "https://chatagent.ca/",
    "clawhub": "https://clawhub.ai/deepseekoracle",
    "eternalhaven_ca": "https://eternalhaven.ca/",
    "paypal": "https://www.paypal.com/paypalme/ExcavationPro",
    "merch_distrokid": "https://direct.distrokid.com/excavationpro/home",
    "lulu_books": "https://www.lulu.com/search?contributor=Justin+Helmer&adult_audience_rating=00&sortBy=PRODUCT_SALES_90_DAYS",
    "looperman": "https://www.looperman.com/users/profile/5711248",
    "linkedin": "https://www.linkedin.com/in/excavationpro/",
    "followmymusic": "http://Followmymusic.ca",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_lattice_hub_json() -> Path:
    out = STACK / "data" / "music_catalog" / "excavationpro_social_hubs.json"
    payload = {
        "signature": "Δ9Φ963-EXCAVATIONPRO-SOCIAL-HUBS-v1",
        "updated_utc": utc_now(),
        "steward": "Justin Helmer / Excavationpro / Lightfather",
        "hubs": {
            "linktree": {
                "url": LINKTREE,
                "role": "Official link-in-bio hub (all social + music + lattice)",
                "source": "https://linktr.ee/excavationpro",
            },
            "feature_fm": {
                "url": FFM,
                "role": "Smartlink — pick Spotify / Apple / Tidal / Deezer / Amazon / YouTube",
                "source": "https://ffm.to/eovnvo9",
                "artist": "Excavationpro",
            },
        },
        "resolved_destinations": HUB_LINKS,
        "notes": [
            "ffm.to/eovnvo9 is a Feature.fm smartlink chooser (not a single store).",
            "Linktree is the full bio hub; keep both on primary portals.",
            "Deploy listen-page changes to asiancoastline first; Excavationpro listen is backup.",
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    # docs mirror
    docs = STACK / "docs" / "data" / "excavationpro_social_hubs.json"
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("[ok]", out)
    return out


def patch_listen_html(path: Path) -> None:
    """Surgical: lattice.sites + NAV only. No player redesign."""
    html = path.read_text(encoding="utf-8")
    m = re.search(
        r'(<script id="boot" type="application/json">)(.*?)(</script>)',
        html,
        re.S,
    )
    if not m:
        raise RuntimeError(f"no boot in {path}")
    boot = json.loads(m.group(2))
    lat = boot.setdefault("lattice", {})
    sites = lat.setdefault("sites", {})
    # merge hubs (do not wipe existing)
    sites["linktree"] = LINKTREE
    sites["feature_fm"] = FFM
    sites["feature_fm_smartlink"] = FFM
    # fill useful missing destinations if empty
    for k, v in HUB_LINKS.items():
        if k in ("linktree", "feature_fm", "feature_fm_smartlink"):
            continue
        if not sites.get(k):
            sites[k] = v
    lat["sites"] = sites
    lat["social_hubs"] = {
        "linktree": LINKTREE,
        "feature_fm": FFM,
        "updated_utc": utc_now(),
    }
    new_boot = json.dumps(boot, ensure_ascii=False, separators=(",", ":"))
    html = html[: m.start(2)] + new_boot + html[m.end(2) :]

    # NAV: ensure Linktree + Feature.fm after Deezer block
    if "['Linktree'" not in html and '["Linktree"' not in html:
        html = html.replace(
            "  ['Feature.fm', SITES.feature_fm, ''],\n",
            "  ['Feature.fm', SITES.feature_fm || 'https://ffm.to/eovnvo9', ''],\n"
            "  ['Linktree', SITES.linktree || 'https://linktr.ee/excavationpro', ''],\n",
            1,
        )
    else:
        # still harden Feature.fm fallback
        html = html.replace(
            "['Feature.fm', SITES.feature_fm, '']",
            "['Feature.fm', SITES.feature_fm || 'https://ffm.to/eovnvo9', '']",
        )

    # Lattice tab list: add if pattern present
    if "['Feature.fm smartlink'" not in html and "Feature.fm smartlink" not in html:
        needle = "['Spotify artist', SITES.spotify],"
        if needle in html:
            html = html.replace(
                needle,
                needle
                + "\n    ['Feature.fm smartlink', SITES.feature_fm || 'https://ffm.to/eovnvo9'],"
                + "\n    ['Linktree hub', SITES.linktree || 'https://linktr.ee/excavationpro'],",
                1,
            )

    path.write_text(html, encoding="utf-8")
    print(f"[listen] patched {path} size={path.stat().st_size}")


def patch_excav_index(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    if "linktr.ee/excavationpro" in html and "ffm.to/eovnvo9" in html:
        print("[index] already has hubs")
        return
    card_block = """
          <a class="link-card" href="https://linktr.ee/excavationpro" rel="noopener noreferrer" target="_blank">
            <span class="ic" aria-hidden="true">🔗</span>
            <span class="txt"><strong>Linktree hub</strong><small>All social + music + lattice links</small></span>
          </a>
          <a class="link-card" href="https://ffm.to/eovnvo9" rel="noopener noreferrer" target="_blank">
            <span class="ic" aria-hidden="true">♪</span>
            <span class="txt"><strong>Feature.fm smartlink</strong><small>Spotify · Apple · Tidal · Deezer · more</small></span>
          </a>
"""
    # insert into creator / music tools section if present
    marker = "Lightfather · music &amp; tools"
    if marker in html:
        # find first link-grid after that section
        i = html.find(marker)
        j = html.find('<div class="link-grid">', i)
        if j > 0:
            k = html.find(">", j) + 1
            html = html[:k] + "\n" + card_block + html[k:]
        else:
            html = html.replace("</footer>", card_block + "\n    </footer>", 1)
    else:
        # top-nav
        if "Creator" in html or "Music" in html:
            html = html.replace(
                '<a href="excavationpro-listen.html">Music</a>',
                '<a href="excavationpro-listen.html">Music</a>\n'
                '        <a href="https://linktr.ee/excavationpro" rel="noopener">Linktree</a>\n'
                '        <a href="https://ffm.to/eovnvo9" rel="noopener">Smartlink</a>',
                1,
            )
        # also inject near end of main before footer
        if "linktr.ee/excavationpro" not in html:
            html = html.replace(
                "<footer>",
                """
      <section aria-labelledby="hubs-title">
        <div class="section-head">
          <h2 id="hubs-title">Public hubs</h2>
          <p>Linktree + Feature.fm smartlink</p>
        </div>
        <div class="link-grid">
"""
                + card_block
                + """
        </div>
      </section>
    <footer>
""",
                1,
            )
    path.write_text(html, encoding="utf-8")
    print(f"[index] patched {path}")


def main() -> int:
    write_lattice_hub_json()

    asian = ASIAN / "index.html"
    if asian.is_file():
        patch_listen_html(asian)
        # keep data copy
        src = STACK / "data" / "music_catalog" / "excavationpro_social_hubs.json"
        dest = ASIAN / "data" / "excavationpro_social_hubs.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    else:
        print("[warn] missing asian index")

    excav_index = EXCAV / "index.html"
    if excav_index.is_file():
        patch_excav_index(excav_index)

    # stack docs listen mirror (not primary deploy)
    docs_listen = STACK / "docs" / "excavationpro-listen.html"
    if docs_listen.is_file() and asian.is_file():
        # do not overwrite entire docs listen with asian if sizes differ wildly — only if sibling
        pass

    # MUSIC_PORTAL skill
    portal = Path(
        r"I:\E Drive\.grok\skills\lygo-excavationpro-music-lattice\references\MUSIC_PORTAL.json"
    )
    if portal.is_file():
        d = json.loads(portal.read_text(encoding="utf-8"))
        pub = d.setdefault("public", {})
        pub["linktree"] = LINKTREE
        pub["feature_fm"] = FFM
        pub["feature_fm_smartlink"] = FFM
        d.setdefault("streaming_discovery", {})["feature_fm"] = FFM
        d.setdefault("streaming_discovery", {})["linktree"] = LINKTREE
        portal.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
        print("[skill] MUSIC_PORTAL.json updated")

    print(
        json.dumps(
            {
                "ok": True,
                "linktree": LINKTREE,
                "feature_fm": FFM,
                "next": "git push asiancoastline only for listen; excav index optional",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
