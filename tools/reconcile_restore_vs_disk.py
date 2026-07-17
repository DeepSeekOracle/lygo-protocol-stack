#!/usr/bin/env python3
"""
Reconcile DistroKid restore list against DONE ALBUM + HOME\\HOME on J:.
Aggressive title matching (exact / substring / token / fuzzy).
Updates catalog + rebuilds public ledger/site when --merge is set.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_music_registry_site import (  # noqa: E402
    RESTORE,
    parse_restore,
    build,
    write_html,
    CAT_DIR,
    EXCAV,
    DOCS,
    STACK,
)

DONE = Path(r"J:\ALL SOUND FILES\. KICK STREAM FOLDER\HOME\1 SOUNDCLOUD  DISTRO KID\0 DONE ALBUM")
HOME = Path(r"J:\ALL SOUND FILES\. KICK STREAM FOLDER\HOME\HOME")
AUDIO = {".mp3", ".wav", ".flac", ".m4a", ".aiff", ".aif", ".ogg", ".aac", ".wma"}
SKIP_DIR = (
    "\\windows\\",
    "\\$recycle",
    "\\node_modules",
    "\\.git\\",
    "apache-openoffice",
    "\\program files",
    "\\steam\\",
    "\\epic games",
)
# Real DistroKid-style compact codes in filenames
ISRC_IN_NAME = re.compile(
    r"(?i)(?:"
    r"QZ[A-Z0-9]{10}"
    r"|QM42K\d{7}"
    r"|QT[A-Z0-9]{10}"
    r")"
)
ISRC_DASHED = re.compile(r"(?i)QZ-?[A-Z0-9]{3}-?\d{2}-?\d{5}")


def norm(t: str) -> str:
    t = (t or "").lower().strip()
    t = re.sub(r"\(feat\.?[^)]*\)", "", t)
    t = re.sub(r"\(with[^)]*\)", "", t)
    t = re.sub(r"\b(feat|ft|featuring)\.?\s*", " ", t)
    t = re.sub(r"\bjustin helmer\b", " ", t)
    t = re.sub(r"\bexcavationpro\b", " ", t)
    t = re.sub(r"\b(hd|mastered|master|explicit|lyrics|radio edit|instrumental)\b", " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_isrcs_from_name(fn: str) -> list[str]:
    compact = fn.replace("-", "").replace("_", "").replace(" ", "")
    found = [m.group(0).upper() for m in ISRC_IN_NAME.finditer(compact)]
    for m in ISRC_DASHED.finditer(fn):
        found.append(re.sub(r"[^A-Za-z0-9]", "", m.group(0)).upper())
    # de-dupe
    out, seen = [], set()
    for x in found:
        if len(x) == 12 and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def title_from_fn(fn: str) -> str:
    stem = Path(fn).stem
    # strip leading hd_
    stem = re.sub(r"(?i)^hd[_ ]+", "", stem)
    for code in extract_isrcs_from_name(fn):
        stem = re.sub(re.escape(code), "", stem, flags=re.I)
        # also dashed form
        if len(code) == 12:
            dashed = f"{code[0:2]}-{code[2:5]}-{code[5:7]}-{code[7:12]}"
            stem = re.sub(re.escape(dashed), "", stem, flags=re.I)
    stem = re.sub(r"(?i)\b(feat|ft)\.?\s*justin\s*helmer\b", "", stem)
    stem = re.sub(r"[_\-]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip(" -_.")
    return stem


def scan_root(root: Path, label: str) -> list[dict]:
    rows: list[dict] = []
    if not root.exists():
        print(f"[warn] missing root {root}", flush=True)
        return rows
    print(f"[scan] {label}: {root}", flush=True)
    n_audio = 0
    for dirpath, dirnames, filenames in os.walk(root):
        low = dirpath.lower()
        if any(x in low for x in SKIP_DIR):
            dirnames[:] = []
            continue
        # prune openoffice etc. from dirnames
        dirnames[:] = [d for d in dirnames if "apache-openoffice" not in d.lower()]
        for fn in filenames:
            ext = Path(fn).suffix.lower()
            if ext not in AUDIO:
                continue
            n_audio += 1
            full = str(Path(dirpath) / fn)
            tg = title_from_fn(fn)
            isrcs = extract_isrcs_from_name(fn)
            rows.append(
                {
                    "root": label,
                    "path": full,
                    "filename": fn,
                    "title": tg,
                    "norm": norm(tg),
                    "isrcs": isrcs,
                    "album": Path(dirpath).name,
                    "extension": ext,
                }
            )
    print(f"[scan] {label}: {n_audio} audio files", flush=True)
    return rows


def best_match(key: str, by_n: dict[str, list], threshold: float = 0.72):
    if not key:
        return None, 0.0, None
    if key in by_n:
        return by_n[key][0], 1.0, key
    # substring (len>=5)
    best_row, best_s, best_k = None, 0.0, None
    for ck, ents in by_n.items():
        if not ck:
            continue
        if len(key) >= 5 and len(ck) >= 5:
            if key in ck or ck in key:
                s = 0.92 if min(len(key), len(ck)) / max(len(key), len(ck)) > 0.6 else 0.85
                if s > best_s:
                    best_s, best_row, best_k = s, ents[0], ck
                    continue
        # token overlap
        kt, ct = set(key.split()), set(ck.split())
        if len(kt) >= 2 and len(ct) >= 1:
            inter = kt & ct
            if len(inter) >= max(2, len(kt) - 1) or (len(inter) / max(len(kt), 1) >= 0.8):
                s = 0.8 + 0.15 * (len(inter) / max(len(kt | ct), 1))
                if s > best_s:
                    best_s, best_row, best_k = s, ents[0], ck
        s = SequenceMatcher(None, key, ck).ratio()
        if s > best_s:
            best_s, best_row, best_k = s, ents[0], ck
    if best_row and best_s >= threshold:
        return best_row, best_s, best_k
    return None, best_s, best_k


def main() -> int:
    merge = "--merge" in sys.argv
    files = scan_root(DONE, "DONE") + scan_root(HOME, "HOME")
    print(f"total audio: {len(files)}", flush=True)

    by_n: dict[str, list] = defaultdict(list)
    by_isrc: dict[str, list] = defaultdict(list)
    for f in files:
        if f["norm"]:
            by_n[f["norm"]].append(f)
        for code in f["isrcs"]:
            by_isrc[code].append(f)

    print(f"unique disk title keys: {len(by_n)}", flush=True)
    print(f"disk files with ISRC in name: {sum(1 for f in files if f['isrcs'])}", flush=True)
    print(f"unique disk ISRCs: {len(by_isrc)}", flush=True)

    restore = parse_restore(RESTORE)
    print(f"restore unique titles: {len(restore)}", flush=True)

    exact, fuzzy, isrc_hit, missing = [], [], [], []
    for r in restore:
        k = norm(r["title"])
        row = None
        score = 0.0
        how = None
        # 1) vault ISRC on disk (rare — QT usually not in old filenames)
        if r.get("isrc") and r["isrc"] in by_isrc:
            row = by_isrc[r["isrc"]][0]
            score = 1.0
            how = "isrc"
            isrc_hit.append((r, row))
        else:
            row, score, mk = best_match(k, by_n, threshold=0.72)
            if row and score >= 0.999:
                how = "exact"
                exact.append((r, row))
            elif row:
                how = "fuzzy"
                fuzzy.append((r, row, score, mk))
            else:
                missing.append(r)
                continue
        r["_match"] = {
            "how": how,
            "score": round(score, 3),
            "file": row["filename"],
            "path": row["path"],
            "disk_title": row["title"],
            "disk_isrcs": row["isrcs"],
            "root": row["root"],
            "album": row["album"],
        }

    found = len(exact) + len(fuzzy) + len(isrc_hit)
    # recount without double-count isrc already in exact
    # rebuild clean buckets from _match
    exact_n = sum(1 for r in restore if (r.get("_match") or {}).get("how") == "exact")
    fuzzy_n = sum(1 for r in restore if (r.get("_match") or {}).get("how") == "fuzzy")
    isrc_n = sum(1 for r in restore if (r.get("_match") or {}).get("how") == "isrc")
    miss_n = sum(1 for r in restore if not r.get("_match"))

    print(
        f"MATCH exact={exact_n} fuzzy={fuzzy_n} isrc={isrc_n} missing={miss_n} "
        f"coverage={exact_n + fuzzy_n + isrc_n}/{len(restore)} "
        f"({100 * (exact_n + fuzzy_n + isrc_n) / max(len(restore), 1):.1f}%)",
        flush=True,
    )

    hard = [r for r in restore if not r.get("_match")]
    print("Still not on disk (sample 40):", flush=True)
    for r in hard[:40]:
        print(f"  - {r['title']}  {r.get('isrc') or ''}", flush=True)

    report = {
        "done_path": str(DONE),
        "home_path": str(HOME),
        "total_audio": len(files),
        "unique_disk_titles": len(by_n),
        "unique_disk_isrcs": len(by_isrc),
        "restore_titles": len(restore),
        "exact": exact_n,
        "fuzzy": fuzzy_n,
        "isrc": isrc_n,
        "missing": miss_n,
        "coverage_pct": round(100 * (exact_n + fuzzy_n + isrc_n) / max(len(restore), 1), 2),
        "missing_titles": [
            {"title": r["title"], "isrc": r.get("isrc"), "date": r.get("date"), "source": r.get("source")}
            for r in hard
        ],
        "matched_sample": [
            {
                "title": r["title"],
                "how": r["_match"]["how"],
                "score": r["_match"]["score"],
                "file": r["_match"]["file"],
                "root": r["_match"]["root"],
            }
            for r in restore
            if r.get("_match")
        ][:50],
        "by_root_audio": {
            "DONE": sum(1 for f in files if f["root"] == "DONE"),
            "HOME": sum(1 for f in files if f["root"] == "HOME"),
        },
    }
    CAT_DIR.mkdir(parents=True, exist_ok=True)
    rep_path = CAT_DIR / "disk_reconcile_report.json"
    rep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {rep_path}", flush=True)

    miss_path = CAT_DIR / "restore_STILL_MISSING_after_disk_scan.txt"
    miss_path.write_text("\n".join(r["title"] for r in hard), encoding="utf-8")
    print(f"wrote {miss_path} ({len(hard)})", flush=True)

    # --- Merge matched disk rows into catalog ---
    cat_path = CAT_DIR / "excavationpro_catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else {"tracks": [], "albums": []}
    tracks = cat.get("tracks") or []

    # index existing by norm title + path
    existing_paths = {(t.get("local_path") or "").lower() for t in tracks}
    existing_norms = defaultdict(list)
    for t in tracks:
        existing_norms[norm(t.get("title") or "")].append(t)

    added = 0
    updated = 0
    for r in restore:
        m = r.get("_match")
        if not m:
            continue
        path = m["path"]
        ntitle = norm(r["title"])
        # update existing track with same path or same title
        hit = None
        for t in existing_norms.get(ntitle) or []:
            hit = t
            break
        if not hit:
            for t in tracks:
                if (t.get("local_path") or "").lower() == path.lower():
                    hit = t
                    break
        disk_isrc = (m.get("disk_isrcs") or [None])[0]
        vault_isrc = r.get("isrc")
        # prefer dashed local form if present
        isrc_val = None
        if disk_isrc and len(disk_isrc) == 12:
            isrc_val = f"{disk_isrc[0:2]}-{disk_isrc[2:5]}-{disk_isrc[5:7]}-{disk_isrc[7:12]}"
        elif vault_isrc:
            isrc_val = vault_isrc

        if hit:
            changed = False
            if not hit.get("local_path"):
                hit["local_path"] = path
                hit["filename"] = m["file"]
                changed = True
            if isrc_val and not hit.get("isrc"):
                hit["isrc"] = isrc_val
                changed = True
            if vault_isrc:
                hit.setdefault("vault_isrc", vault_isrc)
                changed = True
            srcs = set(hit.get("sources") or [])
            srcs.add("disk_reconcile")
            if m["root"] == "DONE":
                srcs.add("done_album")
            if m["root"] == "HOME":
                srcs.add("home_home")
            hit["sources"] = sorted(srcs)
            if changed:
                updated += 1
        else:
            if path.lower() in existing_paths:
                continue
            row = {
                "title": r["title"],
                "artist": r.get("artist") or "Excavationpro",
                "album": m.get("album"),
                "isrc": isrc_val,
                "vault_isrc": vault_isrc,
                "upc": None,
                "local_path": path,
                "filename": m["file"],
                "spotify_url": None,
                "sources": ["disk_reconcile", "done_album" if m["root"] == "DONE" else "home_home"],
                "match_how": m["how"],
                "match_score": m["score"],
            }
            tracks.append(row)
            existing_paths.add(path.lower())
            existing_norms[ntitle].append(row)
            added += 1

    print(f"catalog merge: added={added} updated={updated}", flush=True)
    cat["tracks"] = tracks
    cat["track_count"] = len(tracks)
    cat["tracks_with_isrc"] = sum(1 for t in tracks if t.get("isrc") or t.get("vault_isrc"))
    cat["disk_reconcile"] = {
        "done": str(DONE),
        "home": str(HOME),
        "exact": exact_n,
        "fuzzy": fuzzy_n,
        "isrc": isrc_n,
        "missing": miss_n,
        "coverage_pct": report["coverage_pct"],
        "added_rows": added,
        "updated_rows": updated,
    }
    if merge:
        cat_path.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {cat_path}", flush=True)

        # Rebuild site with improved matcher (use same norm + lower fuzzy)
        # Patch build matching by writing a side index file used by site builder
        index = {
            "by_title": {},
            "matches": {},
        }
        for r in restore:
            m = r.get("_match")
            if not m:
                continue
            index["matches"][norm(r["title"])] = m
        (CAT_DIR / "disk_title_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

        # Improve build_music_registry_site matching by re-running after we also
        # inject disk-only titles into a helper list the site builder already reads (tracks).
        payload = build()
        # Force-status fix from disk reconcile for any still-missing that we actually matched
        matched_keys = {norm(r["title"]) for r in restore if r.get("_match")}
        still_missing = []
        promote = []
        for row in payload.get("restore_missing") or []:
            if norm(row["title"]) in matched_keys:
                m = next(r["_match"] for r in restore if norm(r["title"]) == norm(row["title"]) and r.get("_match"))
                row["status"] = "have"
                row["has_local"] = True
                row["local_files"] = [m["file"]]
                if m.get("disk_isrcs"):
                    row["has_isrc"] = True
                    row.setdefault("isrcs", [])
                    for c in m["disk_isrcs"]:
                        if c not in row["isrcs"]:
                            row["isrcs"].append(c)
                if row.get("isrc") and row["isrc"] not in (row.get("isrcs") or []):
                    row.setdefault("isrcs", []).insert(0, row["isrc"])
                    row["has_isrc"] = True
                row["disk_root"] = m["root"]
                promote.append(row)
            else:
                still_missing.append(row)
        payload["restore_matched"] = (payload.get("restore_matched") or []) + promote
        payload["restore_missing"] = still_missing
        payload["stats"]["matched_titles"] = len(payload["restore_matched"])
        payload["stats"]["missing_titles"] = len(still_missing)
        payload["stats"]["disk_reconcile_coverage_pct"] = report["coverage_pct"]
        payload["stats"]["disk_audio_files"] = len(files)
        payload["disk_reconcile"] = report

        # rewrite outputs (mirror main())
        ledger_path = CAT_DIR / "excavationpro_music_ledger.json"
        ledger_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        if EXCAV.exists():
            write_html(payload, EXCAV / "excavationpro-music-catalog.html")
            (EXCAV / "data").mkdir(exist_ok=True)
            (EXCAV / "data" / "excavationpro_music_ledger.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        write_html(payload, DOCS / "excavationpro-music-catalog.html")
        (DOCS / "excavationpro_music_ledger.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (CAT_DIR / "restore_MISSING_titles.txt").write_text(
            "\n".join(r["title"] for r in still_missing), encoding="utf-8"
        )
        print(
            f"REBUILT site: matched={payload['stats']['matched_titles']} "
            f"missing={payload['stats']['missing_titles']}",
            flush=True,
        )
    else:
        print("Dry-run only. Pass --merge to update catalog + webpage.", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
