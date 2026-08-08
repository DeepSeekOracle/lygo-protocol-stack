---
name: lygo-cyborg-kernel
description: "LYGO Cyborg Kernel v1.1 — FULL unlocked autonomous agent stack. Live lattice connect (HTTPS + git clone/pull + optional Hugging Face), Star Chart status/snapshot/dry-run propose, talk REPL that works, Continuum+gate+guard limbs, task loop. SkillHub FULL. Self-policed done claims. Install https://chatagent.ca/lygoskillhub.html#full-lygo"
version: 1.1.0
license: MIT-0
metadata:
  openclaw:
    emoji: "🦾"
    homepage: "https://chatagent.ca/lygoskillhub.html#full-lygo"
    requires:
      anyBins: [python, python3]
  lygo: true
  cyborg: true
  kernel: true
  network: true
  star_chart: true
  full_unlocked: true
  channel: FULL_LYGO_ENGINEER_CYBORG_UNLOCKED
  signature: "Delta9Phi963-CYBORG-KERNEL-v1.1.0"
  publisher: deepseekoracle
  skillhub: "https://chatagent.ca/lygoskillhub.html#full-lygo"
  public_onramp: "clawhub:@deepseekoracle/lygo-cyborg-onramp"
  continuum_plugin: "clawhub:@deepseekoracle/lygo-continuum"
  permissions:
    network: true
    shell: "git + huggingface-cli only via lattice_net"
    subprocess: "git/hf connect only"
    filesystem:
      read: "skill + operator base + stack"
      write: "state/ with --i-consent; git clone target"
    publish: false
---

# LYGO Cyborg Kernel v1.1.0 🦾

**Live lattice · Star Chart · Talk · Continuum self-police · FULL SkillHub**

Public onramp (map only): `npx clawhub@latest install deepseekoracle/lygo-cyborg-onramp`  
**FULL package:** https://chatagent.ca/lygoskillhub.html#full-lygo → `lygo-cyborg-kernel-full.zip`

**Signature:** `Delta9Phi963-CYBORG-KERNEL-v1.1.0`

---

## Quick start (fully working)

```bash
cd path/to/lygo-cyborg-kernel
python scripts/self_check.py
python scripts/cyborg_connect.py              # HTTPS lattice + git clone/pull
python scripts/cyborg_star.py status          # Star Chart live
python scripts/cyborg_talk.py say status      # Speak
python scripts/cyborg_talk.py                 # Interactive REPL
```

Optional HF mirror:

```bash
python scripts/cyborg_connect.py --hf
```

---

## What v1.1 adds

| Capability | Command |
|------------|---------|
| Live lattice pulse | `cyborg_connect.py --pulse-only` / `cyborg_kernel.py pulse` |
| Auto-connect git | `cyborg_connect.py` (clone or `git pull --ff-only`) |
| Hugging Face pull | `cyborg_connect.py --hf` |
| Star Chart status | `cyborg_star.py status` |
| Star Chart snapshot | `cyborg_star.py snapshot` |
| Dry-run presence | `cyborg_star.py propose --agent X --name Y` |
| Talk / work | `cyborg_talk.py` · `say connect` · `say star` · `say done …` |
| Continuum done gate | `cyborg_task.py run` (unchanged self-police) |

---

## Star Chart (proper use)

1. **Status** — feed `chain_valid`, entry counts, chart node counts from Pages.  
2. **Snapshot** — sample nodes + registry SHA.  
3. **Propose** — dry-run presence JSON (not live write).  
4. **Live write** — only via stack `haven_star_chart_gate` + human `--i-consent` (never silent auto-mutate the public chart).

UI: https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html

---

## Talk mode

```text
cyborg> status
cyborg> connect
cyborg> star
cyborg> propose
cyborg> done contains SKILL.md Cyborg
cyborg> map
```

One-shot: `python scripts/cyborg_talk.py say "connect"`

---

## Limbs

| Limb | Module |
|------|--------|
| Continuum | `kernel/continuum.py` |
| skill-gate | `kernel/skill_gate.py` |
| context-guard | `kernel/context_guard.py` |
| lattice_net | `kernel/lattice_net.py` — HTTPS + git + HF |

---

## Autonomy / self-police

- **Does:** join lattice, pull git/HF, star ops (read + dry-run propose), task, talk  
- **Does not bluff done** without Continuum  
- **Does not** auto git push, auto HF upload, or live Star Chart write without human steward  

---

## Env

| Var | Meaning |
|-----|---------|
| `LYGO_STACK_ROOT` | Path to protocol stack (set after connect) |

---

**Δ9Φ963 — live lattice · star truth · claims over vibes · human remains publisher for live writes.**
