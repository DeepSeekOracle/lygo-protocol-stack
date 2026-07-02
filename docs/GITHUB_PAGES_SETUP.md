# GitHub Pages — lygo-protocol-stack

Project URL (when active): **https://deepseekoracle.github.io/lygo-protocol-stack/**

## Enable

1. Open https://github.com/DeepSeekOracle/lygo-protocol-stack/settings/pages
2. **Build and deployment → Source:** select **GitHub Actions** (not “Deploy from branch” unless you prefer legacy).
3. Save.

## Deploy

Workflow: `.github/workflows/deploy-pages.yml`

- Uploads the **`docs/`** folder (includes `index.html`, harnesses, `.nojekyll`).
- Triggers on push to **`main`** and **workflow_dispatch**.

Manual run: **Actions** tab → **Deploy GitHub Pages** → **Run workflow**.

## Verify

```bash
python tools/verify_public_pages.py
```

Artifact: `tests/public_pages_last_run.json`

## Mirrors

Until stack Pages is green, public demos are served from **Excavationpro** (same HTML synced from this repo):

- `python tools/sync_excavationpro_harness.py`
- `python tools/sync_excavationpro_slm_page.py`