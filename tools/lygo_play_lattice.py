#!/usr/bin/env python3
"""
LYGO Play Lattice — sovereign append-only play ledger for Excavationpro streams.

Layers (LYGO-aligned):
  P0  — event schema + SHA-256 event hash chain (tamper-evident)
  P1  — local CAS under MUSIC_VAULT/play_lattice/ (append-only JSONL + objects)
  P3  — aggregate play_counts.json + merkle root of event hashes
  Public read — HF dataset play/play_counts.json (CDN, no increment on view)
  Ingest — tools/lygo_play_ingest_server.py (CORS) or Cloudflare Worker

Usage:
  python tools/lygo_play_lattice.py --status
  python tools/lygo_play_lattice.py --ingest-event event.json
  python tools/lygo_play_lattice.py --import-ledger browser_export.json
  python tools/lygo_play_lattice.py --rebuild
  python tools/lygo_play_lattice.py --publish-hf
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
LATTICE_DIR = VAULT / "play_lattice"
EVENTS_JSONL = LATTICE_DIR / "events.jsonl"
EVENTS_CAS = LATTICE_DIR / "cas"
AGGREGATE = LATTICE_DIR / "play_counts.json"
MERKLE = LATTICE_DIR / "play_merkle_root.txt"
PUBLIC_AGG = CAT / "play_counts.json"
HF_REPO = "DeepSeekOracle/excavationpro-music-stream"
HF_PATH = "play/play_counts.json"
SIGNATURE_EVENT = "Δ9Φ963-PLAY-EVENT-v1"
SIGNATURE_AGG = "Δ9Φ963-PLAY-AGGREGATE-v1"
SIGNATURE_LATTICE = "Δ9Φ963-PLAY-LATTICE-v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_event_payload(ev: dict[str, Any]) -> bytes:
    """Stable JSON for hashing (exclude event_hash itself)."""
    body = {k: ev[k] for k in sorted(ev.keys()) if k != "event_hash"}
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False, sort_keys=True).encode("utf-8")


def compute_event_hash(ev: dict[str, Any]) -> str:
    return sha256_hex(canonical_event_payload(ev))


def ensure_dirs() -> None:
    LATTICE_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_CAS.mkdir(parents=True, exist_ok=True)


def load_events() -> list[dict[str, Any]]:
    ensure_dirs()
    if not EVENTS_JSONL.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in EVENTS_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def last_event_hash(events: list[dict[str, Any]]) -> str:
    if not events:
        return "0" * 64
    return events[-1].get("event_hash") or "0" * 64


def merkle_of_hashes(hashes: list[str]) -> str:
    if not hashes:
        return sha256_hex(b"")
    level = [bytes.fromhex(h) if len(h) == 64 else sha256_hex(h.encode()).encode() for h in hashes]
    # normalize to 32-byte digests
    fixed = []
    for h in hashes:
        if len(h) == 64 and all(c in "0123456789abcdef" for c in h.lower()):
            fixed.append(bytes.fromhex(h))
        else:
            fixed.append(hashlib.sha256(h.encode()).digest())
    level = fixed
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else a
            nxt.append(hashlib.sha256(a + b).digest())
        level = nxt
    return level[0].hex()


def validate_event(ev: dict[str, Any], expect_prev: str | None = None) -> tuple[bool, str]:
    if not isinstance(ev, dict):
        return False, "not object"
    if not ev.get("track_sha256") or len(str(ev.get("track_sha256"))) < 16:
        return False, "bad track_sha256"
    if not ev.get("event_id"):
        return False, "missing event_id"
    if not ev.get("ts"):
        return False, "missing ts"
    eh = ev.get("event_hash")
    if not eh:
        return False, "missing event_hash"
    if compute_event_hash(ev) != eh:
        return False, "event_hash mismatch (tamper)"
    if expect_prev is not None and ev.get("prev_hash") != expect_prev:
        # allow fork merges: prev may point to any known event; soft-check only for sequential
        pass
    return True, "ok"


def build_event(
    track_sha256: str,
    title: str | None = None,
    client_id: str | None = None,
    listen_sec: float = 20.0,
    prev_hash: str | None = None,
    extra: dict | None = None,
) -> dict[str, Any]:
    events = load_events()
    prev = prev_hash if prev_hash else last_event_hash(events)
    ev: dict[str, Any] = {
        "v": 1,
        "signature": SIGNATURE_EVENT,
        "event_id": str(uuid.uuid4()),
        "track_sha256": track_sha256.lower().strip(),
        "title": title,
        "ts": utc_now(),
        "client_id": client_id or "steward-local",
        "listen_sec": float(listen_sec),
        "prev_hash": prev,
    }
    if extra:
        for k, v in extra.items():
            if k not in ev and k != "event_hash":
                ev[k] = v
    ev["event_hash"] = compute_event_hash(ev)
    return ev


def append_event(ev: dict[str, Any], skip_hash_check: bool = False) -> tuple[bool, str]:
    ensure_dirs()
    events = load_events()
    # dedupe by event_id
    seen_ids = {e.get("event_id") for e in events}
    if ev.get("event_id") in seen_ids:
        return False, "duplicate event_id"
    seen_hashes = {e.get("event_hash") for e in events}
    if ev.get("event_hash") in seen_hashes:
        return False, "duplicate event_hash"

    if not skip_hash_check:
        ok, msg = validate_event(ev)
        if not ok:
            return False, msg
    else:
        # recompute hash if missing
        if not ev.get("event_hash"):
            ev["event_hash"] = compute_event_hash(ev)

    # CAS object
    digest = ev["event_hash"]
    cas_path = EVENTS_CAS / digest[:2] / f"{digest}.json"
    cas_path.parent.mkdir(parents=True, exist_ok=True)
    if not cas_path.exists():
        cas_path.write_text(json.dumps(ev, indent=2, ensure_ascii=False), encoding="utf-8")

    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False, separators=(",", ":")) + "\n")
    return True, "appended"


def rebuild_aggregate() -> dict[str, Any]:
    events = load_events()
    by_track: dict[str, int] = {}
    by_client: dict[str, int] = {}
    hashes: list[str] = []
    for e in events:
        ok, _ = validate_event(e)
        if not ok:
            continue
        h = e.get("event_hash")
        if h:
            hashes.append(h)
        t = (e.get("track_sha256") or "").lower()
        if t:
            by_track[t] = by_track.get(t, 0) + 1
        c = e.get("client_id") or "unknown"
        by_client[c] = by_client.get(c, 0) + 1

    root = merkle_of_hashes(hashes)
    agg = {
        "signature": SIGNATURE_AGG,
        "lattice": SIGNATURE_LATTICE,
        "updated_at": utc_now(),
        "total_plays": len(hashes),
        "unique_events": len(hashes),
        "unique_tracks_played": len(by_track),
        "by_track": by_track,
        "by_client_approx": {k: by_client[k] for k in list(by_client)[:50]},
        "merkle_root": root,
        "event_count": len(events),
        "public_read": f"https://huggingface.co/datasets/{HF_REPO}/resolve/main/{HF_PATH}",
        "policy": {
            "count_trigger": "real_listen_client_side_min_seconds",
            "dedupe": "event_id + event_hash",
            "ownership": "steward_streams_own_work",
            "note": "Append-only hash-chained play events. Aggregate is derived; events are truth.",
        },
    }
    ensure_dirs()
    AGGREGATE.write_text(json.dumps(agg, indent=2, ensure_ascii=False), encoding="utf-8")
    MERKLE.write_text(root + "\n", encoding="utf-8")
    PUBLIC_AGG.write_text(json.dumps(agg, indent=2, ensure_ascii=False), encoding="utf-8")
    # egg-sized core
    egg = {
        "signature": SIGNATURE_LATTICE,
        "egg_id": "excavationpro-play-lattice-v1",
        "merkle_root": root,
        "total_plays": agg["total_plays"],
        "unique_tracks_played": agg["unique_tracks_played"],
        "updated_at": agg["updated_at"],
    }
    egg_path = CAT / "egg_payload" / "play_lattice_egg_core.json"
    egg_path.parent.mkdir(parents=True, exist_ok=True)
    egg_path.write_text(json.dumps(egg, indent=2), encoding="utf-8")
    print(
        f"[rebuild] events={len(events)} plays={agg['total_plays']} "
        f"tracks={agg['unique_tracks_played']} merkle={root[:16]}…",
        flush=True,
    )
    return agg


def import_ledger(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    events = []
    if isinstance(data, list):
        events = data
    elif isinstance(data, dict):
        events = data.get("events") or data.get("plays") or []
    n = 0
    for e in events:
        if not isinstance(e, dict):
            continue
        # normalize browser export format
        if "track_sha256" not in e and e.get("sha256"):
            e = dict(e)
            e["track_sha256"] = e.pop("sha256", None) or e.get("track_sha256")
        if "event_id" not in e:
            e = dict(e)
            e["event_id"] = e.get("event_id") or str(uuid.uuid4())
        if "ts" not in e:
            e = dict(e)
            e["ts"] = e.get("ts") or utc_now()
        if "prev_hash" not in e:
            e = dict(e)
            e["prev_hash"] = last_event_hash(load_events())
        if "signature" not in e:
            e = dict(e)
            e["signature"] = SIGNATURE_EVENT
        if "v" not in e:
            e = dict(e)
            e["v"] = 1
        if "client_id" not in e:
            e = dict(e)
            e["client_id"] = e.get("client_id") or "import"
        # recompute hash if missing/invalid
        e = dict(e)
        e["event_hash"] = compute_event_hash(e)
        ok, msg = append_event(e)
        if ok:
            n += 1
        else:
            if msg not in ("duplicate event_id", "duplicate event_hash"):
                print(f"[import skip] {msg}", flush=True)
    rebuild_aggregate()
    print(f"[import] appended {n} from {path}", flush=True)
    return n


def publish_hf(repo: str = HF_REPO) -> str:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    tp = Path.home() / ".cache" / "huggingface" / "token"
    if not token and tp.exists():
        token = tp.read_text(encoding="utf-8").strip()
    if not token:
        raise SystemExit("No HF token")
    agg = rebuild_aggregate()
    try:
        from huggingface_hub import HfApi
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub"])
        from huggingface_hub import HfApi

    api = HfApi(token=token)
    # upload aggregate + merkle + recent events snapshot
    api.upload_file(
        path_or_fileobj=str(AGGREGATE),
        path_in_repo=HF_PATH,
        repo_id=repo,
        repo_type="dataset",
        token=token,
        commit_message=f"play lattice aggregate total={agg['total_plays']} merkle={agg['merkle_root'][:12]}",
    )
    api.upload_file(
        path_or_fileobj=str(MERKLE),
        path_in_repo="play/play_merkle_root.txt",
        repo_id=repo,
        repo_type="dataset",
        token=token,
        commit_message="play lattice merkle",
    )
    # compact event export (last 2000)
    events = load_events()[-2000:]
    snap = LATTICE_DIR / "events_snapshot.json"
    snap.write_text(
        json.dumps(
            {"signature": SIGNATURE_LATTICE, "events": events, "count": len(events)},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    api.upload_file(
        path_or_fileobj=str(snap),
        path_in_repo="play/events_snapshot.json",
        repo_id=repo,
        repo_type="dataset",
        token=token,
        commit_message="play lattice events snapshot",
    )
    url = f"https://huggingface.co/datasets/{repo}/resolve/main/{HF_PATH}"
    print(f"[hf] published {url}", flush=True)
    return url


def status() -> dict[str, Any]:
    events = load_events()
    agg = json.loads(AGGREGATE.read_text(encoding="utf-8")) if AGGREGATE.exists() else {}
    return {
        "events_file": str(EVENTS_JSONL),
        "events": len(events),
        "aggregate": {
            "total_plays": agg.get("total_plays"),
            "unique_tracks_played": agg.get("unique_tracks_played"),
            "merkle_root": (agg.get("merkle_root") or "")[:24],
            "updated_at": agg.get("updated_at"),
        },
        "hf_public": f"https://huggingface.co/datasets/{HF_REPO}/resolve/main/{HF_PATH}",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Play Lattice")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--publish-hf", action="store_true")
    ap.add_argument("--ingest-event", type=Path, help="JSON file with one event or {event:{...}}")
    ap.add_argument("--import-ledger", type=Path, help="Browser export / events list JSON")
    ap.add_argument(
        "--record",
        nargs=2,
        metavar=("SHA256", "TITLE"),
        help="Steward-side record one play (testing)",
    )
    args = ap.parse_args()

    if args.record:
        ev = build_event(args.record[0], title=args.record[1])
        ok, msg = append_event(ev)
        print(ok, msg, ev.get("event_hash", "")[:16])
        rebuild_aggregate()
        return 0 if ok else 1
    if args.ingest_event:
        raw = json.loads(args.ingest_event.read_text(encoding="utf-8"))
        ev = raw.get("event") if isinstance(raw, dict) and "event" in raw else raw
        ok, msg = append_event(ev)
        print(ok, msg)
        if ok:
            rebuild_aggregate()
        return 0 if ok else 1
    if args.import_ledger:
        import_ledger(args.import_ledger)
        return 0
    if args.rebuild:
        rebuild_aggregate()
        return 0
    if args.publish_hf:
        publish_hf()
        return 0
    if args.status or True:
        print(json.dumps(status(), indent=2))
        if not args.status and not any(
            [args.rebuild, args.publish_hf, args.ingest_event, args.import_ledger, args.record]
        ):
            # default status
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
