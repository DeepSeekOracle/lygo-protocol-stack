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
# Official Rumble live radio (publisher pub=1th29y)
RUMBLE_RADIO = (
    "https://rumble.com/v7cuiw2-content-you-can-digoriginal-music-radiocoffee-room-chat-lurk-friendly247-st.html"
    "?mref=1th29y&mc=2p3fp"
)
RUMBLE_EMBED = "https://rumble.com/embed/v7anxls/?pub=1th29y"
RUMBLE_VIDEO_ID = "v7anxls"
RUMBLE_CHANNEL = "https://rumble.com/user/Excavationpro"
OG_IMAGE = "https://deepseekoracle.github.io/Excavationpro/assets/og-haven-star-chart.jpg"
CANONICAL = "https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html"
LATTICE_STACK = "https://deepseekoracle.github.io/lygo-protocol-stack/"
PUBLIC_ARCHIVE = "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/LYGO_PUBLIC_LINK_ARCHIVE.json"


def norm(t: str) -> str:
    t = (t or "").lower().strip()
    t = re.sub(r"\(feat\.?[^)]*\)", "", t)
    t = re.sub(r"\(with[^)]*\)", "", t)
    t = re.sub(r"\b(feat|ft|featuring)\.?\s*", " ", t)
    t = re.sub(r"\bjustin helmer\b", " ", t)
    t = re.sub(r"\bexcavationpro\b", " ", t)
    t = re.sub(r"\b(hd|mastered|master|explicit|lyrics|radio edit)\b", " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# Compact ISRC: CC-XXX-YY-NNNNN without dashes (e.g. QT6EW2634453, QZS672411119)
ISRC_COMPACT_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{10}$")
# Dashed display form from local filenames (QZ-S67-24-11119)
ISRC_DASHED_RE = re.compile(r"^[A-Z]{2}-[A-Z0-9]{3}-\d{2}-\d{5}$", re.I)
DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}")
TRACK_NUM_RE = re.compile(r"^\d{1,4}$")
VAULT_UI = {
    "plain lyrics",
    "synced lyrics",
    "credits",
    "vizy",
    "audio swap",
    "download",
    "isrc",
    "lyrics",
    "explicit lyrics",
}


def is_isrc_code(s: str) -> bool:
    s = (s or "").strip().upper().replace(" ", "")
    if ISRC_COMPACT_RE.match(s):
        return True
    if ISRC_DASHED_RE.match(s):
        return True
    return False


def normalize_isrc(s: str) -> str:
    """Return compact uppercase ISRC (no dashes)."""
    s = (s or "").strip().upper().replace(" ", "").replace("-", "")
    return s if ISRC_COMPACT_RE.match(s) else (s or "")


def clean_vault_title(t: str) -> str:
    t = (t or "").strip()
    t = re.sub(r"\s+Explicit lyrics\s*$", "", t, flags=re.I).strip()
    t = re.sub(r"\s+Clean lyrics\s*$", "", t, flags=re.I).strip()
    return t


