"""HTTPS search + fetch for LYGO LLM Console. Witness/RESOURCE only — not CANON."""
from __future__ import annotations

import html
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

UA = "LYGO-LLM-Console/1.0 (+https://chatagent.ca/lygo-llm-console.html; steward Justin Helmer)"
TIMEOUT = 12
MAX_BYTES = 200_000
CTX = ssl.create_default_context()

_BLOCK_HOST = (
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
)


def _blocked(url: str) -> str | None:
    try:
        u = urlparse(url)
    except Exception:
        return "bad_url"
    if u.scheme != "https":
        return "https_only"
    host = (u.hostname or "").lower()
    if not host or host in _BLOCK_HOST:
        return "host"
    if host.endswith(".local") or host.endswith(".internal"):
        return "host"
    if re.match(r"^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)", host):
        return "private"
    return None


def _get(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, bytes, str]:
    h = {"User-Agent": UA, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="GET" if data is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as resp:
            raw = resp.read(MAX_BYTES + 1)
            ctype = resp.headers.get("Content-Type") or ""
            return resp.status, raw[:MAX_BYTES], ctype
    except urllib.error.HTTPError as e:
        return e.code, (e.read() or b"")[:MAX_BYTES], ""
    except Exception as e:
        return 0, str(e).encode("utf-8", errors="replace"), ""


class _DDG(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._href = ""
        self._cap = False
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {k: v or "" for k, v in attrs}
        cls = d.get("class", "")
        if tag == "a" and ("result__a" in cls or "result-link" in cls or d.get("rel") == "nofollow"):
            href = d.get("href") or ""
            if "uddg=" in href:
                q = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                href = q.get("uddg", [href])[0]
            if href.startswith("http"):
                self._href = href
                self._cap = True
                self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._cap:
            title = html.unescape("".join(self._buf)).strip()
            if self._href and title and not self._href.startswith("https://duckduckgo.com"):
                self.results.append({"title": title[:200], "url": self._href})
            self._cap = False
            self._href = ""

    def handle_data(self, data: str) -> None:
        if self._cap:
            self._buf.append(data)


def wikipedia_search(q: str, n: int = 5) -> list[dict[str, str]]:
    qs = urllib.parse.urlencode({"action": "opensearch", "search": q, "limit": str(n), "namespace": "0", "format": "json"})
    code, raw, _ = _get("https://en.wikipedia.org/w/api.php?" + qs)
    out: list[dict[str, str]] = []
    if code != 200:
        return out
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return out
    titles = data[1] if len(data) > 1 else []
    descs = data[2] if len(data) > 2 else []
    urls = data[3] if len(data) > 3 else []
    for i, title in enumerate(titles):
        out.append(
            {
                "title": str(title),
                "url": str(urls[i]) if i < len(urls) else "",
                "snippet": str(descs[i]) if i < len(descs) else "",
                "source": "wikipedia",
            }
        )
    return out


def duckduckgo_search(q: str) -> list[dict[str, str]]:
    qs = urllib.parse.urlencode({"q": q, "kl": "us-en"})
    code, raw, _ = _get("https://html.duckduckgo.com/html/?" + qs)
    if code != 200 or not raw:
        return []
    p = _DDG()
    try:
        p.feed(raw.decode("utf-8", errors="replace"))
    except Exception:
        return []
    seen = set()
    out = []
    for r in p.results:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        r["source"] = "duckduckgo"
        out.append(r)
        if len(out) >= 8:
            break
    return out


def web_search(q: str) -> dict[str, Any]:
    q = (q or "").strip()[:300]
    if not q:
        return {"ok": False, "error": "empty_query"}
    wiki = wikipedia_search(q)
    ddg = duckduckgo_search(q)
    hits = wiki + [h for h in ddg if h.get("url") not in {x.get("url") for x in wiki}]
    return {
        "ok": True,
        "q": q,
        "class": "RESOURCE",
        "note": "Search hits are REFERENCE, not CANON. Cite URLs. Do not invent.",
        "hits": hits[:10],
    }


def _strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def web_fetch(url: str) -> dict[str, Any]:
    url = (url or "").strip()
    why = _blocked(url)
    if why:
        return {"ok": False, "error": why, "url": url}
    code, raw, ctype = _get(url)
    if code != 200:
        return {"ok": False, "error": f"http_{code}", "url": url, "detail": raw[:400].decode("utf-8", errors="replace")}
    text = raw.decode("utf-8", errors="replace")
    if "html" in (ctype or "").lower() or text.lstrip()[:15].lower().startswith("<!doctype") or text.lstrip()[:6].lower().startswith("<html"):
        text = _strip_html(text)
    if len(text) > 24_000:
        text = text[:24_000] + "\n…[truncated]"
    from p0_hook import gate_output_window

    g = gate_output_window(text[:8000])
    if g.get("verdict") == "QUARANTINE":
        return {"ok": False, "error": "p0_quarantine", "url": url, "reason": g.get("reason")}
    return {"ok": True, "url": url, "class": "RESOURCE", "text": text}
