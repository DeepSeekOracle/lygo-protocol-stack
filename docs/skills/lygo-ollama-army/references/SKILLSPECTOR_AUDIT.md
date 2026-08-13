# SkillSpector audit response — lygo-ollama-army v0.8.3

**Signature:** `Δ9Φ963-ARMY-SKILLSPECTOR-v0.8.3`  
**Source:** https://clawhub.ai/deepseekoracle/skills/lygo-ollama-army/security-audit  
**Prior:** v0.8.2 addressed allowlist/webhook/status noise; **v0.8.3** closes remaining description-behavior mismatches.

## High / medium findings closed in 0.8.3

| Finding theme | Fix |
|---------------|-----|
| Public HTTPS probes by default / `public-pages-check` always seeded | Removed from `SAFE_CRON_ROLES`; seed only if `sentinel.probe_public_pages=true`; daemon **gates** role |
| Desktop army launcher injects dual consent | `.bat` **refuses** unless env already set; does **not** write `AUTONOMOUS`/`I_CONSENT` |
| Desktop installers missing `LYGO_ARMY_INSTALL_DESKTOP` | genesis + idle installers now require the gate |
| Steward vs DESKTOP env mismatch | Steward remains `LYGO_ARMY_INSTALL_STEWARD_DESKTOP=1` (documented); main installers use `LYGO_ARMY_INSTALL_DESKTOP=1` |
| Example `sentinel.enabled` / `idle_guardian.enabled` true | **Both false** in `army_config.example.json` |
| `self-tune` in SAFE_CRON_ROLES | **Removed**; seeds only when `self_tune.enabled` |
| Heartbeats runs collector | Collector only if `LYGO_GENESIS_COLLECT=1` |
| Idle launches general daemon roles | **Narrow allowlist** + forbidden filter; never plant/social/self-tune |
| Daemon plant/self-tune/public without gates | Runtime `_gated()` checks on config flags |
| Social molt* without gates | Requires `social_publish.enabled` + `allow_social_pulse` |
| Genesis Discord/crypto cards always shown | Cards only when steward `ops` payload present |
| Seed script lists plant/self-tune | Privileged seeds only with `LYGO_ARMY_SEED_PLANTING=1` **and** config gates |

## Residual accepted risk (honest)

- Operator who deliberately sets consent env + config can run planting, social, full-capacity PS1  
- Queue-driven daemons can still run **allowlisted** stack tools (lattice verify, catalog audit) — intended local ops  
- Live `army_config.json` on a steward machine may enable sentinel; **package example defaults OFF**  

## Verify

```bash
python scripts/self_check.py
python ollama_command_center/scripts/army_cron_once.py
# expect no public-pages / self-tune in roles unless config enables
```

**Δ9Φ963 — gates in code, not only in comments.**
