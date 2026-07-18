"""Finish remaining HF stream uploads with rate-limit-aware batch commits."""
from __future__ import annotations
import json
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, CommitOperationAdd
from huggingface_hub.utils import HfHubHTTPError

REPO = "DeepSeekOracle/excavationpro-music-stream"
STREAM = Path(r"I:\E Drive\MUSIC_VAULT\public_stream")
CAT = Path(r"I:\E Drive\lygo-protocol-stack\data\music_catalog")
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
EXCAV = Path(r"I:\E Drive\Excavationpro")

# Stay under ~128 commits/hour and API window
BATCH = 80
SLEEP_BETWEEN_COMMITS = 40  # seconds
MAX_RETRIES = 12


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_remote(api: HfApi, token: str) -> set[str]:
    files = list(api.list_repo_files(REPO, repo_type="dataset", token=token))
    return {Path(f).name for f in files if f.startswith("stream/") and f.endswith(".mp3")}


def commit_batch(api: HfApi, token: str, paths: list[Path], attempt: int = 0) -> None:
    ops = [
        CommitOperationAdd(path_in_repo=f"stream/{p.name}", path_or_fileobj=str(p))
        for p in paths
    ]
    msg = f"Add {len(paths)} stream MP3s (batch)"
    try:
        api.create_commit(
            repo_id=REPO,
            repo_type="dataset",
            operations=ops,
            commit_message=msg,
            token=token,
        )
    except Exception as e:
        err = str(e)
        if "429" in err or "rate limit" in err.lower():
            wait = 90 + attempt * 30
            # try parse Retry after N
            if "Retry after" in err:
                try:
                    wait = max(wait, int(err.split("Retry after")[1].split()[0]))
                except Exception:
                    pass
            if attempt >= MAX_RETRIES:
                raise
            print(f"[hf] rate limited; sleep {wait}s (attempt {attempt+1})", flush=True)
            time.sleep(wait)
            return commit_batch(api, token, paths, attempt + 1)
        # shrink batch on other commit failures
        if len(paths) > 10 and attempt < MAX_RETRIES:
            mid = len(paths) // 2
            print(f"[hf] commit fail ({e}); split {len(paths)} -> {mid}+{len(paths)-mid}", flush=True)
            commit_batch(api, token, paths[:mid], attempt + 1)
            time.sleep(SLEEP_BETWEEN_COMMITS)
            commit_batch(api, token, paths[mid:], attempt + 1)
            return
        raise


def rewrite_playlist(remote_count: int, token: str, api: HfApi) -> None:
    base = f"https://huggingface.co/datasets/{REPO}/resolve/main/stream"
    pl_path = CAT / "public_stream_playlist.json"
    pl = json.loads(pl_path.read_text(encoding="utf-8"))
    pl["public_base_url"] = base
    pl["hf_dataset"] = f"https://huggingface.co/datasets/{REPO}"
    pl["published_at"] = utc_now()
    pl.setdefault("stats", {})["remote_streams"] = remote_count
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
    for attempt in range(MAX_RETRIES):
        try:
            api.upload_file(
                path_or_fileobj=str(pl_path),
                path_in_repo="public_stream_playlist.json",
                repo_id=REPO,
                repo_type="dataset",
                token=token,
                commit_message=f"playlist {len(pl.get('tracks') or [])} tracks",
            )
            break
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                print(f"[hf] playlist upload rate limit; sleep 90s", flush=True)
                time.sleep(90)
            else:
                raise
    print(f"[hf] playlist uploaded tracks={len(pl.get('tracks') or [])}", flush=True)


def main() -> int:
    token = Path.home().joinpath(".cache/huggingface/token").read_text(encoding="utf-8").strip()
    api = HfApi(token=token)

    print("[hf] listing remote...", flush=True)
    for attempt in range(MAX_RETRIES):
        try:
            remote = list_remote(api, token)
            break
        except Exception as e:
            if "429" in str(e):
                print("[hf] list rate limit; sleep 90s", flush=True)
                time.sleep(90)
            else:
                raise
    else:
        raise SystemExit("could not list remote")

    local = sorted(STREAM.glob("*.mp3"))
    missing = [p for p in local if p.name not in remote]
    print(f"[hf] local={len(local)} remote={len(remote)} missing={len(missing)}", flush=True)

    if missing:
        total = len(missing)
        done = 0
        for i in range(0, total, BATCH):
            chunk = missing[i : i + BATCH]
            print(f"[hf] commit batch {i//BATCH+1}/{(total+BATCH-1)//BATCH} files={len(chunk)}", flush=True)
            commit_batch(api, token, chunk)
            done += len(chunk)
            print(f"[hf] committed {done}/{total}", flush=True)
            if i + BATCH < total:
                print(f"[hf] sleep {SLEEP_BETWEEN_COMMITS}s (rate limit safety)", flush=True)
                time.sleep(SLEEP_BETWEEN_COMMITS)

        # re-list
        time.sleep(5)
        for attempt in range(MAX_RETRIES):
            try:
                remote2 = list_remote(api, token)
                break
            except Exception as e:
                if "429" in str(e):
                    time.sleep(90)
                else:
                    raise
        still = [p for p in local if p.name not in remote2]
        print(f"[hf] after upload remote={len(remote2)} still_missing={len(still)}", flush=True)
        if still:
            print(f"[hf] WARNING {len(still)} still missing — will retry once more", flush=True)
            for i in range(0, len(still), max(10, BATCH // 2)):
                chunk = still[i : i + max(10, BATCH // 2)]
                commit_batch(api, token, chunk)
                time.sleep(SLEEP_BETWEEN_COMMITS)
            remote2 = list_remote(api, token)
            still = [p for p in local if p.name not in remote2]
            print(f"[hf] final remote={len(remote2)} still_missing={len(still)}", flush=True)
    else:
        remote2 = remote
        print("[hf] nothing missing", flush=True)

    rewrite_playlist(len(remote2), token, api)
    print("[hf] COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
