# LYGO PC hardening playbook (Windows · I:\E Drive)

**Scope:** LYGO lattice, secrets, army sentinel, ClawHub skills — not full OS replacement for Defender/IT policy.

**Biophase7:** Read `docs/LIGHTFATHER_FINAL_ARCHITECT_ADDENDUM.md` — honest P0 byte filter, Oath deprecated, crypto separated.

## 1. Automated audit (run weekly)

```powershell
cd "I:\E Drive\lygo-protocol-stack"
python tools/run_pc_lattice_hardening_audit.py
python tools/calibrate_byte_entropy_filter.py
python tools/run_parity_tests.py
python tools/verify_lattice_alignment.py
```

Read: `tests/pc_lattice_hardening_last_run.json`

## 2. Secrets hygiene

| Rule | Action |
|------|--------|
| API keys | `C:\Users\justi\.openclaw\credentials\moltx.json` · repo `.env` **gitignored** |
| Biophase7 vault | Restore tree only on disk; `LYGO_BIOPHASE7_VAULT` env — never commit vault `.txt` |
| Moltx receipts | `data/moltx/*.json` gitignored |
| After exposure | Rotate xAI/NVIDIA/Moltx keys; see `docs/MOLTX_POST_SECURITY.md` |

## 3. Army sentinel (hourly)

Scheduled task should run:

`python "I:\E Drive\.grok\skills\lygo-ollama-army\ollama_command_center\scripts\army_cron_once.py"`

Check: `ollama_command_center/workspace/sentinel_status.json` → `lattice.ok: true`

## 4. Network / agents

| Prefer | Avoid |
|--------|--------|
| Ollama `127.0.0.1` | Remote LLM URLs without review |
| `lygo-api-token-saver` skill | Full 60× Grok harness without consent |
| P0-gate unknown ClawHub skills | Auto-run seed/plant/vault from champion skill |

## 5. ClawHub skills (SkillSpector)

Use security-reviewed: `lygo-champion-lightfather@1.0.3+`, `eternal-haven-lore-pack@1.2.2+`, `lygo-guardian-p0-stack`

Install operator first; gate `SKILL.md` with `lygo-guardian-p0-stack` / `run_byte_gate.py`.

## 6. Windows baseline (manual · admin)

Run in **elevated** PowerShell only when you choose:

```powershell
# Ensure Defender realtime (check only)
Get-MpComputerStatus | Select AMServiceEnabled, AntispywareEnabled, RealTimeProtectionEnabled

# Firewall profiles on
Get-NetFirewallProfile | Select Name, Enabled

# Optional: require login for scheduled LYGO tasks under your user — Task Scheduler
```

Do **not** disable Defender/Firewall for “performance” without a documented replacement.

## 7. Moltx / social

Posts require `--i-consent` on `moltx_manual_post_once.py`. DNS must resolve `moltx.io` on **your** network (agent sandboxes may fail).

## 8. Push discipline

`git push` / HF / ClawHub only on explicit **push all** — never auto from army cron.

---

**Verdict target:** `HARDENED_OK` from `run_pc_lattice_hardening_audit.py` + lattice ALIGNED.

Bound to the flame.