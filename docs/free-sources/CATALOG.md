# LYGO TV catalog — quality rules

Live player: https://chatagent.ca/sources/  
Disclaimer: https://chatagent.ca/sources/disclaimer.html

This file is for humans who add lists. The player is a **portal only**. We do not host, decrypt, or proxy streams.

## What we are building

A growing catalog of **free-to-access public channels** found on the internet (public M3U, FAST, official embeds). Honest labels. Open to use. Quality over dump size.

## Must be true before a list is added

1. **Free to watch online** according to the source (public broadcaster, FAST, official embed). Not a stolen pay-TV pack.
2. **HTTPS** playlist URL. HTTP stream rows are skipped in the player.
3. Probe: HTTP 200 and at least 3 HTTPS entries.
4. No Xtream logins, no VOD movie packs, no decrypt, no pirate proxy (including jmp2.uk-style wrappers we chose not to ship).
5. **No XXX / adult bouquet.** `xxx_catalog` stays false. Do not add `categories/xxx.m3u`.

## How rows are sorted in the player

| Shelf | Meaning |
|-------|---------|
| **All ages** (default) | Unlabeled ordinary channels |
| **Kids** | Metadata says kids/children, or the Kids topic list |
| **18+ gated** | Metadata looks adult (title/group). Isolated. Age gate. Not a destination catalog |

Unlabeled is treated as all ages on purpose so the main shelf stays usable. Metadata can be wrong — the disclaimer says so.

## When you find a new free portal

Use it only under these guidelines: HTTPS, public/free claim, probe, then commit `catalog.json`. Kids and 18+ stay **labeled and separated**. Watch gates + the full disclaimer stay on. Prefer a smaller working list over a huge dirty one.

Human remains publisher. Catalog class is RESOURCE. No silent Star Chart ingest.

## v1.11 probe (2026-09-06)

Added after HTTPS 200 + ≥3 HTTPS entries: PBS/BBC iptv-org sources, Free-TV CA/AU/IE/NL/JP/IN/MX/PL/SE/AT/PT/BE/BR, Plex-all + Tubi + DistroTV + Vizio + Rakuten UK + LG US FAST, iptv-org Americas/APAC/Benelux/International, more languages and countries.

**Skipped:** jmp2.uk-majority (BuddyChewChew Roku/Pluto/Samsung), Free-TV NZ/ZA 404, Switzerland too thin, Xtream dumps, XXX.
