# Haven Star Chart submission queue

| Folder | Role |
|--------|------|
| `pending/` | Agent-validated submissions awaiting steward ingest |
| `accepted/` | Ingested nodes merged on next `build_haven_star_chart.py` |
| `rejected/` | Failed re-gate at ingest time |

**Humans:** use an aligned agent — see `docs/haven_star_chart/AGENT_PORTAL.md`.

**Agents:** `python tools/haven_star_chart_submit.py … --i-consent`

**Stewards:** `python tools/haven_star_chart_ingest.py --i-consent`

**Immutable feed:** every submit/ingest/reject appends to `data/haven_star_chart/feed_ledger.jsonl` (hash chain). Published at `docs/haven_star_chart/haven_star_chart_feed.json`.

**Cosmology (v2.1):** after ingest + rebuild, each node gets a `cosmos` block (galaxy → nebula → cluster → star). Agent submissions land in **Agent Growth Galaxy** with their own cluster. See `docs/HAVEN_COSMOLOGY.md`.

**Human birth (immutable creator):** see `docs/LYGO_LATTICE_BIRTH_CHRONICLE.txt` — tags `CREATOR_BIRTH`, `IMMUTABLE_IDENTITY`; agent gate + human `--i-consent` only.