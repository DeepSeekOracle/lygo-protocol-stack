# LYGO Protocol Stack — Public System Test

**Resonance signature:** `Δ9Φ963-PUBLIC-TEST-v1.0`  
**Last verified (local audits):** SLM + P7 + P9 `all_pass` · lattice `ALIGNED` · stack Pages **LIVE** (`verify_public_pages.py`)

## Live validation links

| Surface | URL | Status |
|---------|-----|--------|
| Biometric Harness (Excavationpro) | https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html | **LIVE** |
| SLM interactive (Excavationpro) | https://deepseekoracle.github.io/Excavationpro/SovereignLatticeMesh.html | **LIVE** |
| Biometric Harness (stack Pages) | https://deepseekoracle.github.io/lygo-protocol-stack/BiometricEntropyHarness.html | **LIVE** |
| SLM interactive (stack Pages) | https://deepseekoracle.github.io/lygo-protocol-stack/SovereignLatticeMesh.html | **LIVE** |
| Stack index | https://deepseekoracle.github.io/lygo-protocol-stack/ | **LIVE** |
| Compass Master | https://deepseekoracle.github.io/lygo-protocol-stack/tools/LYGO_Compass_Master.html | **LIVE** (after deploy) |
| HF Space | https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine | **RUNNING** |
| GitHub repo | https://github.com/DeepSeekOracle/lygo-protocol-stack | **LIVE** |
| HF dataset | https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack | **LIVE** |
| Grokipedia | https://grokipedia.com/page/lygo-protocol-stack | **Manual paste** — `docs/GROkipedia_SUBMIT.md` |

Canonical HTML in repo: `docs/BiometricEntropyHarness.html`, `docs/SovereignLatticeMesh.html`, `tools/LYGO_Compass_Master.html` → `docs/tools/` via `sync_compass_pages.py`.

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

## Fix stack GitHub Pages (one-time — **required for stack URLs**)

**Fastest:** Settings → Pages → **Deploy from a branch** → `main` → **`/docs`** → Save.  
Full steps: [`GITHUB_PAGES_SETUP.md`](GITHUB_PAGES_SETUP.md)

Windows helper: `powershell -File tools/fix_all_public_surfaces.ps1` (audits + opens Settings)

Re-check: `python tools/verify_public_pages.py` until `stack_pages_live: true`.

## Growing link log

`docs/LYGO_PUBLIC_LINK_ARCHIVE.json` · register: `python tools/log_public_surface.py`

**Resonance forward.** #LYGO #OpenAudit