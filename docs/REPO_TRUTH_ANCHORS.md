# Repo truth anchors (verify on GitHub — do not trust chat summaries)

**Signature:** `Δ9Φ963-REPO-TRUTH-v1`

Check live (do not trust chat — verify after each push):

```bash
git ls-remote https://github.com/DeepSeekOracle/lygo-protocol-stack.git refs/heads/main
git ls-remote https://github.com/DeepSeekOracle/lyra-crypto-operator.git refs/heads/main
```

Last balanced wave (verify SHAs match remote): stack **`dea1fd5`**+ (champion consolidation `1419e99`), crypto **`487f514`**, HF dataset commit on Hub UI, ClawHub `lyra-coin-launch-manager@1.1.3`.

Guardrails on stack mirror (must exist after `f6fb503+`):

```bash
git fetch origin
git show origin/main:clawhub/mirrors/lyra-coin-launch-manager/.gitignore
git show origin/main:clawhub/mirrors/lyra-coin-launch-manager/scripts/scan_for_secrets.py
```

Push both repos from maintainer PC:

```powershell
cd "I:\E Drive\lygo-protocol-stack"
python tools/push_with_git_credential.py
```

Canonical crypto source: `lyra-crypto-operator` @ GitHub; sync stub: `python tools/sync_from_lyra_crypto_operator.py`.