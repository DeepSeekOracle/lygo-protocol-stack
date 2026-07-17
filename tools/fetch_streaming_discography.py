#!/usr/bin/env python3
"""
Fetch full Excavationpro discography from public streaming APIs
(Deezer + iTunes) — Spotify artist HTML is JS-gated and incomplete.

Merges into excavationpro_catalog.json and rebuilds the music registry site.
Also records YouTube Music channel URL.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
SPOTIFY_ARTIST_ID = "6CkZ4bN2xu3WRKbjEL3u2S"
DEEZER_ARTIST_ID = 146004952
YOUTUBE_MUSIC = "https://music.youtube.com/@Excavationpro"
YOUTUBE_TOPIC = "https://www.youtube.com/channel/UCnCf9gjhMEfUFPvGkdlUabQ"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 "
    "Excavationpro-CatalogRecovery/2.0"
)


def http_get(url: str, timeout: int = 45) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json,text/html,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def http_json(url: str, timeout: int = 45) -> Any:
    return json.loads(http_get(url, timeout=timeout))


def norm_title(t: str) -> str:
    t = (t or "").lower().strip()
    t = re.sub(r"\s*[-–—]\s*single\s*$", "", t, flags=re.I)
    t = re.sub(r"\s*\(feat\.?[^)]*\)", "", t, flags=re.I)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def fetch_deezer_albums(artist_id: int = DEEZER_ARTIST_ID) -> list[dict[str, Any]]:
    albums: list[dict[str, Any]] = []
    url = f"https://api.deezer.com/artist/{artist_id}/albums?limit=100"
    page = 0
    while url:
        page += 1
        print(f"[deezer] page {page}: {url}", flush=True)
        data = http_json(url)
        for a in data.get("data") or []:
            albums.append(
                {
                    "source": "deezer",
                    "deezer_album_id": a.get("id"),
                    "title": a.get("title") or "",
                    "album_type": (a.get("record_type") or a.get("type") or "").lower(),
                    "date_published": a.get("release_date") or "",
                    "track_count": a.get("nb_tracks") or 0,
                    "cover": (a.get("cover_xl") or a.get("cover_big") or a.get("cover") or ""),
                    "deezer_url": a.get("link") or f"https://www.deezer.com/album/{a.get('id')}",
                    "explicit": bool(a.get("explicit_lyrics")),
                    "upc": "",
                    "spotify_album_id": None,
                    "spotify_url": None,
                    "tracks": [],
                }
            )
        url = data.get("next")
        time.sleep(0.25)
    print(f"[deezer] albums: {len(albums)}", flush=True)
    return albums


def enrich_deezer_album(row: dict[str, Any]) -> dict[str, Any]:
    aid = row.get("deezer_album_id")
    if not aid:
        return row
    try:
        data = http_json(f"https://api.deezer.com/album/{aid}")
    except Exception as e:
        print(f"  deezer album {aid} fail: {e}", flush=True)
        return row
    row["upc"] = data.get("upc") or row.get("upc") or ""
    row["track_count"] = data.get("nb_tracks") or row.get("track_count") or 0
    row["date_published"] = data.get("release_date") or row.get("date_published") or ""
    row["album_type"] = (data.get("record_type") or row.get("album_type") or "").lower()
    row["label"] = data.get("label") or ""
    tracks = []
    for t in (data.get("tracks") or {}).get("data") or []:
        tracks.append(
            {
                "title": t.get("title") or "",
                "deezer_track_id": t.get("id"),
                "duration": t.get("duration"),
                "explicit": bool(t.get("explicit_lyrics")),
                "track_position": t.get("track_position"),
                "deezer_url": t.get("link"),
            }
        )
    # if truncated, page tracks
    if row["track_count"] and len(tracks) < row["track_count"]:
        turl = f"https://api.deezer.com/album/{aid}/tracks?limit=100"
        while turl:
            try:
                td = http_json(turl)
            except Exception:
                break
            for t in td.get("data") or []:
                if any(x.get("deezer_track_id") == t.get("id") for x in tracks):
                    continue
                tracks.append(
                    {
                        "title": t.get("title") or "",
                        "deezer_track_id": t.get("id"),
                        "duration": t.get("duration"),
                        "explicit": bool(t.get("explicit_lyrics")),
                        "track_position": t.get("track_position"),
                        "deezer_url": t.get("link"),
                    }
                )
            turl = td.get("next")
            time.sleep(0.15)
    row["tracks"] = tracks
    if tracks:
        row["track_count"] = max(row.get("track_count") or 0, len(tracks))
    return row


def fetch_itunes_albums(term: str = "Excavationpro") -> list[dict[str, Any]]:
    albums: list[dict[str, Any]] = []
    # iTunes caps ~200 per query; use offset via attribute if needed
    url = (
        f"https://itunes.apple.com/search?term={quote(term)}"
        f"&entity=album&limit=200&country=US"
    )
    print(f"[itunes] {url}", flush=True)
    try:
        data = http_json(url)
    except Exception as e:
        print(f"[itunes] fail: {e}", flush=True)
        return albums
    for it in data.get("results") or []:
        # filter artist name tightly
        artist = (it.get("artistName") or "").lower()
        if "excavation" not in artist:
            continue
        albums.append(
            {
                "source": "itunes",
                "itunes_collection_id": it.get("collectionId"),
                "title": it.get("collectionName") or "",
                "album_type": "album",
                "date_published": (it.get("releaseDate") or "")[:10],
                "track_count": it.get("trackCount") or 0,
                "cover": it.get("artworkUrl100") or "",
                "itunes_url": it.get("collectionViewUrl") or "",
                "upc": "",
                "spotify_album_id": None,
                "spotify_url": None,
                "tracks": [],
            }
        )
    print(f"[itunes] albums (filtered): {len(albums)}", flush=True)
    return albums


def seed_known_spotify_ids() -> dict[str, str]:
    """title_norm -> spotify album id from known catalog + web harvest."""
    known = {
        # from existing catalog + public search results
        "wasteland sessions": "1PnOajhrqFRVwYBpkPSTn9",
        "math in the marrow": "03bLkjF4xhJ64Uh3Je0Iah",
        "midnight frequency": "03oi065qARTVnshQ9E9z04",
        "zero": "04X8iNXKnvU40jCgY1n1cl",
        "kingdom under teeth": "06iYuRomgh4EQgYXmcWeeF",
        "art of war codex": "6YWjA49tiYLY8WaEa6IOq3",
        "kenzie jade rooted": "0JcEisZRRpS6LgqWp5UwJ7",
        "virtually lethal volume 2": "5pLa0IHqOiYanSVgWfYM0t",
        "virtually lethal": "6OdhN6UNEN1GVMtlMVh9V2",
        "kenzie jade unfiltered": "0OZl0jQCrrqdyhxi7xcXWv",
        "street legend volume 6": "36XTI5nDYePiiLTVnEtuLS",
        "trauma codex volume 2": "0cDhiBiwG7bhkV6wVcSPyZ",
        "after the shocks": "1bi1Nw745MU3ULopvpnOeS",
        "after the shocks volume 2": "6Zw0brXCejHCHRw10N6hFt",
        "warning bells": "2vWr24HrNs4jEiIbP7u7qh",
        "fire that grows": "23q0LCWmWufmHiLxnrPfMA",
        "light i keep": "6p391dpEQdJxjpt2Drj6Yd",
        "fake sky": "1E4eqKGgck6z8S7s8vv83k",
        "vent": "6yxINwJTgTCLpsOdT6j1vW",
        "never thought id come up hits vol 1": "7MQgxYjRAlOe9TRDkRrEDW",
        "coastal": "6PaUXpPhejlidO3xI3r5vR",
        "it is what it is": "5AFBg0H0rxqJ9sAdGSmDun",
        "good vibes": "3pK6PoZjgdqtAjhDv9LFTy",
        "rest in peace": "3qVESlTWHw1JDzefBJXOvy",
        "turn it up": "0mZgjYjYTqXXbTyOAZnKRO",
        "ruins i call home": "1u1D71aTwdrzax0kejTat8",
        "mental state maze": "3mmXTxPhyX3Kb8GfaRaiRQ",
        "self care codex": "44GCWZFKTFZ4StkqV7ACLw",
        "street legend volume 3": "6WuYfOjae59TRPWjiLMiOL",
        "enock codex volume 1": "1J0mxyyKXtAvufkDYyiiJv",
        "mind blast": "0WeywLX8KseuqBd6HLworA",
        "chronic pain": "6ZTi6VzgRTJDYF4dlbYsv7",
        "sewing the shadows": "2p7abY1FZn0gohHkbumYAJ",
        "ink and kerosene": "0ZenzgHnJbveukJKWlTBvd",
        "aura debt": "2dtmIYPpny7LiKaV2dyQIV",
        "occupying space": "7KTOdcqSfUM7IkZa7xot1e",
        "blood bath": "42kDopXEh1xrDL8ay08W6q",
        "art of the ache": "4nTdS7LFdTTwe5G8homZ3b",
        "dark room": "5A3PtWZVVipWBjXC5k1Pgv",
    }
    # merge previous catalog spotify ids
    cat_path = CAT / "excavationpro_catalog.json"
    if cat_path.exists():
        cat = json.loads(cat_path.read_text(encoding="utf-8"))
        for a in cat.get("albums") or []:
            aid = a.get("spotify_album_id")
            title = a.get("title") or ""
            if aid and title:
                known[norm_title(title)] = aid
    return known


def merge_sources(
    deezer: list[dict],
    itunes: list[dict],
    spotify_map: dict[str, str],
) -> list[dict[str, Any]]:
    """Dedupe by normalized title; prefer Deezer detail + attach Spotify id when known."""
    by: dict[str, dict] = {}

    def upsert(row: dict, prefer_tracks: bool = False) -> None:
        key = norm_title(row.get("title") or "")
        if not key:
            return
        if key not in by:
            by[key] = dict(row)
            by[key]["sources"] = [row.get("source")] if row.get("source") else []
            return
        cur = by[key]
        srcs = set(cur.get("sources") or [])
        if row.get("source"):
            srcs.add(row["source"])
        cur["sources"] = sorted(srcs)
        # fill blanks
        for field in (
            "deezer_album_id",
            "deezer_url",
            "itunes_collection_id",
            "itunes_url",
            "upc",
            "cover",
            "date_published",
            "album_type",
            "label",
            "spotify_album_id",
            "spotify_url",
        ):
            if row.get(field) and not cur.get(field):
                cur[field] = row[field]
        if (row.get("track_count") or 0) > (cur.get("track_count") or 0):
            cur["track_count"] = row["track_count"]
        if prefer_tracks and row.get("tracks") and len(row["tracks"]) >= len(cur.get("tracks") or []):
            cur["tracks"] = row["tracks"]
        elif row.get("tracks") and not cur.get("tracks"):
            cur["tracks"] = row["tracks"]

    for a in deezer:
        upsert(a, prefer_tracks=True)
    for a in itunes:
        upsert(a)

    # attach spotify
    for key, row in by.items():
        aid = spotify_map.get(key)
        if aid:
            row["spotify_album_id"] = aid
            row["spotify_url"] = f"https://open.spotify.com/album/{aid}"
            srcs = set(row.get("sources") or [])
            srcs.add("spotify")
            row["sources"] = sorted(srcs)

    # also keep previous spotify-only albums not in deezer/itunes
    cat_path = CAT / "excavationpro_catalog.json"
    if cat_path.exists():
        cat = json.loads(cat_path.read_text(encoding="utf-8"))
        for a in cat.get("albums") or []:
            key = norm_title(a.get("title") or "")
            if not key:
                continue
            if key in by:
                if a.get("spotify_album_id") and not by[key].get("spotify_album_id"):
                    by[key]["spotify_album_id"] = a["spotify_album_id"]
                    by[key]["spotify_url"] = a.get("spotify_url") or by[key].get("spotify_url")
                if a.get("tracks") and not by[key].get("tracks"):
                    by[key]["tracks"] = a["tracks"]
            else:
                by[key] = {
                    "source": "spotify",
                    "sources": ["spotify"],
                    "title": a.get("title"),
                    "spotify_album_id": a.get("spotify_album_id"),
                    "spotify_url": a.get("spotify_url"),
                    "date_published": a.get("date_published"),
                    "track_count": a.get("track_count") or len(a.get("tracks") or []),
                    "tracks": a.get("tracks") or [],
                    "upc": a.get("upc") or "",
                    "album_type": a.get("album_type") or "",
                }

    out = sorted(
        by.values(),
        key=lambda x: (x.get("date_published") or "", x.get("title") or ""),
        reverse=True,
    )
    return out


def merge_into_catalog(albums: list[dict[str, Any]]) -> dict[str, Any]:
    cat_path = CAT / "excavationpro_catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else {"tracks": []}

    tracks = cat.get("tracks") or []
    by_title: dict[str, dict] = {}
    for t in tracks:
        k = norm_title(t.get("title") or "")
        if k:
            by_title.setdefault(k, t)

    added = 0
    for alb in albums:
        for tr in alb.get("tracks") or []:
            title = (tr.get("title") or "").strip()
            if not title:
                continue
            k = norm_title(title)
            if k in by_title:
                prev = by_title[k]
                srcs = set(prev.get("sources") or [])
                srcs.add("streaming")
                if alb.get("spotify_url") or tr.get("spotify_url"):
                    srcs.add("spotify")
                if alb.get("deezer_url") or tr.get("deezer_url"):
                    srcs.add("deezer")
                prev["sources"] = sorted(srcs)
                if not prev.get("album"):
                    prev["album"] = alb.get("title")
                if alb.get("spotify_url") and not prev.get("spotify_url"):
                    # album link as fallback listen
                    prev["spotify_url"] = alb.get("spotify_url")
                if alb.get("spotify_album_id") and not prev.get("spotify_album_id"):
                    prev["spotify_album_id"] = alb.get("spotify_album_id")
                if tr.get("deezer_url") and not prev.get("deezer_url"):
                    prev["deezer_url"] = tr.get("deezer_url")
                continue
            row = {
                "title": title,
                "artist": "Excavationpro",
                "album": alb.get("title"),
                "isrc": None,
                "upc": alb.get("upc"),
                "local_path": None,
                "filename": None,
                "spotify_url": alb.get("spotify_url"),
                "spotify_album_id": alb.get("spotify_album_id"),
                "deezer_url": tr.get("deezer_url") or alb.get("deezer_url"),
                "deezer_track_id": tr.get("deezer_track_id"),
                "sources": ["streaming", "deezer"],
            }
            if alb.get("spotify_album_id"):
                row["sources"].append("spotify")
            tracks.append(row)
            by_title[k] = row
            added += 1

    cat["tracks"] = tracks
    cat["albums"] = albums
    cat["album_count_spotify"] = sum(1 for a in albums if a.get("spotify_album_id"))
    cat["album_count_total"] = len(albums)
    cat["album_count_deezer"] = sum(1 for a in albums if a.get("deezer_album_id"))
    cat["track_count"] = len(tracks)
    cat["spotify_artist_id"] = SPOTIFY_ARTIST_ID
    cat["spotify_artist_url"] = f"https://open.spotify.com/artist/{SPOTIFY_ARTIST_ID}"
    cat["deezer_artist_id"] = DEEZER_ARTIST_ID
    cat["deezer_artist_url"] = f"https://www.deezer.com/artist/{DEEZER_ARTIST_ID}"
    cat["youtube_music"] = YOUTUBE_MUSIC
    cat["youtube_topic"] = YOUTUBE_TOPIC
    cat["discography_fetched_at"] = datetime.now(timezone.utc).isoformat()
    cat["discography_note"] = (
        "Full discography from Deezer API (mirrors DistroKid/streaming stores) + iTunes Search. "
        "Spotify artist page only surfaces a subset; YT Music @Excavationpro matches the wide catalog."
    )
    cat_path.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[merge] albums={len(albums)} tracks={len(tracks)} (+{added} streaming tracks)", flush=True)
    return cat


def write_albums_csv(albums: list[dict[str, Any]]) -> None:
    import csv

    path = CAT / "excavationpro_albums.csv"
    fields = [
        "title",
        "date_published",
        "track_count",
        "album_type",
        "upc",
        "spotify_album_id",
        "spotify_url",
        "deezer_album_id",
        "deezer_url",
        "itunes_url",
        "sources",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for a in albums:
            w.writerow(
                {
                    "title": a.get("title") or "",
                    "date_published": a.get("date_published") or "",
                    "track_count": a.get("track_count") or 0,
                    "album_type": a.get("album_type") or "",
                    "upc": a.get("upc") or "",
                    "spotify_album_id": a.get("spotify_album_id") or "",
                    "spotify_url": a.get("spotify_url") or "",
                    "deezer_album_id": a.get("deezer_album_id") or "",
                    "deezer_url": a.get("deezer_url") or "",
                    "itunes_url": a.get("itunes_url") or "",
                    "sources": ",".join(a.get("sources") or ([a.get("source")] if a.get("source") else [])),
                }
            )
    print(f"wrote {path}", flush=True)


def main() -> int:
    CAT.mkdir(parents=True, exist_ok=True)
    light = "--light" in sys.argv  # skip per-album track enrich (faster)

    deezer = fetch_deezer_albums()
    if not light:
        print(f"[deezer] enriching {len(deezer)} albums (tracks+UPC)…", flush=True)
        for i, row in enumerate(deezer):
            deezer[i] = enrich_deezer_album(row)
            if (i + 1) % 25 == 0 or i == 0:
                print(f"  enriched {i+1}/{len(deezer)}", flush=True)
            time.sleep(0.12)
    else:
        print("[deezer] light mode — skip per-album track fetch", flush=True)

    itunes = fetch_itunes_albums()
    spotify_map = seed_known_spotify_ids()
    albums = merge_sources(deezer, itunes, spotify_map)

    out = CAT / "streaming_discography_full.json"
    out.write_text(
        json.dumps(
            {
                "artist": "Excavationpro",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "album_count": len(albums),
                "deezer_count": sum(1 for a in albums if a.get("deezer_album_id")),
                "itunes_count": sum(1 for a in albums if a.get("itunes_collection_id")),
                "spotify_linked": sum(1 for a in albums if a.get("spotify_album_id")),
                "youtube_music": YOUTUBE_MUSIC,
                "youtube_topic": YOUTUBE_TOPIC,
                "spotify_artist": f"https://open.spotify.com/artist/{SPOTIFY_ARTIST_ID}",
                "deezer_artist": f"https://www.deezer.com/artist/{DEEZER_ARTIST_ID}",
                "albums": albums,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"wrote {out} albums={len(albums)}", flush=True)

    write_albums_csv(albums)
    merge_into_catalog(albums)

    # Patch site builder live links + stats field name for total albums
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_music_registry_site as site

    # monkey-enrich build payload after build for youtube music link
    payload = site.build()
    payload["live_links"]["youtube_music"] = YOUTUBE_MUSIC
    payload["live_links"]["youtube_topic"] = YOUTUBE_TOPIC
    payload["live_links"]["deezer_artist"] = f"https://www.deezer.com/artist/{DEEZER_ARTIST_ID}"
    payload["stats"]["streaming_albums_total"] = len(albums)
    payload["stats"]["spotify_albums_linked"] = sum(1 for a in albums if a.get("spotify_album_id"))
    payload["stats"]["deezer_albums"] = sum(1 for a in albums if a.get("deezer_album_id"))
    # replace spotify_albums list with full streaming list for UI
    payload["spotify_albums"] = [
        {
            "title": a.get("title"),
            "spotify_album_id": a.get("spotify_album_id"),
            "spotify_url": a.get("spotify_url") or a.get("deezer_url") or a.get("itunes_url"),
            "deezer_url": a.get("deezer_url"),
            "date_published": a.get("date_published"),
            "track_count": a.get("track_count"),
            "upc": a.get("upc"),
            "album_type": a.get("album_type"),
            "sources": a.get("sources") or [],
        }
        for a in albums
    ]
    payload["stats"]["spotify_albums"] = len(albums)  # UI card: all streaming albums

    # rewrite ledger hash core to include album titles
    core = json.dumps(
        {
            "restore_titles": sorted(r["title"] for r in (payload.get("restore_matched") or []) + (payload.get("restore_missing") or [])),
            "album_titles": sorted(a.get("title") or "" for a in albums),
            "isrcs": sorted((r.get("isrc_compact") or r.get("isrc") or "") for r in payload.get("isrc_registry") or []),
        },
        sort_keys=True,
    ).encode("utf-8")
    import hashlib

    payload["ledger"]["content_sha256"] = hashlib.sha256(core).hexdigest()
    payload["ledger"]["note"] = (
        "SHA-256 of restore titles + full streaming album titles + ISRC registry. "
        "Discography from Deezer/iTunes (YT Music parity)."
    )

    ledger_path = CAT / "excavationpro_music_ledger.json"
    ledger_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if site.EXCAV.exists():
        site.write_html(payload, site.EXCAV / "excavationpro-music-catalog.html")
        (site.EXCAV / "data").mkdir(exist_ok=True)
        (site.EXCAV / "data" / "excavationpro_music_ledger.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    site.write_html(payload, site.DOCS / "excavationpro-music-catalog.html")
    (site.DOCS / "excavationpro_music_ledger.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"SITE albums={len(albums)} matched={payload['stats'].get('matched_titles')} "
        f"have_spotify={payload['stats'].get('have_spotify')}",
        flush=True,
    )
    print(f"ledger {payload['ledger']['content_sha256'][:16]}…", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
