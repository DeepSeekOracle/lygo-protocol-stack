from __future__ import annotations

import difflib
import json
import re
from typing import Any

from align import load_align
from p0_hook import gate_output_window
from tools import ALIASES as TOOL_ALIASES, TOOLS_SCHEMA, dispatch, parse_fence_tool

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
    # Some small models drop the wrapper entirely and send the call object as their whole reply
    # ({"name": "arxiv_search", "arguments": {...}}), so nothing above matches and the call is lost.
    # Accept it only when the *whole* trimmed reply is that object, so prose that merely quotes JSON
    # is left alone.
    stripped = (content or "").strip().strip("`").strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            obj = None
        if isinstance(obj, dict):
            fn = obj.get("function")
            if isinstance(fn, dict):
                name = fn.get("name") or obj.get("name")
                args_raw = fn.get("arguments")
            else:
                name = obj.get("name") or obj.get("tool")
                args_raw = obj.get("arguments") or obj.get("parameters")
            if name:
                out.append({"name": str(name), "arguments": _args(args_raw)})
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


def _flat(v: Any, depth: int = 0) -> str:
    """One-line rendering of a tool result value (never a dict repr — a small model parrots those)."""
    if isinstance(v, (str, int, float, bool)) or v is None:
        return str(v)
    if isinstance(v, dict):
        return ", ".join(f"{k}={_flat(x, depth + 1)}" for k, x in list(v.items())[:8])
    if isinstance(v, (list, tuple)):
        return "; ".join(_flat(x, depth + 1) for x in list(v)[:6])
    return str(v)


def tool_prose(traces: list[dict[str, Any]], limit: int = 700) -> str:
    """Readable summary of the newest tool result — the answer of last resort when the model echoed
    its own tool call instead of narrating what came back."""
    if not traces:
        return ""
    t = traces[-1]
    name = str(t.get("name") or "tool")
    res = t.get("result")
    args = t.get("arguments") if isinstance(t.get("arguments"), dict) else {}
    if not isinstance(res, dict):
        return ""
    if res.get("ok") is False:
        why = res.get("error") or "unknown error"
        hint = res.get("hint")
        return f"{name} could not answer ({why})" + (f" — {hint}" if hint else "") + "."
    body = {k: v for k, v in res.items() if k not in {"class", "ok", "url"} and v not in (None, "", [], {})}
    text = f"{name}({_flat(args)}) -> {_flat(body)}"
    return text[:limit].rstrip() + ("…" if len(text) > limit else "")


def is_tool_call_echo(text: str, message: dict[str, Any] | None = None) -> bool:
    """True when the whole reply is a tool call (or a dump of one) with no prose around it."""
    raw = (text or "").strip()
    if not raw or not extract_tool_calls(message or {}, raw):
        return False
    body = re.sub(r"(?s)```.*?```", " ", raw)
    body = re.sub(r"(?s)<tool_call>.*?</tool_call>", " ", body)
    body = re.sub(r"(?s)\{.*\}", " ", body)
    return len(re.sub(r"\W+", "", body)) < 24


# --- the limb the operator asked for BY NAME ------------------------------------------------
# Measured 2026-09-18: a prompt like "Use the skill_list tool" matched SEARCH_HINT on "how many",
# so host_prefetch ran web_search+web_fetch and the model never got a turn in which it could call
# the named limb; "Use the wayback tool on <url>" was answered with a plain page fetch. When the
# operator names a limb, the host defers and the model gets the clean turn.
WEBISH = {
    "web_search", "web_fetch", "jina_fetch", "download_url", "wayback", "http_json",
    "page_thumbnail", "github_search", "hn_search", "arxiv_search", "web",
}
NAMED_TOOL_RE = re.compile(
    r"\b(?:use|using|via|with|call|run|invoke)\s+(?:the\s+)?([a-z_][a-z0-9_]{2,})\s+(?:tool|limb)\b",
    re.I,
)


def tool_names() -> set[str]:
    """Every limb name plus its aliases (read -> read_file)."""
    names = set(TOOL_ALIASES)
    for t in TOOLS_SCHEMA:
        fn = t.get("function") if isinstance(t, dict) else None
        if isinstance(fn, dict) and fn.get("name"):
            names.add(str(fn["name"]))
    return names


def named_tool(text: str) -> str:
    """The limb the operator asked for by name ("use the weather tool"), else ""."""
    names = tool_names()
    for m in NAMED_TOOL_RE.finditer(text or ""):
        cand = m.group(1).lower()
        if cand in names:
            return TOOL_ALIASES.get(cand, cand)
    for m in re.finditer(r"`([a-z_][a-z0-9_]{2,})`", text or ""):
        cand = m.group(1).lower()
        if cand in names:
            return TOOL_ALIASES.get(cand, cand)
    return ""


