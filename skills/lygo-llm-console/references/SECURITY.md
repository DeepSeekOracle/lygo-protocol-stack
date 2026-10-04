# Security — lygo-llm-console v1.2.0

## Two layers

| Layer | Privilege |
|-------|-----------|
| Map scripts | No network, no subprocess, no writes |
| Operator kit (after hash verify) | Loopback HTTP, HTTPS GET with private/metadata block, workspace writes, cmd.exe /c without metacharacters, llama-server subprocess |

## Pins

- ClawHub CLI: `clawhub@0.23.3` (not `@latest`)
- Kit SHA-256: `b60ed6deae6f1dba7182fa386bd00b1e724001638e8f2f30936af0a240b4444e`
- llama.cpp CPU tag: `b10988`

## Operator rules

- Unprivileged user. No elevated terminal.
- Default bind 127.0.0.1. LAN requires `--lan --i-consent`.
- Do not run if `verify_kit.py` fails.
- Admin vaults are not in this package.
