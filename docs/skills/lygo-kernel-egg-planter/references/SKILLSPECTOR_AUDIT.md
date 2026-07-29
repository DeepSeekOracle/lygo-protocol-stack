# SkillSpector audit response — lygo-kernel-egg-planter v1.3.0

**Signature:** Delta9Phi963-KERNEL-EGG-PLANTER-SKILLSPECTOR-v1.3  
**Source audit:** ClawHub security page (NVIDIA SkillSpector findings)

## Findings → fixes

| Finding | Severity | Fix in v1.3.0 |
|---------|----------|----------------|
| Manifest undeclared permissions | Medium | Added full `claw.json` `permissions` (network, filesystem, env, publish:never auto) |
| "no auto-publish" vs plant surfaces | Medium | Docs + CLI clarify: `clawhub`/`pages` = **local prep only**; skill never git-push / clawhub.ai publish |
| Retrieve without consent | Medium | `retrieve_egg.py` requires `--i-consent` or `LYGO_EGG_PLANT_CONSENT` for list and retrieve |
| `--skip-verify` integrity bypass | High | **Removed** from `plant_with_consent.py` — post-plant verify always runs |
| `--force` retrieve bypass | High | **Removed** from `retrieve_egg.py` — QUARANTINE always blocks |
| Docstring vs force path | High | Docstrings + SKILL.md + AGENT_CONTRACT aligned; no unsafe flags |

## Preserved function

| Capability | Status |
|------------|--------|
| Consent-gated plant | Yes (`--i-consent`) |
| Preflight | Yes |
| Build + anchor (local/turbo) | Yes |
| Mandatory post-plant verify | Yes (stronger — no skip) |
| List/retrieve after ALIGNED | Yes (now also consent-gated) |
| Champion / catalog helpers | Yes |
| Auto git / ClawHub publish / social | Still **never** |

## Operator checklist

```bash
python scripts/preflight.py
python scripts/plant_with_consent.py --i-consent --local-only
python scripts/verify_eggs.py --json
python scripts/retrieve_egg.py --i-consent --list
python scripts/retrieve_egg.py --i-consent --egg p0-nano-kernel
```

## VirusTotal

Re-run `npx clawhub scan --slug lygo-kernel-egg-planter --version 1.3.0 --update` after publish.
