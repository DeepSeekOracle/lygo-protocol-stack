# LYGO TV — embed the player

Two ways in. Take the hosted one unless you have a reason not to: it stays current by itself.

## 1. Hosted (recommended) — three lines, any page

```html
<link rel="stylesheet" href="https://chatagent.ca/assets/lygo-tv-ninja.css?v=7">
<div data-lygo-tv></div>
<script src="https://chatagent.ca/assets/lygo-tv-ninja.js?v=7" defer></script>
```

That is the whole install. The player:

- opens on **Excavationpro Rumble LIVE** (`rumble_live`) by default
- walks the pool with **Prev / Next** — about **12,000 channels**, with a `title · 3 / 12165` counter
- carries a **Sound** button (sound starts off: browsers block unmuted autoplay without a gesture)
- links back to the full player at https://chatagent.ca/sources/

It reads its channel list from **https://chatagent.ca/sources/catalog.json** in the visitor's browser.
That response is served with `Access-Control-Allow-Origin: *`, so any site may pull it — no proxy, no key,
no build step. Add a channel on our side and it appears in your embed.

Hosted files are versioned by query string (`?v=7`). Bump it when the player changes; the old version stops
being served when the file changes, so a bump is safe.

## 2. Vendored (self-hosted)

`lygo-tv-ninja.js` and `lygo-tv-ninja.css` in this folder are the complete player, byte-for-byte the files
the site serves. Copy them beside your page and point the tags at your copies:

```html
<link rel="stylesheet" href="/assets/lygo-tv-ninja.css">
<div data-lygo-tv></div>
<script src="/assets/lygo-tv-ninja.js" defer></script>
```

The player still fetches `catalog.json` from chatagent.ca — self-hosting the code does not cut the channel feed.
Trade-off: you keep the file, but you also own updating it. Vendored copies go stale.

## A whole page, branded and ready

`lygo-tv-embed.html` is a complete, styled page you can serve as-is or paste from.

## Theme it

The stylesheet inherits your variables, so the player matches your site without editing it:

| Variable | Use |
|----------|-----|
| `--bg` | player background |
| `--fg` | player text |
| `--line` | borders |
| `--gold` / `--accent` | kicker, buttons, links |
| `--muted` | meta line, hints |

## Honest limits

- **Autoplay:** sound is off until the visitor presses Sound. No page can override that; it is the browser's rule.
- **Geo-blocks and dead rooms:** some channels refuse some countries, and streams come and go. The player names a
  miss rather than faking a channel.
- **Third-party platforms:** Rumble, Kick, Twitch and YouTube rooms load as their own embeds, so their terms
  apply to their content.
- **No proxy, no decrypt, no XXX list.** Do not wrap this player in one. If you need a channel that will not
  embed, link it instead.

## Licence and brand

MIT-0: use it, restyle it, ship it. Keep the LYGO TV name and the link to https://chatagent.ca/sources/ in place —
that link is the whole payment for the feed. Do not present it as your own player, and do not sell access to it.
