#!/usr/bin/env python3
"""
DistroKid Vault scraper via Chrome CDP (agent-browser / remote-debugging).

Uses YOUR logged-in session if you sign into the controlled Chrome window.
Does not steal passwords — only reads pages after you authenticate.

Usage:
  1) Run:  python tools/distrokid_vault_browser_scrape.py --launch
     A Chrome window opens to DistroKid vault. Log in if prompted.
  2) When vault list is visible, run (same or another terminal):
       python tools/distrokid_vault_browser_scrape.py --scrape
     Or use --launch --scrape and wait for login (waits up to --login-wait seconds).

Outputs → data/music_catalog/distrokid_vault_*.json/csv
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import urlopen

try:
    import websocket  # websocket-client
except ImportError:
    print("Need: pip install websocket-client")
    raise

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "music_catalog"
CDP_PORT = 9222
PROFILE = OUT / "browser_profile"  # fresh Chrome profile (no cookies)
YANDEX_EXE = Path(r"C:\Program Files\Yandex\YandexBrowser\Application\browser.exe")
YANDEX_USER_DATA = Path(os.environ.get("LOCALAPPDATA", "")) / "Yandex" / "YandexBrowser" / "User Data"

ISRC_RE = re.compile(r"(?i)\bISRC[:\s]*([A-Z0-9\-]{12,15})\b|([A-Z]{2}-?[A-Z0-9]{3}-?\d{2}-?\d{5})\b")
UPC_RE = re.compile(r"(?i)\bUPC[:\s]*(\d{12,13})\b")


def find_chrome() -> str:
    cands = [
        Path.home() / ".agent-browser" / "browsers" / "chrome-151.0.7922.34" / "chrome.exe",
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        YANDEX_EXE,
    ]
    ab = Path.home() / ".agent-browser" / "browsers"
    if ab.exists():
        for p in ab.rglob("chrome.exe"):
            cands.insert(0, p)
    for c in cands:
        if c and Path(c).exists():
            return str(c)
    raise SystemExit("Chrome/Yandex not found")


def find_yandex() -> str:
    cands = [
        YANDEX_EXE,
        Path(os.environ.get("LOCALAPPDATA", "")) / "Yandex" / "YandexBrowser" / "Application" / "browser.exe",
        Path(r"C:\Program Files (x86)\Yandex\YandexBrowser\Application\browser.exe"),
    ]
    for c in cands:
        if c.exists():
            return str(c)
    raise SystemExit("Yandex Browser not found")


def cdp_ok() -> bool:
    try:
        urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=2).read()
        return True
    except Exception:
        return False


def kill_yandex() -> None:
    """Close running Yandex so we can relaunch with remote-debugging (same profile)."""
    # Process name is often just "browser" for Yandex — only kill if path contains Yandex
    try:
        import psutil  # optional
        for p in psutil.process_iter(["pid", "name", "exe"]):
            exe = (p.info.get("exe") or "")
            if "Yandex" in exe.replace("/", "\\"):
                print(f"[launch] stopping Yandex pid={p.info['pid']}")
                p.terminate()
        time.sleep(2)
    except Exception:
        # taskkill by image path filter is hard; kill known yandex image
        subprocess.call(
            ["taskkill", "/IM", "browser.exe", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)


def launch_browser(
    url: str = "https://distrokid.com/vault/?ref=globalmenu",
    *,
    yandex: bool = False,
    reuse_profile: bool = True,
) -> None:
    """
    yandex=True → use Yandex Browser + real User Data (keeps DistroKid login).
    Must restart Yandex if already open (Chromium locks user-data-dir).
    """
    if yandex:
        exe = find_yandex()
        # IMPORTANT: user-data-dir must NOT contain spaces (Yandex breaks CLI parsing on "E Drive")
        # Dedicated profile under %USERPROFILE%\.agent-browser keeps CDP stable.
        user_data = str(Path.home() / ".agent-browser" / "distrokid-yandex-profile")
        Path(user_data).mkdir(parents=True, exist_ok=True)
        print("[launch] Yandex CDP profile:", user_data)
        print("[launch] Restarting Yandex… (log into DistroKid in that window)")
        kill_yandex()
        if reuse_profile and YANDEX_USER_DATA.exists():
            print("[launch] Note: using dedicated CDP profile (not full main profile) for stability.")
            print("[launch] Log in once; session is saved to this profile for next runs.")
    else:
        exe = find_chrome()
        user_data = str(Path.home() / ".agent-browser" / "distrokid-chrome-profile")
        Path(user_data).mkdir(parents=True, exist_ok=True)

    args = [
        exe,
        f"--remote-debugging-port={CDP_PORT}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data}",
        "--no-first-run",
        "--no-default-browser-check",
        "--profile-directory=Default",
        url,
    ]
    print(f"[launch] {exe}")
    print(f"[launch] user-data-dir: {user_data}")
    print("[launch] Leave this window open. Open Vault if not already.")
    subprocess.Popen(args)
    for i in range(40):
        time.sleep(1)
        if cdp_ok():
            print(f"[launch] CDP ready on {CDP_PORT}")
            return
    raise SystemExit("CDP never came up")


def launch_chrome(url: str = "https://distrokid.com/vault/?ref=globalmenu") -> None:
    launch_browser(url, yandex=False)


def list_targets() -> List[Dict[str, Any]]:
    raw = urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list", timeout=5).read()
    return json.loads(raw)


def pick_page(prefer: str = "distrokid") -> Dict[str, Any]:
    tabs = list_targets()
    pages = [t for t in tabs if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
    for t in pages:
        if prefer in (t.get("url") or "").lower():
            return t
    # any real http page
    for t in pages:
        u = (t.get("url") or "")
        if u.startswith("http") and "chrome://" not in u:
            return t
    if not pages:
        raise SystemExit("No page targets in CDP — is browser open with --remote-debugging-port?")
    return pages[0]


class CDP:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=60)
        self._id = 0

    def call(self, method: str, params: Optional[dict] = None, timeout: float = 60) -> Any:
        self._id += 1
        msg = {"id": self._id, "method": method, "params": params or {}}
        self.ws.send(json.dumps(msg))
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == self._id:
                if "error" in data:
                    raise RuntimeError(data["error"])
                return data.get("result")
        raise TimeoutError(method)

    def eval(self, expression: str) -> Any:
        r = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return (r.get("result") or {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def wait_for_login(cdp: CDP, max_wait: int = 300) -> bool:
    print(f"[auth] Waiting up to {max_wait}s for DistroKid vault (log in if needed)…")
    t0 = time.time()
    while time.time() - t0 < max_wait:
        try:
            url = cdp.eval("location.href") or ""
            text = cdp.eval("document.body ? document.body.innerText.slice(0,500) : ''") or ""
            # heuristics
            if "vault" in url.lower() and (
                "logout" in text.lower()
                or "sign out" in text.lower()
                or "/vault/file/" in text.lower()
                or "download" in text.lower()
                or "folder" in text.lower()
            ):
                # not stuck on login
                if "password" not in text.lower() or "vault" in text.lower():
                    if "log in" in text.lower() and "password" in text.lower() and len(text) < 400:
                        time.sleep(3)
                        continue
                    print("[auth] Looks like vault is available.")
                    return True
            if "login" in url.lower() or "signin" in url.lower():
                print("[auth] Login page — please sign in…")
        except Exception as e:
            print(f"[auth] wait: {e}")
        time.sleep(3)
    return False


def collect_file_links(cdp: CDP, scrolls: int = 40) -> List[str]:
    """Scroll vault list and collect /vault/file/ links."""
    hrefs: List[str] = []
    js_collect = r"""
