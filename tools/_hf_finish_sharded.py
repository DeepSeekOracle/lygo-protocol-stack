"""Upload remaining streams into sharded dirs (HF 10k files/dir limit on stream/)."""
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, CommitOperationAdd

REPO = "DeepSeekOracle/excavationpro-music-stream"
STREAM = Path(r"I:\E Drive\MUSIC_VAULT\public_stream")
CAT = Path(r"I:\E Drive\lygo-protocol-stack\data\music_catalog")
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
EXCAV = Path(r"I:\E Drive\Excavationpro")
BATCH = 50
SLEEP = 45
MAX_RETRIES = 15


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def shard_path(name: str) -> str:
    # stream/ab/<sha>.mp3 — spreads across 256 dirs
    stem = name.replace(".mp3", "")
    pref = (stem[:2] if len(stem) >= 2 else "00").lower()
    return f"stream/{pref}/{name}"


def list_remote_map(api: HfApi, token: str) -> dict[str, str]:
    """filename -> path_in_repo"""
    files = list(api.list_repo_files(REPO, repo_type="dataset", token=token))
    out = {}
    for f in files:
        if not f.endswith(".mp3"):
            continue
        if not (f.startswith("stream/") or f.startswith("stream_")):
            continue
        out[Path(f).name] = f
    return out


def commit_batch(api: HfApi, token: str, items: list[tuple[Path, str]], attempt: int = 0) -> None:
    ops = [
        CommitOperationAdd(path_in_repo=repo_path, path_or_fileobj=str(local))
        for local, repo_path in items
    ]
    try:
        api.create_commit(
            repo_id=REPO,
            repo_type="dataset",
            operations=ops,
            commit_message=f"Add {len(items)} sharded stream MP3s",
            token=token,
        )
    except Exception as e:
        err = str(e)
        if "429" in err or "rate limit" in err.lower():
            wait = 120 + attempt * 30
            if "Retry after" in err:
                try:
                    wait = max(wait, int(err.split("Retry after")[1].split()[0]) + 5)
                except Exception:
                    pass
            if attempt >= MAX_RETRIES:
                raise
            print(f"[hf] rate limit sleep {wait}s attempt={attempt+1}", flush=True)
            time.sleep(wait)
            return commit_batch(api, token, items, attempt + 1)
        if len(items) > 5 and attempt < MAX_RETRIES:
            mid = len(items) // 2
            print(f"[hf] split batch {len(items)} -> {mid}+{len(items)-mid}: {e}", flush=True)
            commit_batch(api, token, items[:mid], attempt + 1)
            time.sleep(SLEEP)
            commit_batch(api, token, items[mid:], attempt + 1)
            return
        raise


def rewrite_playlist(remote: dict[str, str], token: str, api: HfApi) -> None:
    base = f"https://huggingface.co/datasets/{REPO}/resolve/main"
    pl_path = CAT / "public_stream_playlist.json"
    pl = json.loads(pl_path.read_text(encoding="utf-8"))
    pl["public_base_url"] = f"{base}/stream"  # legacy flat
    pl["hf_dataset"] = f"https://huggingface.co/datasets/{REPO}"
    pl["published_at"] = utc_now()
    pl.setdefault("stats", {})["remote_streams"] = len(remote)
    missing_urls = 0
    for t in pl.get("tracks") or []:
        sf = t.get("stream_file") or ((t.get("sha256") or "") + ".mp3")
        t["stream_file"] = sf
        if sf in remote:
            t["stream_url"] = f"{base}/{remote[sf]}"
            t["hf_path"] = remote[sf]
        else:
            # expected sharded path even if not yet remote
            sp = shard_path(sf)
            t["stream_url"] = f"{base}/{sp}"
            t["hf_path"] = sp
            missing_urls += 1
    pl["stats"]["playlist_missing_remote"] = missing_urls
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
                commit_message=f"playlist sharded URLs remote={len(remote)}",
            )
            break
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                print("[hf] playlist rate limit sleep 120s", flush=True)
                time.sleep(120)
            else:
                raise
    print(f"[hf] playlist ok tracks={len(pl.get('tracks') or [])} remote={len(remote)} missing_remote={missing_urls}", flush=True)


def main() -> int:
    token = Path.home().joinpath(".cache/huggingface/token").read_text(encoding="utf-8").strip()
    api = HfApi(token=token)

    print("[hf] listing remote map...", flush=True)
    for attempt in range(MAX_RETRIES):
        try:
            remote = list_remote_map(api, token)
            break
        except Exception as e:
            if "429" in str(e):
                print("[hf] list 429 sleep 90s", flush=True)
                time.sleep(90)
            else:
                raise
    else:
        raise SystemExit("list failed")

    local = sorted(STREAM.glob("*.mp3"))
    missing = [p for p in local if p.name not in remote]
    print(f"[hf] local={len(local)} remote={len(remote)} missing={len(missing)}", flush=True)
    print(f"[hf] note: flat stream/ is at HF 10k/dir limit — new files go stream/xx/sha.mp3", flush=True)

    if missing:
        jobs = [(p, shard_path(p.name)) for p in missing]
        total = len(jobs)
        done = 0
        for i in range(0, total, BATCH):
            chunk = jobs[i : i + BATCH]
            print(f"[hf] batch {i//BATCH+1}/{(total+BATCH-1)//BATCH} n={len(chunk)}", flush=True)
            commit_batch(api, token, chunk)
            done += len(chunk)
            print(f"[hf] committed {done}/{total}", flush=True)
            if i + BATCH < total:
                print(f"[hf] sleep {SLEEP}s", flush=True)
                time.sleep(SLEEP)
        time.sleep(5)
        remote = list_remote_map(api, token)
        still = [p for p in local if p.name not in remote]
        print(f"[hf] remote now={len(remote)} still_missing={len(still)}", flush=True)
        if still:
            print(f"[hf] retry still_missing={len(still)}", flush=True)
            jobs2 = [(p, shard_path(p.name)) for p in still]
            for i in range(0, len(jobs2), 20):
                commit_batch(api, token, jobs2[i : i + 20])
                time.sleep(SLEEP)
            remote = list_remote_map(api, token)
            still = [p for p in local if p.name not in remote]
            print(f"[hf] final remote={len(remote)} still_missing={len(still)}", flush=True)
    else:
        print("[hf] nothing missing", flush=True)

    rewrite_playlist(remote, token, api)
    print("[hf] COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
