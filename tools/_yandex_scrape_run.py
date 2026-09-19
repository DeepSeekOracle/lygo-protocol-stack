"""One-shot: wait for CDP Yandex, login wait, scrape vault."""
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from distrokid_vault_browser_scrape import (  # noqa: E402
    CDP,
    collect_file_links,
    merge_into_catalog,
    pick_page,
    scrape_file_page,
    wait_for_login,
)

for i in range(40):
    try:
        urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2).read()
        print("CDP ready", i, flush=True)
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("no cdp")

page = pick_page("distrokid")
print("page", page.get("url"), flush=True)
cdp = CDP(page["webSocketDebuggerUrl"])
cdp.call("Page.enable")
cdp.call("Runtime.enable")
print("url", cdp.eval("location.href"), flush=True)
print("title", cdp.eval("document.title"), flush=True)
text = cdp.eval("document.body ? document.body.innerText.slice(0, 800) : ''")
print("body sample:\n", text, flush=True)
print("--- LOG IN to DistroKid in Yandex if needed (wait up to 3 min) ---", flush=True)
ok = wait_for_login(cdp, 180)
print("login_ok", ok, flush=True)
print("url after", cdp.eval("location.href"), flush=True)
links = collect_file_links(cdp, scrolls=40)
print("links", len(links), flush=True)
for h in links[:8]:
    print(" ", h, flush=True)
rows = []
limit = min(len(links), 100)  # first 100; re-run for more
for i, link in enumerate(links[:limit]):
    try:
        row = scrape_file_page(cdp, link)
        rows.append(row)
        print(f"{i+1}/{limit}", row.get("isrc"), (row.get("title") or "")[:50], flush=True)
    except Exception as e:
        print("fail", e, flush=True)
    time.sleep(0.25)
if rows:
    merge_into_catalog(rows)
print("DONE rows", len(rows), flush=True)
cdp.close()
