#!/usr/bin/env python3
"""Refresh Excavationpro music lattice egg cores (catalog + vault) for planting."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
EGG = CAT / "egg_payload"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    EGG.mkdir(parents=True, exist_ok=True)

    # --- catalog egg (ISRC + links) ---
    by = {}
    cat_path = CAT / "excavationpro_catalog.json"
    if cat_path.exists():
        cat = json.loads(cat_path.read_text(encoding="utf-8"))
        for t in cat.get("tracks") or []:
            isrc = t.get("isrc")
            if isrc:
                by[isrc] = {"title": t.get("title"), "isrc": isrc}

    led = {}
    led_path = CAT / "excavationpro_music_ledger.json"
    if led_path.exists():
        led = json.loads(led_path.read_text(encoding="utf-8"))

    pl = {}
    pl_path = CAT / "public_stream_playlist.json"
    if pl_path.exists():
        pl = json.loads(pl_path.read_text(encoding="utf-8"))

    vault = {}
    vault_path = CAT / "music_vault_manifest.json"
    if vault_path.exists():
        vault = json.loads(vault_path.read_text(encoding="utf-8"))

    catalog_egg = {
        "signature": "Δ9Φ963-EXCAVATIONPRO-MUSIC-EGG-v1",
        "egg_id": "excavationpro-music-catalog-v1",
        "artist": "Excavationpro",
        "generated_at": utc(),
        "stats": {
            "unique_isrcs": len(by),
            "catalog_rows": len((json.loads(cat_path.read_text(encoding="utf-8")).get("tracks") or []) if cat_path.exists() else []),
            "streaming_albums": (led.get("stats") or {}).get("streaming_albums_total")
            or (led.get("stats") or {}).get("spotify_albums"),
            "ledger_sha256": (led.get("ledger") or {}).get("content_sha256"),
            "public_streams": len(pl.get("tracks") or []),
            "stream_gb": (pl.get("stats") or {}).get("total_stream_gb"),
        },
        "isrc_registry": [{"isrc": k, "title": by[k].get("title")} for k in sorted(by)],
        "live_links": {
            "listen": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
            "catalog": "https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html",
            "sovereign_vault": "https://deepseekoracle.github.io/Excavationpro/excavationpro-sovereign-music-hub.html",
            "eternal_haven": "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html",
            "hf_streams": "https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream",
            "spotify": "https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S",
            "kick": "https://kick.com/excavationpro",
            "rumble_live": "https://rumble.com/user/excavationpro/live",
            "twitch": "https://twitch.tv/excavationpro",
            "donate_paypal": "https://www.paypal.com/paypalme/ExcavationPro",
            "ffm": "https://ffm.to/eovnvo9",
        },
    }
    core_isrcs = json.dumps({"isrcs": sorted(by.keys())}, sort_keys=True).encode()
    catalog_egg["content_sha256"] = hashlib.sha256(core_isrcs).hexdigest()
    raw = json.dumps(catalog_egg, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(raw) > 90_000:
        catalog_egg["isrc_registry"] = [{"isrc": k} for k in sorted(by)]
        raw = json.dumps(catalog_egg, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    (EGG / "music_egg_core.json").write_bytes(raw)
    print("catalog egg bytes", len(raw), "isrcs", len(by), "sha", catalog_egg["content_sha256"][:16])

    # --- vault egg ---
    vault_egg = {
        "signature": "Δ9Φ963-SOVEREIGN-MUSIC-VAULT-v1",
        "egg_id": "excavationpro-music-vault-v1",
        "merkle_root": vault.get("merkle_root"),
        "stats": vault.get("stats") or {},
        "generated_at": utc(),
        "public_streams": len(pl.get("tracks") or []),
        "stream_gb": (pl.get("stats") or {}).get("total_stream_gb"),
        "stream_base": pl.get("public_base_url"),
        "hub": "excavationpro-sovereign-music-hub.html",
        "listen": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
        "hf_dataset": "https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream",
        "skill": "lygo-excavationpro-music-lattice",
        "live_portals": {
            "kick": "https://kick.com/excavationpro",
            "rumble_live": "https://rumble.com/user/excavationpro/live",
            "twitch": "https://twitch.tv/excavationpro",
        },
        "donate_paypal": "https://www.paypal.com/paypalme/ExcavationPro",
    }
    if vault.get("merkle_root"):
        (CAT / "music_vault_merkle_root.txt").write_text(vault["merkle_root"] + "\n", encoding="utf-8")
    (EGG / "music_vault_egg_core.json").write_text(
        json.dumps(vault_egg, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("vault egg merkle", (vault_egg.get("merkle_root") or "")[:24], "streams", vault_egg["public_streams"])

    # lattice seed receipt
    seed = {
        "signature": "Δ9Φ963-MUSIC-LATTICE-SEED-v1",
        "generated_at": utc(),
        "eggs": [
            "excavationpro-music-catalog-v1",
            "excavationpro-music-vault-v1",
            "excavationpro-music-lattice-skill-v1",
        ],
        "catalog_content_sha256": catalog_egg["content_sha256"],
        "vault_merkle_root": vault_egg.get("merkle_root"),
        "public_streams": vault_egg["public_streams"],
        "listen": vault_egg["listen"],
        "skill_slug": "lygo-excavationpro-music-lattice",
    }
    (CAT / "music_lattice_seed.json").write_text(json.dumps(seed, indent=2), encoding="utf-8")
    print("wrote seed", CAT / "music_lattice_seed.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
