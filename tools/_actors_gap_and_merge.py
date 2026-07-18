#!/usr/bin/env python3
"""
I:\\Actors own-music gap check:
  1) List all audio under Actors
  2) Match vault by path and/or (size + basename) and SHA when needed
  3) Report missing; optional --merge only missing files into vault
  4) Optional --encode-missing for public streams (skips existing MP3)
No iPod / third-party. Dedup by SHA-256.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
ACTORS = Path(r"I:\Actors")
STREAM = VAULT / "public_stream"
AUDIO = {".mp3", ".wav", ".flac", ".m4a", ".aiff", ".aif", ".ogg", ".aac", ".wma", ".opus", ".m4b"}


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def list_actors() -> list[Path]:
    files: list[Path] = []
    if not ACTORS.exists():
        print(f"[err] missing {ACTORS}", flush=True)
        return files
    for dirpath, dirnames, filenames in os.walk(str(ACTORS)):
        low = dirpath.lower().replace("/", "\\")
        if any(x in low for x in ("\\ipod\\", "\\itunes\\", "\\node_modules", "\\$recycle")):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d.lower() not in ("ipod", "itunes", "node_modules")]
        for fn in filenames:
            if Path(fn).suffix.lower() in AUDIO:
                files.append(Path(dirpath) / fn)
    return files


def load_vault() -> tuple[dict, dict[str, dict]]:
    for p in (VAULT / "manifest" / "vault_index.json", CAT / "music_vault_index_full.json"):
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            by_hash: dict[str, dict] = {}
            for o in data.get("objects") or []:
                d = o.get("sha256")
                if d:
                    by_hash[d] = o
            print(f"[vault] {len(by_hash)} objects from {p}", flush=True)
            return data, by_hash
    return {}, {}


def main() -> int:
    do_merge = "--merge" in sys.argv
    do_encode = "--encode-missing" in sys.argv
    files = list_actors()
    print(f"[actors] audio files on disk: {len(files)}", flush=True)
    if not files:
        return 1

    data, by_hash = load_vault()

    # path map: lower path -> sha
    path_to_sha: dict[str, str] = {}
    size_name_to_sha: dict[tuple[int, str], str] = {}
    for o in by_hash.values():
        d = o["sha256"]
        sz = int(o.get("size") or 0)
        for p in o.get("paths") or []:
            path_to_sha[str(p).lower()] = d
        for fn in o.get("filenames") or []:
            size_name_to_sha[(sz, fn.lower())] = d

    present_path = 0
    present_size_name = 0
    need_hash: list[Path] = []
    already_sha: dict[str, Path] = {}

    for p in files:
        key = str(p).lower()
        try:
            st = p.stat()
        except OSError:
            continue
        if key in path_to_sha:
            present_path += 1
            already_sha[path_to_sha[key]] = p
            continue
        sn = (st.st_size, p.name.lower())
        if sn in size_name_to_sha:
            # likely same master elsewhere — treat as present (dedup)
            present_size_name += 1
            already_sha[size_name_to_sha[sn]] = p
            # still attach path on merge
            need_hash.append(p)  # will only add path if hash matches, or new if not
            continue
        need_hash.append(p)

    print(
        f"[match] path_exact={present_path} size+name_candidate={present_size_name} "
        f"to_verify={len(need_hash)}",
        flush=True,
    )

    missing_new: list[dict] = []
    path_attach: list[tuple[str, str]] = []  # sha, path
    errors = 0

    for i, p in enumerate(need_hash, 1):
        try:
            st = p.stat()
            digest = sha256_file(p)
        except OSError as e:
            errors += 1
            if errors <= 5:
                print(f"[err] {p}: {e}", flush=True)
            continue
        if digest in by_hash:
            # duplicate content already vaulted — just path alias
            path_attach.append((digest, str(p)))
        else:
            missing_new.append(
                {
                    "sha256": digest,
                    "path": str(p),
                    "size": st.st_size,
                    "name": p.name,
                    "ext": p.suffix.lower(),
                }
            )
        if i % 100 == 0 or i == len(need_hash):
            print(
                f"  verify {i}/{len(need_hash)} new_unique={len(missing_new)} "
                f"dup_attach={len(path_attach)}",
                flush=True,
            )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "actors_files": len(files),
        "path_exact_matches": present_path,
        "verified_new_unique": len(missing_new),
        "duplicate_content_path_attach": len(path_attach),
        "errors": errors,
        "missing_sample": missing_new[:30],
        "policy": "own_work_I_Actors_only",
    }
    CAT.mkdir(parents=True, exist_ok=True)
    out = CAT / "actors_gap_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n=== ACTORS GAP ===", flush=True)
    print(f"  on disk:     {len(files)}", flush=True)
    print(f"  already in vault (path): {present_path}", flush=True)
    print(f"  NEW unique hashes:       {len(missing_new)}", flush=True)
    print(f"  dups (attach path only): {len(path_attach)}", flush=True)
    print(f"  wrote {out}", flush=True)

    if not do_merge:
        print("Re-run with --merge to add missing (and path aliases).", flush=True)
        if do_encode:
            print("Encode skipped until merge (or run after).", flush=True)
        return 0

    # Merge into vault index
    changed = 0
    for digest, path in path_attach:
        row = by_hash.get(digest)
        if not row:
            continue
        paths = list(row.get("paths") or [])
        if path not in paths:
            paths.append(path)
            row["paths"] = paths
            changed += 1
        fn = Path(path).name
        fns = list(row.get("filenames") or [])
        if fn not in fns:
            fns.append(fn)
            row["filenames"] = fns

    for m in missing_new:
        digest = m["sha256"]
        if digest in by_hash:
            continue
        by_hash[digest] = {
            "sha256": digest,
            "size": m["size"],
            "ext": m["ext"],
            "title_guess": Path(m["name"]).stem,
            "commercial_title": None,
            "aliases": [Path(m["name"]).stem],
            "isrcs": [],
            "paths": [m["path"]],
            "filenames": [m["name"]],
            "cas_path": None,
            "mtime": datetime.now(timezone.utc).isoformat(),
            "steward_claim": "own_work",
            "source_root": "I:\\Actors",
        }
        changed += 1

    objects = list(by_hash.values())
    digests = sorted(o["sha256"] for o in objects if o.get("sha256"))

    def merkle(ds: list[str]) -> str:
        if not ds:
            return hashlib.sha256(b"").hexdigest()
        level = [bytes.fromhex(d) for d in ds]
        while len(level) > 1:
            nxt = []
            for i in range(0, len(level), 2):
                a = level[i]
                b = level[i + 1] if i + 1 < len(level) else a
                nxt.append(hashlib.sha256(a + b).digest())
            level = nxt
        return level[0].hex()

    root = merkle(digests)
    total_bytes = sum(int(o.get("size") or 0) for o in objects)
    data["objects"] = objects
    data["merkle_root"] = root
    data["actors_merge_at"] = datetime.now(timezone.utc).isoformat()
    stats = dict(data.get("stats") or {})
    stats["unique_objects"] = len(objects)
    stats["total_bytes"] = total_bytes
    stats["total_gb"] = round(total_bytes / 1e9, 3)
    stats["actors_new_this_merge"] = len(missing_new)
    stats["actors_path_attach"] = len(path_attach)
    data["stats"] = stats
    roots = list(data.get("scan_roots") or [])
    if r"I:\Actors" not in roots:
        roots.append(r"I:\Actors")
    data["scan_roots"] = roots

    for dest in (
        VAULT / "manifest" / "vault_index.json",
        CAT / "music_vault_index_full.json",
    ):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[wrote] {dest} objects={len(objects)}", flush=True)

    (CAT / "music_vault_merkle_root.txt").write_text(root + "\n", encoding="utf-8")
    (VAULT / "manifest" / "merkle_root.txt").write_text(root + "\n", encoding="utf-8")
    print(f"[merge] unique={len(objects)} new={len(missing_new)} path_attach={len(path_attach)} merkle={root[:16]}…", flush=True)

    if do_encode:
        # Encode only actors-related hashes missing stream files
        from tools.build_public_music_stream import encode_one, find_ffmpeg  # type: ignore

        # run encode via subprocess for whole vault is OK (skips existing)
        print("[encode] invoking build_public_music_stream --encode (skips existing)", flush=True)
        r = subprocess.run(
            [sys.executable, str(STACK / "tools" / "build_public_music_stream.py"), "--encode", "--workers", "3"],
            cwd=str(STACK),
        )
        print(f"[encode] exit={r.returncode}", flush=True)

    return 0


if __name__ == "__main__":
    # fix load_vault return bug - rewrite cleanly below if needed
    raise SystemExit(main())
