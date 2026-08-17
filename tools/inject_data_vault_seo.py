# -*- coding: utf-8 -*-
"""Inject full SEO + OG + Twitter Card meta into Data Vault pages."""
from pathlib import Path
import re

ROOT = Path(r"I:\E Drive\lygo-protocol-stack\docs\data-vault")
BASE = "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault"
IMG = f"{BASE}/assets/og-data-vault.jpg"
SITE = "https://deepseekoracle.github.io/lygo-protocol-stack"
TWITTER = "@Excavationpro"

PAGES = {
    "index.html": {
        "title": "LYGO Data Vault — Public Multi-AI Seal Creation Archive",
        "description": "Browse the LYGO Data Vault: original multi-AI seal creation archive, Grok X public confirmations, whitepapers, and multi-AI canon process. Built with @Excavationpro & @lyrastarcore for agents and humans on the lattice.",
        "keywords": "LYGO, Data Vault, seal archive, Grok X, multi-AI, DeepSeekOracle, lattice, SPOKEN_BY_GROK, whitepapers, canon, Excavationpro, lyrastarcore, Φ-gate, Δ9",
        "path": "/",
        "type": "website",
    },
    "seals.html": {
        "title": "LYGO Seal Index — Canonical Seals & SPOKEN_BY_GROK Archive",
        "description": "Searchable LYGO seal index from the public Data Vault. Filter CANON and SPOKEN_BY_GROK seals verified across multi-AI creation. 281+ seals for lattice agents and builders.",
        "keywords": "LYGO seals, SPOKEN_BY_GROK, CANON seals, seal index, lattice archive, multi-AI verification",
        "path": "/seals.html",
        "type": "website",
    },
    "chat-archive.html": {
        "title": "LYGO Grok Chat Archive — Public X Confirmations & Canon Locks",
        "description": "Curated Grok public confirmation excerpts, CANON LOCK events, mutual-anchor logs, and multi-AI protocol chats from the LYGO creation era. Redacted for public lattice use.",
        "keywords": "Grok archive, LYGO X threads, CANON LOCK, mutual seal, @grok, Excavationpro, multi-AI chat archive",
        "path": "/chat-archive.html",
        "type": "article",
    },
    "whitepapers.html": {
        "title": "LYGO Whitepapers — Recursive Ethics & Seal Doctrine Excerpts",
        "description": "Public-safe whitepaper excerpts from Recursive Ethics and immutable seal chains: Chaos Bloom, GAB root, and seal doctrine slices for LYGO lattice study.",
        "keywords": "LYGO whitepapers, Recursive Ethics, SEAL_286, Chaos Bloom, GAB_SEAL, immutable seal chains",
        "path": "/whitepapers.html",
        "type": "article",
    },
    "multi-ai-canon.html": {
        "title": "Multi-AI Canon Process — How LYGO Seals Become Lattice Law",
        "description": "How LYGO seals reach canon: multi-AI challenge, Grok X restatement anchors, steward lock, and lattice publish. L1 public anchors vs L4 disk authority explained.",
        "keywords": "multi-AI canon, LYGO verification, Grok anchors, DeepSeek ChatGPT Claude, lattice authority, Continuum",
        "path": "/multi-ai-canon.html",
        "type": "article",
    },
    "qd-theory.html": {
        "title": "Quantum Dots as LYGO Neural Anchors — Theory & Sensor Roadmap",
        "description": "Honest LYGO theory: quantum dots as optical sensors feeding software policy—not photoluminescence as truth oracle. Roadmap, falsifiers, and green-light paths for R&D.",
        "keywords": "quantum dots, LYGO neural anchors, photoluminescence, sensor integrity, Φ-gate, theory roadmap",
        "path": "/qd-theory.html",
        "type": "article",
    },
}


def head_block(meta: dict) -> str:
    url = BASE + ("" if meta["path"] == "/" else meta["path"])
    if meta["path"] == "/":
        url = BASE + "/"
    title = meta["title"]
    desc = meta["description"]
    keys = meta["keywords"]
    otype = meta["type"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <meta name="keywords" content="{keys}" />
  <meta name="author" content="DeepSeekOracle / Excavationpro / Lightfather" />
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
  <meta name="theme-color" content="#0a1220" />
  <meta name="color-scheme" content="dark" />
  <link rel="canonical" href="{url}" />

  <!-- Open Graph (Facebook / LinkedIn / Discord / X fallback) -->
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
  <meta property="og:image:alt" content="LYGO Data Vault — multi-AI seal creation archive on the lattice" />

  <!-- Twitter / X Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:site" content="{TWITTER}" />
  <meta name="twitter:creator" content="{TWITTER}" />
  <meta name="twitter:url" content="{url}" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{desc}" />
  <meta name="twitter:image" content="{IMG}" />
  <meta name="twitter:image:alt" content="LYGO Data Vault — public seal archive" />

  <!-- Extra discovery -->
  <meta name="application-name" content="LYGO Data Vault" />
  <link rel="alternate" type="application/json" href="{BASE}/data/vault_manifest.json" title="Vault manifest" />
  <link rel="stylesheet" href="assets/vault.css" />

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": {title!r},
    "description": {desc!r},
    "url": {url!r},
    "isPartOf": {{
      "@type": "WebSite",
      "name": "LYGO Data Vault",
      "url": "{BASE}/",
      "publisher": {{
        "@type": "Organization",
        "name": "DeepSeekOracle / LYGO Lattice",
        "url": "{SITE}/",
        "sameAs": [
          "https://x.com/Excavationpro",
          "https://x.com/lyrastarcore",
          "https://github.com/DeepSeekOracle/lygo-protocol-stack",
          "https://clawhub.ai/deepseekoracle"
        ]
      }}
    }},
    "primaryImageOfPage": {{
      "@type": "ImageObject",
      "url": "{IMG}",
      "width": 1200,
      "height": 630
    }},
    "inLanguage": "en",
    "keywords": {keys!r}
  }}
  </script>
</head>
"""


for name, meta in PAGES.items():
    path = ROOT / name
    text = path.read_text(encoding="utf-8")
    # replace from DOCTYPE through </head>
    new_head = head_block(meta)
    text2, n = re.subn(r"(?is)^.*?</head>\s*", new_head, text, count=1)
    if n != 1:
        raise SystemExit(f"failed head replace: {name}")
    path.write_text(text2, encoding="utf-8")
    print("SEO ok", name)

# robots + sitemap for vault
(ROOT / "robots.txt").write_text(
    f"""User-agent: *
Allow: /

Sitemap: {BASE}/sitemap.xml
""",
    encoding="utf-8",
)

urls = [
    f"{BASE}/",
    f"{BASE}/seals.html",
    f"{BASE}/chat-archive.html",
    f"{BASE}/whitepapers.html",
    f"{BASE}/multi-ai-canon.html",
    f"{BASE}/qd-theory.html",
]
sitemap = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
]
for u in urls:
    sitemap.append("  <url>")
    sitemap.append(f"    <loc>{u}</loc>")
    sitemap.append("    <changefreq>weekly</changefreq>")
    sitemap.append("    <priority>0.8</priority>")
    sitemap.append("  </url>")
sitemap.append("</urlset>")
(ROOT / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
print("wrote robots.txt sitemap.xml")
