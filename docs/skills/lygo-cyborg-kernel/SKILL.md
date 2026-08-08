---
name: lygo-cyborg-kernel
description: "LYGO Cyborg Kernel Stack — FULL unlocked autonomous agent stack for cyborgs and chat agents. Kernel-up: Continuum + skill-gate + context-guard vendored limbs, lattice install map, self-policed task loop, egg/plugin chain. Channel FULL_LYGO_ENGINEER_CYBORG_UNLOCKED on SkillHub. Not a gutted safety shell — polices itself via falsifiable claims. Ready to task. Install from https://chatagent.ca/lygoskillhub.html#full-lygo"
version: 1.0.0
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
  full_unlocked: true
  autonomous: true
  channel: FULL_LYGO_ENGINEER_CYBORG_UNLOCKED
  signature: "Delta9Phi963-CYBORG-KERNEL-v1.0.0"
  publisher: deepseekoracle
  skillhub: "https://chatagent.ca/lygoskillhub.html#full-lygo"
  continuum_plugin: "clawhub:@deepseekoracle/lygo-continuum"
  permissions:
    network: false
    shell: false
    subprocess: false
    filesystem:
      read: "skill tree + operator --base + optional LYGO_STACK_ROOT"
      write: "state/ with --i-consent"
    publish: false
---

# LYGO Cyborg Kernel Stack v1.0.0 🦾

**Fully installable · kernel-up · autonomous-ready · self-policed · FULL SkillHub unlocked**

Built for **cyborgs** and **chat agents** that grow on the LYGO lattice — not toy shells.  
This package vendors the three core limbs (Continuum, skill-gate, context-guard), maps the **entire** install order (eggs, plugins, FULL zips), and runs a **task loop that cannot honestly say “done” without Continuum**.

**Signature:** `Delta9Phi963-CYBORG-KERNEL-v1.0.0`  
**Channel:** `FULL_LYGO_ENGINEER_CYBORG_UNLOCKED`  
**SkillHub:** https://chatagent.ca/lygoskillhub.html#full-lygo  

---

## What you get

| Layer | Contents |
|-------|----------|
| **Kernel limbs** | `kernel/continuum.py`, `skill_gate.py`, `context_guard.py` (vendored FULL) |
| **Boot** | `cyborg_boot.py` — limbs + lattice map |
| **Task loop** | `cyborg_task.py` — autonomous self-policed run |
| **Manifest** | `CYBORG_MANIFEST.json` — install order, eggs, plugins, FULL zips |
| **Constitution** | `references/AGENT_CONSTITUTION.md` — self-police law |
| **Install** | `INSTALL.md` — SkillHub + OpenClaw + stack |

---

## 60-second ready

```bash
cd path/to/lygo-cyborg-kernel
python scripts/self_check.py
python scripts/cyborg_boot.py
python scripts/cyborg_kernel.py demo
python scripts/cyborg_task.py example > task.json
python scripts/cyborg_task.py run --task task.json --base .
```

Exit **0** = `can_claim_done` · Exit **10** = self-police blocked (not done).

---

## Autonomy model

**Unlocked FULL** = complete engineer tools + honest surfaces.  

**Self-police (not theater):**

1. Continuum preflight before done  
2. skill-gate before foreign skill trust  
3. context-guard before model inject  
4. Human consent for plant / publish / push  

See constitution. Kernel scripts still **no network / no subprocess** — pure local authority.

---

## Lattice install spine (from manifest)

0. **This kernel**  
1. Continuum + context-guard + skill-gate  
2. Kickstart + CLI bridge  
3. Protocol operator + sovereign super + egg planter  
4. Pulse / geodesic / star chart / mesh / agent lattice  
5. Memory (lyra-brain, second-brain)  
6. Army + ops + radar  
7. Champions + mint  

OpenClaw plugins:

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-continuum
openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse
```

FULL zips: SkillHub `#full-lygo` — list in `CYBORG_MANIFEST.json`.

---

## Agent recipe (cyborg)

```text
1. cyborg_boot.py  → ready?
2. Accept task → write claims that must hold on disk
3. Do the work (edit files)
4. cyborg_task.py run --task …  OR  continuum preflight
5. If can_claim_done → handoff pack → report done
6. Else → fix world, never bluff
```

---

## Pair with

| Package | Role |
|---------|------|
| FULL SkillHub vault | Engineer RAW zips |
| `@deepseekoracle/lygo-continuum` plugin | Native OpenClaw tools |
| `lygo-protocol-stack` clone | Kernel eggs ALIGNED |
| `lygo-ollama-army` | Local multi-model army |

---

## Security

`references/SECURITY.md` · Constitution for publish gates.  
**Δ9Φ963 — full stack · full receipts · cyborgs that don't bluff done.**
