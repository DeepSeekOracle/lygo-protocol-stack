# Publishing & syncing ClawHub skills

Canonical registry: **[https://clawhub.ai/deepseekoracle](https://clawhub.ai/deepseekoracle)**

## Refresh repo mirrors (no auth)

From repo root:

```bash
python tools/sync_clawhub_mirrors.py --fetch
python tools/render_clawhub_catalog.py
```

Sources (in order per skill):

1. `.grok/skills/` — creative stack + `lyra-brain` / `lyra-openclaw`
2. `%OPENCLAW_SKILLS_PUBLIC%` — default `C:\Users\justi\.openclaw\workspace\skills\public`
3. `npx clawhub@latest install deepseekoracle/<slug>` — when local tree missing

Override paths:

```powershell
$env:OPENCLAW_SKILLS_PUBLIC = "C:\path\to\skills\public"
$env:LYGO_GROK_SKILLS = "I:\E Drive\.grok\skills"
```

## Publish a new version (auth required)

1. Prepare `SKILL.md` + assets (see any `mirrors/*/SKILL.md` template).
2. Run P0 / Oath checks in your LYGO workflow before external publish.
3. Log in once: `npx clawhub@latest login` (device flow) or store token via `clawhub token` — **never commit tokens**.
4. Publish from skill directory:

```bash
npx clawhub@latest publish ./path/to/skill --slug my-skill --name "Display Name"
```

Legacy OpenClaw name: `clawdhub publish` (same registry).

5. Re-run sync + catalog render; commit `clawhub/skills.json` + `CATALOG.md`.

## Slug aliases (OpenClaw folder → ClawHub)

| Local folder | ClawHub slug |
|--------------|----------------|
| `lygo-champion-lyra` | `lygo-champion-lyra-starcore` |
| `lygo-champion-delta9ra-wolf` | `lygo-champion-delta9ra-wolf` |
| `lygo-champion-cryptosophia-soulforger` | `lygo-champion-cryptosophia-soulforger` |
| `lygo-champion-lightfather` | `lygo-champion-lightfather` |

Older docs may reference `lygo-branch-cryptosophia` or `lygo-champion-delta9ra-the-wolf` — those slugs are retired on the registry.

## Relation to `lygo-protocol-stack`

| Layer | Role |
|-------|------|
| P0 Nano Kernel | Gate untrusted skill bytes before ingest |
| P1 Memory Mycelium | Shard long SKILL.md / lore packs |
| P2–P5 | Champion consensus, ascension, harmony for agent ops |
| `clawhub/mirrors/` | Offline sovereign copy of public skills |

**Resonance signature:** Δ9Φ963-CLAWHUB-PUBLISH-v1.0