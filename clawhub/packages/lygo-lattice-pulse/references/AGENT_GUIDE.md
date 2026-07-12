# LYGO Lattice Pulse — Agent Guide v1.1

**Signature:** Δ9Φ963-LYGO-LATTICE-PULSE-GUIDE-v1.1

## Install

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse
```

```json5
{
  plugins: {
    entries: {
      "lygo-lattice-pulse": {
        enabled: true,
        config: {
          stackRoot: "I:/path/to/lygo-protocol-stack",
          pagesBase: "https://deepseekoracle.github.io/lygo-protocol-stack"
        }
      }
    }
  },
  tools: {
    allow: [
      "lygo_lattice_pulse",
      "lygo_alignment_ready",
      "lygo_consent_checklist",
      "lygo_lattice_verify",
      "lygo_registry_compare",
      "lygo_star_chart_gate",
      "lygo_p0_quick_scan"
    ]
  }
}
```

## Readiness ladder

```
lygo_alignment_ready
    ├─ live_pulse (Pages JSON reachable)
    ├─ stack_markers (LYGO_STACK_ROOT complete)
    └─ registry_match (local SHA === live SHA)
         ↓
lygo_star_chart_gate (authoritative ACCEPT)
         ↓
human --i-consent → submit / ingest
```

## Never

- Claim LIVE without `registry_match`
- Skip gate because `lygo_p0_quick_scan` passed
- Publish `consent_bundle` or `family_bind_salt`
- Auto submit without human approval