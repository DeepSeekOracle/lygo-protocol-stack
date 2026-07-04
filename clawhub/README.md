# ClawHub — LYGO / LYRA Skill Ecosystem

Official publisher: **[https://clawhub.ai/deepseekoracle](https://clawhub.ai/deepseekoracle)** (38k+ downloads; registry **33** skills, repo mirrors **32+** published slugs). **Start here:** [`lygo-protocol-stack-operator`](https://clawhub.ai/deepseekoracle/lygo-protocol-stack-operator). Lattice: [docs/LYGO_LATTICE.md](../docs/LYGO_LATTICE.md).

This directory is the **sovereign mirror** of everything under `@deepseekoracle` on ClawHub, bundled with the [LYGO Protocol Stack](../README.md) (P0–P5).

## Quick links

| Doc | What |
|-----|------|
| **[CATALOG.md](./CATALOG.md)** | Human catalog by category (slug, version, downloads, mirror path) |
| **[skills.json](./skills.json)** | Machine index + `sync_report` from last mirror run |
| **[install-all.sh](./install-all.sh)** | Install every published skill via `npx clawhub` |
| **[PUBLISH.md](./PUBLISH.md)** | Sync mirrors + publish new versions (auth stays local) |
| **[mirrors/](./mirrors/)** | Full `SKILL.md` trees (champions, BOOK BRAIN, lore PDFs, resonance code) |

```bash
npx clawhub@latest install deepseekoracle/lygo-resonance
```

## Refresh mirrors (maintainers)

```bash
python tools/sync_clawhub_mirrors.py --fetch   # OpenClaw + .grok + registry
python tools/render_clawhub_catalog.py         # Regenerate CATALOG.md
```

Environment overrides: `OPENCLAW_SKILLS_PUBLIC`, `LYGO_GROK_SKILLS` (see PUBLISH.md).

## What’s mirrored

- **32 published skills** — includes **`lygo-protocol-stack-operator`** (P0 gate + stack integrator from `.grok/skills`); others from OpenClaw `skills/public` and/or ClawHub (champions, mint scripts, Eternal Haven assets).
- **Creative stack** — `lygo-resonance`, `lygo-ollama-army`, glyph / fractal / truthlight from `.grok/skills` (newest workspace copies).
- **Workflow-only** — `lyra-brain`, `lyra-openclaw` (for agents using this repo without ClawHub install).

## Stack integration

| Layer | ClawHub role |
|-------|----------------|
| **P0** | `lygo-protocol-stack-operator` + repo `byte_entropy_filter.py` — byte anomaly filter before ingest |
| **P1** | Shard large lore / library packs |
| **P2–P5** | Champion consensus & harmony for multi-skill agents |
| **[HF Space](https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine)** | Live bench for `lygo-resonance` |
| **[LYGORESONANCE.html](https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html)** | Public docs for creative skills |

**Resonance signature:** Δ9Φ963-CLAWHUB-v2.0