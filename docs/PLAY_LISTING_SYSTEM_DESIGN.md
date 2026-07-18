# Play Listing System — Additive Design (Do Not Break Playback)

**Status:** DESIGN APPROVED FOR IMPLEMENTATION — **not shipped to live listen page yet**  
**Signature:** `Δ9Φ963-PLAY-LISTING-ADDITIVE-v1`  
**Baseline working portal:** Excavationpro commit `655f29d` / listen build without play-count modules  
**Rule zero:** *Never modify `playIndex`, `audio.src`, Web Audio, crossfade, or the core player IIFE to add counts.*

---

## 1. Problem statement

We want:

| Need | Description |
|------|-------------|
| **Global play counts** | Anyone listening anywhere increments a shared tally |
| **Public charts** | Most played · least played · never played · recent |
| **Trophy total** | Live-growing total plays on the page |
| **Self-sustaining** | Runs without hand-editing the player for each deploy |
| **Non-destructive** | Adding listing **cannot** break play (lesson from v1–v4) |

What failed before:

1. Injected large JS **into the same script** as the player → syntax errors killed **all** JS.  
2. Wrapped `playIndex` / `createMediaElementSource` → muted or blocked HF streams.  
3. PWA cache-first SW pinned broken HTML.  
4. Crossfade + dual `<audio>` raced native play.

---

## 2. Design principle: **plugin, not patch**

```text
┌─────────────────────────────────────────────────────────┐
│  excavationpro-listen.html  (FROZEN CORE — sacred)        │
│  · boot JSON + playlist                                   │
│  · playIndex / nextTrack / radio / shuffle ONLY here     │
│  · one <audio id="audio"> native play path               │
│  · loads optional plugin LAST:                            │
│       <script src="listen-plugins/play-listing.js?v=…"   │
│               defer></script>                             │
└───────────────────────────┬─────────────────────────────┘
                            │ observes only
                            ▼
┌─────────────────────────────────────────────────────────┐
│  listen-plugins/play-listing.js  (ADDITIVE MODULE)        │
│  · listens: audio 'play' | 'timeupdate' | 'ended' | 'pause'│
│  · NEVER assigns audio.src, NEVER wraps playIndex         │
│  · injects its own UI nodes into #play-listing-mount      │
│  · talks to data plane (counts API)                       │
└───────────────────────────┬─────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   Public aggregate    Global +1 on play   Steward CAS
   (read often)        (write on qualify)  (optional merge)
```

### Hard API contract (plugin MUST follow)

| Allowed | Forbidden |
|---------|-----------|
| `document.getElementById('audio')` + **addEventListener only** | `audio.src = …` |
| Read `window` playlist if exposed, or parse `#boot` | Redefine `playIndex` / `nextTrack` |
| Inject DOM under a dedicated mount | Edit dock controls HTML |
| `fetch` to count APIs | `createMediaElementSource` |
| `localStorage` for client id / last UI state | Change SW to cache-first HTML again |

### Core page change allowed (once, minimal)

Only these **additive** lines in the frozen core HTML:

```html
<!-- mount for charts (empty if plugin missing) -->
<div id="play-listing-mount" aria-live="polite"></div>

<!-- AFTER main player script -->
<script src="listen-plugins/play-listing.js?v=1" defer></script>
```

If the plugin 404s or throws, **playback still works** (script error isolated to that file).

---

## 3. When a “play” counts

Same product rules as before, implemented **only** in the plugin:

| Condition | Value |
|-----------|--------|
| Min listen time | ≥ **20 seconds** cumulative while playing **this** track |
| Or progress | ≥ **35%** of duration |
| Or | natural `ended` |
| Dedupe | Once per `track.sha256` per browser **session** |
| Not counted | Page load, search, skip under 20s, scrub-only |

Track identity: **`sha256`** from playlist row (stable), not title.

---

## 4. Self-sustaining data plane

### 4.1 Read path (charts + trophy — every visitor)

