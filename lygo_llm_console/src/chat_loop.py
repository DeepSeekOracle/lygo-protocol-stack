from __future__ import annotations

import difflib
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

# --- arithmetic is answered here, never searched for -----------------------------
# Measured: "What is 17 * 23?" matched SEARCH_HINT on the words "what is", so host_prefetch ran
# web_search + web_fetch before the model and the 7B answered with a search-page number (53, 401).
# These helpers let the host do the sum itself, and run_tools_round redirect a web call that is
# really arithmetic.
MATH_HEAD = re.compile(
    r"^\s*(?:what(?:'s|\s+is)|whats|how\s+much\s+is|how\s+many\s+is|"
    r"calc(?:ulate)?|compute|solve|eval(?:uate)?)\s*",
    re.I,
)
MATH_INSTR = re.compile(
    r"[\s,;.?!]*(?:(?:and\s+)?(?:please\s+)?(?:use|using|with|via|by)\s+(?:the\s+)?"
    r"(?:calc|calculator|math)(?:\s+tool)?|please|thanks|thank\s+you)[\s.?!]*$",
    re.I,
)
MATH_TAIL = re.compile(r"[\s=?!.:]+$")
MATH_CHARS = re.compile(r"^[\s\d.,()+\-*/%^×÷]+$")
MATH_OP = re.compile(r"[+\-*/%^×÷]")
MATH_WORDS = (
    (re.compile(r"\bmultiplied\s+by\b", re.I), "*"),
    (re.compile(r"\bdivided\s+by\b", re.I), "/"),
    (re.compile(r"\btimes\b", re.I), "*"),
    (re.compile(r"\bplus\b", re.I), "+"),
    (re.compile(r"\bminus\b", re.I), "-"),
)


def math_expr(text: str) -> str:
    """The arithmetic inside a plain question, in a form `calc` can evaluate.

    "What is 17 * 23?" -> "17 * 23"; "17 times 23" -> "17 * 23"; "1,000 + 500" -> "1000 + 500".
    Anything that is not purely arithmetic comes back as itself and fails math_only().
    """
    s = MATH_HEAD.sub("", str(text or ""))
    while True:
        smaller = MATH_INSTR.sub("", s)
        if smaller == s:
            break
        s = smaller
    s = MATH_TAIL.sub("", s)
    for rx, rep in MATH_WORDS:
        s = rx.sub(rep, s)
    s = s.replace("×", "*").replace("÷", "/").replace("^", "**")
    s = re.sub(r"(?<=\d),(?=\d)", "", s)
    return s.strip()


def math_only(text: str) -> bool:
    """True when the whole message is a bare arithmetic question and nothing else."""
    s = math_expr(text)
    if not MATH_CHARS.match(s):
        return False
    return bool(re.search(r"\d", s)) and bool(MATH_OP.search(s))


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


def normalise_messages(obj: Any) -> list[dict[str, Any]]:
    """Accept every payload shape a caller might send and return a real messages[] list.

    `messages[]` is the contract; `prompt` is the documented shorthand. Anything else with no
    user text is NOT silently answered — the caller gets 400 no_input (see server._api_chat).
    """
    if not isinstance(obj, dict):
        return []
    msgs = obj.get("messages")
    out = [m for m in msgs if isinstance(m, dict)] if isinstance(msgs, list) else []
    if out:
        return out
    for key in ("prompt", "message", "input", "text"):
        val = obj.get(key)
        if isinstance(val, str) and val.strip():
            return [{"role": "user", "content": val}]
    return []


