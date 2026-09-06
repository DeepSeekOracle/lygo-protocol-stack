# LYGO Bench

Live: https://chatagent.ca/bench/

Browser workbench matching `lygo-site-card` + `lygo-context-guard`.

- Card: HTTPS GET or dropped HTML → title, CSP, SHA-256, ALIGNED / DRIFT / SHADOW
- Hash: local SHA-256 (text or file, cap 8 MB)
- Redact: local secret patterns (never uploaded)

No POST. No live Star Chart write. CORS miss = named SHADOW.

CLI:

```text
npx clawhub@latest install deepseekoracle/lygo-site-card
npx clawhub@latest install deepseekoracle/lygo-context-guard
```
