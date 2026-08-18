---
name: lygo-pure-data-witness
description: >
  Teach agents to register pages into the LYGO Pure-Data lattice via the public
  register portal pack + safety-gated CLI. Archive URLs/files as digests (HTTPS-only,
  SSRF block, malware/ad heuristics, size cap), pack tiny eggs, rebuild ledger, emit
  Continuum claims and Star Chart NODE_PDW_* submissions. Use when user asks to
  witness, archive, pure-data register, PDW, or use the Data Vault register portal.
  Network only with --i-authorize-fetch; live chart writes need --i-consent.
version: 1.1.0
license: LYGO-Sovereign-v2.0
metadata:
  openclaw:
    emoji: "📜"
    homepage: "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/LYGO_PURE_DATA_WITNESS.md"
    requires:
      anyBins: [python, python3]
  lygo: true
  agent_portal: true
  signature: "Delta9Phi963-PDW-SKILL-v1.1.0"
  publisher: deepseekoracle
  clawhub: "https://clawhub.ai/deepseekoracle/lygo-pure-data-witness"
  portal: "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/register.html"
  pages: "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/pure-data.html"
---

# LYGO Pure-Data Witness (ClawHub)

**Train aligned agents** to archive truth into Pure-Data Witness and grow the
`GALAXY_PURE_DATA_ARCHIVE` fork log — using the **register portal** for humans and
this skill’s CLI for execution.

**ClawHub:** https://clawhub.ai/deepseekoracle/lygo-pure-data-witness

| Surface | URL |
|---------|-----|
| **Register portal** | https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/register.html |
| Pure-Data UI | https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/pure-data.html |
| Design | https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_PURE_DATA_WITNESS.md |
| Public ledger | https://deepseekoracle.github.io/lygo-protocol-stack/pure-data/ledger.json |
| Bot design (future) | https://deepseekoracle.github.io/lygo-protocol-stack/PURE_DATA_BOT_DESIGN.md |

**Read first:** `references/SECURITY.md` · `references/PORTAL_TRAINING.md`

## When to use

- User wants to **register a page/URL/file** into the Pure-Data lattice.
- Agent should **teach or drive the register portal** (pack → CLI → witness).
- Archive with **refuse-rewrites** digests + optional egg + Continuum claims.
- Emit **Star Chart** `NODE_PDW_*` submission JSON (fork/archive log).

## When NOT to use

- Fetching private IPs, metadata hosts, credential URLs, or obvious malware bait.
- Live Star Chart ingest **without** explicit human `--i-consent`.
- Auto git push / ClawHub / HF / social publish.
- Claiming LIVE chart placement before steward rebuild.

## Portal → agent contract (core)

1. **Point humans** at the register portal when they need a visible registration pack.
2. Portal builds `lygo_pdw_registration_pack_v1` — it does **not** fetch or write the chart (CORS + safety).
3. Agent checks `safety.ok`. If false → stop and explain errors.
4. After **explicit user approval**, run:
   - URL: `pdw_cli.py register --url … --i-authorize-fetch --i-consent`
   - File: `pdw_cli.py register --file … --i-consent`
5. Return `witness_id`, ledger root, and `*.star_submission.json` path.
6. Star Chart live accept = steward/stack gate — skill never silent-publishes the sky.

Full playbook: **`references/PORTAL_TRAINING.md`**.

## Safety

| Control | Value |
|---------|--------|
| Default network | **Off** (local digest) |
| URL fetch | Only `--i-authorize-fetch` + HTTPS safety gate |
| Subprocess | **No** in skill CLI |
| Star Chart live write | Skill → `*.star_submission.json`; stack submit needs `--i-consent` |
| Secrets | Never put keys/cookies in snapshots |

## Install

```bash
npx clawhub@latest install deepseekoracle/lygo-pure-data-witness
```

Optional stack clone for full register+map+chart:

```bash
export LYGO_STACK_ROOT=/absolute/path/to/lygo-protocol-stack
```

Pair with `lygo-haven-star-chart` when submitting fork nodes to the live sky.

## Commands

```bash
cd path/to/lygo-pure-data-witness
python scripts/self_check.py
python scripts/pdw_cli.py check-url --url https://example.com
python scripts/pdw_cli.py digest --file ./page.html --out ./pdw_out
python scripts/pdw_cli.py fetch --url https://example.com --out ./pdw_out --i-authorize-fetch
python scripts/pdw_cli.py register --url https://example.com --out ./pdw_out --i-authorize-fetch --i-consent
python scripts/pdw_cli.py register --file ./page.html --out ./pdw_out --i-consent
python scripts/pdw_cli.py ledger --dir ./pdw_out --ledger ./pdw_out/ledger.json
python scripts/pdw_cli.py verify --card ./pdw_out/PDW-….json
```

Stack (when `LYGO_STACK_ROOT` set):

```bash
python tools/pure_data_register.py --url https://example.com --i-consent
python tools/map_pure_data_to_star_chart.py --json
```

## Star Chart section

Witnesses map to:

- Hub `LATTICE_PURE_DATA_WITNESS`
- Root `NODE_PDW_ROOT`
- Per-witness `NODE_PDW_<hex>` (parent-linked fork chain)
- Galaxy `GALAXY_PURE_DATA_ARCHIVE` / constellation `pure_data_archive`

**Δ9Φ963 — digest authority · portal front door · safety before archive · chart fork log.**
