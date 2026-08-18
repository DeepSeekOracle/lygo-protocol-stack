---
name: lygo-pure-data-witness
description: >
  Archive URLs/files as Pure-Data Witness digests with safety gates (HTTPS-only, SSRF block,
  malware/ad heuristics, size cap). Pack tiny kernel-egg fragments, rebuild ledger, emit
  Continuum claims and Star Chart submission JSON. Use when user asks to witness, archive,
  pure-data register, or PDW. Network only for optional --url fetch with --i-authorize-fetch.
version: 1.0.0
license: LYGO-Sovereign-v2.0
metadata:
  openclaw:
    emoji: "📜"
    homepage: "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/LYGO_PURE_DATA_WITNESS.md"
    requires:
      anyBins: [python, python3]
  lygo: true
  signature: "Delta9Phi963-PDW-SKILL-v1.0.0"
  publisher: deepseekoracle
  clawhub: "https://clawhub.ai/deepseekoracle/skills/lygo-pure-data-witness"
---

# LYGO Pure-Data Witness (ClawHub)

**When:** User asks to archive/witness a URL or file, register pure data, PDW, refuse rewrites.

## Safety

| Control | Value |
|---------|--------|
| Default network | **Off** (local digest) |
| URL fetch | Only with `--i-authorize-fetch` + HTTPS safety gate |
| Subprocess | **No** in skill CLI |
| Star Chart live write | Skill writes `*.star_submission.json`; steward/stack `haven_star_chart_submit.py --i-consent` |
| Secrets | Redaction heuristics; never put keys in snapshots |

## Commands

```bash
cd path/to/lygo-pure-data-witness
python scripts/self_check.py
python scripts/pdw_cli.py digest --file ./page.html --out ./pdw_out
python scripts/pdw_cli.py fetch --url https://example.com --out ./pdw_out --i-authorize-fetch
python scripts/pdw_cli.py register --url https://example.com --out ./pdw_out --i-authorize-fetch --i-consent
python scripts/pdw_cli.py ledger --dir ./pdw_out --ledger ./pdw_out/ledger.json
```

**Interactive human UI:** https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/register.html  
**Design:** https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_PURE_DATA_WITNESS.md  
**Bot summon (future):** docs/PURE_DATA_BOT_DESIGN.md

**Δ9Φ963 — digest authority · safety before archive · chart fork log.**