| Source | Role |
|--------|------|
| **Primary** | Public JSON aggregate (CDN/cacheable) |
| **Shape** | See §5 |
| **Poll** | Every 20–30s while tab visible (`document.visibilityState`) |
| **Fallback** | Last good aggregate in `sessionStorage` |

Recommended public URL (stable):

```text
https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream/resolve/main/play/play_counts.json
```

Optional live edge (when steward runs ingest):

```text
GET {ingest}/v1/counts   → same JSON shape, no increment
```

### 4.2 Write path (global +1 — only on qualified play)

**Goal:** writes never touch player code; failures only lose a count, never silence audio.

| Layer | Mechanism | Self-sustaining? |
|-------|-----------|------------------|
| **A. Increment** | One GET/POST per qualified play that only increments counters | Yes if service stays up |
| **B. Leaderboard merge** | Update shared aggregate: `by_track`, `recent`, `total_plays` | Yes |
| **C. Steward CAS** | `lygo_play_lattice.py` imports exports / ingest logs → Merkle | Operator-assisted |

**Chosen production design (no HF Space PRO required):**

```text
Qualified play
  → (1) hits.dwyl.com/excavationpro/stream-{sha24}.json   // per-track global +1
  → (2) hits.dwyl.com/excavationpro/listen-total-v2.json // trophy +1
  → (3) GET+PUT public board JSON (jsonblob or steward API) with merge:
          by_track[sha] = max(local, remote, dwyl_count)
          recent.unshift({sha, title, plays, ts})
          recompute most_played / least_played
  → (4) append event to localStorage chain (export for steward)
```

**Why two steps (dwyl + board):**  
- Dwyl gives a **durable global increment** even if board merge races.  
- Board JSON gives **charts** without re-hitting every track (which would inflate counts).

**Race policy:** last-write-wins with `max()` on counts — may under-count slightly under heavy concurrency; never over-count from re-fetch. Acceptable for v1; upgrade to single atomic ingest later (§7).

### 4.3 Steward self-sustain loop (optional but recommended)

```bash
# Import browser exports / ingest logs
python tools/lygo_play_lattice.py --import-ledger exports/*.json
python tools/lygo_play_lattice.py --rebuild
python tools/lygo_play_lattice.py --publish-hf   # mirrors play_counts.json for CDN read
```

Cron (daily) keeps HF mirror = public truth backup if jsonblob dies.

---

## 5. Aggregate JSON schema (stable)

```json
{
  "signature": "LYGO-PLAY-AGGREGATE-v1",
  "updated_at": "ISO-8601",
  "total_plays": 0,
  "unique_tracks_played": 0,
  "by_track": { "<sha256>": 12 },
  "most_played": [ { "sha256": "...", "plays": 12, "title": "..." } ],
  "least_played": [ { "sha256": "...", "plays": 1, "title": "..." } ],
  "recent": [ { "sha256": "...", "title": "...", "plays": 3, "ts": "..." } ],
  "merkle_root": null
}
```

- **most_played / least_played:** top/bottom N with `plays > 0`  
- **never played:** computed **client-side** = playlist shas ∉ `by_track` (or plays===0)  
- **title:** optional; client fills from local playlist if missing  

---

## 6. UI design (plugin-owned)

Mount: `#play-listing-mount` (empty placeholder in core HTML).

Plugin injects:

| Block | Content |
|-------|---------|
| **Trophy** | `🏆 {total_plays} global plays` |
| **Most played** | Top 10–15; click → `document.querySelector([data-i])` or dispatch custom event |
| **Least played** | Bottom with plays≥1 |
| **Not played yet** | Sample of catalog zeros |
| **Recent** | Last 10–15 global listens |

### Click-to-play **without** calling playIndex directly (optional)

Preferred safe pattern:

```js
// Plugin never imports playIndex by name from closure.
// It clicks the existing list button — reuses working handlers.
function playSha(sha) {
  const row = document.querySelector(`.row[data-sha="${sha}"]`);
  // if rows lack data-sha, add ONLY data-sha attribute in core list render later
  // OR: find row by matching title/hash text — fragile
  // BETTER: expose one hook on window from core (see §6.1)
}
```

