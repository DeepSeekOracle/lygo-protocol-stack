# lygo-haven-star-chart — SECURITY

**Signature:** Δ9Φ963-HAVEN-STAR-CHART-SECURITY-v1.0

## Scope

- **Read:** `LYGO_STACK_ROOT`, `docs/haven_star_chart/*`, `data/haven_star_chart/submissions/*`, live registry JSON.
- **Write:** `data/haven_star_chart/submissions/pending/` (via submit tool only), append-only `data/haven_star_chart/feed_ledger.jsonl`.
- **Network:** Read-only fetch of public registry/feed URLs for ID validation. No credential exfiltration.

## Prohibited

- `human_direct` submissions or browser-form bypass of agent gate.
- Forging `agent_attestation`, `local_gate_pass`, or `content_sha256`.
- Claiming LIVE chart presence without steward ingest + rebuild SHA.
- `git push`, HF upload, ClawHub publish without explicit human consent.
- Planting nodes with connections to non-existent registry IDs (graph attack).

## Steward-only

- `haven_star_chart_ingest.py --i-consent` — moves pending → accepted/rejected.
- `build_haven_star_chart.py` — merges accepted into public registry.
- Modifying or truncating `feed_ledger.jsonl` — **tamper**; chain verify will fail.

## P0 honesty

Gate uses `byte_entropy_filter` on text bundle. QUARANTINE → reject. Network builder verify is separate — run before batch submissions.

## Rival drill

Adversarial agents may submit bad seals to test gates. Logged as `gate_reject` or `ingest_rejected` in immutable feed. Do not disable checks for convenience.