# Limbs the HOST may run itself when the operator named one and the model would not call it.
# Read-only or trivially reversible only — a shell command, a python snippet, a file write or an
# edit is NEVER invented on the operator's behalf; those stay honest "I did not call it" answers.
AUTO_ZERO = {
    "list_dir", "whoami", "soul_read", "todo_list", "stack_health", "notepad_list",
    "sessions_list", "self_check", "kernel_status", "workspace_map", "memory_read", "identity_read",
}
AUTO_ONE = {
    "skill_read": "slug", "skill_enable": "slug", "skill_disable": "slug",
    "skillhub_list": "q", "clawhub_search": "q", "search_corpus": "q", "memory_recall": "q",
    "recall_history": "q", "session_list": "q", "session_open": "sid",
    "session_search": "q", "session_label": "title", "session_resume": "sid",
    "http_json": "url", "wayback": "url", "download_url": "url", "jina_fetch": "url",
    "web_fetch": "url", "page_thumbnail": "url", "geocode": "place", "weather": "place",
}


# Limb the host may run for the operator, but ONLY with arguments the operator's own message
# carries — never invented: a write needs the text AND the filename, a shell call needs a single
# read-only command the operator typed, a python call needs a print(...) they typed.
AUTO_OPERATOR = {"write_file", "shell", "python_exec"}
SHELL_READONLY = {
    "echo", "dir", "ls", "pwd", "whoami", "hostname", "ver", "date", "time", "type",
    "where", "find", "tasklist", "netstat", "ipconfig", "systeminfo",
}
SHELL_META = re.compile(r"[|&;<>$`(){}!\n\r]")


def _operator_args(name: str, text: str) -> dict[str, Any] | None:
    """Args taken only from the operator's words. None = not enough there; answer honestly."""
    t = str(text or "")
    if name == "write_file":
        body = re.search(r"['\"]([^'\"]{1,400})['\"]", t)
        dest = re.search(r"([A-Za-z0-9_.\-/\\]+\.(?:txt|md|json|html|csv|log|py|tsv))", t)
        if body and dest:
            return {"path": dest.group(1), "content": body.group(1)}
        return None
    if name == "shell":
        m = re.search(r"\b(?:run|execute)\s*:?\s+(.+)$", t.strip(), re.I)
        if not m:
            return None
        cmd = m.group(1).strip().strip('"').strip("'").strip()
        if not cmd or SHELL_META.search(cmd):
            return None
        if cmd.split()[0].lower().rstrip(".") not in SHELL_READONLY:
            return None
        return {"cmd": cmd}
    if name == "python_exec":
        m = re.search(r"\bprint\s*\(([^()]{1,200})\)", t)
        if m:
            return {"code": "print(" + m.group(1).strip() + ")"}
        m = re.search(r"\bprint\s+([0-9A-Za-z_+\-*/%. ]{1,120})", t)
        if m:
            expr = m.group(1).strip().rstrip(".")
            if expr:
                return {"code": "print(" + expr + ")"}
        return None
    return None


def auto_limb(name: str, text: str) -> dict[str, Any] | None:
    """Args to run `name` on the host when the model would not call it. None = do not run it."""
    if name in AUTO_OPERATOR:
        return _operator_args(name, text)
    if name in AUTO_ZERO:
        args: dict[str, Any] = {}
        if name == "list_dir":
            m = re.search(r"([A-Za-z]:[\\/][^\s\"']{2,}|/[^\s\"']{3,})", text or "")
            hit = re.search(r"([A-Za-z]:[\\/][^\n]{2,})", text or "")
            if hit:
                tail = re.split(r"\s+(?:and|then|please|tool)\b", hit.group(1).strip().strip('"').strip("'"), 1)[0]
                args = {"path": tail.rstrip(" .,;:!?")}
            else:
                hit = re.search(r"(/[^\s]{3,})", text or "")
                args = {"path": hit.group(1).rstrip(" .,;:!?")} if hit else {}
        return args
    key = AUTO_ONE.get(name)
    if not key:
        return None
    if key == "url":
        urls = extract_urls(text or "")
        return {"url": urls[0]} if urls else None
    if key == "place":
        m = re.search(r"\b(?:in|for|at)\s+([A-Z][A-Za-z .'\-]{2,40})", text or "")
        return {"place": m.group(1).strip(" .,")} if m else None
    if key == "q":
        q = re.sub(r"^\s*use\s+(?:the\s+)?[a-z_]+\s+(?:tool|limb)\b", " ", text or "", flags=re.I)
        q = re.sub(r"\b(search for|search|browse for|browse|look for|for|about|to)\b", " ", q, flags=re.I)
        q = re.sub(r"[^A-Za-z0-9_.\- ]+", " ", q).strip()
        return {"q": q[:120]} if q else None
    m = re.search(r"\bslug\s+([A-Za-z0-9_.\-]{2,})", text or "", re.I)
    if not m:
        m = re.search(r"\b([a-z0-9]+-[a-z0-9][a-z0-9\-]{2,})\b", text or "")
    return {key: m.group(1)} if m else None


