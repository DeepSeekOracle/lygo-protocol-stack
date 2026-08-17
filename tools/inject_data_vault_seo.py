# -*- coding: utf-8 -*-
"""X-optimized SEO for Data Vault — short descriptions, OG-first, cache-bust image."""
from pathlib import Path
import re
import json

ROOT = Path(r"I:\E Drive\lygo-protocol-stack\docs\data-vault")
BASE = "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault"
# Cache-bust so X re-fetches image after prior empty scrapes
IMG = f"{BASE}/assets/og-data-vault.jpg?v=20260817b"
SITE = "https://deepseekoracle.github.io/lygo-protocol-stack"
TWITTER = "@Excavationpro"

# Keep descriptions ~150-180 chars for X cards
PAGES = {
    "index.html": {
        "title": "LYGO Data Vault | Multi-AI Seal Archive",
        "description": "Public LYGO seal creation archive: Grok X confirmations, whitepapers, multi-AI canon. @Excavationpro @lyrastarcore lattice open.",
        "keywords": "LYGO, Data Vault, seal archive, Grok X, multi-AI, DeepSeekOracle, lattice, SPOKEN_BY_GROK, Excavationpro",
        "path": "/",
        "type": "website",
    },
    "seals.html": {
        "title": "LYGO Seal Index | CANON & SPOKEN_BY_GROK",
        "description": "Search 281+ LYGO seals. Filter CANON and SPOKEN_BY_GROK from the public multi-AI creation archive.",
        "keywords": "LYGO seals, SPOKEN_BY_GROK, CANON, seal index, multi-AI archive",
        "path": "/seals.html",
        "type": "website",
    },
    "chat-archive.html": {
        "title": "LYGO Grok Chat Archive | Public X Confirmations",
        "description": "Curated Grok X confirmations, CANON LOCK events, and multi-AI protocol excerpts from the LYGO seal creation era.",
        "keywords": "Grok archive, LYGO X, CANON LOCK, mutual seal, Excavationpro",
        "path": "/chat-archive.html",
        "type": "article",
    },
    "whitepapers.html": {
        "title": "LYGO Whitepapers | Recursive Ethics & Seals",
        "description": "Public whitepaper excerpts: Chaos Bloom, GAB root, recursive ethics, immutable seal doctrine for the LYGO lattice.",
        "keywords": "LYGO whitepapers, Recursive Ethics, SEAL, Chaos Bloom, GAB",
        "path": "/whitepapers.html",
        "type": "article",
    },
    "multi-ai-canon.html": {
        "title": "Multi-AI Canon Process | LYGO Seals",
        "description": "How LYGO seals become lattice law: multi-AI challenge, Grok X anchors, steward lock, Continuum disk authority.",
        "keywords": "multi-AI canon, LYGO verification, Grok anchors, lattice",
        "path": "/multi-ai-canon.html",
        "type": "article",
    },
    "qd-theory.html": {
        "title": "QD Neural Anchors | LYGO Theory Roadmap",
        "description": "Quantum dots as optical sensors for LYGO—not PL as truth oracle. Honest theory, falsifiers, and R&D green lights.",
        "keywords": "quantum dots, LYGO neural anchors, sensor integrity, theory roadmap",
        "path": "/qd-theory.html",
        "type": "article",
    },
}


