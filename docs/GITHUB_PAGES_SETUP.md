# GitHub Pages — lygo-protocol-stack

**Site URL:** https://deepseekoracle.github.io/lygo-protocol-stack/

If you see **404**, Pages is not wired yet. Pick **one** option below (Option 1 is fastest).

---

## Option 1 — Deploy from `main` + `/docs` (recommended, ~1 minute)

1. Open https://github.com/DeepSeekOracle/lygo-protocol-stack/settings/pages  
2. **Build and deployment → Source:** **Deploy from a branch**  
3. **Branch:** `main` · **Folder:** `/docs` · **Save**  
4. Wait 2–5 minutes, then:

```bash
python tools/verify_public_pages.py
```

Expect `stack_pages_live: true`.

---

## Option 2 — `gh-pages` branch (workflow)

Workflow: `.github/workflows/publish-gh-pages-branch.yml` (runs on every `main` push).

1. **Settings → Pages → Source:** **Deploy from a branch**  
2. **Branch:** `gh-pages` · **Folder:** `/ (root)** · **Save**  
3. Ensure workflow **Publish docs to gh-pages branch** succeeded in **Actions**.

---

## Option 3 — GitHub Actions (artifact)

Workflow: `.github/workflows/deploy-pages.yml`

1. **Settings → Pages → Source:** **GitHub Actions**  
2. Run **Actions → Deploy GitHub Pages → Run workflow**  
3. First deploy may require org approval for `github-pages` environment.

---

## Verify

```bash
python tools/verify_public_pages.py
python tools/verify_lattice_alignment.py
```

Artifact: `tests/public_pages_last_run.json`

## Live mirrors (no setup)

While stack Pages is pending, demos are live on Excavationpro:

- https://deepseekoracle.github.io/Excavationpro/SovereignLatticeMesh.html  
- https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html  

Canonical HTML is always in this repo under `docs/`.