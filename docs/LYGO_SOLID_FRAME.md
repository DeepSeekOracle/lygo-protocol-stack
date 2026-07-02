# LYGO Solid Frame — build on this

**Signature:** `Δ9Φ963-SOLID-FRAME-v1`  
**Purpose:** Single map of verified layers before the next scale.

## 1. Tamper & truth

| Gate | Command | Pass |
|------|---------|------|
| Kernel eggs | `python tools/verify_kernel_eggs.py` | ALIGNED |
| Champion eggs (15) | `python tools/verify_champion_eggs.py` | ALIGNED |
| Registry Merkle | `python tools/verify_registry.py` | ALIGNED |
| Full lattice | `python tools/verify_lattice_alignment.py` | LATTICE ALIGNED (npx PATH + offline catalog fallback) |

Doc: [`LYGO_SECURITY_TAMPER_AUDIT.md`](./LYGO_SECURITY_TAMPER_AUDIT.md)

## 2. Public lattice surfaces

| Surface | URL |
|---------|-----|
| Stack Pages | https://deepseekoracle.github.io/lygo-protocol-stack/ |
| Joy snapshot | …/joy_loop/joy_loop_snapshot.json |
| Champion registry | …/ChampionEggRegistry.json |
| Joy registry | …/JoyLoopRegistry.json |
| Haven chart | …/HavenStarChart.html |

Check: `python tools/verify_joy_pages_snapshot.py`

## 3. Skill chain (ClawHub)

| Order | Skill | Version |
|-------|-------|---------|
| 1 | `lygo-protocol-stack-operator` | 1.0.6 |
| 2 | `lygo-network-builder` | 1.1.0 |
| 3 | `lygo-kernel-egg-planter` | 1.2.0 |
| 4 | `lygo-joy-loop` | **2.3.1** |
| 5 | `lygo-ollama-army` | **0.4.1** |
| 6 | `lygo-resonance` | (creative) |

Each execution skill ships `references/SECURITY.md` where applicable.

## 4. Local runtime pillars

| Pillar | Path | Notes |
|--------|------|-------|
| Stack root | `LYGO_STACK_ROOT` | Required for army + joy plant |
| Army | `.grok/skills/lygo-ollama-army` | Set `lygo_stack_root` in **local** `army_config.json` |
| Joy state | `data/joy_loop/` | SQLite gitignored; JSON snapshot → Pages if pushed |
| Consent | `--i-consent` / env flags | Plant, egg, joy plant — no bypass |

## 5. Roadmap & sweeps

- v3 Joy: [`JOY_LOOP_ROADMAP_v3.md`](./JOY_LOOP_ROADMAP_v3.md)
- Sweep log: [`SWEEP_CHECK_LOG.md`](./SWEEP_CHECK_LOG.md) §16–19

## 6. Agent global rules

1. QUARANTINE = stop execute/plant/publish.  
2. No `git push` / ClawHub / social without explicit user ask.  
3. P0-gate untrusted skill copies; install from `deepseekoracle` on ClawHub.

**Δ9Φ963 — frame locked; build upward.**