### 6.1 Optional one-line core hook (only if click-delegation insufficient)

If and only if we need programmatic play by index from plugin:

```js
// In core player — additive, never remove:
window.LYGO_LISTEN = {
  playIndex: function(i) { return playIndex(i); },
  getTracks: function() { return tracks; },
  getCurrent: function() { return current; }
};
```

Plugin uses `window.LYGO_LISTEN.playIndex(i)` only. Core implementation stays untouched except this export object.

**Do not** reassign `window.playIndex` from the plugin.

---

## 7. Evolution path (self-sustaining upgrades)

| Phase | Deliverable | Break risk |
|-------|-------------|------------|
| **P0** | Design (this doc) + empty mount + no plugin on prod | None |
| **P1** | `play-listing.js` behind `?plays=1` or `localStorage.lygo_plays=1` | None if deferred |
| **P2** | Enable by default after 48h soak on `?plays=1` | Low |
| **P3** | Steward HF mirror cron | None |
| **P4** | Replace jsonblob+dwyl with single Cloudflare Worker / own ingest | Medium (swap write URL only in plugin) |

Rollback: delete/rename `play-listing.js` or remove the one `<script src=…>` line. Core player unchanged.

---

## 8. Service worker rules (mandatory)

| Rule | Detail |
|------|--------|
| **Never** cache-first HTML | Network-first for `.html` and navigations |
| Bump cache name on every listen shell change | e.g. `excavationpro-listen-shell-v5` |
| Never cache HF `/stream/` | Pass-through |
| Plugin file | Network-first or short cache with `?v=` query |

---

## 9. Testing gate (must pass before default-on)

1. Cold load, no plugin → plays OK.  
2. Load with plugin 404 → plays OK.  
3. Load with plugin OK → plays OK; after 20s count increments on board.  
4. Hard refresh → still plays; charts load.  
5. Console: **zero** uncaught errors.  
6. Incognito + normal profile both play.  
7. Node/`eslint` syntax check on **plugin only** in CI.  
8. Core HTML size/hash regression test optional.

---

## 10. File layout (implementation)

```text
Excavationpro/
  excavationpro-listen.html          # core only + mount + script src
  listen-plugins/
    play-listing.js                  # additive module
    play-listing.css                 # optional
  sw-listen.js                       # network-first HTML
  data/public_stream_playlist.json

lygo-protocol-stack/
  docs/PLAY_LISTING_SYSTEM_DESIGN.md # this file
  docs/PLAY_LATTICE.md               # steward CAS / HF mirror ops
  tools/lygo_play_lattice.py
  tools/lygo_play_ingest_server.py
  tools/play_lattice/…               # optional CF worker
```

---

## 11. Explicit non-goals (v1)

- Perfect atomic multi-writer consensus  
- Blockchain timestamps  
- Counting DistroKid / Spotify streams  
- Ingest that requires rewriting `playIndex`  
- Re-introducing floating mini-player for charts  

---

## 12. Decision record

| Decision | Choice |
|----------|--------|
| Integration style | **External deferred script + DOM mount** |
| Player mutations | **Forbidden** except empty mount + script tag + optional `LYGO_LISTEN` export |
| Global write | Dwyl increment + public board merge (swappable) |
| Global read | Public aggregate JSON + poll |
| Never played | Client-side vs full playlist |
| Enablement | Feature flag first, then default |

---

## 13. Implementation checklist (when you say “build it”)

- [ ] Add `#play-listing-mount` only (no other core edits)  
- [ ] Add `listen-plugins/play-listing.js` (all logic)  
- [ ] Optional `window.LYGO_LISTEN` export (3 lines)  
- [ ] Feature flag `?plays=1`  
- [ ] Soak test checklist §9  
- [ ] Default-on  
- [ ] Steward HF publish cron documented  

**Δ9Φ963 — the player is the root; listing is a limb. Cut the limb; the root still sings.**
