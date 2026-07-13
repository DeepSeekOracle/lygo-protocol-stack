# SkillSpector audit response — lygo-lattice-pulse v1.2

**Signature:** Δ9Φ963-LATTICE-PULSE-SKILLSPECTOR-v1.2

NVIDIA SkillSpector flagged **`suspicious.dangerous_exec`** (`child_process.spawnSync`) in v1.1. This revision removes all subprocess usage from the OpenClaw plugin runtime.

## Mitigations applied (v1.2)

| Finding | Mitigation |
|---------|------------|
| `child_process` / `spawnSync` | **Removed** from `src/index.ts` and bundled `dist/index.js`. Plugin tools use read-only `fs` + `fetch` + in-process JS gate preview only. |
| Shell command execution | Authoritative Python gate runs **outside** the plugin via bundled `scripts/gate_submission.py` (in-process import allowlist — same pattern as `lygo-haven-star-chart` skill). Humans/agents invoke explicitly in terminal. |
| Alignment probe subprocess | Replaced with `lattice_alignment_probe: deferred_no_subprocess` + documented `python tools/verify_lattice_alignment.py` command. |
| Unrestricted tool access | `LYGO_STACK_ROOT` required for local reads; submission paths rejected if outside stack root or cwd; `..` and unsafe chars blocked. |
| Autonomous live submit | Unchanged policy: plugin never writes; human `--i-consent` on `haven_star_chart_submit.py` / ingest. |

## Plugin tool vs authoritative gate

| Layer | Mechanism | Authoritative? |
|-------|-----------|----------------|
| `lygo_star_chart_gate` | JS preview (`gate_preview.ts`) | No — schema/math/connection checks only |
| `scripts/gate_submission.py` | In-process `haven_star_chart_gate.py` | **Yes** — full P0 + lineage |
| `lygo-haven-star-chart` skill | Same allowlist pattern | **Yes** |

## Operator checklist

1. Point `LYGO_STACK_ROOT` at **your** cloned `lygo-protocol-stack`.
2. Run `python scripts/self_check.py` from the plugin directory.
3. Use plugin tools for pulse, verify, registry compare (read-only).
4. Before live submit: `python scripts/gate_submission.py your_submission.json`
5. Human `--i-consent` on submit/ingest only after authoritative ACCEPT.

## VirusTotal

Package ships static docs + small Python helpers + bundled ESM (`dist/index.js`) with **no** `child_process` import.