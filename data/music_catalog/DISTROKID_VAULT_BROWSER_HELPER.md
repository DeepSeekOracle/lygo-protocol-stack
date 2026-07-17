# DistroKid Vault Browser Helper (run while logged in)

DistroKid vault pages are **session-authenticated**. This helper does **not** bypass login —
you paste it into the browser console on vault pages while signed in as EXCAVATIONPRO.

## A. From a vault folder page (list of songs)

1. Open https://distrokid.com/vault/ (or your folder URL)
2. Press F12 → Console
3. Paste:

```javascript
(async () => {
  const links = [...document.querySelectorAll('a[href*="/vault/file/"]')];
  const hrefs = [...new Set(links.map(a => a.href))];
  console.log('Found file links:', hrefs.length);
  copy(hrefs.join('\n'));
  alert('Copied ' + hrefs.length + ' vault file URLs to clipboard. Paste into vault_urls.txt');
})();
```

## B. From each song page (metadata scrape)

On a single song/file page (`/vault/file/?id=...`), paste:

```javascript
(() => {
  const text = document.body.innerText;
  const isrc = (text.match(/ISRC[:\s]*([A-Z0-9\-]{12,15})/i) || [])[1] || '';
  const upc = (text.match(/UPC[:\s]*(\d{12,13})/i) || [])[1] || '';
  const title = (document.querySelector('h1,h2,.title') || {}).innerText || document.title;
  const row = {url: location.href, title, isrc, upc, rawSnippet: text.slice(0, 2000)};
  copy(JSON.stringify(row, null, 2));
  console.log(row);
  alert('Metadata JSON copied');
})();
```

## C. Bulk: open all folder links and collect (manual queue)

1. Save folder link list to `vault_urls.txt` (one URL per line)
2. Run local collector later:  
   `python tools/music_catalog_recovery.py --import-json path\to\scraped.jsonl`

## D. What DistroKid support can still give you

Even with store restriction, email **support@distrokid.com** and request:

- Full **ISRC / UPC / release date / store delivery** export for account artist **Excavationpro**
- Confirmation whether existing live releases remain on stores or will be taken down
- Any bank/tax export for your records

Keep the Ania email as a record. Ask for a **data export** — many distributors can still provide metadata even when delivery is blocked.

## E. Alternate public sources

- Spotify artist: https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S
- Feature.fm / ffm: https://ffm.to/eovnvo9
- Local disk: J:\ (ISRC often in filename)

## F. New distributor checklist (per release)

For each track/album you need typically:

| Field | Source |
|-------|--------|
| Artist name | Excavationpro |
| Track title | vault / Spotify / filename |
| Album / release title | vault |
| ISRC | vault / filename |
| UPC (album) | vault |
| Release date | vault / Spotify |
| Genre | your notes |
| Lyrics / explicit | your notes |
| Audio master | vault download / J:\ |

Primary deliverable from this toolkit: `excavationpro_catalog.csv`
