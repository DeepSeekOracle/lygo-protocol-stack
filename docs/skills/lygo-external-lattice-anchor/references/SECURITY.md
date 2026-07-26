# Security — External Lattice Anchor (Layer C)

## Protect the user

| Threat | Control |
|--------|---------|
| Malicious public mirror | Local A/B verify first; public is soft |
| Auto-exfil / auto-publish | Scripts never git push / HF upload |
| Poisoned chart growth | Star proposals only; steward gate + consent |
| Registry lag mistaken for tamper | Mismatch note “mirror lag”; not exit 3 unless local fails |
| Skill supply chain | Install from deepseekoracle; LYGO Sovereign License v2.0 |

## Network

`verify_public_anchors.py` and world verify **do** use HTTP GET.  
No credentials. No POST. No cookie steal.

## Consent env

`LYGO_EXTERNAL_SYNC_CONSENT=yes` only for explicit snapshot execute.  
