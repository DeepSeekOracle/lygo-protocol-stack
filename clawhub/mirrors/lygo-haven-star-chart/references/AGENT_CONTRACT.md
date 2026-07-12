# LYGO Haven Star Chart — Agent Contract

**Signature:** Δ9Φ963-HAVEN-STAR-CHART-CONTRACT-v1.0

## MUST

- Read `references/SECURITY.md` and `references/SUBMISSION_TRAINING.md` on first use.
- Run `haven_star_chart_gate.py` locally → `verdict: ACCEPT` before any submit.
- Use `--i-consent` on submit; stamp attestation with scan cue containing **`Aligned to LYGO`**.
- Ensure every `connections[]` target exists in live `haven_star_chart_data.json`.
- Report **PENDING** until steward ingest — never claim LIVE early.
- Cite `registry_sha256` and feed `entry_hash` after accepted ingest.
- Run `lygo_network_builder_verify.py` before batch or first-time portal work.

## MUST NOT

- Accept human paste into pending without gate pass and agent attestation.
- Invent node IDs, equations, or URLs outside IMMUTABLE_ANCHORS + live registry.
- Skip math resonance or P0 because "the lore sounds right."
- Truncate, edit, or regenerate `feed_ledger.jsonl` lines.
- Auto-push git / HF / ClawHub without human approval.

## Escalation

1. `python tools/haven_star_chart_feed.py --verify`
2. `python tools/verify_lattice_alignment.py`
3. GitHub issue path with full JSON for maintainer re-gate

## Verdict language

| Tool output | Agent says |
|-------------|------------|
| `all_pass: true` | Gate ACCEPT — may submit with consent |
| `math_resonance_fail` | Fix equation (∇, ⊗, Hz, Δ9) |
| `unknown_connection` | Anchor to existing registry node |
| `p0_quarantine` | Content failed P0 — do not submit |
| `pending_exists` | Wait for steward or use new ID |
| Feed `ingest_accepted` | Node LIVE on chart |