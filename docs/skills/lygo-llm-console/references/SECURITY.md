# Security — lygo-llm-console v1.2.0

## Two layers

| Layer | Privilege |
|-------|-----------|
| Map scripts | No network, no subprocess, no writes |
| Operator kit (after hash verify) | Loopback HTTP, HTTPS GET with private/metadata block, workspace writes, cmd.exe /c without metacharacters, llama-server subprocess |

## Pins

- ClawHub CLI: `clawhub@0.23.3` (not `@latest`)
- Kit SHA-256: `0df99aeb65593e336d33a8252101364fb7b4e595e888ed79280341aa7195e4ce`
- llama.cpp CPU tag: `b10988`

## Operator rules

- Unprivileged user. No elevated terminal.
- Default bind 127.0.0.1. LAN requires `--lan --i-consent`.
- Do not run if `verify_kit.py` fails.
- Admin vaults are not in this package.
