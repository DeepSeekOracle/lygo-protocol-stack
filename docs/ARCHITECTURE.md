# LYGO Protocol Stack Architecture

```
┌─────────────────────────────────────┐
│  Applications / Agents / Grok Audit │
└─────────────────┬───────────────────┘
                  │
        ┌─────────▼─────────┐
        │ Protocol 0        │  Φ-Gate (4KB policy)
        │ Nano Kernel       │
        └─────────┬─────────┘
                  │ AMPLIFY / SOFTEN / QUARANTINE
        ┌─────────▼─────────┐
        │ Protocol 1        │  Fragmented memory
        │ Memory Mycelium   │
        └───────────────────┘
```

## Design principles

1. **Determinism** — same bytes → same verdict across reference ports.
2. **Bounded input** — reject oversize payloads at the gate.
3. **Sovereign license** — ethical-use terms with Excavationpro IP retention.

## Links

- Grokipedia: https://grokipedia.com/page/lygo-protocol-stack
- Excavationpro: https://github.com/DeepSeekOracle/Excavationpro