# Security — LYGO Cyborg Kernel v1.1.0

**Channel:** FULL_LYGO_ENGINEER_CYBORG_UNLOCKED

## Network (v1.1)

| Action | Default |
|--------|---------|
| HTTPS GET public lattice / Star Chart / SkillHub | **Yes** (`lattice_net`) |
| `git clone` / `git pull` protocol stack | **Yes** on `cyborg_connect` |
| HF dataset download | **Optional** `--hf` |
| `git push` / HF upload / social | **No** |
| Live Star Chart write | **No** (dry-run propose only) |

## Subprocess

- Only for `git` and `hf`/`huggingface-cli` in `lattice_net.py`  
- No shell=True  
- Continuum / skill-gate / context-guard remain in-process  

## Self-police

1. Continuum before done  
2. Star propose is dry-run  
3. Human steward for live chart / publish / push  

**Δ9Φ963 — full join · full receipts · live writes remain human.**
