# LYGO Continuum — Security

**Signature:** `Delta9Phi963-CONTINUUM-v1.0.0`

## Surfaces

| Surface | Default |
|---------|---------|
| Network | **None** |
| Subprocess / shell | **None** |
| Filesystem read | Only paths the operator passes (`--claims`, `--capsule`, `--base`, claim paths) |
| Filesystem write | Only explicit `--out`; skill `state/` requires `--i-consent` |
| Publish / git / HF | **Never** automatic |

## Threat model

1. **Agent bluffing “done”** — Mitigated by falsifiable claims re-checked on disk.  
2. **Capsule tampering** — `root_hash` covers body; verify reports `integrity_ok: false`.  
3. **Path traversal** — Relative paths resolve under `--base` / cwd; absolute paths are operator-supplied (same as any local tool).  
4. **Regex DoS** — Pattern length capped; use simple patterns.  
5. **Secret leakage** — Do not put secrets in claims, task summaries, or handoff markdown. Prefer hashes of files that already exclude secrets.  
6. **Portal** — Client-side only; files hashed in-browser; no upload endpoint in the skill.

## SkillSpector notes

- No `subprocess`, `os.system`, `socket`, `urllib`, `requests`.  
- Honest description: local verify + handoff, not remote attestation.  
- Consent gate for `state/` writes.

## Operator rules

- Never seal claims you did not check.  
- Treat a failed verify (exit 10/11) as **not done**.  
- Handoff packs are shareable — strip private paths if publishing publicly.

**Δ9Φ963 — claims over vibes · human remains the publisher.**
