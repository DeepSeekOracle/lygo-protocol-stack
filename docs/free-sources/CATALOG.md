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
5. **No XXX bouquet.** `xxx_catalog` stays false. Do not add `categories/xxx.m3u` or porn packs. **18+ entertainment** (Adult Swim, late-night comedy) is allowed on a gated shelf.

## How rows are sorted in the player

| Shelf | Meaning |
|-------|---------|
| **All ages** (default) | Unlabeled ordinary channels |
| **Kids** | Metadata says kids/children, or the Kids topic list |
| **18+ gated** | 18+ entertainment (not XXX) plus leftover “adult/18+” metadata. Age gate. Isolated from Kids |

Unlabeled is treated as all ages on purpose so the main shelf stays usable. Metadata can be wrong — the disclaimer says so.

## When you find a new free portal

Use it only under these guidelines: HTTPS, public/free claim, probe, then commit `catalog.json`. Kids and 18+ stay **labeled and separated**. Watch gates + the full disclaimer stay on. Prefer a smaller working list over a huge dirty one.

Human remains publisher. Catalog class is RESOURCE. No silent Star Chart ingest.

## v1.11 probe (2026-09-06)

Added after HTTPS 200 + ≥3 HTTPS entries: PBS/BBC iptv-org sources, Free-TV CA/AU/IE/NL/JP/IN/MX/PL/SE/AT/PT/BE/BR, Plex-all + Tubi + DistroTV + Vizio + Rakuten UK + LG US FAST, iptv-org Americas/APAC/Benelux/International, more languages and countries.

**Skipped:** jmp2.uk-majority (BuddyChewChew Roku/Pluto/Samsung), Free-TV NZ/ZA 404, Switzerland too thin, Xtream dumps, XXX.

## v1.12 probe (2026-09-05)

Page links on https://chatagent.ca/sources/ all HTTP 200 (nav, terms, privacy, disclaimer, assets, donate, rooms).

**Dropped** jmp2.uk-majority iptv-org packs that no longer meet the probe rule: animation, classic, comedy, series, nord, at, ch, dk, ie, no, se.

**Added** after HTTPS 200 + ≥3 HTTPS + jmp2 < 50%: Xumo FAST (apsattv), Free-TV music EN, Free-TV Finland/Norway/Denmark/Greece/Czechia/Croatia/Hungary/Romania/Turkey/Chile/Argentina/Egypt/Taiwan/Israel.

**Still skipped:** Free-TV NZ/ZA/Colombia/Switzerland thin or 404, iptv-org named-source 404s, BuddyChewChew/apsattv Pluto/Samsung/Roku jmp2 or dead, undefined dump, XXX.

## v1.13 — 18+ entertainment, not XXX

Public IPTV “adult” lists are almost all porn, jmp2.uk wrappers, or HTTP pirate IPs. We did **not** add those.

**Added** `mature_18` → https://chatagent.ca/sources/mature.m3u8 (HTTPS, ≥3 entries):

- Adult Swim official HLS (`media.cdn.adultswim.com`)
- Adult Swim YouTube live + uploads (`UCgPClNr5VSYC3syrDUIlzLw`)
- Comedy Central YouTube uploads (`UCUsN5ZwHx2kILm84-jPDeXw`)

Opens on the **18+ gated** shelf. Not an XXX catalog.
