# Security — lygo-lattice-pulse v1.1

- `lygo_star_chart_gate` runs local Python only; paths restricted to stack root or cwd.
- `lygo_lattice_pulse` / `lygo_registry_compare` fetch public GitHub Pages JSON only.
- No credentials in package; no auto publish or git push.
- Authoritative gates remain `haven_star_chart_gate.py` and steward ingest.
- Pair with human `--i-consent` on all live writes.