(() => {
  const as = [...document.querySelectorAll('a[href*="/vault/file/"], a[href*="vault/file"]')];
  return as.map(a => a.href);
})()
"""
    for i in range(scrolls):
        batch = cdp.eval(js_collect) or []
        for h in batch:
            if h and h not in hrefs:
                hrefs.append(h)
        # also try data attributes / buttons
        more = cdp.eval(
            r"""
(() => {
  const out = [];
  document.querySelectorAll('[href]').forEach(el => {
    const h = el.getAttribute('href') || '';
    if (h.includes('vault/file') || h.includes('id=')) out.push(el.href || h);
  });
  return out;
})()
"""
        ) or []
        for h in more:
            if isinstance(h, str) and "vault" in h and h not in hrefs:
                hrefs.append(h)
        cdp.eval("window.scrollBy(0, Math.max(600, window.innerHeight * 0.9))")
        time.sleep(0.45)
        if i % 5 == 0:
            print(f"  scroll {i+1}/{scrolls} — links so far: {len(hrefs)}")
    # unique keep order
    seen = set()
    out = []
    for h in hrefs:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def scrape_file_page(cdp: CDP, url: str) -> Dict[str, Any]:
    cdp.call("Page.navigate", {"url": url})
    time.sleep(1.2)
    # wait body
    for _ in range(20):
        ready = cdp.eval("document.readyState")
        if ready == "complete":
            break
        time.sleep(0.3)
    time.sleep(0.5)
    text = cdp.eval("document.body ? document.body.innerText : ''") or ""
    title = cdp.eval(
        r"""
