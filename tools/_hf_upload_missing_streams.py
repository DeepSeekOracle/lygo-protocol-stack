"""Upload only missing stream/*.mp3 to HF dataset (skip already remote)."""
from __future__ import annotations
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from huggingface_hub import HfApi

REPO = "DeepSeekOracle/excavationpro-music-stream"
STREAM = Path(r"I:\E Drive\MUSIC_VAULT\public_stream")
CAT = Path(r"I:\E Drive\lygo-protocol-stack\data\music_catalog")
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
EXCAV = Path(r"I:\E Drive\Excavationpro")

def main() -> int:
    token = Path.home().joinpath(".cache/huggingface/token").read_text(encoding="utf-8").strip()
    api = HfApi(token=token)
    print("[hf] listing remote...", flush=True)
    files = list(api.list_repo_files(REPO, repo_type="dataset"))
    remote = {Path(f).name for f in files if f.startswith("stream/") and f.endswith(".mp3")}
    local = sorted(STREAM.glob("*.mp3"))
    missing = [p for p in local if p.name not in remote]
    print(f"[hf] local={len(local)} remote={len(remote)} missing={len(missing)}", flush=True)
    if not missing:
        print("[hf] nothing to upload", flush=True)
    else:
        # batch upload via upload_folder on a temp dir of only missing is heavy on disk.
        # use multi-commit upload_file in batches of 50
        batch = 40
        ok = fail = 0
        for i in range(0, len(missing), batch):
            chunk = missing[i:i+batch]
            print(f"[hf] batch {i//batch+1}/{(len(missing)+batch-1)//batch} size={len(chunk)}", flush=True)
            for p in chunk:
                try:
                    api.upload_file(
                        path_or_fileobj=str(p),
                        path_in_repo=f"stream/{p.name}",
                        repo_id=REPO,
                        repo_type="dataset",
                        token=token,
                        commit_message=f"stream {p.name[:12]}",
                    )
                    ok += 1
                except Exception as e:
                    fail += 1
                    print(f"[hf] FAIL {p.name}: {e}", flush=True)
            print(f"[hf] progress ok={ok} fail={fail} / {len(missing)}", flush=True)
        print(f"[hf] done ok={ok} fail={fail}", flush=True)

    # rewrite playlist public URLs
    base = f"https://huggingface.co/datasets/{REPO}/resolve/main/stream"
    pl_path = CAT / "public_stream_playlist.json"
    pl = json.loads(pl_path.read_text(encoding="utf-8"))
    pl["public_base_url"] = base
    pl["hf_dataset"] = f"https://huggingface.co/datasets/{REPO}"
    for t in pl.get("tracks") or []:
        sf = t.get("stream_file") or (t.get("sha256", "") + ".mp3")
        t["stream_url"] = f"{base}/{sf}"
        t["stream_file"] = sf
    pl_path.write_text(json.dumps(pl, indent=2, ensure_ascii=False), encoding="utf-8")
    (VAULT / "manifest").mkdir(parents=True, exist_ok=True)
    (VAULT / "manifest" / "public_stream_playlist.json").write_text(
        json.dumps(pl, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if EXCAV.exists():
        (EXCAV / "data").mkdir(exist_ok=True)
        (EXCAV / "data" / "public_stream_playlist.json").write_text(
            json.dumps(pl, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    # upload playlist
    api.upload_file(
        path_or_fileobj=str(pl_path),
        path_in_repo="public_stream_playlist.json",
        repo_id=REPO,
        repo_type="dataset",
        token=token,
        commit_message="playlist 10762 with public stream URLs",
    )
    print(f"[hf] playlist uploaded base={base}", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
