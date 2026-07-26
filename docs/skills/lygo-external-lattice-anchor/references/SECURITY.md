# Security — External Lattice Anchor (Layer C) v1.1

## Trust boundary

- Point `LYGO_STACK_ROOT` only at a **checkout you control**.  
- Untrusted stack roots can feed untrusted Python tools into allowlisted `runpy` paths under that root — treat stack as trusted code.  
- Public HTTP is **mirror data**, not authority over local eggs.

## Protect the user

| Threat | Control |
|--------|---------|
| Malicious public mirror | Local A+B verify first; public is soft |
| Auto-exfil / auto-publish | Scripts never git push / HF upload / ClawHub |
| Poisoned chart growth | Star **proposals** only; steward gate + consent |
| Registry lag as tamper | Mismatch note “mirror lag”; not exit 3 |
| Shell injection | **No `os.system`**; no shell=True |
| Surprising mutation | Verify **does not** auto-run builders (v1.1) |
| Skill supply chain | Install from `deepseekoracle`; LYGO Sovereign v2.0 |

## What runs by default

| Script | Network | Writes | Spawns builders |
|--------|---------|--------|-----------------|
| `verify_public_anchors.py` | HTTP GET | `tests/public_anchors_last_run.json` unless `--no-write-report` | Only if `--build-manifest` |
| `verify_world_lattice.py` | via public verify | `tests/world_lattice_last_run.json` unless `--no-write-report` | Only if `--refresh-local` |
| `build_public_verify_manifest.py` | no | `docs/public_verify_manifest.json` | n/a |
| `map_eggs_to_star_chart.py` | no | proposals JSON | n/a |
| `sync_external_plan.py` | no | none (dry) / docs snapshot with `--i-consent --execute-local-only` | n/a |

## Invocation model (v1.1)

- Sibling and stack scripts: `scripts/_safe_invoke.py` → `runpy.run_path`  
- Path must be under skill `scripts/` or under trusted `stack` root  
- Argv rejects shell metacharacters  
- No `eval` / string `exec`

## Network

- GET only for verify  
- No credentials, cookies, or POST in this skill  

## Consent env

`LYGO_EXTERNAL_SYNC_CONSENT=yes` only for explicit snapshot execute (with `--execute-local-only`).

## VirusTotal / static

Prior clean VT scan expected; re-scan after publish if required by policy.
