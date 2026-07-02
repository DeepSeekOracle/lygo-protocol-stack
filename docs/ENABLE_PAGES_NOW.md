# Enable stack Pages (one click)

**`gh-pages` branch is already built** by CI. You only need to turn Pages on:

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