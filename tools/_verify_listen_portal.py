#!/usr/bin/env python3
"""Verify listen portal integrity: playlist, streams, HTML SEO, live Pages, HF."""
from __future__ import annotations

import json
import random
import re
import sys
import urllib.request
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
EXCAV = STACK.parent / "Excavationpro"
CAT = STACK / "data" / "music_catalog"
STREAM = Path(r"I:\E Drive\MUSIC_VAULT\public_stream")


def main() -> int:
    errors: list[str] = []
    warns: list[str] = []

    pl = json.loads((CAT / "public_stream_playlist.json").read_text(encoding="utf-8"))
    tracks = pl.get("tracks") or []
    n = len(tracks)
    playable = sum(1 for t in tracks if t.get("stream_url"))
    base = pl.get("public_base_url") or ""
    print("=== PLAYLIST ===")
    print(f"tracks={n} playable={playable} gb={(pl.get('stats') or {}).get('total_stream_gb')}")
    print(f"base={base}")
    if playable != n:
        errors.append(f"playable {playable} != tracks {n}")
    if "huggingface.co" not in base:
        errors.append("missing HF base url")

    mp3s = list(STREAM.glob("*.mp3")) if STREAM.exists() else []
    print(f"disk_mp3={len(mp3s)}")
    if len(mp3s) != n:
        warns.append(f"disk mp3 {len(mp3s)} vs playlist {n}")

    missing_file = 0
    for t in tracks:
        sf = t.get("stream_file") or f"{t.get('sha256')}.mp3"
        if not (STREAM / sf).exists():
            missing_file += 1
    print(f"missing_local_file={missing_file}")
    if missing_file:
        warns.append(f"{missing_file} playlist entries missing local mp3")

    random.seed(42)
    sample = random.sample(tracks, min(8, len(tracks)))
    ok_http = 0
    for t in sample:
        url = t["stream_url"]
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 Excavationpro-Verify/1.0",
                    "Range": "bytes=0-2047",
                },
            )
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read()
                if r.status in (200, 206) and body:
                    ok_http += 1
                else:
                    errors.append(f"HTTP {r.status} {(t.get('title') or '')[:40]}")
        except Exception as e:
            errors.append(f"HTTP fail {(t.get('title') or '')[:40]}: {e}")
    print(f"HTTP_sample_OK={ok_http}/{len(sample)}")

    print("=== LISTEN HTML ===")
    html = (EXCAV / "excavationpro-listen.html").read_text(encoding="utf-8")
    checks = {
        "PayPal": "paypalme/ExcavationPro" in html or "paypal.com/paypalme/ExcavationPro" in html,
        "AdSense_pub": "ca-pub-0646320966060599" in html,
        "robots_index": "index, follow" in html.lower(),
        "JSON-LD": "application/ld+json" in html,
        "canonical": 'rel="canonical"' in html and "excavationpro-listen.html" in html,
        "Kick": "kick.com/excavationpro" in html.lower(),
        "Twitch": "twitch.tv/excavationpro" in html.lower(),
        "Rumble_live": "rumble.com/user/excavationpro/live" in html.lower(),
        "cookie_consent": "cookiesAccepted" in html,
        "ads_consent_gate": "loadAdSenseScript" in html,
        "MusicPlaylist": "MusicPlaylist" in html,
        "numTracks_4283": '"numTracks": 4283' in html or f'"numTracks":{n}' in html.replace(" ", ""),
        "track_count_text": str(n) in html,
    }
    for k, v in checks.items():
        print(("OK" if v else "FAIL"), k)
        if not v:
            errors.append(f"HTML missing {k}")

    m = re.search(r'<script id="boot"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        errors.append("no boot JSON")
    else:
        boot = json.loads(m.group(1))
        bt = len((boot.get("playlist") or {}).get("tracks") or [])
        print(f"embedded_tracks={bt}")
        if bt != n:
            errors.append(f"embedded {bt} != playlist {n}")
        # ensure stream urls in boot
        with_url = sum(1 for t in (boot.get("playlist") or {}).get("tracks") or [] if t.get("stream_url"))
        print(f"embedded_with_url={with_url}")
        if with_url != bt:
            errors.append(f"embedded urls {with_url} != {bt}")

    print("=== VAULT ===")
    vault = json.loads((CAT / "music_vault_manifest.json").read_text(encoding="utf-8"))
    vo = (vault.get("stats") or {}).get("unique_objects")
    print(f"vault_objects={vo} merkle={(vault.get('merkle_root') or '')[:32]}")
    if vo != n:
        warns.append(f"vault objects {vo} != playlist {n}")

    print("=== CRAWLERS ===")
    sm = (EXCAV / "sitemap.xml").read_text(encoding="utf-8")
    rob = (EXCAV / "robots.txt").read_text(encoding="utf-8")
    ads = (EXCAV / "ads.txt").read_text(encoding="utf-8")
    for label, ok in [
        ("sitemap_listen", "excavationpro-listen.html" in sm),
        ("robots_allow", "Allow: /" in rob),
        ("ads_txt_pub", "pub-0646320966060599" in ads),
    ]:
        print(("OK" if ok else "FAIL"), label)
        if not ok:
            errors.append(label)

    print("=== LIVE PAGES ===")
    for url in [
        "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
        "https://deepseekoracle.github.io/Excavationpro/sitemap.xml",
        "https://deepseekoracle.github.io/Excavationpro/ads.txt",
        "https://deepseekoracle.github.io/Excavationpro/robots.txt",
    ]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read()
                print(url.rsplit("/", 1)[-1], r.status, "len", len(body))
                if url.endswith("listen.html"):
                    text = body.decode("utf-8", "replace")
                    for label, needle in [
                        ("live_paypal", "paypalme"),
                        ("live_adsense", "ca-pub-0646320966060599"),
                        ("live_kick", "kick.com"),
                        ("live_4283", "4283"),
                        ("live_stream_url", "huggingface.co/datasets/DeepSeekOracle"),
                    ]:
                        hit = needle.lower() in text.lower()
                        print(("OK" if hit else "FAIL"), label)
                        if not hit:
                            # Pages lag is warning not hard fail for 4283
                            if label == "live_4283":
                                warns.append("Live Pages may still be old cache (no 4283 yet)")
                            else:
                                errors.append(f"live missing {label}")
        except Exception as e:
            errors.append(f"live fetch {url}: {e}")
            print("FAIL", url, e)

    print("=== HF ===")
    try:
        from huggingface_hub import HfApi

        token = (Path.home() / ".cache" / "huggingface" / "token").read_text(encoding="utf-8").strip()
        api = HfApi(token=token)
        files = list(api.list_repo_files("DeepSeekOracle/excavationpro-music-stream", repo_type="dataset"))
        mp3 = sum(1 for f in files if f.endswith(".mp3"))
        print(f"HF_files={len(files)} mp3={mp3}")
        if mp3 != n:
            warns.append(f"HF mp3 {mp3} vs playlist {n}")
    except Exception as e:
        warns.append(f"HF list fail: {e}")
        print("HF list fail", e)

    print("=== SUMMARY ===")
    for w in warns:
        print("W", w)
    for e in errors:
        print("E", e)
    print("WARNINGS", len(warns), "ERRORS", len(errors))
    print("RESULT", "PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
