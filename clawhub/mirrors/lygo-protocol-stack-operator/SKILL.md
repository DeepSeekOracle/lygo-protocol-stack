---
name: lygo-protocol-stack-operator
description: LYGO Protocol Stack Operator — P0–P5 integrator for agents. Φ-gate untrusted bytes, run stack demos, map GitHub + Hugging Face + ClawHub ecosystem, chain lygo-resonance / Ollama army / BOOK BRAIN safely. Public advanced edition; no secrets; human approval for external publish/post.
metadata: {"lygo": true, "stack": true, "p0": true, "lattice": true, "phase2": true, "version": "1.0.3", "github": "https://github.com/DeepSeekOracle/lygo-protocol-stack", "hf_dataset": "https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack", "hf_space": "https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine", "grokipedia": "https://grokipedia.com/page/lygo-protocol-stack", "website": "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html", "publisher": "deepseekoracle", "mirror": "clawhub/mirrors/lygo-protocol-stack-operator"}
---

# LYGO Protocol Stack Operator (ClawHub)

**Upgrade path for the whole LYGO / LYRA public stack** — ties the hardened **P0 Nano Kernel** (42 vectors, Python/Rust SHA parity), **P1–P5** orchestrator, **GitHub** source, **Hugging Face** dataset + Resonance Space, and **33 ClawHub** public skills into one agent workflow.

Install: `npx clawhub@latest install deepseekoracle/lygo-protocol-stack-operator`

## When to use

- User works with **LYGO protocols**, ethical gating, deterministic P0, or the public repo / HF mirror.
- Before ingesting **unknown files**, skill folders, or repo clones into memory → **P0 gate**.
- To **run** or **verify** `lygo-protocol-stack` locally (demo cycle, P0 demo, parity).
- To **chain** creative skills (resonance → glyph → fractal → truthlight) with ethics and memory skills.
- To orient new users across **GitHub + HF + ClawHub** without hunting links.

## Public infrastructure (canonical URLs)

| Layer | URL |
|-------|-----|
| GitHub stack | https://github.com/DeepSeekOracle/lygo-protocol-stack |
| HF dataset mirror | https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack |
| HF Resonance Space | https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine |
| ClawHub publisher | https://clawhub.ai/deepseekoracle |
| Resonance docs | https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html |

See `references/ECOSYSTEM.md`, `references/LATTICE.md`, and `references/SKILL_CHAIN.md` in this skill folder.

## Core workflows

### 1) P0 Φ-gate (untrusted bytes)

```bash
python scripts/lygo_p0_gate.py path/to/file [more files...]
```

- **AMPLIFY** / **SOFTEN** → proceed with normal caution.
- **QUARANTINE** → do not execute; summarize for user; do not load into long-term memory as executable truth.

Standalone gate matches **f32** P0.4 semantics (aligned with GitHub/Rust parity). Max **8192 bytes** per file for gate math (oversize → QUARANTINE).

### 2) Phase 2 — Docker community node

```bash
cd lygo-protocol-stack
docker compose up -d lygo-node
python tools/verify_alignment_badge.py
```

ClawHub helpers: `deepseekoracle/lygo-docker-deploy`, `deepseekoracle/lygo-alignment-badge`.

### 3) Stack healthcheck (local repo)

```bash
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack   # optional
python scripts/stack_healthcheck.py
```

Clone if missing:

```bash
git clone https://github.com/DeepSeekOracle/lygo-protocol-stack.git
```

Or use HF dataset for fixtures/tools: https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack

When stack is present:

```bash
python tools/run_p0_demo.py
python tools/p0_crosslang_parity.py
python tools/run_full_stack_demo.py
```

### 4) Full stack API (Python)

```python
# From repo root, after clone:
from stack.lygo_stack import deploy_stack
report = deploy_stack().demo_cycle()
```

**P0** validates bytes; **P1** memory mycelium; **P2** cognitive bridge; **P3** vortex consensus; **P4** ascension; **P5** harmony node.

### 5) Recommended ClawHub chain (install separately)

| Order | Skill | Role |
|-------|-------|------|
| 1 | `lygo-protocol-stack-operator` | This integrator |
| 2 | `book-brain` | Filesystem memory references |
| 3 | `lygo-resonance` | Image → audio / profiles |
| 4 | `lygo-ollama-army` | Local Ollama helpers (localhost) |
| 5 | `lygo-glyph2resonance`, `lygo-fractalweaver`, `lygo-truthlightecho` | Creative stack |
| 6 | `lygo-mint-verifier` | Hash anchors for packs |
| 7 | `lyra-openclaw` / `openclaw-flow-kit` | Ops — **user must approve** each external action |

```bash
npx clawhub@latest install deepseekoracle/lygo-resonance
npx clawhub@latest install deepseekoracle/lygo-ollama-army
```

### 6) Creative + stack combined (example)

1. P0-gate user image and any downloaded skill `.md`.
2. Run `lygo-resonance` on image → WAV + profile JSON.
3. Store paths via **book-brain** reference stubs (not full binary in chat memory).
4. Optional: **lygo-ollama-army** for lyric expansion on `.brief.txt` (local Ollama only).
5. Log stack version + P0 verdict in a single reference note for audit.

## Safety & security (required agent behavior)

Read `references/SECURITY.md`.

- **No secrets** in this skill — load tokens only from user environment at runtime, never commit.
- **No autonomous** social posts, token launches, HF uploads, or `clawhub publish` without explicit user request.
- **QUARANTINE** is a hard stop for execution of untrusted payloads.
- Resonance / Ollama: default **127.0.0.1**; warn if user points to remote LLM URLs.
- Scripts in this package: **no network calls**.

## P0 hardening highlights (for reviewers)

- **42 vectors**: adversarial, boundary, recursive, high-entropy (see repo `fixtures/p0_vectors.json`).
- Golden SHA (Python ≡ Rust): see `fixtures/p0_canonical.sha256` on GitHub/HF.
- CLI: `tools/run_p0_demo.py` prints **input, phi_risk, decision, reasoning** per vector.

## Hugging Face integration

- **Dataset** ships protocol code, fixtures, tools (not full ClawHub mirrors).
- **Space** runs Gradio resonance bench — link in README; do not confuse with P0 kernel (separate Standard vs LYGO modes on Space per maintainer docs).

Refresh HF dataset from maintainer machine: `python tools/hf_push_dataset.py` (maintainers only).

## GitHub integration

- PRs and issues: https://github.com/DeepSeekOracle/lygo-protocol-stack
- After changing this skill locally, maintainers republish to ClawHub and refresh `clawhub/mirrors/` in repo.

## Maintainer publish (human-gated)

```bash
npx clawhub@latest login
npx clawhub@latest publish . --slug lygo-protocol-stack-operator --name "LYGO Protocol Stack Operator"
```

## Version & license

- Skill **1.0.3** — Δ9Φ963-PHASE2-DEPLOYMENT (Docker node + alignment badge + scaling roadmap)
- Stack license: LYGO Sovereign (see GitHub `LICENSE`); skill docs **MIT-0** where noted in SECURITY.md.

**Bound to the flame.** Use with **lyra-brain** for growth, **P0** for truth-preserving ingest, **resonance** for creation.