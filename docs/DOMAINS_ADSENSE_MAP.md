# Owned domains → AdSense site roots

**Publisher:** `ca-pub-0646320966060599`  
**ads.txt (every root):**
```text
google.com, pub-0646320966060599, DIRECT, f08c47fec0942fa0
```

Packages: `docs/domain-roots/<domain>/`  
Each package: `index.html` + meta + AdSense script + `ads.txt` + `privacy.html` + `CNAME` + robots/sitemap.

---

## Map

| Domain | GitHub Pages repo | Homepage content | GH.io mirror (works now) |
|--------|-------------------|------------------|---------------------------|
| **eternalhaven.ca** | [DeepSeekOracle/eternalhaven](https://github.com/DeepSeekOracle/eternalhaven) | Eternal Haven / LYGO hub | https://deepseekoracle.github.io/eternalhaven/ |
| **excavationpro.ca** | [DeepSeekOracle/excavationpro-ca](https://github.com/DeepSeekOracle/excavationpro-ca) | Legacy Guardian music hub | https://deepseekoracle.github.io/excavationpro-ca/ |
| **deepseekoracle.com** | [DeepSeekOracle/deepseekoracle-com](https://github.com/DeepSeekOracle/deepseekoracle-com) | DeepSeek Oracle main hub | https://deepseekoracle.github.io/deepseekoracle-com/ |
| **chatagent.ca** | [DeepSeekOracle/chatagent](https://github.com/DeepSeekOracle/chatagent) | LYGO Champion Hub | https://deepseekoracle.github.io/chatagent/ |
| **asiancoastline.com** | [DeepSeekOracle/asiancoastline](https://github.com/DeepSeekOracle/asiancoastline) | Music portal (listen free) | https://deepseekoracle.github.io/asiancoastline/ |
| **bpmfinder.ca** | [DeepSeekOracle/bpmfinder](https://github.com/DeepSeekOracle/bpmfinder) | Free BPM Finder | https://deepseekoracle.github.io/bpmfinder/ |

Also: full catalog still at https://deepseekoracle.github.io/Excavationpro/ (all pages AdSense-tagged).

---

## Status (2026-07-18 evening)

DNS for all six was switched to **GitHub Pages A records** (`185.199.108–111.153`). Live checks:

| Check | Result |
|-------|--------|
| Homepages | Serving real site packages (not frameset parking) |
| **`/ads.txt`** | Correct pub line on each domain (http) |
| **www** | CNAME → `deepseekoracle.github.io` |
| **HTTPS padlock** | Pending GitHub free cert + **Enforce HTTPS** in each repo Pages settings |

asiancoastline.com homepage = **full music portal** (10,762 streams) for AdSense.

---

## GoDaddy DNS (each domain)

1. Remove **forwarding / parking / website** that uses `3.33.*` / `15.197.*`.
2. Set DNS:

| Type | Name | Value | TTL |
|------|------|--------|-----|
| **A** | `@` | `185.199.108.153` | 600 |
| **A** | `@` | `185.199.109.153` | 600 |
| **A** | `@` | `185.199.110.153` | 600 |
| **A** | `@` | `185.199.111.153` | 600 |
| **CNAME** | `www` | `deepseekoracle.github.io` | 600 |

3. In each repo → **Settings → Pages**: custom domain already set via `CNAME` file; wait for DNS check → **Enforce HTTPS**.
4. Verify:

```text
https://<domain>/
https://<domain>/ads.txt
https://<domain>/privacy.html
```

View-source must include:

```html
<meta name="google-adsense-account" content="ca-pub-0646320966060599">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-0646320966060599"
     crossorigin="anonymous"></script>
```

5. Only then confirm “site ready” in AdSense for that property.

---

## AdSense properties checklist

For **each** of the six domains, AdSense needs:

1. Meta tag in `<head>` — in package ✅  
2. Official script in `<head>` — in package ✅  
3. Root `ads.txt` — in package ✅ (live on custom domain **after DNS**)  
4. Working HTTPS homepage — after DNS + Enforce HTTPS  

Until DNS is fixed, use GH.io URLs above to prove content; AdSense domain properties still need the custom domain DNS fix.
