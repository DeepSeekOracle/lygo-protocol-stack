# LYGO LLM Console — ClawHub skill v1.6.0 (ships console 1.5.6)

Sovereign local LLM runtime and agent portal. Not Ollama, and not the steward's admin tree.

This package holds two layers with different privileges, and says so in `SKILL.md`:

| Layer | Contents | Privileges |
|---|---|---|
| **map** | `scripts/` | prints URLs, hashes, self-check. No network, no subprocess, no writes. |
| **operator runtime** | `kit/` (unpacked tree, 152 files) | loopback HTTP, HTTPS GET to public hosts, writes inside its own folder, pinned llama-server subprocess, optional workspace shell/Python. **Not a sandbox.** |

## Verify, then run

```bash
npx --yes clawhub@0.23.3 install deepseekoracle/lygo-llm-console
python scripts/self_check.py
python scripts/verify_kit.py        # every file in kit/ checked against kit/KIT_SHA256SUMS.txt
```

`kit/PUBLIC_KIT.json` lists every shipped file with its SHA-256, the source tree it came from, and
what was deliberately left out (weights, engine binaries, tests/fixtures, the steward's admin files).

Then: put ggml-org CPU `llama-server.exe` (tag **b11074**) in `kit/engine/`, run `kit/INSTALL.bat`
once, then `kit/LYGO_LLM_CONSOLE.bat` as an unprivileged user. Portal: <http://127.0.0.1:9641/>.

## Why the kit ships unpacked

The v1.2.0 package shipped a zip. A registry scanner cannot read a zip completely, and reported four
HIGH findings ("referenced artifact was not completely inspected", "text artifact contains embedded
NUL bytes" from binary test fixtures inside it). This release ships the tree itself, with a per-file
manifest, so the same scanner reads exactly what would run.

## Links

- Page: <https://chatagent.ca/lygo-llm-console.html>
- ClawHub: <https://clawhub.ai/deepseekoracle/skills/lygo-llm-console>
- Source: <https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/clawhub/mirrors/lygo-llm-console>

Steward: Justin Helmer (Excavationpro / Lightfather). Dual ledgers / Haven Star Chart are CANON; this
package is RESOURCE. Donate: <https://www.paypal.com/paypalme/ExcavationPro>
