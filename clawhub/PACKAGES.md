# ClawHub packages (OpenClaw plugins)

| Package | Type | ClawHub |
|---------|------|---------|
| [@deepseekoracle/lygo-lattice-pulse](./packages/lygo-lattice-pulse/) | Code Plugin | https://clawhub.ai/deepseekoracle/lygo-lattice-pulse |

## Publish

```bash
cd clawhub/packages/lygo-lattice-pulse
clawhub package validate .
clawhub package publish . --family code-plugin --name @deepseekoracle/lygo-lattice-pulse --display-name "LYGO Lattice Pulse" --version 1.0.0
```

Or from GitHub after push:

```bash
clawhub package publish DeepSeekOracle/lygo-protocol-stack \
  --source-path clawhub/packages/lygo-lattice-pulse \
  --family code-plugin --name @deepseekoracle/lygo-lattice-pulse --version 1.0.0
```