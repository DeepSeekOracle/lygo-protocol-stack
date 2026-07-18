"""Bulk-upload missing stream MP3s to HF (upload_large_folder under stream/)."""
from __future__ import annotations
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi

REPO = "DeepSeekOracle/excavationpro-music-stream"
STREAM = Path(r"I:\E Drive\MUSIC_VAULT\public_stream")
CAT = Path(r"I:\E Drive\lygo-protocol-stack\data\music_catalog")
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
EXCAV = Path(r"I:\E Drive\Excavationpro")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    token = Path.home().joinpath(".cache/huggingface/token").read_text(encoding="utf-8").strip()
    api = HfApi(token=token)

    print("[hf] listing remote streams...", flush=True)
    files = list(api.list_repo_files(REPO, repo_type="dataset"))
    remote = {Path(f).name for f in files if f.startswith("stream/") and f.endswith(".mp3")}
    local = sorted(STREAM.glob("*.mp3"))
    missing = [p for p in local if p.name not in remote]
    print(f"[hf] local={len(local)} remote={len(remote)} missing={len(missing)}", flush=True)

    if missing:
        # layout: stage/stream/*.mp3 so paths land as stream/xxx.mp3
        stage_root = Path(tempfile.mkdtemp(prefix="hf_bulk_root_"))
        stage = stage_root / "stream"
        stage.mkdir(parents=True)
        print(f"[hf] staging {len(missing)} under {stage}", flush=True)
        for i, p in enumerate(missing, 1):
            dest = stage / p.name
            try:
                os.link(p, dest)
            except OSError:
                shutil.copy2(p, dest)
            if i % 500 == 0 or i == len(missing):
                print(f"[hf] staged {i}/{len(missing)}", flush=True)

        print("[hf] upload_large_folder starting (resumable, multi-worker)...", flush=True)
        try:
            api.upload_large_folder(
                repo_id=REPO,
                folder_path=str(stage_root),
                repo_type="dataset",
                num_workers=6,
                print_report=True,
                print_report_every=60,
            )
        except TypeError as e:
            print(f"[hf] large_folder signature issue ({e}); upload_folder fallback", flush=True)
            api.upload_folder(
                folder_path=str(stage),
                path_in_repo="stream",
                repo_id=REPO,
                repo_type="dataset",
                token=token,
                commit_message=f"Add {len(missing)} public stream MP3s (160k)",
            )
        except Exception as e:
            print(f"[hf] large_folder error ({e}); upload_folder fallback", flush=True)
            api.upload_folder(
                folder_path=str(stage),
                path_in_repo="stream",
                repo_id=REPO,
                repo_type="dataset",
                token=token,
                commit_message=f"Add {len(missing)} public stream MP3s (160k)",
            )
        print("[hf] cleaning stage...", flush=True)
        shutil.rmtree(stage_root, ignore_errors=True)
    else:
        print("[hf] no missing streams", flush=True)

    files2 = list(api.list_repo_files(REPO, repo_type="dataset"))
    remote2 = [f for f in files2 if f.startswith("stream/") and f.endswith(".mp3")]
    print(f"[hf] remote_stream_mp3 now={len(remote2)}", flush=True)

    base = f"https://huggingface.co/datasets/{REPO}/resolve/main/stream"
    pl_path = CAT / "public_stream_playlist.json"
    pl = json.loads(pl_path.read_text(encoding="utf-8"))
    pl["public_base_url"] = base
    pl["hf_dataset"] = f"https://huggingface.co/datasets/{REPO}"
    pl["published_at"] = utc_now()
    pl.setdefault("stats", {})["remote_streams"] = len(remote2)
    for t in pl.get("tracks") or []:
        sf = t.get("stream_file") or ((t.get("sha256") or "") + ".mp3")
        t["stream_file"] = sf
        t["stream_url"] = f"{base}/{sf}"
    text = json.dumps(pl, indent=2, ensure_ascii=False)
    pl_path.write_text(text, encoding="utf-8")
    (VAULT / "manifest").mkdir(parents=True, exist_ok=True)
    (VAULT / "manifest" / "public_stream_playlist.json").write_text(text, encoding="utf-8")
    if EXCAV.exists():
        (EXCAV / "data").mkdir(exist_ok=True)
        (EXCAV / "data" / "public_stream_playlist.json").write_text(text, encoding="utf-8")

    api.upload_file(
        path_or_fileobj=str(pl_path),
        path_in_repo="public_stream_playlist.json",
        repo_id=REPO,
        repo_type="dataset",
        token=token,
        commit_message=f"playlist {len(pl.get('tracks') or [])} tracks public URLs",
    )
    print(f"[hf] playlist uploaded tracks={len(pl.get('tracks') or [])} base={base}", flush=True)
    print("[hf] COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
