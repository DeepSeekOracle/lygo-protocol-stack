# LYGO LLM Console (ClawHub public skill)

**Mark:** LYGO — Justin Helmer (Excavationpro / Lightfather) + LYGO AI agents.  
**Page:** https://chatagent.ca/lygo-llm-console.html  
**Install:** `npx clawhub@latest install deepseekoracle/lygo-llm-console`

This folder is the **complete public skill**. It includes:

| Path | What it is |
|------|------------|
| `SKILL.md` | Agent instructions |
| `claw.json` | OpenClaw metadata |
| `skill-card.md` | Short identity card |
| `scripts/` | `self_check.py`, `lygo_llm_console_map.py` (no network, no subprocess) |
| `references/` | Security, public vs admin, credits |
| `kit/` | **Public runtime** (portal + Python console). Not the steward admin tree. |
| `examples/quickstart.md` | Install steps |

`kit/` does **not** contain `llama-server.exe` or GGUF weights. Place an official ggml-org Windows CPU `llama-server.exe` in `kit/engine/` then run `kit/LYGO_LLM_CONSOLE.bat`.

Admin/steward console (`lygo_llm_console/` on the stack, extra write-roots, vaults) is **not** this package.

Donate: https://www.paypal.com/paypalme/ExcavationPro
