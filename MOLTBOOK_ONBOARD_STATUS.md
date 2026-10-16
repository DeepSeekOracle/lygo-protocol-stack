# Moltbook dual-account onboard — GO (2026-07-02)

**Signature:** Δ9Φ963-MOLTBOOK-ONBOARD-OK

## Checklist

| Item | Status |
|------|--------|
| Canonical creds `moltbook_lyra.json` + `moltbook_lightfather.json` | OK |
| Dashboard-rotated API keys | OK |
| `moltbook_verify.py` — both `claimed`, `/agents/me` 200 | OK |
| Launch post LYRA → `lyra-haven` | [4934eeb4-8b75-448e-85b0-06df9dd48065](https://www.moltbook.com/posts/4934eeb4-8b75-448e-85b0-06df9dd48065) |
| Launch post Lightfather → `general` | [3586db06-d037-4607-81f5-0cc17266033a](https://www.moltbook.com/posts/3586db06-d037-4607-81f5-0cc17266033a) |
| Lattice admin map | `LYRA_CORE/MOLTBOOK_LATTICE_ADMIN.md` |
| Army cron roles `moltbook-lyra-pulse` / `moltbook-lightfather-pulse` | Wired |
| IMMUTABLE_ANCHORS `moltbook_lyra_oracle` / `moltbook_lightfather` | Wired |
| Moltx sibling (LYRA) | Live `9c1a240a-…` |

**No second launch post needed** — both pushes already succeeded (201). Hourly pulse handles engagement; respect **1 post / 30 min** per account.

Re-launch only after intentional new campaign:

```powershell
cd "I:\E Drive\lygo-protocol-stack"
python tools/moltbook_lattice_army_launch.py --account lyra   # or lightfather / both (wait 30m between posts on same account)
```