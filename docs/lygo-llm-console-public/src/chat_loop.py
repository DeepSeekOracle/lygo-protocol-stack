from __future__ import annotations

import json
import re
from typing import Any

from align import load_align
from p0_hook import gate_output_window
from tools import dispatch, parse_fence_tool

SYSTEM = load_align()
URL_RE = re.compile(r"https://[^\s<>\]\)\"'`]+", re.I)
SEARCH_HINT = re.compile(
    r"\b(look\s*up|google|web_search|search for|find out|how many|how much|what is|what are|who is|where is|do \w+ have|does \w+ have)\b",
    re.I,
)
META_TOOLS = re.compile(
    r"(access the internet|search tools|hooked up|are your tools|can you search|tools working)",
    re.I,
)
STEWARD_HINT = re.compile(
    r"\b(github|hugging\s*face|\bhf\b|huggingface|lattice|webpage|webpages|clawhub|"
    r"chatagent|eternalhaven|password|passwords|drives?|whoami|this pc|"
    r"on (the|this) (pc|disk|usb)|find files|manage our|huggingface)\b",
    re.I,
)
PASS_HINT = re.compile(r"\b(password|passwords|credential|\.pass|gitea|winrm)\b", re.I)
FIND_HINT = re.compile(
    r"\b(find files|look for files|on this pc|list (the )?drives|search (the )?(pc|disk|usb))\b",
    re.I,
)
GH_HINT = re.compile(r"\bgithub\b", re.I)
HF_HINT = re.compile(r"\b(hugging\s*face|huggingface|\bhf\b)\b", re.I)
NOTE_HINT = re.compile(
    r"\b(notepad|look at (my |the )?notes|read (my |the )?notes|from (the |my )?notes|"
    r"saved notes|note pad)\b",
    re.I,
)
SELF_CHECK_HINT = re.compile(r"\b(self[-\s]?check|admin check|end of admin check)\b", re.I)
SKILL_HINT = re.compile(
    r"\b(/skill|skill_read|clawhub|skillhub|skill hub|lygoskillhub|invoke|summon|align with|"
    r"enable (the )?(skill|champion)|skills panel|champion)\b",
    re.I,
)


