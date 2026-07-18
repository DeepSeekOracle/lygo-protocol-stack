#!/usr/bin/env python3
"""Remove iPod / third-party library objects from sovereign music vault.
Only keep Excavationpro / Haven / own-music paths — never J:\\IPOD.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
STREAM_DIR = VAULT / "public_stream"

# Path markers that are NOT your music (copyright / device dumps)
PURGE_PATH_RE = re.compile(
    r"(?i)(?:[/\\]|^)(?:IPOD|iPod|iTunes|Music\\Purchase|Amazon Music|Google Play Music)(?:[/\\]|$)"
)

# Also drop scan roots that should never be re-ingested
BLOCKED_ROOT_SUBSTR = ("IPOD", "iPod", "iTunes")


def is_purge_path(p: str) -> bool:
    if not p:
        return False
    if PURGE_PATH_RE.search(p.replace("/", "\\")):
        return True
    # explicit drive roots we refuse
    low = p.lower().replace("/", "\\")
    if "\\ipod\\" in low or low.rstrip("\\").endswith("\\ipod") or low.startswith("j:\\ipod"):
        return True
    return False


def object_is_ipod(o: dict) -> bool:
    for p in o.get("paths") or []:
        if is_purge_path(str(p)):
            return True
    for fn in o.get("filenames") or []:
        # only if path already tagged — bare filenames alone not enough
        pass
    return False


def merkle_root(digests: list[str]) -> str:
    if not digests:
        return hashlib.sha256(b"").hexdigest()
    level = [bytes.fromhex(d) if len(d) == 64 and all(c in "0123456789abcdef" for c in d.lower()) else hashlib.sha256(d.encode()).digest() for d in digests]
    # digests are already sha256 hex of files
    level = [bytes.fromhex(d) for d in digests]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else a
            nxt.append(hashlib.sha256(a + b).digest())
        level = nxt
    return level[0].hex()


def load_index(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_index(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path} objects={len(data.get('objects') or [])}", flush=True)


def main() -> int:
    sources = [
        VAULT / "manifest" / "vault_index.json",
        CAT / "music_vault_index_full.json",
        CAT / "music_vault_manifest.json",
    ]
    primary = None
    for p in sources:
        if p.exists():
            primary = p
            break
    if not primary:
        print("no vault index found", flush=True)
        return 1

    data = load_index(primary)
    objs = data.get("objects") or []
    kept = []
    purged = []
    for o in objs:
        if object_is_ipod(o):
            purged.append(o)
        else:
            # also strip any ipod path aliases from multi-path objects
            paths = [p for p in (o.get("paths") or []) if not is_purge_path(str(p))]
            if not paths and (o.get("paths") or []):
                purged.append(o)
                continue
            if paths:
                o = dict(o)
                o["paths"] = paths
            kept.append(o)

    digests = sorted({o["sha256"] for o in kept if o.get("sha256")})
    root = merkle_root(digests)

    roots = list(data.get("scan_roots") or [])
    roots = [r for r in roots if not any(b.lower() in r.lower() for b in BLOCKED_ROOT_SUBSTR)]

    total_bytes = sum(o.get("size") or 0 for o in kept)
    data["objects"] = kept
    data["scan_roots"] = roots
    data["merkle_root"] = root
    data["purged_at"] = datetime.now(timezone.utc).isoformat()
    data["purge_note"] = "Removed J:\\IPOD and third-party library paths — Excavationpro / Haven own music only"
    stats = dict(data.get("stats") or {})
    stats["unique_objects"] = len(kept)
    stats["total_bytes"] = total_bytes
    stats["total_gb"] = round(total_bytes / 1e9, 3)
    stats["purged_ipod_objects"] = len(purged)
    stats["purged_ipod_bytes"] = sum(o.get("size") or 0 for o in purged)
    stats["purged_ipod_gb"] = round(stats["purged_ipod_bytes"] / 1e9, 3)
    data["stats"] = stats

    print(
        f"kept={len(kept)} purged={len(purged)} "
        f"purged_gb={stats['purged_ipod_gb']} merkle={root[:16]}…",
        flush=True,
    )

    # write all known index locations
    for out in (
        VAULT / "manifest" / "vault_index.json",
        CAT / "music_vault_index_full.json",
    ):
        write_index(data, out)

    # public manifest: drop path details if present, keep hashes
    pub = {
        "signature": data.get("signature") or "Δ9Φ963-SOVEREIGN-MUSIC-VAULT-v1",
        "merkle_root": root,
        "generated_at": data.get("generated_at"),
        "purged_at": data["purged_at"],
        "stats": stats,
        "scan_roots": roots,
        "objects": [
            {
                "sha256": o.get("sha256"),
                "size": o.get("size"),
                "ext": o.get("ext"),
                "title": o.get("commercial_title") or o.get("title_guess"),
                "aliases": o.get("aliases") or [],
                "isrcs": o.get("isrcs") or [],
            }
            for o in kept
        ],
    }
    write_index(pub, CAT / "music_vault_manifest.json")
    (CAT / "music_vault_merkle_root.txt").write_text(root + "\n", encoding="utf-8")
    (VAULT / "manifest" / "merkle_root.txt").parent.mkdir(parents=True, exist_ok=True)
    (VAULT / "manifest" / "merkle_root.txt").write_text(root + "\n", encoding="utf-8")

    # Remove public stream MP3s for purged hashes (if any encoded)
    removed_streams = 0
    if STREAM_DIR.is_dir():
        for o in purged:
            d = o.get("sha256")
            if not d:
                continue
            f = STREAM_DIR / f"{d}.mp3"
            if f.is_file():
                try:
                    f.unlink()
                    removed_streams += 1
                except OSError as e:
                    print(f"[warn] stream unlink {f}: {e}", flush=True)
    print(f"removed public_stream files: {removed_streams}", flush=True)

    # Filter playlist if present
    for pl_path in (
        CAT / "public_stream_playlist.json",
        VAULT / "manifest" / "public_stream_playlist.json",
    ):
        if not pl_path.exists():
            continue
        pl = json.loads(pl_path.read_text(encoding="utf-8"))
        purged_set = {o.get("sha256") for o in purged if o.get("sha256")}
        before = len(pl.get("tracks") or [])
        pl["tracks"] = [t for t in (pl.get("tracks") or []) if t.get("sha256") not in purged_set]
        st = dict(pl.get("stats") or {})
        st["encoded_or_ready"] = len(pl["tracks"])
        st["purged_ipod_from_playlist"] = before - len(pl["tracks"])
        pl["stats"] = st
        pl_path.write_text(json.dumps(pl, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"playlist {pl_path.name}: {before} → {len(pl['tracks'])}", flush=True)

    report = {
        "purged_at": data["purged_at"],
        "kept": len(kept),
        "purged": len(purged),
        "purged_gb": stats["purged_ipod_gb"],
        "merkle_root": root,
        "blocked_roots": ["J:\\IPOD"],
        "note": "Own music + Haven books only. iPod / third-party libraries excluded.",
    }
    (CAT / "ipod_purge_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"report → {CAT / 'ipod_purge_report.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
