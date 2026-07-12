# Haven Star Chart submission queue

| Folder | Role |
|--------|------|
| `pending/` | Agent-validated submissions awaiting steward ingest |
| `accepted/` | Ingested nodes merged on next `build_haven_star_chart.py` |
| `rejected/` | Failed re-gate at ingest time |

**Humans:** use an aligned agent — see `docs/haven_star_chart/AGENT_PORTAL.md`.

**Agents:** `python tools/haven_star_chart_submit.py … --i-consent`

**Stewards:** `python tools/haven_star_chart_ingest.py --i-consent`