def parse_restore(path: Path) -> list[dict]:
    """
    Parse DistroKid restore export. Supports mixed formats:
    1) Vault export blocks: track# / title [Explicit lyrics] / UI rows / ISRC / QT…
    2) Legacy triples: title / artist / date  (or title / date)
    """
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = [ln.strip() for ln in raw]
    releases: list[dict] = []

    # --- Format 1: vault ISRC blocks (label "ISRC" then code) ---
    for i, ln in enumerate(lines):
        if ln.upper() != "ISRC":
            continue
        if i + 1 >= len(lines) or not is_isrc_code(lines[i + 1]):
            continue
        isrc = normalize_isrc(lines[i + 1])
        title = None
        for j in range(i - 1, max(-1, i - 25), -1):
            cand = lines[j]
            if not cand:
                continue
            low = cand.lower()
            if low in VAULT_UI:
                continue
            if TRACK_NUM_RE.match(cand):
                continue
            if is_isrc_code(cand):
                continue
            if DATE_RE.match(cand):
                continue
            if low == "excavationpro":
                continue
            title = clean_vault_title(cand)
            break
        if title:
            releases.append(
                {
                    "title": title,
                    "artist": "Excavationpro",
                    "date": "",
                    "isrc": isrc,
                    "source": "distrokid_vault",
                }
            )

    # --- Format 2: title / artist / date triples (and title / date) ---
    # Skip lines already consumed as vault UI / ISRCs / track numbers.
    vault_noise = set()
    for i, ln in enumerate(lines):
        if ln.upper() == "ISRC" and i + 1 < len(lines) and is_isrc_code(lines[i + 1]):
            vault_noise.add(i)
            vault_noise.add(i + 1)
            # mark UI + track# window above
            for j in range(max(0, i - 12), i):
                c = lines[j]
                if not c or c.lower() in VAULT_UI or TRACK_NUM_RE.match(c) or is_isrc_code(c):
                    vault_noise.add(j)
                # title line itself — still allow re-parse as triple only if no vault hit;
                # vault already captured it with ISRC, so mark title as used for triple skip via dedupe

    i = 0
    n = len(lines)
    while i < n:
        if i in vault_noise:
            i += 1
            continue
        title = lines[i]
        if not title or title.lower() in VAULT_UI or TRACK_NUM_RE.match(title) or is_isrc_code(title):
            i += 1
            continue
        if title.upper() == "ISRC":
            i += 1
            continue

        artist = lines[i + 1] if i + 1 < n else ""
        date = lines[i + 2] if i + 2 < n else ""

        # title / date (artist omitted)
        if DATE_RE.match(artist or ""):
            releases.append(
                {
                    "title": clean_vault_title(title),
                    "artist": "Excavationpro",
                    "date": artist,
                    "isrc": None,
                    "source": "restore_list",
                }
            )
            i += 2
            continue

        # title / artist / date
        if artist and DATE_RE.match(date or ""):
            # skip if artist looks like vault UI
            if artist.lower() in VAULT_UI or is_isrc_code(artist):
                i += 1
                continue
            releases.append(
                {
                    "title": clean_vault_title(title),
                    "artist": artist or "Excavationpro",
                    "date": date,
                    "isrc": None,
                    "source": "restore_list",
                }
            )
            i += 3
            continue

        i += 1

    # Dedupe by normalized title; prefer row with ISRC, then with date
    uniq: OrderedDict[str, dict] = OrderedDict()
    for r in releases:
        title = (r.get("title") or "").strip()
        if not title:
            continue
        k = norm(title)
        if not k:
            continue
        if k not in uniq:
            uniq[k] = r
            continue
        cur = uniq[k]
        if r.get("isrc") and not cur.get("isrc"):
            # keep dates/artist from existing if present
            merged = {**cur, **{kk: vv for kk, vv in r.items() if vv}}
            if cur.get("date") and not r.get("date"):
                merged["date"] = cur["date"]
            if cur.get("artist") and cur.get("artist") != "Excavationpro":
                merged["artist"] = cur["artist"]
            uniq[k] = merged
        elif r.get("date") and not cur.get("date"):
            cur["date"] = r["date"]
        elif r.get("isrc") and cur.get("isrc") and r["isrc"] != cur["isrc"]:
            # keep first; attach alternate
            alts = list(cur.get("alt_isrcs") or [])
            if r["isrc"] not in alts and r["isrc"] != cur["isrc"]:
                alts.append(r["isrc"])
            cur["alt_isrcs"] = alts
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

    # indexes (tracks + nested Spotify album tracks + cleaned filename stems)
    by_title: dict[str, list] = {}

    def _index(entry: dict, *extra_keys: str) -> None:
        keys = [norm(entry.get("title") or "")]
        keys.extend(extra_keys)
        for k in keys:
            if k:
                by_title.setdefault(k, []).append(entry)

    for t in tracks:
        fn = t.get("filename") or ""
        stem = Path(fn).stem if fn else ""
        # strip compact ISRC from stem for indexing
        stem_clean = re.sub(r"(?i)[A-Z]{2}[A-Z0-9]{10}", "", stem)
        stem_clean = re.sub(r"(?i)QZ-?[A-Z0-9]{3}-?\d{2}-?\d{5}", "", stem_clean)
        stem_clean = re.sub(r"(?i)^hd[_ ]+", "", stem_clean)
        _index(t, norm(stem), norm(stem_clean))

    for a in albums:
        album_meta = {
            "title": a.get("title"),
            "album": a.get("title"),
            "spotify_url": a.get("spotify_url"),
            "spotify_album_id": a.get("spotify_album_id"),
            "date_published": a.get("date_published"),
            "track_count": a.get("track_count"),
            "isrc": None,
            "sources": ["spotify_album"],
        }
        _index(album_meta)
        for tr in a.get("tracks") or []:
            _index(
                {
                    "title": tr.get("title"),
                    "album": a.get("title"),
                    "spotify_url": tr.get("spotify_url"),
                    "spotify_track_id": tr.get("spotify_track_id"),
                    "spotify_album_id": a.get("spotify_album_id"),
                    "isrc": tr.get("isrc"),
                    "local_path": tr.get("local_path"),
                    "filename": tr.get("filename"),
                    "sources": ["spotify_album_track"],
                }
            )

    # ISRC registry from local catalog files (QZ/QM dashed + compact)
    isrc_rows = []
    seen_isrc = set()
    for t in tracks:
        isrc = t.get("isrc")
        if not isrc:
            continue
        # store both display and compact keys for dedupe
        compact = normalize_isrc(isrc) if is_isrc_code(isrc) else (isrc or "").upper()
        key = compact or isrc
        if key in seen_isrc:
            continue
        seen_isrc.add(key)
        isrc_rows.append(
            {
                "title": t.get("title"),
                "isrc": isrc,
                "isrc_compact": compact or None,
                "upc": t.get("upc"),
                "album": t.get("album"),
                "local_path": t.get("local_path"),
                "filename": t.get("filename"),
                "spotify_url": t.get("spotify_url"),
                "source": "local_catalog",
            }
        )

    # Merge DistroKid vault ISRCs (QT* etc.) from restore list
    vault_isrc_count = 0
    for r in restore:
        isrc = r.get("isrc")
        if not isrc:
            continue
        compact = normalize_isrc(isrc)
        key = compact or isrc
        if key in seen_isrc:
            # enrich existing row title if blank
            continue
        seen_isrc.add(key)
        vault_isrc_count += 1
        isrc_rows.append(
            {
                "title": r.get("title"),
                "isrc": compact or isrc,
                "isrc_compact": compact or isrc,
                "upc": None,
                "album": None,
                "local_path": None,
                "filename": None,
                "spotify_url": None,
                "source": "distrokid_vault",
                "date": r.get("date") or None,
            }
        )
        for alt in r.get("alt_isrcs") or []:
            ak = normalize_isrc(alt) or alt
            if ak in seen_isrc:
                continue
            seen_isrc.add(ak)
            vault_isrc_count += 1
            isrc_rows.append(
                {
                    "title": r.get("title"),
                    "isrc": ak,
                    "isrc_compact": ak,
                    "upc": None,
                    "album": None,
                    "local_path": None,
                    "filename": None,
                    "spotify_url": None,
                    "source": "distrokid_vault",
                    "date": r.get("date") or None,
                }
            )

    isrc_rows.sort(key=lambda x: ((x.get("title") or "").lower(), x.get("isrc") or ""))

    matched = []
    missing = []
    title_keys = list(by_title.keys())

    def _fuzzy_lookup(k: str) -> tuple[str | None, float]:
        if not k:
            return None, 0.0
        best, score = None, 0.0
        for ck in title_keys:
            if not ck:
                continue
            # fast path: substring / token overlap
            if len(k) >= 5 and len(ck) >= 5 and (k in ck or ck in k):
                s = 0.9
            else:
                kt, ct = set(k.split()), set(ck.split())
                if len(kt) >= 2 and kt <= ct:
                    s = 0.88
                elif len(kt) >= 2 and len(kt & ct) >= max(2, len(kt) - 1):
                    s = 0.84
                else:
                    s = SequenceMatcher(None, k, ck).ratio()
            if s > score:
                score, best = s, ck
        return best, score

    for r in restore:
        k = norm(r["title"])
        entries = by_title.get(k) or []
        status = "missing"
        fuzzy = None
        if entries:
            status = "have"
        else:
            best, score = _fuzzy_lookup(k)
            if best and score >= 0.75:
                status = "fuzzy"
                fuzzy = {
                    "score": round(score, 3),
                    "matched_as": by_title[best][0].get("title"),
                    "key": best,
                }
                entries = by_title[best]

        restore_isrc = r.get("isrc")
        local_isrcs = list({e.get("isrc") for e in entries if e.get("isrc")})
        vault_isrcs = list({e.get("vault_isrc") for e in entries if e.get("vault_isrc")})
        isrcs = list(dict.fromkeys([*local_isrcs, *vault_isrcs]))
        if restore_isrc and restore_isrc not in isrcs:
            isrcs.insert(0, restore_isrc)
        for alt in r.get("alt_isrcs") or []:
            if alt not in isrcs:
                isrcs.append(alt)

        has_isrc = bool(isrcs)
        has_local = any(e.get("local_path") for e in entries)
        has_spotify = any(
            e.get("spotify_url") or e.get("spotify_track_id") or e.get("spotify_album_id") for e in entries
        )
        spotify_url = next(
            (e.get("spotify_url") for e in entries if e.get("spotify_url")),
            None,
        )
        local_files = list({e.get("filename") for e in entries if e.get("filename")})[:5]
        local_paths = list({e.get("local_path") for e in entries if e.get("local_path")})[:3]

        # Refine status for public ledger honesty
        if has_local and status in ("have", "fuzzy", "missing"):
            status = "have" if not fuzzy else "fuzzy"
        elif has_spotify and not has_local:
            status = "spotify_fuzzy" if fuzzy else "spotify"
        elif restore_isrc and not has_local and not has_spotify:
            status = "vault_isrc"
        elif not has_local and not has_spotify and not restore_isrc:
            status = "missing"

        row = {
            "title": r.get("title"),
            "artist": r.get("artist") or "Excavationpro",
            "date": r.get("date") or "",
            "isrc": restore_isrc,
            "source": r.get("source"),
            "status": status,
            "fuzzy": fuzzy,
            "has_isrc": has_isrc,
            "has_local": has_local,
            "has_spotify": has_spotify,
            "isrcs": isrcs,
            "spotify_url": spotify_url,
            "local_files": local_files,
            "local_paths": local_paths,
            "entry_count": len(entries),
        }
        # Matched = recoverable/known (local, spotify, or vault ISRC). Missing = no trace.
        if status == "missing":
            missing.append(row)
        elif status == "vault_isrc":
            # Known DistroKid code but no local master / Spotify hit yet — recovery gap
            missing.append(row)
        else:
            matched.append(row)

    restore_with_isrc = sum(1 for r in restore if r.get("isrc"))
    local_only_isrcs = sum(1 for r in isrc_rows if r.get("source") == "local_catalog")
    status_counts = {}
    for row in matched + missing:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    have_local_n = sum(1 for r in matched if r.get("has_local"))
    have_spotify_n = sum(1 for r in matched if r.get("has_spotify"))
    vault_only_n = sum(1 for r in missing if r.get("status") == "vault_isrc")
    true_missing_n = sum(1 for r in missing if r.get("status") == "missing")

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
            "rumble_embed": RUMBLE_EMBED,
            "rumble_channel": RUMBLE_CHANNEL,
            "lygo_stack_pages": LATTICE_STACK,
            "public_link_archive": PUBLIC_ARCHIVE,
            "music_catalog_page": CANONICAL,
            "og_image": OG_IMAGE,
        },
        "stats": {
            "restore_unique_titles": len(restore),
            "restore_with_vault_isrc": restore_with_isrc,
            "matched_titles": len(matched),
            "missing_titles": len(missing),
            "have_local_master": have_local_n,
            "have_spotify": have_spotify_n,
            "vault_isrc_only_no_file": vault_only_n,
            "true_missing_no_trace": true_missing_n,
            "status_counts": status_counts,
            "unique_isrcs_local": local_only_isrcs,
            "unique_isrcs_vault_added": vault_isrc_count,
            "unique_isrcs_total": len(isrc_rows),
            "spotify_albums": len(albums),
            "catalog_track_rows": len(tracks),
            "scan_roots_note": (
                r"DONE ALBUM + HOME\HOME on J: hold local masters (QZ/QM ISRCs in filenames). "
                "Newer DistroKid vault QT* titles often exist only on streaming / DistroKid until WAVs are re-downloaded."
            ),
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
            "restore_isrcs": sorted(r["isrc"] for r in restore if r.get("isrc")),
            "isrcs": sorted((r.get("isrc_compact") or r.get("isrc") or "") for r in isrc_rows),
            "spotify_albums": sorted(a.get("spotify_album_id") or "" for a in albums),
        },
        sort_keys=True,
    ).encode("utf-8")
    payload["ledger"] = {
        "content_sha256": hashlib.sha256(core).hexdigest(),
        "note": "SHA-256 of sorted restore titles + vault ISRCs + full ISRC registry + Spotify album IDs. Recompute after each catalog growth.",
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
<title>Excavationpro Music Catalog — Live Immutable Ledger | Official Discography</title>
<meta name="description" content="Official Excavationpro music catalog: searchable discography, ISRC ledger, Spotify albums, 24/7 live radio on Rumble, and SHA-256 immutable lattice ledger. Listen free — hip-hop, experimental, LYGO originals.">
<meta name="keywords" content="Excavationpro, Justin Helmer, music catalog, ISRC, Spotify, live radio, Rumble, LYGO, Eternal Haven, discography, independent artist, hip hop, immutable ledger">
<meta name="author" content="Justin Helmer / Excavationpro / Lightfather">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="googlebot" content="index, follow">
<meta name="theme-color" content="#0a0a12">
<link rel="canonical" href="{CANONICAL}">
<link rel="alternate" href="{CANONICAL}" title="Excavationpro Music Catalog">
<link rel="sitemap" type="application/xml" title="Sitemap" href="https://deepseekoracle.github.io/Excavationpro/sitemap.xml">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="Excavationpro / Eternal Haven">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="Excavationpro Music Catalog — Live Immutable Ledger">
<meta property="og:description" content="Searchable discography, ISRC codes, Spotify albums, and 24/7 live radio. Public lattice-anchored music ledger.">
<meta property="og:url" content="{CANONICAL}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:alt" content="Excavationpro / LYGO Eternal Haven">

<!-- X / Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@Excavationpro">
<meta name="twitter:creator" content="@Excavationpro">
<meta name="twitter:title" content="Excavationpro Music Catalog — Live Immutable Ledger">
<meta name="twitter:description" content="Official catalog · ISRCs · Spotify · 24/7 Rumble live radio · immutable ledger.">
<meta name="twitter:image" content="{OG_IMAGE}">
<meta name="twitter:url" content="{CANONICAL}">

<!-- JSON-LD: MusicGroup + WebPage + ItemList (Google) -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "MusicGroup",
      "@id": "{CANONICAL}#artist",
      "name": "Excavationpro",
      "alternateName": ["Justin Helmer", "Lightfather"],
      "url": "{CANONICAL}",
      "sameAs": [
        "{SPOTIFY_ARTIST}",
        "{FFM}",
        "{RUMBLE_CHANNEL}",
        "https://twitter.com/Excavationpro",
        "https://instagram.com/Excavationpro",
        "https://excavationpro.ca/",
        "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html"
      ],
      "genre": ["Hip Hop", "Experimental", "Electronic"],
      "description": "Independent artist Excavationpro — original music, LYGO-tagged releases, and 24/7 live radio."
    }},
    {{
      "@type": "WebPage",
      "@id": "{CANONICAL}",
      "url": "{CANONICAL}",
      "name": "Excavationpro Music Catalog — Live Immutable Ledger",
      "description": "Public searchable music catalog with ISRC ledger, Spotify albums, and live radio.",
      "isPartOf": {{
        "@type": "WebSite",
        "name": "Eternal Haven / Excavationpro",
        "url": "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html"
      }},
      "about": {{"@id": "{CANONICAL}#artist"}},
      "primaryImageOfPage": {{"@type": "ImageObject", "url": "{OG_IMAGE}"}}
    }},
    {{
      "@type": "BroadcastEvent",
      "name": "Excavationpro 24/7 Live Radio",
      "isLiveBroadcast": true,
      "videoFormat": "HD",
      "publishedOn": {{
        "@type": "BroadcastService",
        "name": "Rumble",
        "url": "{RUMBLE_RADIO}"
      }},
      "url": "{RUMBLE_EMBED}"
    }}
  ]
}}
</script>
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
      <h3 style="margin:0 0 10px;color:var(--gold);">Live stream — 24/7 radio</h3>
      <!-- Official Rumble monetized embed: video v7anxls / pub 1th29y -->
      <div class="embed-wrap" id="rumble_live_wrap">
        <div id="rumble_v7anxls" style="width:100%;height:100%;min-height:280px;"></div>
      </div>
      <p class="sub" style="margin-top:10px;">
        <a href="{RUMBLE_RADIO}" target="_blank" rel="noopener">Open on Rumble (monetized)</a>
        · <a href="{RUMBLE_EMBED}" target="_blank" rel="noopener">Pop-out player</a>
        · <a href="{RUMBLE_CHANNEL}" target="_blank" rel="noopener">@Excavationpro channel</a>
      </p>
    </div>
    <script src="https://rumble.com/embedJS/u1th29y"></script>
    <script>
    (function() {{
      function playRumble() {{
        if (typeof Rumble === "function") {{
          try {{
            Rumble("play", {{"video":"v7anxls","div":"rumble_v7anxls"}});
            return;
          }} catch (e) {{}}
        }}
        var w = document.getElementById("rumble_live_wrap");
        if (w) {{
          w.innerHTML = '<iframe src="https://rumble.com/embed/v7anxls/?pub=1th29y" title="Excavationpro 24/7 Live Radio" allowfullscreen allow="autoplay; encrypted-media; picture-in-picture" style="position:absolute;inset:0;width:100%;height:100%;border:0;" loading="lazy" referrerpolicy="origin-when-cross-origin"><\\/iframe>';
        }}
      }}
      if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", playRumble);
      else playRumble();
      setTimeout(function() {{
        var el = document.getElementById("rumble_v7anxls");
        if (el && !el.querySelector("iframe") && !el.querySelector("video") && el.childElementCount === 0) playRumble();
      }}, 2500);
    }})();
    </script>
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
  const isrcs = s.unique_isrcs_total || s.unique_isrcs_local || (DATA.isrc_registry || []).length;
  const vault = s.restore_with_vault_isrc || 0;
  const localM = s.have_local_master || allReleases().filter(r => r.has_local).length;
  const spotifyN = s.have_spotify || allReleases().filter(r => r.has_spotify || r.spotify_url).length;
  const gap = s.vault_isrc_only_no_file || 0;
  const unknown = s.true_missing_no_trace || 0;
  $('#stats').innerHTML = [
    ['Releases', total],
    ['Local masters', localM],
    ['On Spotify', spotifyN],
    ['ISRCs on ledger', isrcs],
    ['Vault ISRCs', vault],
    ['Need re-download', gap],
    ['No trace yet', unknown],
    ['Spotify albums', s.spotify_albums || 0],
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
  const rows = (DATA.isrc_registry||[]).filter(r => rowMatch([r.isrc,r.title,r.album,r.filename,r.source].join(' ')));
  $('#tb-isrc').innerHTML = rows.map(r => {{
    const src = r.source === 'distrokid_vault' ? '<span class="badge live">vault</span>' : (r.album ? esc(r.album) : '<span class="badge catalog">local</span>');
    return `
    <tr>
      <td><span class="badge isrc">${{esc(r.isrc)}}</span></td>
      <td>${{esc(r.title||'')}}</td>
      <td>${{src}}</td>
    </tr>`;
  }}).join('') || '<tr><td colspan="3">No ISRCs</td></tr>';
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
| Titles with DistroKid vault ISRC (QT*) | {s.get('restore_with_vault_isrc', 0)} |
| Known / matched (local or Spotify) | {s['matched_titles']} |
| Local masters found | {s.get('have_local_master', 0)} |
| On Spotify (no local or with) | {s.get('have_spotify', 0)} |
| Vault ISRC only (no local file — re-download) | {s.get('vault_isrc_only_no_file', 0)} |
| **No local / Spotify / ISRC trace** | **{s.get('true_missing_no_trace', s['missing_titles'])}** |
| Unique ISRCs from J: filenames | {s['unique_isrcs_local']} |
| Vault ISRCs newly on ledger | {s.get('unique_isrcs_vault_added', 0)} |
| **Total unique ISRCs on ledger** | **{s.get('unique_isrcs_total', s['unique_isrcs_local'])}** |
| Spotify albums (public page) | {s['spotify_albums']} |

### Why DONE ALBUM / HOME are not 100%
Those folders were fully scanned. Local masters there use older **QZ/QM** ISRCs in filenames.
Many DistroKid vault rows use newer **QT*** codes and exist on streaming only until WAVs are saved again.
See `restore_NO_LOCAL_FILE.txt` and `restore_STILL_MISSING_after_disk_scan.txt`.

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

    # snapshot restore source + vault ISRC export for recovery
    try:
        if RESTORE.exists():
            (CAT_DIR / "All_music_Restore.txt").write_bytes(RESTORE.read_bytes())
            print("copied restore snapshot ->", CAT_DIR / "All_music_Restore.txt")
    except OSError as e:
        print("warn: could not copy restore file:", e)

    vault_csv = CAT_DIR / "excavationpro_vault_isrcs.csv"
    vault_lines = ["title,isrc,source"]
    for r in payload.get("isrc_registry") or []:
        if r.get("source") != "distrokid_vault":
            continue
        title = (r.get("title") or "").replace('"', '""')
        vault_lines.append(f'"{title}",{r.get("isrc") or ""},distrokid_vault')
    vault_csv.write_text("\n".join(vault_lines) + "\n", encoding="utf-8")
    print("wrote", vault_csv)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
