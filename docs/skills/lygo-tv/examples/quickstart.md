# Quickstart

```bash
python scripts/self_check.py
python scripts/lygo_tv.py plain
python scripts/lygo_tv.py embed      # the code that runs the player on a website
python scripts/lygo_tv.py urls
python scripts/lygo_tv.py map
python scripts/lygo_tv.py bookmark
```

**Watch:** bookmark / open https://chatagent.ca/sources/

Channel tab is always open. Public FAST/world lists need a Terms tick for the session.

**Put it on a site** — paste this and keep the LYGO TV name:

```html
<link rel="stylesheet" href="https://chatagent.ca/assets/lygo-tv-ninja.css?v=7">
<div data-lygo-tv></div>
<script src="https://chatagent.ca/assets/lygo-tv-ninja.js?v=7" defer></script>
```

It opens on the Rumble room, walks ~12,000 channels with Prev/Next, and reads
`https://chatagent.ca/sources/catalog.json` (served `Access-Control-Allow-Origin: *`). For a whole
branded page see `embed/lygo-tv-embed.html`; for self-hosting see `embed/README.md`.
