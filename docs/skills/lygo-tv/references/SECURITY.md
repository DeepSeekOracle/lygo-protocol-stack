# Security — lygo-tv v1.3.0

**This folder is a ClawHub pointer plus the player code to paste.** Isolation claims apply only to the
Python and the shipped files here; nothing in this folder fetches anything when you install it.

| Surface | This package |
|---------|----------------|
| Network in scripts | **None** (no urllib/requests/http.client) |
| Subprocess / shell | **None** |
| Filesystem write | **None** |
| Stream proxy / CORS bypass | **No** |
| Pay-TV decrypt | **No** |
| Live Star Chart write | **No** |
| git / HF / ClawHub / social | **No** |

Printed URLs (player, catalog.json, terms, disclaimer, donate) are for **you** to open. If another skill fetches them, that skill must declare network.

## The embed (v1.3.0)

`embed/lygo-tv-ninja.js` + `embed/lygo-tv-ninja.css` are the player, and `embed/lygo-tv-embed.html` is a page
built on it. They are **code for the human's website**, not code this skill runs: the visitor's browser loads
the player and reads `https://chatagent.ca/sources/catalog.json`, which is served
`Access-Control-Allow-Origin: *` so any origin may read it. Embedding puts the channels on someone else's page
in their visitors' browsers — it does not proxy, decrypt, or store anything, and no stream passes through this
package or through the steward's servers. Loading a page is the human's decision on the human's site.

The live player is a static GitHub Pages page. Catalog class is **RESOURCE**. Dual ledgers remain **CANON**.

**Δ9Φ963 — point · do not proxy · do not invent channels.**
