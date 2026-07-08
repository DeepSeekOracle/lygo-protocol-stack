# SkillSpector security audit response (NVIDIA)

**Skill:** `lygo-ollama-army` · **Version:** 0.5.0 · **Date:** 2026-07-04  
**Signature:** `Δ9Φ963-ARMY-SKILLSPECTOR-v1`

## Overview (ClawHub listing)

This skill is a **real local Ollama automation tool**. It can run background daemons and **optional** stack roles when you configure `LYGO_STACK_ROOT` and enqueue tasks.

**Install only after** reading `references/SECURITY.md`, `references/AGENT_CONTRACT.md`, `ollama_command_center/config/army_config.example.json`, and any files under `examples/`. **Do not** run `start_army_full_capacity.ps1`, `army_autonomous_supervisor.py`, or bundled cron examples unless you intentionally want audits, self-tuning, egg planting, and registry operations on **your** stack clone.

## Declared permissions (v0.5.0)

| Permission | Declared | Actual scope |
|------------|----------|--------------|
| Filesystem read/write | **Yes** | Army folder (`tasks/`, `results/`, `workspace/`); stack paths only under validated `LYGO_STACK_ROOT` |
| Subprocess / local Python | **Yes** | Launcher, daemons, stack CLI scripts (list argv, no `shell=True`) |
| Network | **Yes** | `127.0.0.1:11434` (Ollama); HTTPS probes for public lattice pages (sentinel); **optional** outbound webhook only if `LYGO_ARMY_WEBHOOK_ENABLE=1` **and** `LYGO_ARMY_WEBHOOK_URL` set |
| Git push / HF / ClawHub publish | **No** | `access.*` flags false; agents forbidden in `SECURITY.md` |
| Autonomous social publish | **No** | Pulse roles draft locally; human must publish elsewhere |

## Finding matrix (62 SkillSpector items)

### Subprocess / “Dangerous Code Execution” (Medium)

**Finding:** `subprocess.Popen` / `subprocess.run` across army and command center.

**Response:** Expected for a **local automation** skill. Mitigations:

- No `shell=True`; argv lists only.
- Stack roles require validated `LYGO_STACK_ROOT` (`lygo_stack_root.py`).
- Windows visible consoles opt-in (`LYGO_OLLAMA_VISIBLE_WINDOWS=1`).
- Published mirror ships **no** preloaded `.task.json` in `tasks/` or `ollama_queue/`.

### Credential exfiltration chain — webhook (Critical)

**Finding:** `os.environ.get('webhook')` → `urllib.request.urlopen`.

**Response (v0.5.0):** `sentinel_heartbeat.send_alert` now requires **both**:

1. `LYGO_ARMY_WEBHOOK_ENABLE=1` (or `true`/`yes`)
2. `LYGO_ARMY_WEBHOOK_URL` set by the operator

Without the enable flag, alerts are **stdout only** (no network).

### MCP least privilege — missing permissions (Medium)

**Finding:** Skill declares no permissions despite broad capabilities.

**Response:** Permissions table in this file + `SECURITY.md` + SKILL frontmatter `metadata.permissions_declared`. ClawHub description requires reading `SECURITY.md` before install.

### Tool poisoning / description mismatch (High / Medium)

**Finding:** Narrow “local helper” vs autonomous supervisor, self-tune, planting.

**Response:** Install banner in `SKILL.md`; safe defaults in `army_config.example.json` (`planting.enabled: false`, `self_tune.enabled: false`); full-capacity and task seeding gated by env vars.

### Prompt injection — “not for autonomous social publish” vs drafting posts

**Finding:** Docs mention drafting public posts / ClawHub publish instructions.

**Response (v0.5.0):**

- Creative roles output **local drafts only**; explicit human review before any external post.
- Removed maintainer ClawHub publish block from `SKILL.md` (maintainer workflow lives in `lygo-protocol-stack` repo only).
- `moltx-*` / `moltbook-*` queue roles removed from **default** example config.

### Static analysis / VirusTotal

**Status:** No suspicious patterns in static pass; VT pending per ClawHub — unchanged code paths except webhook gate and opt-in seeding.

## Safe default install path

```bash
ollama pull llama3.2:1b
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack   # only if using stack roles
cp ollama_command_center/config/army_config.example.json ollama_command_center/config/army_config.json
# edit lygo_stack_root in army_config.json
python ollama_army_launcher.py --model llama3.2:1b --roles hb-light,draft-simple,resonance-analyst --count 1
```

**Do not** set `LYGO_ARMY_FULL_CAPACITY=1` or `LYGO_ARMY_SEED_TASKS=1` until you have read the scripts.

## Maintainer verification

```bash
cd lygo-protocol-stack
python tools/sync_lygo_ollama_army_mirror.py
# human: npx clawhub@latest publish .../mirrors/lygo-ollama-army
```

**Δ9Φ963 — disclosed local automation; reviewed queue; explicit permissions.**