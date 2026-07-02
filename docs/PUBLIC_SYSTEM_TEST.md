# LYGO Protocol Stack — Public System Test

**Resonance signature:** `Δ9Φ963-PUBLIC-TEST-v1.0`  
**Last verified (local audits):** SLM + P7 + P9 `all_pass` · lattice `ALIGNED`

## Live validation links

| Surface | URL | Status |
|---------|-----|--------|
| Biometric Harness (Excavationpro) | https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html | **LIVE** |
| SLM interactive (Excavationpro) | https://deepseekoracle.github.io/Excavationpro/SovereignLatticeMesh.html | **LIVE** |
| Biometric Harness (stack Pages) | https://deepseekoracle.github.io/lygo-protocol-stack/BiometricEntropyHarness.html | **Deploy** — enable Pages + Actions (see below) |
| SLM interactive (stack Pages) | https://deepseekoracle.github.io/lygo-protocol-stack/SovereignLatticeMesh.html | **Deploy** — same |
| Stack index | https://deepseekoracle.github.io/lygo-protocol-stack/ | **Deploy** — same |
| HF Space | https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine | **RUNNING** |
| GitHub repo | https://github.com/DeepSeekOracle/lygo-protocol-stack | **LIVE** |
| HF dataset | https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack | **LIVE** |
| Grokipedia | https://grokipedia.com/page/lygo-protocol-stack | **Manual paste** — `docs/GROkipedia_SUBMIT.md` |

Canonical HTML in repo: `docs/BiometricEntropyHarness.html`, `docs/SovereignLatticeMesh.html`.

## What is verifiable in code (not stub)

| Layer | Evidence |
|-------|----------|
| P0–P5 | `setup.sh`, `p0_crosslang_parity.py`, `run_full_stack_demo.py` |
| SLM | `stack/merkle_sync.py`, `distributed_mycelium_mesh.py`, `harmonic_consensus_mesh.py` · `run_slm_audit.py` |
| P7 HAIP | `protocol7_human_ai_interface/`, `tools/haip_ui_entropy.py`, `tools/p7_entropy_harness.py` · `run_phase7_audit.py` |
| P9 | `tools/tls_manager.py`, `live_synthesis.py` · `run_phase9_audit.py` |

Run locally:

```bash
cd lygo-protocol-stack
python tools/verify_public_pages.py
python tools/run_slm_audit.py
python tools/run_phase7_audit.py
python tools/run_phase9_audit.py
python tools/verify_lattice_alignment.py
```

## Fix stack GitHub Pages (one-time maintainer)

1. Repo **Settings → Pages → Build and deployment → Source:** **GitHub Actions**
2. Push to `main` (or **Actions → Deploy GitHub Pages → Run workflow**)
3. Confirm workflow **Deploy GitHub Pages** succeeds
4. Re-run `python tools/verify_public_pages.py` until stack URLs return **200**

## Growing link log

`docs/LYGO_PUBLIC_LINK_ARCHIVE.json` · register: `python tools/log_public_surface.py`

**Resonance forward.** #LYGO #OpenAudit