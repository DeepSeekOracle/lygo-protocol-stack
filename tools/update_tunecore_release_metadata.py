#!/usr/bin/env python3
"""
Merge TuneCore release metadata (UPC / release_id / dates) into catalog + playlist.

Safe for listen portals: updates data only; optional surgical playlist inject via
safe_add_music_to_listen_portal.py --inject-playlist-only (call separately).

Does NOT redesign HTML.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
RELEASES = CAT / "tunecore_releases.json"
PLAYLIST = CAT / "public_stream_playlist.json"
ALBUMS_CSV = CAT / "excavationpro_albums.csv"
MATCH_REPORT = CAT / "tunecore_match_report.json"


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def norm(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def title_tokens(s: str) -> set[str]:
    stop = {"the", "a", "an", "feat", "ft", "and", "of", "in", "on", "to"}
    return {t for t in norm(s).split() if t and t not in stop}


def score_match(release_title: str, track_title: str, album: str) -> float:
    """Strict match — empty title/album must NEVER count as a hit."""
    rt = norm(release_title)
    tt = norm(track_title)
    al = norm(album)
    if not rt:
        return 0.0
    if tt and rt == tt:
        return 1.0
    if al and rt == al:
        return 1.0
    # substring only when both sides non-empty and meaningful length
    # Avoid generic single-word false positives (Memory, Eternal, etc.)
    if tt and len(tt) >= 8 and (rt in tt or (len(tt) >= 8 and tt in rt)):
        return 0.93
    if al and len(al) >= 8 and (rt in al or (len(al) >= 8 and al in rt)):
        return 0.91
    a = title_tokens(release_title)
    b = title_tokens(track_title) | title_tokens(album)
    if not a or not b:
        return 0.0
    # require at least 2 overlapping tokens OR full coverage of short release titles
    inter = len(a & b)
    if inter <= 0:
        return 0.0
    if len(a) == 1:
        # single-token releases are too ambiguous — demand exact token equality in title
        return 1.0 if tt and a.issubset(title_tokens(track_title)) and len(next(iter(a))) >= 5 else 0.0
    if len(a) == 2:
        # both tokens must appear (e.g. "moon man", "dies irae")
        return 0.95 if a.issubset(b) else 0.0
    return inter / len(a)


def load_releases() -> dict:
    return json.loads(RELEASES.read_text(encoding="utf-8"))


def save_playlist(pl: dict) -> None:
    pl["generated_at"] = utc()
    pl.setdefault("stats", {})["playlist_tracks"] = len(pl.get("tracks") or [])
    text = json.dumps(pl, indent=2, ensure_ascii=False) + "\n"
    for dest in (
        PLAYLIST,
        STACK / "docs" / "data" / "public_stream_playlist.json",
        Path(r"I:\E Drive\MUSIC_VAULT\manifest\public_stream_playlist.json"),
        Path(r"D:\asiancoastline\data\public_stream_playlist.json"),
        Path(r"D:\Excavationpro\data\public_stream_playlist.json"),
    ):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
        except OSError as e:
            print("[warn]", dest, e)


def upsert_albums_csv(releases: list[dict]) -> None:
    rows: list[dict] = []
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
        "release_id",
        "status",
        "distributor",
    ]
    existing: dict[str, dict] = {}
    if ALBUMS_CSV.is_file():
        with ALBUMS_CSV.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                existing[norm(r.get("title") or "")] = r
                rows.append(r)
    for rel in releases:
        key = norm(rel["title"])
        base = existing.get(key) or {k: "" for k in fields}
        base["title"] = rel["title"]
        base["date_published"] = rel.get("release_date") or base.get("date_published") or ""
        base["album_type"] = (rel.get("release_type") or base.get("album_type") or "").lower()
        if rel.get("upc"):
            base["upc"] = rel["upc"]
        base["release_id"] = rel.get("release_id") or ""
        base["status"] = rel.get("status") or ""
        base["distributor"] = "TuneCore"
        src = set(filter(None, (base.get("sources") or "").split("|")))
        src.add("tunecore_dashboard")
        base["sources"] = "|".join(sorted(src))
        if key in existing:
            existing[key].update(base)
        else:
            rows.append(base)
            existing[key] = base
    # rewrite with extended fields
    with ALBUMS_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-score", type=float, default=0.72)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    reg = load_releases()
    releases = reg.get("releases") or []
    pl = json.loads(PLAYLIST.read_text(encoding="utf-8"))
    tracks = pl.get("tracks") or []

    report = {
        "signature": "Delta9Phi963-TUNECORE-MATCH-REPORT-v1",
        "generated_utc": utc(),
        "min_score": args.min_score,
        "releases": [],
        "playlist_updates": 0,
    }

    for rel in releases:
        rtitle = rel["title"]
        matches = []
        for t in tracks:
            sc = score_match(rtitle, t.get("title") or "", t.get("album") or "")
            if sc >= args.min_score:
                matches.append((sc, t))
        matches.sort(key=lambda x: x[0], reverse=True)
        # Prefer high-confidence; for singles keep top few; for albums keep all decent
        kept = []
        for sc, t in matches:
            title_n = norm(t.get("title") or "")
            album_n = norm(t.get("album") or "")
            if not title_n and not album_n:
                continue
            if rel.get("release_type") == "Single":
                # Singles: title must clearly reference the release
                if sc >= 0.9:
                    kept.append((sc, t))
                elif "anthem" in norm(rtitle) and "human flaw anthem" in title_n:
                    kept.append((0.96, t))
                elif sc >= 0.85 and title_tokens(rtitle).issubset(title_tokens(t.get("title") or "")):
                    kept.append((sc, t))
            else:
                # Albums: album name match OR strong title containment
                if album_n and (norm(rtitle) == album_n or norm(rtitle) in album_n):
                    kept.append((max(sc, 0.95), t))
                elif sc >= 0.93:
                    kept.append((sc, t))
                # Moon Man: only tracks literally titled Moon Man (pending album)
                elif norm(rtitle) == "moon man" and title_n == "moon man":
                    kept.append((1.0, t))

        # Deduplicate by sha
        seen = set()
        uniq = []
        for sc, t in kept:
            sha = t.get("sha256")
            if sha in seen:
                continue
            seen.add(sha)
            uniq.append((sc, t))

        updated = []
        for sc, t in uniq:
            before = {
                "upc": t.get("upc"),
                "release_id": t.get("release_id"),
                "release_date": t.get("release_date"),
            }
            if not args.dry_run:
                if rel.get("upc"):
                    t["upc"] = rel["upc"]
                    t["distrokid_upc"] = rel["upc"]  # legacy field name used by tools
                    t["tunecore_upc"] = rel["upc"]
                t["release_id"] = rel.get("release_id")
                t["release_date"] = rel.get("release_date")
                t["release_type"] = rel.get("release_type")
                t["release_status"] = rel.get("status")
                t["distributor"] = "TuneCore"
                # Only set album when track already album-empty AND exact title match
                if (
                    rel.get("release_type") == "Album"
                    and not (t.get("album") or "").strip()
                    and norm(t.get("title") or "") == norm(rel["title"])
                ):
                    t["album"] = rel["title"]
            updated.append(
                {
                    "score": round(sc, 3),
                    "title": t.get("title"),
                    "album": t.get("album"),
                    "sha256": t.get("sha256"),
                    "before": before,
                    "upc": rel.get("upc"),
                    "release_id": rel.get("release_id"),
                }
            )
            report["playlist_updates"] += 1

        report["releases"].append(
            {
                "title": rtitle,
                "upc": rel.get("upc"),
                "release_id": rel.get("release_id"),
                "status": rel.get("status"),
                "match_count": len(updated),
                "matches": updated[:40],
            }
        )
        print(f"{rtitle}: matches={len(updated)} upc={rel.get('upc')} id={rel.get('release_id')}")

    if not args.dry_run:
        save_playlist(pl)
        upsert_albums_csv(releases)
        reg["updated_utc"] = utc()
        RELEASES.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
        # also mirror registry
        for dest in (
            STACK / "docs" / "data" / "tunecore_releases.json",
            Path(r"D:\asiancoastline\data\tunecore_releases.json"),
            Path(r"D:\Excavationpro\data\tunecore_releases.json"),
        ):
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
            except OSError:
                pass

    MATCH_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "playlist_updates": report["playlist_updates"], "report": str(MATCH_REPORT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
