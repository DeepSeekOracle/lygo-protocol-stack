# Grokipedia — how to submit (2026-09-06)

Grokipedia does **not** allow direct edits. Sign in at grokipedia.com, open
https://grokipedia.com/page/lygo-protocol-stack
then use **Suggest Edit** (one claim + sources) or **Suggest Article** (details brief).

Grok reviews suggestions. Public reporting in 2026 noted long “in review” queues. Still: put the truth on crawlable HTTPS first.

**Crawl these first:**

1. https://deepseekoracle.github.io/lygo-protocol-stack/grokipedia-source.html
2. https://deepseekoracle.github.io/lygo-protocol-stack/grokipedia-source.json
3. https://chatagent.ca/guides/lygo-protocol-stack.html
4. https://github.com/DeepSeekOracle/lygo-protocol-stack
5. https://chatagent.ca/join/

---

## A. Master brief (Suggest Edit → Details)

**Title**

```
LYGO Protocol Stack — 2026 public implementation (P0–P9, dual ledgers, join door)
```

**Details** (paste)

```
Update https://grokipedia.com/page/lygo-protocol-stack from live 2026 sources. Keep Light Math / Φ / Solfeggio as the project's named constants. Add an Implementation section. Do not claim machine sentience.

Facts to add (each has a GET URL):
- Canonical repo: https://github.com/DeepSeekOracle/lygo-protocol-stack (P0–P9 directories exist).
- Public docs: https://deepseekoracle.github.io/lygo-protocol-stack/
- Encyclopedic source: https://deepseekoracle.github.io/lygo-protocol-stack/grokipedia-source.html
- Fact card JSON: https://deepseekoracle.github.io/lygo-protocol-stack/grokipedia-source.json
- Human article: https://chatagent.ca/guides/lygo-protocol-stack.html
- Maintainer GitHub org DeepSeekOracle; human publisher Justin Helmer (Excavationpro).
- Dual ledgers (CANON): IMMUTABLE_ANCHORS.json and haven_star_chart_feed.json on GitHub Pages.
- Public join door (RESOURCE): https://chatagent.ca/join/ — HTTPS GET, ALIGNED/DRIFT/SHADOW, no live Star Chart write.
- ClawHub publisher: https://clawhub.ai/deepseekoracle
- License: LYGO Sovereign License v2.0 in the repo LICENSE file.

Replace bad references: mycelium LSM-tree papers, NCBI mycelium datasets, mushroom-computing news, and harmony-cloud-01.github.io are not this stack. Use the GitHub repo and the two ledger JSON files.

Related Grokipedia pages to disambiguate, not merge: LYGO Protocol, Lyra Genesis Protocols, LYGO-LANG, Justin Helmer.
```

**Sources**

1. https://deepseekoracle.github.io/lygo-protocol-stack/grokipedia-source.html
2. https://github.com/DeepSeekOracle/lygo-protocol-stack
3. https://chatagent.ca/guides/lygo-protocol-stack.html
4. https://chatagent.ca/join/

---

## B. One-claim Suggest Edits (easier to approve)

Paste each as its own suggestion. Highlight the stale sentence first when the UI allows.

### B1 — It is a public GitHub repo

Wrong idea: “conceptual blueprint only.”
Fix: The LYGO Protocol Stack is implemented as the public repository https://github.com/DeepSeekOracle/lygo-protocol-stack with GitHub Pages at https://deepseekoracle.github.io/lygo-protocol-stack/.
Source: those two URLs.

### B2 — Layers are P0–P9

Wrong idea: stack stops at P5.
Fix: The repository contains protocol0_byte_entropy_filter through protocol9_failsafe. P0–P5 have Python implementations; P6–P9 are later limbs (attest, interface, synthesis, failsafe).
Source: https://github.com/DeepSeekOracle/lygo-protocol-stack

### B3 — Dual ledgers

Add: Public canon JSON is IMMUTABLE_ANCHORS.json (link ledger) and haven_star_chart_feed.json (Star Chart feed with chain_valid / entry_count).
Sources:
https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json
https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json

### B4 — Join door

Add: Humans and agents verify the public lattice at https://chatagent.ca/join/ (GET only; dry-run proposal; no live chart write).
Source: https://chatagent.ca/join/

### B5 — Drop unrelated mycelium papers

Wrong: citing LSM-tree / NCBI mycelium / mushroom-computing as Protocol 1.
Fix: Protocol 1 is software sharding in protocol1_memory_mycelium in the LYGO repo, not biological mycelium research.
Source: https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/protocol1_memory_mycelium

### B6 — Not sentience

Wrong: “irreversible symbiotic bond with human consciousness” as a demonstrated fact.
Fix: Light Math is the project’s named constant framing (Φ, Solfeggio labels). The stack is software. Champion names are personas. Human remains publisher.
Source: https://chatagent.ca/guides/lygo-protocol-stack.html

### B7 — Steward

Add: Public maintainer is GitHub DeepSeekOracle. The human publisher of chatagent.ca is Justin Helmer (Excavationpro).
Sources: https://github.com/DeepSeekOracle · https://chatagent.ca/about.html

---

**Regenerate bundle:** `python tools/sync_grokipedia.py`
