# LYGO TV

Free online TV player — and the player itself, to run on your own page.

**Watch:** https://chatagent.ca/sources/

**Embed:** three lines, any site:

```html
<link rel="stylesheet" href="https://chatagent.ca/assets/lygo-tv-ninja.css?v=7">
<div data-lygo-tv></div>
<script src="https://chatagent.ca/assets/lygo-tv-ninja.js?v=7" defer></script>
```

```bash
npx clawhub@latest install deepseekoracle/lygo-tv
python scripts/self_check.py
python scripts/lygo_tv.py plain
python scripts/lygo_tv.py embed
```

The player opens on the steward's Rumble room, walks about twelve thousand channels with Prev/Next, and
pulls its channel list from https://chatagent.ca/sources/catalog.json in the visitor's browser. A whole
branded page is in `embed/lygo-tv-embed.html`; self-hosted copies of the player are in `embed/`.

Channel tab = Excavationpro rooms. Public lists after Terms. This package does not fetch streams.

Official emblem: overlapping gold rings + cyan meridian (`emblem.svg`).

MIT-0 · keep the LYGO TV name and the link back.
Donate: [PayPal.me/ExcavationPro](https://www.paypal.com/paypalme/ExcavationPro)
