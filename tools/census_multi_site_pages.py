#!/usr/bin/env python3
"""Map every HTML page on Excavationpro + DeepSeekOracle GitHub Pages."""
from __future__ import annotations
import argparse, json, concurrent.futures, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
USB = Path("E:/LYGO_LATTICE_MEMORY")
BASES = {
  "excavationpro": ("https://deepseekoracle.github.io/Excavationpro/", "DeepSeekOracle/Excavationpro"),
  "deepseekoracle": ("https://deepseekoracle.github.io/DeepSeekOracle/", "DeepSeekOracle/DeepSeekOracle"),
}

def utc(): return datetime.now(timezone.utc).isoformat()

def fetch_html(repo: str):
  url = f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1"
  req = urllib.request.Request(url, headers={"User-Agent":"LYGO-SiteMap/1","Accept":"application/vnd.github+json"})
  with urllib.request.urlopen(req, timeout=90) as r:
    data = json.loads(r.read().decode())
  return [t["path"] for t in (data.get("tree") or []) if t.get("type")=="blob" and t["path"].endswith(".html")], data.get("truncated")

def enc_url(base: str, path: str) -> str:
  return base + "/".join(quote(seg, safe="") for seg in path.split("/"))

def probe(url: str):
  try:
    req = urllib.request.Request(url, headers={"User-Agent":"LYGO-SiteMap/1"})
    with urllib.request.urlopen(req, timeout=20) as r:
      return True, r.status
  except Exception as e:
    return False, str(e)

def classify(path: str) -> str:
  p = path.lower()
  if path.startswith("LYGO-Network/"): return "lygo_network"
  if path.startswith("aichat/"): return "aichat"
  if "hytale" in p: return "hytale"
  if path.startswith("LYRA") or path.startswith("LYRA/"): return "lyra"
  if path.startswith("domain-roots/"): return "domain_roots"
  if path.startswith("grok"): return "grok_ritual"
  if any(x in p for x in ("listen","music","bpm","catalog","sovereign-music")): return "music"
  if "haven" in p or "starchart" in p: return "haven_star"
  if any(x in p for x in ("guardian","ethical","firmware","chip")): return "guardian_firmware"
  if "seal" in p or "repo" in p: return "seals_repo"
  if path in ("index.html","main.html","Expromain.html"): return "gateway"
  if any(x in p for x in ("skillhub","continuum","ascii")): return "skills_tools"
  return "other"

def main():
  ap = argparse.ArgumentParser(); ap.add_argument("--usb-copy", action="store_true"); args = ap.parse_args()
  sites = {}
  all_urls = []
  for key, (base, repo) in BASES.items():
    html, trunc = fetch_html(repo)
    pages = [{"path": h, "url": enc_url(base, h), "group": classify(h) if key=="excavationpro" else "hub"} for h in sorted(html)]
    groups = {}
    for p in pages:
      groups[p["group"]] = groups.get(p["group"], 0) + 1
    sites[key] = {"base": base, "repo": f"https://github.com/{repo}", "git_tree_truncated": trunc, "html_count": len(html), "groups": groups, "pages": pages}
    all_urls.extend(p["url"] for p in pages)
  ok = 0; bad = []
  with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    for url, (good, status) in zip(all_urls, ex.map(probe, all_urls)):
      if good: ok += 1
      else: bad.append({"url": url, "error": str(status)})
  doc = {"signature":"Delta9Phi963-MULTI-SITE-PAGES-CENSUS-v1","generated_utc":utc(),"mapped_fully":True,"method":"GitHub git trees recursive + live probe","sites":sites,"probe":{"checked":len(all_urls),"ok":ok,"failed":len(bad),"failures":bad}}
  (DOCS/"MULTI_SITE_PAGES_CENSUS.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
  lines = ["# Multi-Site Pages Census — Excavationpro + DeepSeekOracle", "", f"**Generated:** {doc['generated_utc']}  ", f"**Live probe:** {ok}/{len(all_urls)} OK", ""]
  for key, s in sites.items():
    lines += [f"## {key}", f"- Base: {s['base']}", f"- HTML: **{s['html_count']}**", ""]
    for p in s["pages"]:
      lines.append(f"- [{p['path']}]({p['url']})")
    lines.append("")
  (DOCS/"MULTI_SITE_PAGES_CENSUS.md").write_text("\n".join(lines), encoding="utf-8")
  if args.usb_copy:
    USB.mkdir(parents=True, exist_ok=True)
    for n in ("MULTI_SITE_PAGES_CENSUS.md","MULTI_SITE_PAGES_CENSUS.json"):
      (USB/n).write_text((DOCS/n).read_text(encoding="utf-8"), encoding="utf-8")
  print(json.dumps({"ok": True, "ok_probe": ok, "total": len(all_urls), "failed": len(bad)}, indent=2))

if __name__ == "__main__":
  raise SystemExit(main())
