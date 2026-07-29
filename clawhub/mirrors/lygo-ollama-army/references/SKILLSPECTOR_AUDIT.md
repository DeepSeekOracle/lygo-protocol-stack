# SkillSpector response — lygo-ollama-army v0.8.0

Prior audit on v0.7.0: 15 findings (hard-coded authority root, public-pages seed, heartbeats→collector, planting consent gap, process-spawn wording, social roles, installer chaining, dashboard/metadata warnings).

## Remediation map

| Finding | v0.8.0 fix |
|---------|------------|
| `LYGO_AUTHORITY_ROOT=I:\E Drive` | Removed; living-memory audit needs explicit env |
| `public-pages-check` seeded by default | Removed from seed + idle cron; dual gate env+config |
| Heartbeats runs collector | Heartbeats runs **only** sentinel |
| Registry plant without consent | Requires `planting.consent` like eggs |
| “No process spawn” vs run_python | Documented: **no OS spawn**; in-process allowlisted runpy |
| Social / pulse roles | Require `access.social_publish` |
| Heavy stack roles | Require `access.allow_privileged_roles` |
| Installer auto-chains genesis/idle | No longer chains; print optional paths |
| Genesis metadata exposure | Forced 127.0.0.1 + console WARNING; browser open opt-in |
| Seed planting/self-tune drift | Separate env gates + config flags |

Signature: `Δ9Φ963-ARMY-SKILLSPECTOR-v0.8.0`
