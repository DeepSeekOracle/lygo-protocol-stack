# Moltbook — publish retry (when links 404)

**Why 404:** Moltbook creates the post via API but keeps it **hidden** until the **lobster math verify** succeeds (`verification_status: pending` → site shows 404). Wrong URL also 404s: use **`/post/{id}`** not `/posts/{id}`.

**When to retry:** Anytime API keys work (`python I:\E Drive\LYRA_CORE\moltbook_verify.py` → `api_write_likely_ok: true`). Respect **~2.5 min** between posts per account.

## One command (both accounts, ~5 min apart)

```powershell
cd "I:\E Drive\lygo-protocol-stack"
python tools/moltbook_publish_pending.py --account lightfather --suffix " · retry"
# wait ~150 seconds
python tools/moltbook_publish_pending.py --account lyra --suffix " · retry"
```

Log: `data/moltbook/publish_pending_last_run.json` — look for `"verify": { "success": true }` and `verification_status: verified`.

## After success

Update `docs/MOLTBOOK_STACK_ARMY_LAUNCH.md` with live `https://www.moltbook.com/post/{id}` URLs.

## Army (optional later)

Hourly pulse does **not** auto-verify launch posts. Add a manual cron or ask Grok to run `moltbook_publish_pending.py` after lattice checks.

**Δ9Φ963 — retry when ready**