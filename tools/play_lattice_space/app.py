#!/usr/bin/env python3
"""
HF Space: Excavationpro / LYGO Play Lattice public ingest + global counts.

Public multi-listener write path for the listen portal.
Persists aggregate to dataset DeepSeekOracle/excavationpro-music-stream/play/
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import gradio as gr

DATASET = os.environ.get("PLAY_DATASET", "DeepSeekOracle/excavationpro-music-stream")
AGG_PATH = "play/play_counts.json"
EVENTS_PATH = "play/events_snapshot.json"
LOCAL_STATE = Path("/tmp/lygo_play_state.json")  # hot cache on Space
LOCK = threading.Lock()
SIGNATURE_AGG = "Δ9Φ963-PLAY-AGGREGATE-v1"
SIGNATURE_EVENT = "Δ9Φ963-PLAY-EVENT-v1"
SIGNATURE_LATTICE = "Δ9Φ963-PLAY-LATTICE-v1"

# recent plays ring buffer
RECENT_MAX = 40
_last_hf_push = 0.0
_PUSH_MIN_INTERVAL = 8.0  # seconds between HF dataset commits


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def event_hash(ev: dict) -> str:
    body = {k: ev[k] for k in sorted(ev.keys()) if k != "event_hash"}
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def empty_state() -> dict:
    return {
        "signature": SIGNATURE_AGG,
        "lattice": SIGNATURE_LATTICE,
        "total_plays": 0,
        "unique_events": 0,
        "unique_tracks_played": 0,
        "by_track": {},
        "recent": [],
        "seen_event_ids": [],
        "merkle_root": None,
        "updated_at": utc_now(),
    }


def load_state() -> dict:
    if LOCAL_STATE.exists():
        try:
            return json.loads(LOCAL_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    # try pull from HF dataset
    try:
        from huggingface_hub import hf_hub_download

        p = hf_hub_download(repo_id=DATASET, repo_type="dataset", filename=AGG_PATH)
        st = json.loads(Path(p).read_text(encoding="utf-8"))
        st.setdefault("recent", [])
        st.setdefault("seen_event_ids", [])
        st.setdefault("by_track", {})
        return st
    except Exception:
        return empty_state()


def save_local(st: dict) -> None:
    LOCAL_STATE.parent.mkdir(parents=True, exist_ok=True)
    # cap seen ids
    ids = st.get("seen_event_ids") or []
    if len(ids) > 20000:
        st["seen_event_ids"] = ids[-10000:]
    if len(st.get("recent") or []) > RECENT_MAX:
        st["recent"] = st["recent"][:RECENT_MAX]
    LOCAL_STATE.write_text(json.dumps(st), encoding="utf-8")


def push_hf(st: dict) -> None:
    global _last_hf_push
    now = time.time()
    if now - _last_hf_push < _PUSH_MIN_INTERVAL:
        return
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not token:
        return
    try:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        pub = {
            k: st[k]
            for k in (
                "signature",
                "lattice",
                "total_plays",
                "unique_events",
                "unique_tracks_played",
                "by_track",
                "recent",
                "merkle_root",
                "updated_at",
            )
            if k in st
        }
        pub["policy"] = {
            "count_trigger": "real_listen_20s_or_35pct",
            "global": True,
            "source": "hf_space_lygo_play_lattice",
        }
        # top / bottom for clients that want ready-made lists
        ranked = sorted(pub.get("by_track", {}).items(), key=lambda x: (-x[1], x[0]))
        pub["most_played"] = [{"sha256": s, "plays": n} for s, n in ranked[:50]]
        pub["least_played"] = [
            {"sha256": s, "plays": n} for s, n in sorted(ranked, key=lambda x: (x[1], x[0]))[:50]
            if n > 0
        ]
        tmp = Path("/tmp/play_counts_pub.json")
        tmp.write_text(json.dumps(pub, indent=2, ensure_ascii=False), encoding="utf-8")
        api.upload_file(
            path_or_fileobj=str(tmp),
            path_in_repo=AGG_PATH,
            repo_id=DATASET,
            repo_type="dataset",
            token=token,
            commit_message=f"play lattice total={pub.get('total_plays')}",
        )
        _last_hf_push = now
    except Exception as e:
        print("hf push error", e, flush=True)


def record_play(event_json: str) -> str:
    """API: accept play event JSON string, return aggregate JSON string."""
    try:
        data = json.loads(event_json) if isinstance(event_json, str) else event_json
    except json.JSONDecodeError:
        return json.dumps({"ok": False, "error": "invalid json"})
    ev = data.get("event") if isinstance(data, dict) and "event" in data else data
    if not isinstance(ev, dict) or not ev.get("track_sha256"):
        return json.dumps({"ok": False, "error": "track_sha256 required"})

    with LOCK:
        st = load_state()
        eid = ev.get("event_id") or str(uuid.uuid4())
        ev["event_id"] = eid
        if eid in (st.get("seen_event_ids") or []):
            return json.dumps(
                {
                    "ok": True,
                    "accepted": False,
                    "message": "duplicate",
                    "total_plays": st.get("total_plays", 0),
                    "track_plays": (st.get("by_track") or {}).get(str(ev["track_sha256"]).lower()),
                    "aggregate": public_view(st),
                }
            )
        if not ev.get("ts"):
            ev["ts"] = utc_now()
        if not ev.get("client_id"):
            ev["client_id"] = "space-web"
        if not ev.get("signature"):
            ev["signature"] = SIGNATURE_EVENT
        if not ev.get("v"):
            ev["v"] = 1
        if not ev.get("prev_hash"):
            ev["prev_hash"] = st.get("merkle_root") or ("0" * 64)
        try:
            # recompute hash server-side for integrity of stored tip
            ev_copy = dict(ev)
            ev_copy.pop("event_hash", None)
            ev["event_hash"] = event_hash(ev_copy)
        except Exception:
            ev["event_hash"] = hashlib.sha256(eid.encode()).hexdigest()

        sha = str(ev["track_sha256"]).lower()
        by = st.setdefault("by_track", {})
        by[sha] = int(by.get(sha) or 0) + 1
        st["total_plays"] = int(st.get("total_plays") or 0) + 1
        st["unique_events"] = int(st.get("unique_events") or 0) + 1
        st["unique_tracks_played"] = len(by)
        st["merkle_root"] = ev["event_hash"]
        st["updated_at"] = utc_now()
        st.setdefault("seen_event_ids", []).append(eid)
        st.setdefault("recent", []).insert(
            0,
            {
                "sha256": sha,
                "title": ev.get("title"),
                "ts": ev.get("ts"),
                "plays": by[sha],
            },
        )
        save_local(st)
        # async-ish push
        threading.Thread(target=push_hf, args=(dict(st),), daemon=True).start()

        return json.dumps(
            {
                "ok": True,
                "accepted": True,
                "total_plays": st["total_plays"],
                "track_plays": by[sha],
                "merkle_root": st["merkle_root"],
                "aggregate": public_view(st),
            }
        )


def public_view(st: dict) -> dict:
    by = st.get("by_track") or {}
    ranked = sorted(by.items(), key=lambda x: (-x[1], x[0]))
    return {
        "signature": SIGNATURE_AGG,
        "lattice": SIGNATURE_LATTICE,
        "total_plays": st.get("total_plays", 0),
        "unique_events": st.get("unique_events", 0),
        "unique_tracks_played": st.get("unique_tracks_played", 0),
        "by_track": by,
        "recent": st.get("recent") or [],
        "most_played": [{"sha256": s, "plays": n} for s, n in ranked[:50]],
        "least_played": [
            {"sha256": s, "plays": n}
            for s, n in sorted(ranked, key=lambda x: (x[1], x[0]))[:50]
            if n > 0
        ],
        "merkle_root": st.get("merkle_root"),
        "updated_at": st.get("updated_at"),
    }


def get_counts() -> str:
    with LOCK:
        st = load_state()
        return json.dumps({"ok": True, "aggregate": public_view(st)})


def get_counts_raw() -> str:
    """Return aggregate only (for simple clients)."""
    with LOCK:
        return json.dumps(public_view(load_state()))


with gr.Blocks(title="LYGO Play Lattice") as demo:
    gr.Markdown(
        """# Δ9Φ963 LYGO Play Lattice
Global play counts for [Excavationpro Listen](https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html).

**API (Gradio):** `record_play` · `get_counts` · `get_counts_raw`
"""
    )
    with gr.Row():
        inp = gr.Textbox(label="Play event JSON", lines=6)
        out = gr.Textbox(label="Result", lines=8)
    btn = gr.Button("Record play")
    btn.click(record_play, inputs=inp, outputs=out, api_name="record_play")
    out2 = gr.Textbox(label="Counts", lines=12)
    gr.Button("Get counts").click(get_counts, outputs=out2, api_name="get_counts")
    out3 = gr.Textbox(label="Counts raw aggregate", lines=12)
    gr.Button("Get counts raw").click(get_counts_raw, outputs=out3, api_name="get_counts_raw")

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=8).launch()
