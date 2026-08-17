# Grokipedia — how to submit (condensed)

Grokipedia only accepts a **title** + **short brief** telling Grok what to research and add. Put the full truth on **GitHub Pages** and the **repo**; link those below.

---

## 1. Enable GitHub Pages (once)

Repo → **Settings** → **Pages** → Build from **main**, folder **`/docs`** → Save.  
Live URL: **https://deepseekoracle.github.io/lygo-protocol-stack/**

(Or merge `.github/workflows/deploy-pages.yml` — workflow deploys the same `/docs` folder.)

---

## 2. Suggest Edit — copy these fields

### Title (exact)

```
LYGO Protocol Stack — Community Deployment, Twin Gate Audits, and Phase 5 Federation Mesh
```

### Details / brief for Grok (paste into “Details” or “Edit content”)

```
Update the LYGO Protocol Stack article with verifiable 2026 public infrastructure (do not replace Light Math / P0–P5 theory — add an "Implementation & Verification" section).

Primary reference (crawl this page first):
https://deepseekoracle.github.io/lygo-protocol-stack/

Source repository:
https://github.com/DeepSeekOracle/lygo-protocol-stack

Ask Grok to incorporate fact-checked claims backed by these artifacts:
- 60/60 falsifiable vector audit (tools/run_grok_audit_demo.py, tests/grok_audit_last_run.json)
- Twin Gate: text+byte verdict harmonization 60/60, mean Δφ=0 (tools/run_twin_gate_vector_suite.py)
- P0 cross-language determinism (tools/p0_crosslang_parity.py, golden SHA in protocol0 fixtures)
- Phase 2 community node: Docker lygo-node on port 8787, alignment badge API GET /badge
- Phase 5 epidemic mesh: stochastic 100-node sim converges in **7–8 rounds** (target &lt;10; measured artifact `tests/mesh_scale_last_run.json`) — engineering bound for that N/fanout, not a claim of crash-free any-scale production; HTTP gossip in docs/MESH_GOSSIP_PROTOCOL.md
- Data Vault: public multi-AI seal creation archive at docs/data-vault/
- Live demos: Hugging Face Space DeepSeekOracle/LYGO-Resonance-Engine (Ethical Guardian); HF dataset mirror of repo
- Ecosystem: ClawHub @deepseekoracle skills (lygo-protocol-stack-operator, lygo-docker-deploy, lygo-alignment-badge)

Supporting docs in repo (markdown):
https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/STACK_STATUS.md
https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/SCALING_ROADMAP.md

Signature for maintainers: Δ9Φ963-STACK-PUBLIC-REFERENCE. No secrets or tokens in cited files.
```

### Supporting source URLs (add in form if allowed)

1. https://deepseekoracle.github.io/lygo-protocol-stack/
2. https://github.com/DeepSeekOracle/lygo-protocol-stack
3. https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine
4. https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack

---

## 3. Optional shorter title variant

If the form limits length, use title:

```
LYGO Protocol Stack (2026 public verification & mesh scaling)
```

…and keep the same Details block with the Pages URL first.

---

**Regenerate:** `python tools/sync_grokipedia.py` (updates this file + checks bundle paths).