def user_text_of(messages: list[dict[str, Any]]) -> str:
    """Text of the newest user turn that actually carries text (else "")."""
    for m in reversed(list(messages or [])):
        if not isinstance(m, dict) or m.get("role") != "user":
            continue
        c = m.get("content")
        text = c if isinstance(c, str) else extract_user_text([m])
        if str(text or "").strip():
            return str(text)
    return ""


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
    if math_only(text):
        # Bare arithmetic: answer it on the host instead of searching the web for the numbers.
        expr = math_expr(text)
        result = dispatch("calc", {"expr": expr})
        if (result or {}).get("ok"):
            traces.append({"name": "calc", "arguments": {"expr": expr}, "result": result, "host": True})
        return traces

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
    if name == "calc":
        return {
            "name": name,
            "expr": (t.get("arguments") or {}).get("expr"),
            "value": res.get("value"),
            "error": res.get("error"),
        }

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
    """What the model sees when the host already ran the limbs for this turn.

    Plain instruction, not a template order: an over-prescriptive prompt here is what made every
    answer look like the same canned readout.
    """
    if not traces:
        return ""
    compact = [_compact_trace(t) for t in traces]
    return (
        "HOST READOUT (RESOURCE, not CANON) — the host already ran these limbs for this turn, "
        "so do not run them again.\n"
        "Use these values for the live facts and answer the operator's newest message in your own "
        "words, as short as the question deserves. Lead with the answer, then the receipts (the real "
        "paths/URLs/values above). Never repeat your previous answer, never narrate the tool calls, "
        "never add next steps.\n"
        + json.dumps(compact, default=str)[:3000]
    )


def _human_skills(v: Any) -> str:
    """`{'n': 18, 'enabled': 6}` is a dict repr; humans (and the transcript) want a phrase."""
    if isinstance(v, dict):
        n, e = v.get("n"), v.get("enabled")
        if n is None:
            return "" if e is None else f"{e} enabled"
        return f"{n} on disk, {e} enabled" if e is not None else f"{n} on disk"
    return str(v or "")


def fallback_from_traces(traces: list[dict[str, Any]]) -> str:
    """Last-resort host readout — ONLY for a turn where the model returned nothing usable.

    This text is saved into the session, and a small model will happily parrot whatever it finds
    there, so it must read like prose, never like a Python dict.
    """
    sc = None
    sm = None
    for t in traces:
        if t.get("name") == "self_check" and isinstance(t.get("result"), dict):
            sc = t["result"]
        if t.get("name") == "steward_map" and isinstance(t.get("result"), dict):
            sm = t["result"]
    if sc:
        sample = ", ".join(str(x) for x in (sc.get("chatagent_sample") or [])[:8]) or "(none)"
        skills = _human_skills(sc.get("skills"))
        lines = [
            f"Self-check: {sc.get('verdict')} — limbs answered, so this is measured, not guessed.",
            f"- GitHub {sc.get('github')}",
            f"- Hugging Face {sc.get('huggingface')}",
            f"- Lattice {sc.get('lattice')}",
            f"- D:\\chatagent present: {sc.get('chatagent_exists')} · sample {sample}",
            f"- Live mounts: {sc.get('n_live_mounts')}" + (f" · skills {skills}" if skills else ""),
            "No placeholder URLs were used.",
        ]
        return "\n".join(lines)
    if not sm:
        return ""
    sites = sm.get("sites") or sm.get("lattice") or []
    return (
        "LYGO admin map is live (RESOURCE, not CANON).\n"
        f"GitHub: {sm.get('github_org') or 'https://github.com/DeepSeekOracle'}\n"
        f"Hugging Face: {sm.get('hf_org') or 'https://huggingface.co/DeepSeekOracle'}\n"
        f"Lattice: {', '.join(str(s) for s in sites[:6]) or 'https://chatagent.ca/'}\n"
        "I will not fetch github.com/user/repo or lattice.example.com.\n"
        "Name a real path (D:\\chatagent) or a URL from this map and I will list_dir / web_fetch it."
    )


PLACEHOLDER_MAP = {
    "github.com/user/repo": "https://github.com/DeepSeekOracle",
    "lattice.example.com": "https://chatagent.ca/",
    "huggingface.co/models/transformers": "https://huggingface.co/DeepSeekOracle",
}

