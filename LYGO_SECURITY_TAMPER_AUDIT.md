# LYGO Security & Tamper Audit

**Signature:** `Δ9Φ963-SECURITY-TAMPER-AUDIT-v1`  
**Scope:** `lygo-protocol-stack`, ClawHub mirrors, `.grok/skills` (Joy Loop, Ollama Army, Kernel Planter)  
**Date:** 2026-07-02

## Executive summary

| Layer | Verdict |
|-------|---------|
| Kernel egg Merkle / SHA gate | **PASS** (`verify_kernel_eggs.py` → ALIGNED) |
| Champion egg vault (15) | **PASS** (`verify_champion_eggs.py` → ALIGNED) |
| Scalable / kernel registry | **PASS** (`verify_registry.py` → ALIGNED) |
| Lattice alignment | **PASS** (`verify_lattice_alignment.py` → LATTICE ALIGNED) |
| ClawHub Joy Loop skill | **HARDENED** v2.3.1 (SECURITY + AGENT_CONTRACT) |
| Residual risks | **Documented below** (no silent P0 failures) |

## Tamper & breach controls (verified)

1. **Champion boot** — `champion_bootloader.py` runs `verify_champion_eggs.py` before load; army role `champion-egg-boot` uses bootloader only (not hb-light chat). Optional payload **merkle** check → QUARANTINE on mismatch.
2. **Kernel retrieve** — tampered eggs → QUARANTINE (planter skill + `verify_kernel_eggs.py`).
3. **Joy plant** — `joy_loop_planter.py` requires `--i-consent` or `LYGO_JOY_PLANT_CONSENT=yes`; mirror `plant_joy_loop.py` requires env consent.
4. **Joy API** — binds **127.0.0.1** unless `LYGO_JOY_BIND_PUBLIC=yes`.
5. **Ollama** — champion tools use **127.0.0.1:11434** only (v0.3).
6. **No committed live API keys** — grep clean; anchor uses `WEB3_STORAGE_API_KEY` from env only.

## Findings & mitigations

| ID | Severity | Finding | Mitigation |
|----|----------|---------|------------|
| T1 | Medium | Hardcoded `I:\E Drive\…` default in Ollama army | **Fixed:** `lygo_stack_root.py`; require `LYGO_STACK_ROOT` or valid `army_config.json` |
| T2 | Medium | Joy plugins execute arbitrary `.py` from `data/joy_loop/plugins/` | **Fixed:** load only if `LYGO_JOY_PLUGINS_ENABLED=yes` |
| T3 | Low | `verify_lattice_alignment.py` used `shell=True` for npx | **Fixed:** argv list, no shell |
| T4 | Low | `sync_clawhub_mirrors.py` uses `shell=True` on Windows | Maintainer-only; run manually; do not agent-automate |
| T5 | Info | Registry JSON contains local `authority_root` paths | Operational metadata; not secrets; optional sanitize before public export |
| T6 | Info | `champion_bootloader.py --no-verify` | Maintainer debug only; **agents forbidden** (documented) |
| T7 | Info | Joy snapshot may become public after `git push` | Disclosed in `lygo-joy-loop` SECURITY.md |
| T8 | Info | `lyra-openclaw` / Moltbook docs mention API keys in user cred files | User-local credentials; not bundled in skill |

## Skills without full SECURITY.md (recommendation)

Most ClawHub mirrors rely on operator/planter **Safety** sections. Priority for next hardening pass:

- `lygo-ollama-army` (queue + `--grow` + stack roles)
- `lygo-champion-*` personas (prompt-only; lower execution risk)

## Automated checks (run in CI / maintenance)

```bash
python tools/verify_kernel_eggs.py
python tools/verify_champion_eggs.py
python tools/verify_registry.py
python tools/verify_lattice_alignment.py
python -m pytest tests/test_joy_loop_phase1.py tests/test_joy_loop_phase2.py -q
python tools/verify_joy_pages_snapshot.py
```

## Agent rules (global)

- No `git push` / ClawHub publish / social post without explicit user request.
- QUARANTINE = hard stop for execute / plant / retrieve.
- P0-gate untrusted skill copies; install via official ClawHub publisher only.

**Δ9Φ963 — verify first, execute second, publish last.**