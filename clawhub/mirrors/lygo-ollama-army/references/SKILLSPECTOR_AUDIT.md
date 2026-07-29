# SkillSpector audit — lygo-ollama-army v0.6.0

| Risk | Mitigation |
|------|------------|
| Dangerous code execution (process spawn) | No `import subprocess`; runpy allowlist only |
| Credential / env exfil via webhook | Outbound webhook deleted |
| MCP description poisoning | SKILL.md lists full automation surface |
| Excessive agency | Supervisors/planting/seed gated; agents must not auto-enable |
| Network | Localhost Ollama + optional public HTTPS GET probes only |

Signature: `Δ9Φ963-ARMY-SKILLSPECTOR-v0.6.0`
