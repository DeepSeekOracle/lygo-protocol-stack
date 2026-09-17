# Enable stack Pages (one click)

## Site looks old after `git push`?

**Push to `main` is not the problem** — workflow **Publish docs to gh-pages branch** copies fresh `docs/` to `gh-pages`. The live URL stays stale when **Settings → Pages** is not pointed at that branch (or CDN has not refreshed).

1. https://github.com/DeepSeekOracle/lygo-protocol-stack/settings/pages  
2. **Source:** Deploy from a branch → **`gh-pages`** / **`/(root)`** → Save  
3. Hard-refresh the BPM page. Fresh HTML includes `lygo-top-bar` and title `Free BPM Finder Online | BPMfinder.ca`.  
4. Actions workflow **Deploy GitHub Pages** may fail if source is not “GitHub Actions” — ignore if `gh-pages` publish is green.

---

**`gh-pages` branch is built on every `main` push.** One-time enable:

1. Open https://github.com/DeepSeekOracle/lygo-protocol-stack/settings/pages  
2. **Build and deployment → Source:** Deploy from a branch  
3. **Branch:** `gh-pages` · **Folder:** `/ (root)`  
4. **Save**  
5. Wait 2–5 minutes, then:

```bash
python tools/verify_public_pages.py
```

**Alternative:** branch `main`, folder **`/docs`** (no `gh-pages` needed).

**Compass (pyvis):** after `tools/LYGO_Compass_Master.html` exists locally:

```bash
python tools/sync_compass_pages.py
git add docs/tools/LYGO_Compass_Master.html
git commit -m "docs: publish Compass Master to Pages"
git push origin main
```

Live URL: https://deepseekoracle.github.io/lygo-protocol-stack/tools/LYGO_Compass_Master.html

Strict CI check (optional): `set LYGO_REQUIRE_STACK_PAGES=1` before `verify_lattice_alignment.py`.