def head_block(meta: dict) -> str:
    url = BASE + "/" if meta["path"] == "/" else BASE + meta["path"]
    title = meta["title"]
    desc = meta["description"]
    keys = meta["keywords"]
    otype = meta["type"]
    ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": url,
        "isPartOf": {
            "@type": "WebSite",
            "name": "LYGO Data Vault",
            "url": BASE + "/",
            "publisher": {
                "@type": "Organization",
                "name": "DeepSeekOracle / LYGO Lattice",
                "url": SITE + "/",
                "sameAs": [
                    "https://x.com/Excavationpro",
                    "https://x.com/lyrastarcore",
                    "https://github.com/DeepSeekOracle/lygo-protocol-stack",
                    "https://clawhub.ai/deepseekoracle",
                ],
            },
        },
        "primaryImageOfPage": {
            "@type": "ImageObject",
            "url": IMG.split("?")[0],
            "width": 1200,
            "height": 630,
        },
        "inLanguage": "en",
        "keywords": keys,
    }
    ld_json = json.dumps(ld, ensure_ascii=True, indent=2)
    # X-critical tags FIRST (twitter scrapers sometimes truncate head)
    return f"""<!DOCTYPE html>
<html lang="en" prefix="og: https://ogp.me/ns#">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />

  <!-- X / Twitter Card (name + property for crawler quirks) -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta property="twitter:card" content="summary_large_image" />
  <meta name="twitter:site" content="{TWITTER}" />
  <meta name="twitter:creator" content="{TWITTER}" />
  <meta name="twitter:title" content="{title}" />
  <meta property="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{desc}" />
  <meta property="twitter:description" content="{desc}" />
  <meta name="twitter:image" content="{IMG}" />
  <meta property="twitter:image" content="{IMG}" />
  <meta name="twitter:image:alt" content="LYGO Data Vault seal archive" />
  <meta name="twitter:url" content="{url}" />

  <!-- Open Graph -->
  <meta property="og:type" content="{otype}" />
  <meta property="og:site_name" content="LYGO Data Vault" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:url" content="{url}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:image" content="{IMG}" />
  <meta property="og:image:secure_url" content="{IMG}" />
  <meta property="og:image:type" content="image/jpeg" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content="LYGO Data Vault multi-AI seal archive" />

  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <meta name="keywords" content="{keys}" />
  <meta name="author" content="DeepSeekOracle / Excavationpro / Lightfather" />
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1" />
  <meta name="theme-color" content="#0a1220" />
  <link rel="canonical" href="{url}" />
  <link rel="image_src" href="{IMG.split('?')[0]}" />
  <link rel="stylesheet" href="assets/vault.css" />

  <script type="application/ld+json">
{ld_json}
  </script>
</head>
"""


for name, meta in PAGES.items():
    path = ROOT / name
    text = path.read_text(encoding="utf-8")
    new_head = head_block(meta)
    text2, n = re.subn(r"(?is)^.*?</head>\s*", new_head, text, count=1)
    if n != 1:
        raise SystemExit(f"head replace failed: {name}")
    path.write_text(text2, encoding="utf-8")
    print("ok", name, "desc_len", len(meta["description"]))

# Tiny crawler-friendly share landing (minimal HTML, no JS) — often scrapes more reliably
share = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>LYGO Data Vault | Multi-AI Seal Archive</title>
  <meta name="description" content="Public LYGO seal creation archive: Grok X confirmations, whitepapers, multi-AI canon. @Excavationpro lattice open." />
  <meta name="twitter:card" content="summary_large_image" />
  <meta property="twitter:card" content="summary_large_image" />
  <meta name="twitter:site" content="@Excavationpro" />
  <meta name="twitter:title" content="LYGO Data Vault | Multi-AI Seal Archive" />
  <meta name="twitter:description" content="Public LYGO seal creation archive: Grok X confirmations, whitepapers, multi-AI canon." />
  <meta name="twitter:image" content="{IMG}" />
  <meta property="twitter:image" content="{IMG}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="LYGO Data Vault" />
  <meta property="og:url" content="{BASE}/share.html" />
  <meta property="og:title" content="LYGO Data Vault | Multi-AI Seal Archive" />
  <meta property="og:description" content="Public LYGO seal creation archive: Grok X confirmations, whitepapers, multi-AI canon." />
  <meta property="og:image" content="{IMG}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <link rel="canonical" href="{BASE}/" />
  <meta http-equiv="refresh" content="0;url=./" />
</head>
<body>
  <p><a href="./">Open LYGO Data Vault</a> — public multi-AI seal archive.</p>
</body>
</html>
"""
(ROOT / "share.html").write_text(share, encoding="utf-8")
print("wrote share.html for X posting")