(() => {
  const h = document.querySelector('h1,h2,.title,[class*="title"]');
  return (h && h.innerText) || document.title || '';
})()
"""
    ) or ""
    isrc = ""
    upc = ""
    m = re.search(r"(?i)ISRC[:\s]*([A-Z0-9\-]{12,15})", text)
    if m:
        isrc = m.group(1).upper()
    else:
        m2 = re.search(r"\b([A-Z]{2}-?[A-Z0-9]{3}-?\d{2}-?\d{5})\b", text)
        if m2:
            isrc = m2.group(1).upper()
    um = re.search(r"(?i)UPC[:\s]*(\d{12,13})", text)
    if um:
        upc = um.group(1)
    # release / album lines
    album = ""
    am = re.search(r"(?i)(?:album|release)\s*[:\-]?\s*(.+)", text)
    if am:
        album = am.group(1).split("\n")[0].strip()[:200]
    return {
        "url": url,
        "title": (title or "").strip()[:300],
        "isrc": isrc,
        "upc": upc,
        "album": album,
        "snippet": text[:2500],
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def merge_into_catalog(rows: List[Dict[str, Any]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "distrokid_vault_scrape.json"
    path.write_text(json.dumps({"count": len(rows), "rows": rows}, indent=2), encoding="utf-8")
    csv_path = OUT / "distrokid_vault_scrape.csv"
    fields = ["title", "isrc", "upc", "album", "url", "scraped_at"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"[out] {path}")
    print(f"[out] {csv_path}")

    # merge ISRCs into main ISRC ready file if present
    ready = OUT / "excavationpro_ISRC_READY_for_distributor.csv"
    if ready.exists() and rows:
        existing = {}
        with ready.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("isrc"):
                    existing[row["isrc"].replace("-", "").upper()] = row
        added = 0
        for r in rows:
            if not r.get("isrc"):
                continue
            key = r["isrc"].replace("-", "").upper()
            if key not in existing:
                existing[key] = {
                    "title": r.get("title") or "",
                    "artist": "Excavationpro",
                    "album": r.get("album") or "",
                    "isrc": r["isrc"],
                    "upc": r.get("upc") or "",
                    "spotify_url": "",
                    "local_path": "",
                    "filename": "",
                    "vault_url": r.get("url") or "",
                }
                added += 1
            else:
                if r.get("upc") and not existing[key].get("upc"):
                    existing[key]["upc"] = r["upc"]
                if r.get("url"):
                    existing[key]["vault_url"] = r["url"]
        fields2 = [
            "title",
            "artist",
            "album",
            "isrc",
            "upc",
            "spotify_url",
            "local_path",
            "filename",
            "vault_url",
        ]
        with ready.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields2, extrasaction="ignore")
            w.writeheader()
            for row in existing.values():
                w.writerow(row)
        print(f"[merge] ISRC_READY updated (+{added} new from vault)")


def scrape(max_files: int = 5000, scrolls: int = 50, login_wait: int = 300) -> None:
    if not cdp_ok():
        raise SystemExit("CDP not up. Run with --launch first and leave Chrome open.")
    page = pick_page("distrokid")
    print(f"[page] {page.get('url')}")
    cdp = CDP(page["webSocketDebuggerUrl"])
    try:
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        # go to vault if not there
        url = cdp.eval("location.href") or ""
        if "vault" not in url.lower():
            cdp.call("Page.navigate", {"url": "https://distrokid.com/vault/?ref=globalmenu"})
            time.sleep(2)
        wait_for_login(cdp, login_wait)
        print("[scrape] Collecting vault file links (scroll)…")
        links = collect_file_links(cdp, scrolls=scrolls)
        print(f"[scrape] Found {len(links)} vault file links")
        if not links:
            # dump text for debug
            snippet = cdp.eval("document.body.innerText.slice(0,1500)")
            print("[scrape] No /vault/file/ links found. Page text sample:")
            print(snippet)
            print("[scrape] Tip: open a folder inside vault, then re-run --scrape")
            # still save page text
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / "distrokid_vault_page_dump.txt").write_text(snippet or "", encoding="utf-8")
            return
        links = links[:max_files]
        rows = []
        for i, link in enumerate(links):
            try:
                row = scrape_file_page(cdp, link)
                rows.append(row)
                print(
                    f"  [{i+1}/{len(links)}] {row.get('isrc') or 'no-isrc'} | "
                    f"{(row.get('title') or '')[:50]}"
                )
            except Exception as e:
                print(f"  [{i+1}] FAIL {link}: {e}")
            time.sleep(0.35)
        merge_into_catalog(rows)
        print(f"[done] scraped {len(rows)} file pages")
    finally:
        cdp.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true", help="Start browser with CDP + open vault")
    ap.add_argument("--yandex", action="store_true", help="Use Yandex Browser + real profile (recommended)")
    ap.add_argument(
        "--fresh-profile",
        action="store_true",
        help="Do not reuse Yandex/Chrome login profile",
    )
    ap.add_argument("--scrape", action="store_true", help="Scroll vault + scrape file pages")
    ap.add_argument("--login-wait", type=int, default=300)
    ap.add_argument("--scrolls", type=int, default=50)
    ap.add_argument("--max-files", type=int, default=5000)
    args = ap.parse_args()
    if not args.launch and not args.scrape:
        ap.print_help()
        print("\nYandex (recommended):")
        print("  python tools/distrokid_vault_browser_scrape.py --yandex --launch")
        print("  # confirm vault visible, then:")
        print("  python tools/distrokid_vault_browser_scrape.py --scrape --login-wait 120 --scrolls 80")
        return 1
    if args.launch:
        if cdp_ok() and not args.yandex:
            print("[launch] CDP already up — reuse it, or close browser and re-run with --yandex --launch")
        else:
            launch_browser(
                yandex=bool(args.yandex),
                reuse_profile=not args.fresh_profile,
            )
    if args.scrape:
        scrape(max_files=args.max_files, scrolls=args.scrolls, login_wait=args.login_wait)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
