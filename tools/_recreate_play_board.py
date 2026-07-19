#!/usr/bin/env python3
"""Recreate jsonblob play board when free blob expires (counts freeze)."""
from __future__ import annotations
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SEED = {
    "signature": "LYGO-PLAY-AGGREGATE-v1",
    "total_plays": 0,
    "unique_tracks_played": 0,
    "by_track": {},
    "most_played": [],
    "least_played": [],
    "recent": [],
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "note": "Excavationpro play board — recreate when jsonblob free TTL expires",
}

def main() -> int:
    data = json.dumps(SEED).encode()
    req = urllib.request.Request(
        "https://jsonblob.com/api/jsonBlob",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        blob_id = r.headers.get("X-jsonblob-id")
        loc = r.headers.get("Location")
        exp = r.headers.get("X-jsonblob-expires-at")
    url = f"https://jsonblob.com/api/jsonBlob/{blob_id}"
    print("NEW_BLOB_ID", blob_id)
    print("URL", url)
    print("EXPIRES", exp)
    print("Update BLOB const in listen-plugins/play-listing.js then bump ?v=")
    # write pointer file
    ptr = Path(__file__).resolve().parents[1] / "data" / "music_catalog" / "play_board_blob.json"
    ptr.parent.mkdir(parents=True, exist_ok=True)
    ptr.write_text(json.dumps({"blob_id": blob_id, "url": url, "expires_at": exp, "created": SEED["updated_at"]}, indent=2), encoding="utf-8")
    print("wrote", ptr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
