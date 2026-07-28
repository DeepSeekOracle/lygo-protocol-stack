#!/usr/bin/env python3
"""
Export public_stream_playlist.json → compact Parquet for agents / DuckDB / Pandas.

Why: HF auto-builds refs/convert/parquet for dataset viewer; we also ship a
steward-owned catalog parquet under catalog/ so queries stay fast without
loading the multi‑MB JSON.

Usage:
  python tools/export_music_playlist_parquet.py
  python tools/export_music_playlist_parquet.py --publish-hf
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
PLAYLIST = CAT / "public_stream_playlist.json"
OUT_DIR = CAT / "parquet"
OUT_PARQUET = OUT_DIR / "public_stream_playlist.parquet"
OUT_META = OUT_DIR / "public_stream_playlist_parquet_meta.json"
HF_REPO = "DeepSeekOracle/excavationpro-music-stream"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_rows(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tracks = data.get("tracks") or []
    rows: list[dict] = []
    for t in tracks:
        if not isinstance(t, dict):
            continue
        isrcs = t.get("isrcs") or []
        if isinstance(isrcs, str):
            isrcs = [isrcs]
        aliases = t.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        rows.append(
            {
                "sha256": str(t.get("sha256") or ""),
                "title": str(t.get("title") or ""),
                "artist": str(t.get("artist") or "Excavationpro"),
                "album": str(t.get("album") or ""),
                "moniker": str(t.get("moniker") or ""),
                "upc": str(t.get("upc") or t.get("distrokid_upc") or ""),
                "size": int(t.get("size") or 0),
                "stream_url": str(t.get("stream_url") or ""),
                "hf_path": str(t.get("hf_path") or ""),
                "isrcs": ",".join(str(x) for x in isrcs if x),
                "aliases": " | ".join(str(x) for x in aliases if x)[:500],
                "release_date": str(t.get("release_date") or ""),
                "label": str(t.get("label") or t.get("record_label") or ""),
            }
        )
    return rows


def write_parquet(rows: list[dict], dest: Path) -> dict:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as e:
        raise SystemExit("pyarrow required: pip install pyarrow") from e

    table = pa.Table.from_pylist(rows)
    dest.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, dest, compression="zstd")
    meta = {
        "signature": "Δ9Φ963-MUSIC-PLAYLIST-PARQUET-v1",
        "generated_at": utc_now(),
        "source": str(PLAYLIST.as_posix()),
        "rows": len(rows),
        "columns": table.column_names,
        "path": str(dest.as_posix()),
        "bytes": dest.stat().st_size,
        "hf_repo": HF_REPO,
        "hf_path": "catalog/public_stream_playlist.parquet",
        "hf_auto_parquet_branch": "refs/convert/parquet",
        "hf_auto_parquet_url": f"https://huggingface.co/datasets/{HF_REPO}/tree/refs%2Fconvert%2Fparquet",
        "usage": {
            "datasets": (
                "from datasets import load_dataset; "
                f"ds = load_dataset('{HF_REPO}', data_files='catalog/public_stream_playlist.parquet', split='train')"
            ),
            "pandas": f"import pandas as pd; df = pd.read_parquet('{dest.name}')",
            "duckdb": f"SELECT title, album, stream_url FROM read_parquet('{dest.name}') WHERE album ILIKE '%HOLLOW%';",
        },
    }
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def publish_hf(parquet_path: Path, meta_path: Path) -> None:
    from huggingface_hub import HfApi

    token = None
    for tp in (
        Path.home() / ".cache" / "huggingface" / "token",
        Path.home() / ".huggingface" / "token",
    ):
        if tp.is_file():
            token = tp.read_text(encoding="utf-8").strip()
            break
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(parquet_path),
        path_in_repo="catalog/public_stream_playlist.parquet",
        repo_id=HF_REPO,
        repo_type="dataset",
        commit_message="catalog: public_stream_playlist.parquet (agent/DuckDB index)",
    )
    api.upload_file(
        path_or_fileobj=str(meta_path),
        path_in_repo="catalog/public_stream_playlist_parquet_meta.json",
        repo_id=HF_REPO,
        repo_type="dataset",
        commit_message="catalog: parquet meta",
    )
    print("HF catalog parquet published")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--playlist", type=Path, default=PLAYLIST)
    ap.add_argument("--out", type=Path, default=OUT_PARQUET)
    ap.add_argument("--publish-hf", action="store_true")
    args = ap.parse_args()

    if not args.playlist.is_file():
        print("missing playlist", args.playlist)
        return 2
    rows = load_rows(args.playlist)
    meta = write_parquet(rows, args.out)
    print(json.dumps({k: meta[k] for k in ("rows", "bytes", "path", "hf_path")}, indent=2))
    # also mirror under docs/data for Pages agents
    docs_mirror = STACK / "docs" / "data" / "public_stream_playlist.parquet"
    try:
        docs_mirror.parent.mkdir(parents=True, exist_ok=True)
        docs_mirror.write_bytes(args.out.read_bytes())
        print("mirrored", docs_mirror)
    except OSError as e:
        print("docs mirror skip", e)

    if args.publish_hf:
        publish_hf(args.out, OUT_META)
    return 0


if __name__ == "__main__":
    # allow json print without import at top in meta
    import json

    raise SystemExit(main())
