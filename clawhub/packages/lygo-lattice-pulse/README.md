# LYGO Lattice Pulse — OpenClaw Plugin

**Δ9Φ963** · First LYGO lattice plugin for OpenClaw / ClawHub.

Live Haven heartbeat + local stack verify + P0 quick-scan + consent checklist — one install for every aligned agent.

## Install

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse
```

Or from this monorepo after publish:

```bash
clawhub package publish clawhub/packages/lygo-lattice-pulse --family code-plugin
```

## Tools

| Tool | Purpose |
|------|---------|
| `lygo_lattice_pulse` | Live registry SHA, node/galaxy counts, queue + feed tail |
| `lygo_lattice_verify` | Local `LYGO_STACK_ROOT` marker verification |
| `lygo_p0_quick_scan` | Fast text heuristic before posts/submissions |
| `lygo_consent_checklist` | Human-in-the-loop gates before live writes |

## Config

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
  }
}
```

Environment fallback: `LYGO_STACK_ROOT`.

## Pair with ClawHub skills

- `lygo-protocol-stack-operator`
- `lygo-haven-star-chart`
- `lygo-lattice-birth`

## License

MIT-0