def tool_card(name: str) -> str:
    """One-limb instruction with the exact schema — the retry when a named limb was not called."""
    desc, props = "", {}
    for t in TOOLS_SCHEMA:
        fn = t.get("function") if isinstance(t, dict) else None
        if isinstance(fn, dict) and fn.get("name") == name:
            desc = str(fn.get("description") or "")
            props = ((fn.get("parameters") or {}).get("properties") or {})
    args = ", ".join('"%s": <%s>' % (k, (v or {}).get("type", "string")) for k, v in props.items()) or "(no arguments)"
    return (
        "You were asked for the " + name + " limb and you did not call it. Reply with exactly ONE "
        'tool call and nothing else:\n{"name": "' + name + '", "arguments": {' + args + "}}\n"
        "Limb: " + desc + "\n"
        "Do not answer in prose. Do not explain. Do not invent a result. Emit the call."
    )


BS = chr(92)  # a literal backslash, built at runtime so no escape layer can mangle it
QUOTES = chr(34) + chr(39)
BADCHARS = chr(34) + chr(39) + "<>|"

# A file path in the operator's message is DATA, not intent. Measured 2026-09-19: the steward sent
# "check this photo <path>" where the path was drive I:, folder "E Drive", YOUTUBE LYGO VIDEOS,
# Pictures, cc988550....png. STEWARD_HINT matched the word "Drive" inside that path, so host_prefetch
# ran steward_map and injected a drives/policy recital BEFORE the model was called - he asked about a
# picture and got a read_roots dump, then the model repeated it. Same trigger hit his earlier "find a
# image on my pc in ..." turn. Mask paths out of every hint test below; the untouched words survive in
# `raw` and the image branch reads the real path back out of it.
PATH_TOKEN = re.compile(
    "[A-Za-z]:" + "[" + BS + BS + "/]" + "[^" + BADCHARS + "]*"
    + "|" + BS + BS + "[^" + BADCHARS + "]+",
    re.I,
)
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff")
LOOK_HINT = re.compile("(check|look|see|view|describe|inspect|analyse|analyze|read|photo|image|picture|what)", re.I)


def mask_paths(text: str) -> str:
    """The text with file paths blanked, so a filename can never select a host limb."""
    return PATH_TOKEN.sub(" ", text or "")


def paths_in(text: str) -> list[str]:
    """Absolute Windows paths in the text, in order, stripped of quotes and trailing punctuation."""
    out: list[str] = []
    for m in PATH_TOKEN.findall(text or ""):
        p = m.strip().strip(QUOTES).rstrip(" .,;:)")
        if p and p not in out:
            out.append(p)
    return out


ATTACH_MARK = re.compile(r"attached file|its contents follow|read_file limb", re.I)
# A path alone on its line. The composer writes it that way because this kit's own folder has a space in
# it ("I:\E Drive\..."), which every inline path pattern truncates.
PATH_LINE = re.compile(r"^\s*\"?([A-Za-z]:[\\/][^\n]*?)\"?\s*$")


def attached_files(text: str) -> list[str]:
    """The files the composer attached to this message, out of the operator's own words.

    The portal sends "<absolute path> - open it with the read_file limb before you answer" for anything
    it could not inline, and a small model often never issues that call: measured 2026-09-19 the console
    answered "I was asked for the read_file limb and did not issue the call" to a message whose own
    attachment line named the file. The path is right there in the operator's message, so the host reads
    it and the answer stops depending on the model remembering to ask. Pictures are left to the image
    path (they need the projector, not read_file).
    """
    out: list[str] = []
    for line in (text or "").splitlines():
        m = PATH_LINE.match(line)
        if not m:
            continue
        p = m.group(1).strip().strip(QUOTES).rstrip(" .,;:)")
        if p and not p.lower().endswith(IMAGE_EXT) and p not in out:
            out.append(p)
    return out


def image_paths_in(text: str) -> list[str]:
    """The image files among the paths in the text."""
    return [p for p in paths_in(text) if p.lower().endswith(IMAGE_EXT)]


