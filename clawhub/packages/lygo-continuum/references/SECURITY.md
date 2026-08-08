# Security — lygo-continuum OpenClaw plugin v1.0.0

**Signature:** `Delta9Phi963-CONTINUUM-v1.0.0`

## Surfaces

| Surface | Default |
|---------|---------|
| Network | **None** |
| Subprocess / shell | **None** |
| Filesystem read | Claim paths relative to `base` / cwd; capsule_path absolute under operator control |
| Filesystem write | **None** in plugin tools (capsule returned as JSON text) |
| Publish / git | **Never** |

## Threat model

1. **Agent bluffs “done”** — Mitigated by `lygo_continuum_preflight_done` requiring sealed claims.  
2. **Capsule tamper** — `root_hash` integrity on verify.  
3. **Path abuse** — Relative paths under base; reject oversized / `..`-ish capsule paths.  
4. **Regex DoS** — Pattern length capped at 500.  
5. **Glob abuse** — No `**`; length cap; no `..`.

## SkillSpector notes

- No `child_process`, `spawn`, `exec`, `curl`, `fetch` to private hosts (no fetch at all).  
- Honest description: local claim engine, not remote attestation.  
- Pair with human review; Continuum does not prove design quality.

**Δ9Φ963 — claims over vibes · human remains the publisher.**
