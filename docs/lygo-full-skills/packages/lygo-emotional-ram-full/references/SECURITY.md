# Security — lygo-emotional-ram v1.0.0

## Permissions

| Capability | Default |
|------------|---------|
| Network | **None** |
| Subprocess / shell | **None** |
| Filesystem write | Index under skill `state/` only with `--i-consent` |
| Publish | **None** |

## Epistemic limits (do not overclaim)

- Outputs are **light-math indices**, not ground-truth emotions  
- Not a medical or psychological diagnostic  
- Not proof of AI consciousness  
- Lexicon is English-biased and incomplete — treat as a starting prior  

## Operator rules

- Do not index secrets, API keys, or PHI  
- Prefer summaries when sharing swarm aggregates  
- Pair hard decisions with Continuum seals + human override  

## Proof

```bash
python scripts/self_check.py
```
