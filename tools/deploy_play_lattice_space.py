#!/usr/bin/env python3
"""Deploy / update HF Space DeepSeekOracle/excavationpro-play-lattice."""
from __future__ import annotations

import os
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
SPACE_DIR = STACK / "tools" / "play_lattice_space"
REPO = "DeepSeekOracle/excavationpro-play-lattice"


def main() -> int:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    tp = Path.home() / ".cache" / "huggingface" / "token"
    if not token and tp.exists():
        token = tp.read_text(encoding="utf-8").strip()
    if not token:
        print("No HF token", file=sys.stderr)
        return 1

    from huggingface_hub import HfApi, create_repo

    api = HfApi(token=token)
    print(f"[space] ensure {REPO}")
    try:
        create_repo(REPO, repo_type="space", space_sdk="gradio", exist_ok=True, token=token, private=False)
    except Exception as e:
        print("[space] create note", e)

    # secret for dataset push from Space
    try:
        api.add_space_secret(REPO, "HF_TOKEN", token)
        print("[space] secret HF_TOKEN set")
    except Exception as e:
        print("[space] secret note", e)

    api.upload_folder(
        folder_path=str(SPACE_DIR),
        repo_id=REPO,
        repo_type="space",
        token=token,
        commit_message="LYGO Play Lattice global ingest Space",
    )
    url = f"https://huggingface.co/spaces/{REPO}"
    direct = f"https://deepseekoracle-excavationpro-play-lattice.hf.space"
    print(f"[space] {url}")
    print(f"[space] runtime {direct}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