def host_prefetch(user_text: str) -> list[dict[str, Any]]:
    """3B models talk about tools instead of calling them. Host runs URL/search/map first."""
    traces: list[dict[str, Any]] = []
    text = user_text or ""
    named = named_tool(text)
    raw = text                  # the operator's own words, for the limbs that need the real path
    text = mask_paths(text)     # every hint test below now sees intent, not filenames
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
    if ATTACH_MARK.search(raw):
        # The composer named the file in this very message. Read it here rather than asking the model to
        # issue the call, and do not go to the web for an answer that is sitting in the attachment.
        read_any = False
        for path in attached_files(raw):
            result = dispatch("read_file", {"path": path})
            traces.append({"name": "read_file", "arguments": {"path": path}, "result": result, "host": True})
            read_any = True
        if read_any:
            return traces
    urls = extract_urls(text) if (not named or named in WEBISH) else []
    for url in urls:
        result = dispatch("web_fetch", {"url": url})
        traces.append({"name": "web_fetch", "arguments": {"url": url}, "result": result, "host": True})
    if urls:
        return traces
    pics = image_paths_in(raw)
    if pics:
        # "check this photo <path>": the picture IS the request. Inspect the file on the host, and when
        # the operator asked to look at it (or sent nothing but the path) hand the bytes to the local
        # vision model, so the answer is grounded in the picture instead of in a filename that looks
        # like a policy question.
        for pic in pics[:2]:
            info = dispatch("image_info", {"path": pic})
            traces.append({"name": "image_info", "arguments": {"path": pic}, "result": info, "host": True})
            if (info or {}).get("ok") and (LOOK_HINT.search(text) or len(text.strip()) < 12):
                traces.append(
                    {
                        "name": "image_see",
                        "arguments": {"path": pic},
                        "result": dispatch("image_see", {"path": pic}),
                        "host": True,
                    }
                )
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
    if math_only(text) and named in ("", "calc"):
        # Bare arithmetic: answer it on the host instead of searching the web for the numbers.
        expr = math_expr(text)
        result = dispatch("calc", {"expr": expr})
        if (result or {}).get("ok"):
            traces.append({"name": "calc", "arguments": {"expr": expr}, "result": result, "host": True})
        return traces

    if META_TOOLS.search(text) and not SEARCH_HINT.search(text) and not STEWARD_HINT.search(text):
        return traces
    if SEARCH_HINT.search(text) and not named and not GH_HINT.search(text) and not HF_HINT.search(text):
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


# Limbs that exist to bring text back to the model. Their body must survive the slim trace.
READOUT_LIMBS = {
    "read_file", "read_text", "search_corpus", "skill_read", "list_dir", "notepad_read",
    "session_read", "memory_read", "identity_read", "whoami", "http_json", "jina_fetch",
}


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
        res = res if isinstance(res, dict) else {}
        return {
            "name": name,
            "ok": res.get("ok"),
            "url": res.get("url") or (t.get("arguments") or {}).get("url"),
            "error": res.get("error"),
            "hint": res.get("hint"),
            "marker": res.get("marker"),
            # An X post read carries the post body in ~600 chars; give it a little more room.
            "text": str(res.get("text") or "")[: 900 if res.get("kind") == "x_post" else 600],
        }
    if name == "github_search":
        hits = res.get("hits") or []
        return {"name": name, "query": res.get("query"), "hits": hits[:6]}
    if name in READOUT_LIMBS:
        # A limb whose whole job is to bring text back must carry that text into the prompt. The slim
        # branch below keeps only name/ok/path, and a host read of the operator's own attached file then
        # reached the model as {"name": "read_file", "ok": true, "path": ...} with none of its contents -
        # so it answered "LUMINA-77" for a file that says OMEGA-441 (measured 2026-09-19). Same class as
        # the calc value that went missing: a readout without its payload is a readout the model invents.
        slim = {"name": name, "ok": res.get("ok", True)}
        for k in ("role", "n", "path", "error", "hint", "marker", "value", "verdict"):
            if res.get(k) is not None:
                slim[k] = res.get(k)
        body = res.get("text")
        if body in (None, ""):
            body = res.get("content")
        if isinstance(body, str) and body:
            slim["text"] = body[:2000]
        for k in ("entries", "hits", "matches", "skills", "lines"):
            v = res.get(k)
            if v:
                slim[k] = v[:20]
        return slim
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
        "never add next steps. "
        "If a readout has ok=false the limb failed: say what failed and why (the url and the error "
        "code), never invent the content it was supposed to bring.\n"
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