def extract_user_text(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for m in messages:
        if m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for p in c:
                if isinstance(p, dict) and p.get("type") == "text":
                    parts.append(str(p.get("text") or ""))
    return "\n".join(parts)


def has_image(messages: list[dict[str, Any]]) -> bool:
    for m in messages:
        c = m.get("content")
        if isinstance(c, list):
            for p in c:
                if isinstance(p, dict) and p.get("type") in {"image_url", "image"}:
                    return True
    return False


def _args(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            v = json.loads(raw)
            return v if isinstance(v, dict) else {"value": raw}
        except json.JSONDecodeError:
            return {"value": raw}
    return {}


def extract_tool_calls(message: dict[str, Any], content: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tc in message.get("tool_calls") or []:
        fn = tc.get("function") or tc
        name = (fn.get("name") if isinstance(fn, dict) else None) or tc.get("name")
        if not name:
            continue
        args = _args(fn.get("arguments") if isinstance(fn, dict) else tc.get("arguments"))
        out.append({"name": str(name), "arguments": args})
    fence = parse_fence_tool(content or "")
    if fence:
        out.append(fence)
    for m in re.finditer(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", content or "", re.S):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        name = obj.get("name") or obj.get("tool")
        if name:
            out.append({"name": str(name), "arguments": _args(obj.get("arguments") or obj.get("parameters") or obj)})
    # dedupe
    seen = set()
    uniq = []
    for c in out:
        key = (c["name"], json.dumps(c.get("arguments") or {}, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    return uniq


def extract_urls(text: str) -> list[str]:
    out: list[str] = []
    for m in URL_RE.finditer(text or ""):
        u = m.group(0).rstrip(".,;:)!?")
        if u not in out:
            out.append(u)
    return out[:3]


def host_prefetch(user_text: str) -> list[dict[str, Any]]:
    """3B models talk about tools instead of calling them. Host runs URL/search/map first."""
    traces: list[dict[str, Any]] = []
    text = user_text or ""
    try:
        from skills_mod import match_invoked

        invoked = match_invoked(text)
    except Exception:
        invoked = []
    if SKILL_HINT.search(text):
        traces.append({"name": "skill_list", "arguments": {}, "result": dispatch("skill_list", {}), "host": True})
    for slug in invoked:
        traces.append(
            {
                "name": "skill_read",
                "arguments": {"slug": slug},
                "result": dispatch("skill_read", {"slug": slug}),
                "host": True,
            }
        )
    if re.search(r"\b(skillhub|skill hub|lygoskillhub)\b", text, re.I):
        q = re.sub(r"\s+", " ", text).strip()[:120]
        traces.append(
            {
                "name": "skillhub_list",
                "arguments": {"q": q, "channel": "all"},
                "result": dispatch("skillhub_list", {"q": q, "channel": "all"}),
                "host": True,
            }
        )
    if re.search(r"\bclawhub\b", text, re.I) and not invoked:
        q = re.sub(r"\s+", " ", text).strip()[:120]
        traces.append(
            {
                "name": "clawhub_search",
                "arguments": {"q": q},
                "result": dispatch("clawhub_search", {"q": q}),
                "host": True,
            }
        )
    if NOTE_HINT.search(text):
        traces.append(
            {
                "name": "notepad_list",
                "arguments": {},
                "result": dispatch("notepad_list", {}),
                "host": True,
            }
        )
    if SELF_CHECK_HINT.search(text):
        traces.append(
            {
                "name": "self_check",
                "arguments": {},
                "result": dispatch("self_check", {}),
                "host": True,
            }
        )
    if STEWARD_HINT.search(text):
        traces.append(
            {
                "name": "steward_map",
                "arguments": {},
                "result": dispatch("steward_map", {}),
                "host": True,
            }
        )
    if PASS_HINT.search(text):
        traces.append(
            {
                "name": "credential_where",
                "arguments": {"q": ""},
                "result": dispatch("credential_where", {"q": ""}),
                "host": True,
            }
        )
    if FIND_HINT.search(text):
        traces.append(
            {
                "name": "list_dir",
                "arguments": {"path": ""},
                "result": dispatch("list_dir", {"path": ""}),
                "host": True,
            }
        )
    urls = extract_urls(text)
    for url in urls:
        result = dispatch("web_fetch", {"url": url})
        traces.append({"name": "web_fetch", "arguments": {"url": url}, "result": result, "host": True})
    if urls:
        return traces
    if GH_HINT.search(text) and not any(t.get("name") == "steward_map" for t in traces):
        traces.append(
            {
                "name": "github_search",
                "arguments": {"q": "lygo"},
                "result": dispatch("github_search", {"q": "lygo"}),
                "host": True,
            }
        )
    if HF_HINT.search(text) and not any(t.get("name") == "steward_map" for t in traces):
        traces.append(
            {
                "name": "web_fetch",
                "arguments": {"url": "https://huggingface.co/DeepSeekOracle"},
                "result": dispatch("web_fetch", {"url": "https://huggingface.co/DeepSeekOracle"}),
                "host": True,
            }
        )
    if META_TOOLS.search(text) and not SEARCH_HINT.search(text) and not STEWARD_HINT.search(text):
        return traces
    if SEARCH_HINT.search(text) and not GH_HINT.search(text) and not HF_HINT.search(text):
        q = re.sub(r"\s+", " ", text).strip()[:220]
        result = dispatch("web_search", {"q": q})
        hits = (result or {}).get("hits") or []
        if hits:
            traces.append({"name": "web_search", "arguments": {"q": q}, "result": result, "host": True})
            top = hits[0].get("url") or ""
            if top.startswith("https://"):
                traces.append(
                    {
                        "name": "web_fetch",
                        "arguments": {"url": top},
                        "result": dispatch("web_fetch", {"url": top}),
                        "host": True,
                    }
                )
    return traces


def _compact_trace(t: dict[str, Any]) -> dict[str, Any]:
    res = t.get("result") if isinstance(t.get("result"), dict) else {}
    name = t.get("name")
    if name == "self_check":
        return {
            "name": name,
            "verdict": res.get("verdict"),
            "github": res.get("github"),
            "huggingface": res.get("huggingface"),
            "lattice": res.get("lattice"),
            "chatagent_exists": res.get("chatagent_exists"),
            "chatagent_sample": res.get("chatagent_sample"),
            "n_live_mounts": res.get("n_live_mounts"),
            "skills": res.get("skills"),
        }
    if name == "steward_map":
        return {
            "name": name,
            "role": res.get("role"),
            "github": res.get("github_org"),
            "hf": res.get("hf_org"),
            "sites": (res.get("sites") or res.get("lattice") or [])[:8],
            "drives": res.get("drives"),
            "rule": "never github.com/user/repo or lattice.example.com",
        }
    if name == "web_fetch":
        return {
            "name": name,
            "ok": res.get("ok"),
            "url": res.get("url") or (t.get("arguments") or {}).get("url"),
            "error": res.get("error"),
            "text": str(res.get("text") or "")[:600],
        }
    if name == "github_search":
        hits = res.get("hits") or []
        return {"name": name, "query": res.get("query"), "hits": hits[:6]}
    slim = {"name": name, "ok": res.get("ok", True)}
    for k in ("role", "n", "path", "error", "github"):
        if res.get(k) is not None:
            slim[k] = res.get(k)
    return slim


def prefetch_message(traces: list[dict[str, Any]]) -> str:
    if not traces:
        return ""
    compact = [_compact_trace(t) for t in traces]
    return (
        "HOST MAP (RESOURCE). Answer NOW in 6–10 short bullets from this JSON. "
        "No Next Steps. No End of Admin Check. Cite only these URLs/paths.\n"
        + json.dumps(compact, default=str)[:5000]
    )


def fallback_from_traces(traces: list[dict[str, Any]]) -> str:
    sc = None
    sm = None
    for t in traces:
        if t.get("name") == "self_check" and isinstance(t.get("result"), dict):
            sc = t["result"]
        if t.get("name") == "steward_map" and isinstance(t.get("result"), dict):
            sm = t["result"]
    if sc:
        sample = ", ".join(str(x) for x in (sc.get("chatagent_sample") or [])[:8])
        return (
            f"Self-check {sc.get('verdict')}.\n"
            f"GitHub {sc.get('github')}\n"
            f"Hugging Face {sc.get('huggingface')}\n"
            f"Lattice {sc.get('lattice')}\n"
            f"D:\\chatagent exists={sc.get('chatagent_exists')} sample={sample}\n"
            f"Live mounts={sc.get('n_live_mounts')} skills={sc.get('skills')}\n"
            "No placeholder URLs."
        )
    if not sm:
        return ""
    sites = sm.get("sites") or sm.get("lattice") or []
    return (
        "LYGO admin map is live (RESOURCE, not CANON).\n"
        f"GitHub: {sm.get('github_org') or 'https://github.com/DeepSeekOracle'}\n"
        f"Hugging Face: {sm.get('hf_org') or 'https://huggingface.co/DeepSeekOracle'}\n"
        f"Lattice: {', '.join(str(s) for s in sites[:6]) or 'https://chatagent.ca/'}\n"
        "I will not fetch github.com/user/repo or lattice.example.com.\n"
        "Say a real path (D:\\chatagent) or a URL from this map and I will list_dir / web_fetch it."
    )


PLACEHOLDER_OUT = re.compile(
    r"github\.com/user/repo|lattice\.example\.com|huggingface\.co/models/transformers",
    re.I,
)


BOILER = re.compile(r"end of admin check|next steps:|tools used:", re.I)


def sanitize_assistant(text: str, traces: list[dict[str, Any]]) -> str:
    raw = (text or "").strip()
    fb = fallback_from_traces(traces)
    if not raw:
        return fb
    if PLACEHOLDER_OUT.search(raw):
        if fb:
            return fb + "\n\n(Ignored placeholder URLs in the draft.)"
    if traces and BOILER.search(raw) and fb:
        return fb
    return raw


def run_tools_round(assistant_text: str, message: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    calls = extract_tool_calls(message or {}, assistant_text or "")
    traces = []
    for spec in calls[:4]:
        result = dispatch(spec["name"], spec.get("arguments") or {})
        traces.append({"name": spec["name"], "arguments": spec.get("arguments"), "result": result})
    return traces
