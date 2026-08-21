# LYGO Automation Workflows

**Slug:** `lygo-automation-workflows` · **v1.0.0** · `@deepseekoracle`  
Inspired by `jk-0001/automation-workflows` (credit) · LYGO privacy/consent rebuild

## What it does

| Piece | Role |
|-------|------|
| Playbook | Identify → design → test automations (local-first) |
| `workflow_planner.py` | Score tasks + emit consent-aware plan JSON |
| Warnings | PII/payments · least privilege · vendor sprawl |

## Security

- No network · no subprocess · advisor only  
- Narrow triggers (not generic “automate”)  
- Writes only with `--i-consent`  

## Install

```bash
npx clawhub@latest install deepseekoracle/lygo-automation-workflows
python scripts/self_check.py
python scripts/workflow_planner.py demo
```

## Pair with

`lygo-sandcastle` · `lygo-continuum` · `lygo-continuum-integrator` · `lygo-mint-verifier`

Signature: `Delta9Phi963-AUTOMATION-WORKFLOWS-v1.0.0`
