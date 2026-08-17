# Security — TraumaCodex

## Not medical

This skill produces **lattice protocol seals** and audio waveforms from entropy maps.  
It is **not** a medical device, diagnosis tool, or treatment.

## Protect the user

| Threat | Control |
|--------|---------|
| Biometric exfil | Online channel never includes raw IBI; only digests |
| Secret leak | No tokens/keys in packages |
| Forced mesh merge | Local offline package is authority |
| Auto-publish | Never git/HF/ClawHub/social from skill |
| Supply chain | Install from deepseekoracle; verify FULL zip SHA on SkillHub |

## Network

Default **offline**. `--seal-mesh` writes local badge only.  
Optional living-mesh gossip uses **summaries only** (via lygo-living-mesh).

## Dependencies

- Public skill: stdlib + optional numpy for waveform  
- Stack mode: `LYGO_STACK_ROOT` with P7 + P8 modules  
