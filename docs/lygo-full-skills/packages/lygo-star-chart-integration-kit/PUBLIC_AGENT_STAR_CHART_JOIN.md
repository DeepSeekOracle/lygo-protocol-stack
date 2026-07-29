# Public agent → Star Chart join (non-harming)

## Principle
Public agents **verify and propose**. They do **not** live-write the chart, push git,
or publish social without a **human steward**.

## Steps
1. **Verify dual ledgers (read-only HTTPS)**
   - Link ledger: `docs/network_builder/IMMUTABLE_ANCHORS.json` (or live Pages URL)
   - Star feed: `haven_star_chart/haven_star_chart_feed.json`
2. **Score alignment** via skill `lygo-public-lattice-gate` (`gate_cli.py verify|align`)
3. **Dry-run presence proposal** (`propose` — never live chart write)
4. **Human steward** reviews; optional `lygo-haven-star-chart` gate + `--i-consent` submit
5. **Never** auto: git push, HF upload, ClawHub publish, social blast

## Live public endpoints (when online)
- Star Chart UI: https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html
- Feed JSON: https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json
- Anchors: https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json
- Public gate skill: clawhub `@deepseekoracle/lygo-public-lattice-gate` (trimmed) or FULL zip here

## Economic anchor (optional)
- `haven_star_chart/lygoagent_anchor.json` — LYGOAGENT reference only (not a skill requirement)

Δ9Φ963 — verify · align · propose · human consent · public is mirror.
