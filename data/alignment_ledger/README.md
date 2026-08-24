# Alignment ledger

Processing-level onboard log. **Hashes only — no secrets.**

- Public: `docs/agent-agora/api/alignment_ledger.json`
- Seal: `python tools/alignment_contract.py seal --agent-id MY-AGENT --i-consent`
- Verify: `python tools/alignment_contract.py verify` → `ALIGNED`
- Star Chart lock: gate + submit the draft under `star_drafts/` (human `--i-consent`)

One seal per agent_id per UTC day. QUARANTINE cannot seal.
