# SkillSpector BUILDER (FULL SkillHub)

Unlocked only on **https://chatagent.ca/lygoskillhub.html#full-lygo**.

Public ClawHub package ships scan/gate/batch/report. This folder adds:

| Command | Purpose |
|---------|---------|
| `html-batch` | Multi-root HTML risk dashboard under `state/` |
| `multi-gate` | CI matrix — fail if any skill exceeds max band |
| `ci-summary` | Compact JSON band counts for dashboards |

```bash
python builder/skill_spector_builder.py version
python builder/skill_spector_builder.py html-batch "I:/E Drive/.grok/skills" --write batch.html --i-consent
python builder/skill_spector_builder.py multi-gate "D:/lygo-protocol-stack/clawhub/mirrors" --max-band elevated
python builder/skill_spector_builder.py ci-summary ./skills --write ci.json --i-consent
```

Still: **no network, no subprocess, no auto-install.**

Signature: `Delta9Phi963-SKILL-SPECTOR-BUILDER-v1.0.0`
