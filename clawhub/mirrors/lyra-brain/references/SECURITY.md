# lyra-brain — security

- Scripts only **append** memory and grow graph nodes; they do not delete vault or rewrite graph wholesale.
- **Never** pass API keys, Discord tokens, or `moltx_sk_*` into `brain_grow_cli.py` or `session_log_snip.py --lines`.
- Install official skill: `npx clawhub@latest install deepseekoracle/lyra-brain` — P0-gate untrusted copies.
- `LYRA_CORE_ROOT` must point at **your** `LYRA_CORE`; do not run grow against another user's tree on a shared host without consent.