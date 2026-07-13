# Security — lygo-lattice-pulse v1.2

**SkillSpector:** No `child_process` / subprocess in plugin runtime (v1.2+). See `references/SKILLSPECTOR_AUDIT.md`.

- `lygo_star_chart_gate` — **read-only JS preview** on submission JSON; paths restricted to stack root or cwd.
- **Authoritative gate** — run `python scripts/gate_submission.py <submission.json>` with `LYGO_STACK_ROOT` set (in-process Python import, no subprocess in plugin).
- `lygo_lattice_pulse` / `lygo_registry_compare` — fetch public GitHub Pages JSON only.
- `lygo_lattice_verify` — local file existence + SHA reads only; no shell execution.
- No credentials in package; no auto publish or git push.
- Pair with human `--i-consent` on all live writes.