PLACEHOLDER_OUT = re.compile("|".join(re.escape(k) for k in PLACEHOLDER_MAP), re.I)


def _scrub_placeholders(raw: str) -> tuple[str, bool]:
    """Rewrite an invented placeholder in place instead of throwing the whole answer away."""
    hit = False

    def rep(m: re.Match[str]) -> str:
        nonlocal hit
        hit = True
        return PLACEHOLDER_MAP.get(m.group(0).lower(), m.group(0))

    return PLACEHOLDER_OUT.sub(rep, raw), hit


BOILER = re.compile(r"end of admin check|next steps:|tools used:", re.I)
BOILER_LEAD = re.compile(r"^\W*(?:end of admin check|next steps|tools used)\W*:?\s*", re.I)


def strip_boiler(text: str) -> str:
    """Drop the template lines the prompt forbids, keep everything the model actually said.

    A line that merely *leads* with the marker ("Next Steps: file the receipt") keeps its substance.
    """
    keep: list[str] = []
    for ln in (text or "").splitlines():
        s = ln.strip()
        if not s:
            keep.append(ln)
            continue
        m = BOILER_LEAD.match(s)
        if not m:
            keep.append(ln)
            continue
        rest = s[m.end() :].strip(" -–—•*")
        if len(rest) >= 12:
            keep.append(rest)
    return "\n".join(keep).strip()


def _is_only_boiler(raw: str) -> bool:
    body = re.sub(r"[\s\-•*_#]+", "", BOILER.sub("", raw or ""))
    return len(body) < 12


def sanitize_assistant(text: str, traces: list[dict[str, Any]]) -> str:
    """Clean the model's answer. It never gets replaced by a canned string any more.

    The old behaviour (any draft containing "End of Admin Check" was thrown away and swapped for a
    hardcoded readout) is what made every turn look identical and killed the agent's voice.
    """
    raw = strip_boiler((text or "").strip())
    if not raw or _is_only_boiler(raw):
        fb = fallback_from_traces(traces)
        return fb or raw
    raw, hit = _scrub_placeholders(raw)
    if hit and traces:
        raw += "\n\n(Placeholder URLs in the draft were replaced with the real org links.)"
    return raw


def same_answer(prev: str, cur: str, ratio: float = 0.86) -> bool:
    """True when the model just repeated its previous answer instead of answering the new turn."""
    a = re.sub(r"\W+", " ", (prev or "").lower()).strip()
    b = re.sub(r"\W+", " ", (cur or "").lower()).strip()
    if not a or not b:
        return False
    if min(len(a), len(b)) < 80:
        # Short replies repeat legitimately ("ok", "done") — not worth a regeneration.
        return False
    if a == b:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= ratio


HISTORY_CHARS = 9000


def trim_history(messages: list[dict[str, Any]], budget: int = HISTORY_CHARS) -> list[dict[str, Any]]:
    """Keep the newest turns inside the engine's window so the system prompt always survives.

    The engine runs 8192 tokens; the RUNTIME/LIMBS/SOUL block is the part that must never be lost.
    """
    out: list[dict[str, Any]] = []
    used = 0
    for m in reversed(messages or []):
        c = m.get("content")
        n = len(c) if isinstance(c, str) else 400
        if out and used + n > budget:
            break
        out.append(m)
        used += n
    out.reverse()
    return out


def run_tools_round(assistant_text: str, message: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    calls = extract_tool_calls(message or {}, assistant_text or "")
    traces = []
    for spec in calls[:4]:
        name, args = spec["name"], spec.get("arguments") or {}
        # A small model will still aim arithmetic at the web tools. The query says what it is, so
        # route it to calc rather than let a search page stand in for a sum.
        q = args.get("q") or args.get("url") or ""
        if name in ("web_search", "web_fetch") and math_only(q):
            name, args = "calc", {"expr": math_expr(q)}
        result = dispatch(name, args)
        traces.append({"name": name, "arguments": args, "result": result})
    return traces
