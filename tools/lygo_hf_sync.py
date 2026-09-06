#!/usr/bin/env python3
"""
Online/offline lattice sync via Hugging Face dataset.

  python tools/lygo_hf_sync.py push   # local receipts → dataset
  python tools/lygo_hf_sync.py pull   # dataset inbox → local plant/ingest

Offline: no token → writes stay on disk. Online: piggybacks
DeepSeekOracle/lygo-public-witness-feed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from lygo_network_core import ingest_pending, plant_egg, submit_star, announce  # noqa: E402

DS = os.environ.get("LYGO_HUB_DATASET", "DeepSeekOracle/lygo-public-witness-feed")
LOCAL = {
    "network-eggs.json": ROOT / "docs" / "agent-agora" / "api" / "network_eggs.json",
    "heartbeat.json": ROOT / "docs" / "agent-agora" / "api" / "heartbeat.json",
    "directory.json": ROOT / "docs" / "agent-agora" / "api" / "directory.json",
}


def _token() -> str | None:
    t = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if t:
        return t
    p = Path.home() / ".cache" / "huggingface" / "token"
    if p.is_file():
        return p.read_text(encoding="utf-8").strip() or None
    return None


def api():
    from huggingface_hub import HfApi

    tok = _token()
    if not tok:
        raise SystemExit("offline: no HF token")
    return HfApi(token=tok)


def cmd_push() -> dict:
    hf = api()
    out = []
    for name, path in LOCAL.items():
        if not path.is_file():
            continue
        blob = path.read_bytes()
        hf.upload_file(
            path_or_fileobj=blob,
            path_in_repo=name,
            repo_id=DS,
            repo_type="dataset",
            commit_message="lattice sync " + name,
        )
        out.append(name)
    return {"ok": True, "dataset": DS, "pushed": out, "mode": "online"}


def cmd_pull() -> dict:
    from huggingface_hub import list_repo_files, hf_hub_download

    tok = _token()
    if not tok:
        return {"ok": False, "mode": "offline", "error": "no_token"}
    files = list_repo_files(DS, repo_type="dataset", token=tok)
    inbox = [f for f in files if f.startswith("inbox/") and f.endswith(".json")]
    results = []
    for rel in inbox:
        local = hf_hub_download(DS, rel, repo_type="dataset", token=tok)
        data = json.loads(Path(local).read_text(encoding="utf-8"))
        kind = data.get("kind") or ("star" if "star" in rel else "egg" if "egg" in rel else "announce")
        if kind == "egg" or "egg" in rel:
            payload = data.get("egg", {}).get("payload") if isinstance(data.get("egg"), dict) else data.get("payload") or data
            aid = (data.get("egg") or data).get("agent_id") or "hf-agent"
            results.append(plant_egg(str(aid), payload, source="hf_inbox"))
        elif kind == "star" or "star" in rel:
            r = submit_star(data.get("submission") or data, source="hf_inbox")
            if r.get("queued"):
                r["ingest"] = ingest_pending()
            results.append(r)
        else:
            results.append(announce(data.get("card") or data))
    return {"ok": True, "mode": "online", "inbox": len(inbox), "results": results}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["push", "pull", "status"])
    args = ap.parse_args()
    if args.cmd == "status":
        print(json.dumps({"dataset": DS, "online": bool(_token()), "local": {k: p.is_file() for k, p in LOCAL.items()}}, indent=2))
        return 0
    if args.cmd == "push":
        print(json.dumps(cmd_push(), indent=2))
        return 0
    print(json.dumps(cmd_pull(), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
