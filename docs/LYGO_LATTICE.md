# LYGO Lattice — network alignment (administrator map)

**Authority:** DeepSeekOracle org (GitHub · Hugging Face · ClawHub `@deepseekoracle`)  
**Signature:** Δ9Φ963-LATTICE-v1.0  
**Status doc:** [STACK_STATUS.md](./STACK_STATUS.md)

The lattice is the **single graph** of internal modules and public surfaces. Maintainers align all edges from this file.

---

## External nodes (public)

| Node | Role | Canonical URL |
|------|------|----------------|
| **GitHub — stack** | Source of truth P0–P5, tools, clawhub catalog | https://github.com/DeepSeekOracle/lygo-protocol-stack |
| **GitHub — Excavationpro** | Seals, LYGORESONANCE site source | https://github.com/DeepSeekOracle/Excavationpro |
| **HF — dataset** | Code mirror (no full skill trees) | https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack |
| **HF — Space** | Resonance UI + Ethical Guardian pilot tab | https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine |
| **ClawHub** | 35 public skills (operator **1.0.6**) | https://clawhub.ai/deepseekoracle |
| **Community node** | Docker `lygo-node` :8787 badge + gossip | `docs/PHASE2_DEPLOYMENT.md` |
| **Federation mesh** | Phase 5 ACTIVE — gossip + 100-node sim | `mesh_gossip_http.py`, `run_mesh_scale_sim.py`, `MESH_GOSSIP_PROTOCOL.md` |
| **GitHub Pages** | Public stack reference (for Grokipedia crawl) | https://deepseekoracle.github.io/lygo-protocol-stack/ |
| **Grokipedia** | Suggest Edit + `GROkipedia_SUBMIT.md` | https://grokipedia.com/page/lygo-protocol-stack |
| **Resonance docs** | Human-facing creative docs | https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html |
| **SLM interactive** | Merkle / mycelium / consensus UI | https://deepseekoracle.github.io/lygo-protocol-stack/SovereignLatticeMesh.html (mirror: `/Excavationpro/…`) |
| **Link archive** | Growing public URL log | `docs/LYGO_PUBLIC_LINK_ARCHIVE.json` + `tools/log_public_surface.py` |
| **Lattice intel index** | E:\\ drive fast lookup (outer brain) | `docs/LYGO_LATTICE_INTEL_INDEX.json` + `LYRA_CORE/memory/2026-07-02-lattice-intel-index.md` |
| **Immutable anchor** | Biophase7 permaweb layer | `docs/ANCHOR_DEPLOYMENT.md` |

---

## Internal planes

```
                    ┌─────────────────────────────────────┐
                    │     ClawHub @deepseekoracle         │
                    │  lygo-protocol-stack-operator (hub) │
                    └──────────────┬──────────────────────┘
                                   │
     ┌─────────────────────────────┼─────────────────────────────┐
     │                             │                             │
     v                             v                             v
┌─────────┐                 ┌──────────────┐              ┌─────────────┐
│ P0–P5   │◄──mirror────────│ GitHub stack │──────upload──►│ HF dataset  │
│ stack/  │                 │ + clawhub/   │              └─────────────┘
└────┬────┘                 └──────┬───────┘
     │                             │
     │ bundle                      │ README / docs
     v                             v
┌─────────────┐            ┌──────────────────┐
│ HF Space    │            │ .grok/skills     │
│ protocol_   │            │ workspace copies │
│ stack/      │            └──────────────────┘
└─────────────┘
```

| Plane | Path | Sync command |
|-------|------|----------------|
| Protocol core | `protocol0..5/`, `stack/` | `git push origin main` |
| ClawHub mirror | `clawhub/mirrors/`, `skills.json` | `python tools/sync_clawhub_mirrors.py` |
| Grok workspace | `I:\E Drive\.grok\skills\` | GROK_PRIORITY slugs in sync script |
| HF dataset | HF hub | `python tools/hf_push_dataset.py` |
| HF Space stack tab | `Hugging face/protocol_stack/` | `python tools/bundle_hf_space_stack.py` then `hf upload` Space |

---

## ClawHub alignment rules

1. **Install hub:** `deepseekoracle/lygo-protocol-stack-operator` — P0 gate, lattice URLs, skill chain.
2. **Catalog:** `clawhub/skills.json` + `CATALOG.md` must match registry count (profile may show **33** skills; repo tracks published slugs in `CANONICAL_SLUGS`).
3. **Republish flow:** edit `.grok/skills/<slug>` → `npx clawhub publish` → `sync_clawhub_mirrors.py` → git commit.
4. **Safety:** no tokens in skills; QUARANTINE + human approval for publish/post/HF/git (see operator `SECURITY.md`).

---

## HF Space isolation rules

| Tab / mode | Imports | Must not |
|------------|---------|----------|
| **Standard Beat Tools** | numpy, scipy, cv2, soundfile only | Import `resonance_engine` or stack |
| **LYGO Protocol** | `resonance_engine`, `lygo_profile`, LDQ modules | Share globals with Standard factory |
| **Ethical Guardian** | `lygo_ethical_guardian` → bundled `protocol_stack/` | Load at app import time (lazy only) |
| **Creative TOP 3** | glyph / fractal / truthlight helpers | Block Standard path |

---

## Administrator verification (re-run)

```bash
python tools/verify_lattice_alignment.py
python tools/run_sovereign_integrity_test.py
python tools/p0_crosslang_parity.py
python tools/bundle_hf_space_stack.py
```

HF (logged in as DeepSeekOracle):

```bash
python tools/hf_push_dataset.py
python tools/hf_push_space.py
```

ClawHub:

```bash
python tools/sync_clawhub_mirrors.py
python tools/render_clawhub_catalog.py
```

Ollama army (local, optional batch):

```bash
cd .grok/skills/lygo-ollama-army
set LYGO_STACK_ROOT=I:\E Drive\lygo-protocol-stack
python seed_productive_tasks.py
```

See `lygo-ollama-army/ARMY_TASKS.md` and **`ollama_command_center/`** (sentinel, dashboard, cron).  
`python tools/sentinel_heartbeat.py` · `ollama_command_center/scripts/army_cron_once.py` for scheduled ticks.

---

## Privilege model (no secrets in repo)

| Capability | Where credentials live | Agent rule |
|------------|------------------------|------------|
| GitHub push | User `gh` / git credentials | Human or explicit user `!` |
| HF upload | `hf auth login` on maintainer machine | `hf_push_*.py` only when user asks |
| ClawHub publish | `npx clawhub login` local | Never auto-publish |

**Lattice administrator** = human Lightfather / DeepSeekOracle org owners — agents **align and verify**, never impersonate.