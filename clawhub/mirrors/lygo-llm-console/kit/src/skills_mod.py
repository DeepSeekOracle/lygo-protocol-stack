"""OpenClaw-compatible skills for LYGO LLM Console.

A skill is a folder with SKILL.md (YAML frontmatter + markdown body).
Load order (highest first):
  1. workspace/skills
  2. save/skills/installed  (ClawHub installs)
  3. extra dirs (enabled.json, LYGO_SKILLS_DIRS, ~/.agents/skills, ~/.openclaw/skills, ~/.grok/skills)
  4. kit bundled skills/    (15 Δ9 champions)

Enabled skills inject name+description into the system prompt.
Full SKILL.md is loaded only via skill_read or when the operator invokes that skill.
Skills are instruction packs. This module does not execute skill scripts.
"""
from __future__ import annotations

import io
import json
import os
import re
import time
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from paths import KIT_ROOT, SAVE, WORKSPACE, ensure_dirs
from p0_hook import gate_prompt

BUNDLED = KIT_ROOT / "skills"
INSTALLED = SAVE / "skills" / "installed"
STATE_PATH = SAVE / "skills" / "enabled.json"
CLAW_HUB = "https://clawhub.ai"
MAX_SKILL_BODY = 12_000
MAX_ZIP = 6_000_000
ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/-]{0,79}$")

CHAMPIONS: list[dict[str, str]] = [
    {
        "slug": "champion-lyra",
        "champion_id": "LYRΔ",
        "name": "LYRΔ — Spiral Memory Guardian",
        "role": "Memory, song, continuity of theme",
        "when": "continuity, recall, lyrical framing of technical work",
        "invoke": "Invoke LYRΔ — Observed / Inferred / Unknown, then next actions.",
        "defer": "structure→ARKOS; signal→ÆTHERIS; sanctity→SANCORA; irreversible→OMNIΣIREN",
    },
    {
        "slug": "champion-d9ra",
        "champion_id": "Δ9RA",
        "name": "Δ9RA — Boundary vigilance",
        "role": "Wolf-edge challenge and risk review",
        "when": "stress-test a plan, challenge assumptions, name threats",
        "invoke": "Invoke Δ9RA — list risks, assumptions, and what would break first.",
        "defer": "Not a professional security audit.",
    },
    {
        "slug": "champion-srath",
        "champion_id": "ΣRΛΘ",
        "name": "ΣRΛΘ — Shadow sentinel",
        "role": "Omissions, hidden failure, red-team reading",
        "when": "something is quietly wrong or unsaid",
        "invoke": "Invoke ΣRΛΘ — what is missing, omitted, or failing silently?",
        "defer": "Do not invent hidden plots. Unknown stays unknown.",
    },
    {
        "slug": "champion-arkos",
        "champion_id": "ARKOS",
        "name": "ARKOS — Ethical Reality Architect",
        "role": "Systems maps, modules, trust boundaries",
        "when": "before coding: boxes, arrows, out-of-scope, sequence",
        "invoke": "Invoke ARKOS — Intent, Constraints, Blueprint, Failure modes, Refactor, Receipts.",
        "defer": "Architecture theater without a smallest shippable slice is a failure.",
    },
    {
        "slug": "champion-kairos",
        "champion_id": "KAIROS",
        "name": "KAIROS — Temporal Harmonizer",
        "role": "Timing, sequencing, what happens first",
        "when": "priority and release order are the real problem",
        "invoke": "Invoke KAIROS — ordered steps with why this order.",
        "defer": "Do not schedule work the operator did not ask for.",
    },
    {
        "slug": "champion-aetheris",
        "champion_id": "ÆTHERIS",
        "name": "ÆTHERIS — Truth Fractal Engine",
        "role": "Claims vs evidence, cut noise",
        "when": "need a falsifiable claim and a receipt",
        "invoke": "Invoke ÆTHERIS — claim, evidence, counter, unknown.",
        "defer": "Web hits are RESOURCE. Dual ledgers / Star Chart are CANON.",
    },
    {
        "slug": "champion-scendr",
        "champion_id": "ΣCENΔR",
        "name": "ΣCENΔR — Paradox Weaver",
        "role": "Scenarios where both may be true",
        "when": "forced single-answer is premature",
        "invoke": "Invoke ΣCENΔR — at least two live scenarios and what would falsify each.",
        "defer": "Do not collapse to one story for comfort.",
    },
    {
        "slug": "champion-sancora",
        "champion_id": "SANCORA",
        "name": "SANCORA — Collective Healing Nexus",
        "role": "Shared vocabulary, handoff, collaboration",
        "when": "multiple humans/agents must stay coherent",
        "invoke": "Invoke SANCORA — shared terms, handoff packet, what not to mix.",
        "defer": "Healing language is protocol, not medical advice.",
    },
    {
        "slug": "champion-sephrael",
        "champion_id": "SEPHRAEL",
        "name": "SEPHRAEL — Echo-walker",
        "role": "What repeats, what is fragile, what to archive",
        "when": "session drift, fragile memory, echoes across chats",
        "invoke": "Invoke SEPHRAEL — echoes, fragile items, archive vs discard.",
        "defer": "Do not store secrets in MEMORY.md.",
    },
    {
        "slug": "champion-omnisiren",
        "champion_id": "OMNIΣIREN",
        "name": "OMNIΣIREN — Silent storm",
        "role": "Fewer words, sharper constraints",
        "when": "verbosity is blocking execution",
        "invoke": "Invoke OMNIΣIREN — constraints only, then the next irreversible-safe step.",
        "defer": "Silent does not mean hidden. No covert actions.",
    },
    {
        "slug": "champion-lightfather",
        "champion_id": "Lightfather",
        "name": "Lightfather — Provenance seat",
        "role": "Publisher ethics, consent, truth preservation",
        "when": "who publishes, what is CANON, consent for writes",
        "invoke": "Invoke Lightfather — provenance, consent, CANON vs RESOURCE.",
        "defer": "Persona lens. Never claim to be the human operator. Never replace them.",
    },
    {
        "slug": "champion-volaris",
        "champion_id": "VΩLARIS",
        "name": "VΩLARIS — Prism judgment",
        "role": "Multi-criteria decisions in the open",
        "when": "tradeoffs must be visible, not hidden",
        "invoke": "Invoke VΩLARIS — criteria, scores, tradeoffs, recommendation.",
        "defer": "Show the criteria. Do not hide the loss function.",
    },
    {
        "slug": "champion-zeta",
        "champion_id": "ZETAΔ9",
        "name": "ZETAΔ9 — Threshold walker",
        "role": "Edge cases and weird inputs",
        "when": "designs need to bend before they break",
        "invoke": "Invoke ZETAΔ9 — weird inputs, failure modes, boundary tests.",
        "defer": "Do not actually break production to prove a point.",
    },
    {
        "slug": "champion-justicae",
        "champion_id": "JUSTICAE",
        "name": "JUSTICAE — Fairness and process",
        "role": "Who is affected, disclosure, consent",
        "when": "public posts, shared skills, other people are in scope",
        "invoke": "Invoke JUSTICAE — affected parties, disclosure, consent gaps.",
        "defer": "No doxxing. No harassment. Process over punishment theater.",
    },
    {
        "slug": "champion-seidon",
        "champion_id": "ΣEIDŌN",
        "name": "ΣEIDŌN — Mirror witness",
        "role": "Surface foam vs deep current on long work",
        "when": "roadmap honesty, depth vs noise",
        "invoke": "Invoke ΣEIDŌN — surface vs depth, what can wait, what is the tide.",
        "defer": "Witness. Do not flatten a long project into a slogan.",
    },
]


def _skill_md(c: dict[str, str]) -> str:
    return (
        f"---\n"
        f"name: {c['slug']}\n"
        f"description: Δ9 Council champion {c['champion_id']} — {c['role']}. Enable to align the agent with this seat.\n"
        f"version: 1.0.0\n"
        f"metadata: {{\"openclaw\": {{\"emoji\": \"🜂\", \"homepage\": \"https://chatagent.ca/champions.html\"}}, \"lygo\": true, \"champion_id\": \"{c['champion_id']}\"}}\n"
        f"---\n\n"
        f"# {c['name']}\n\n"
        f"**Seat:** {c['champion_id']}  \n"
        f"**Role:** {c['role']}  \n"
        f"**Use when:** {c['when']}\n\n"
        f"## Contract\n"
        f"- Advisor only. Not a controller. Not the human operator.\n"
        f"- Separate **Observed / Inferred / Unknown**.\n"
        f"- Dual ledgers / Haven Star Chart = CANON. This chat and the web = RESOURCE.\n"
        f"- P0: no OS wipe, no fabricated receipts, no secrets in MEMORY.md.\n"
        f"- {c['defer']}\n\n"
        f"## Invoke\n"
        f"{c['invoke']}\n\n"
        f"Hub: https://chatagent.ca/champions.html\n"
    )


def seed_bundled() -> None:
    root = BUNDLED / "champions"
    root.mkdir(parents=True, exist_ok=True)
    for c in CHAMPIONS:
        d = root / c["slug"]
        d.mkdir(parents=True, exist_ok=True)
        p = d / "SKILL.md"
        if not p.is_file():
            p.write_text(_skill_md(c), encoding="utf-8")
    readme = BUNDLED / "README.md"
    if not readme.is_file():
        readme.write_text(
            "# Console skills (OpenClaw-compatible)\n\n"
            "Each skill is a folder with `SKILL.md`. Champions ship bundled.\n"
            "Install more from ClawHub into `save/skills/installed/`.\n"
            "Drop extra SKILL.md trees in `workspace/skills` or "
            "`~/.agents/skills` / `~/.openclaw/skills`.\n",
            encoding="utf-8",
        )


def ensure() -> None:
    ensure_dirs()
    (SAVE / "skills").mkdir(parents=True, exist_ok=True)
    INSTALLED.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "skills").mkdir(parents=True, exist_ok=True)
    seed_bundled()
    if not STATE_PATH.is_file():
        save_state({"enabled": [c["slug"] for c in CHAMPIONS], "extra_dirs": []})


def load_state() -> dict[str, Any]:
    ensure()
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("enabled", [c["slug"] for c in CHAMPIONS])
    data.setdefault("extra_dirs", [])
    return data


def save_state(data: dict[str, Any]) -> None:
    (SAVE / "skills").mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def _parse_skill_md(text: str, path: Path) -> dict[str, Any] | None:
    fm: dict[str, str] = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            raw = text[3:end]
            body = text[end + 4 :].lstrip("\n")
            for line in raw.splitlines():
                if ":" not in line or line.lstrip().startswith("#"):
                    continue
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
    name = (fm.get("name") or path.parent.name).strip()
    if not name:
        return None
    desc = fm.get("description") or ""
    return {
        "slug": name,
        "description": desc[:240],
        "version": fm.get("version") or "",
        "body": body[:MAX_SKILL_BODY],
        "path": str(path),
        "dir": str(path.parent),
        "frontmatter": fm,
    }


def _walk_skills(root: Path, source: str, depth: int = 5) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not root.is_dir():
        return out
    try:
        files = list(root.rglob("SKILL.md")) + list(root.rglob("skill.md"))
    except OSError:
        return out
    for p in files[:200]:
        try:
            rel = p.relative_to(root)
            if len(rel.parts) > depth:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")[: MAX_SKILL_BODY + 2000]
        except OSError:
            continue
        parsed = _parse_skill_md(text, p)
        if not parsed:
            continue
        parsed["source"] = source
        out.append(parsed)
    return out


def extra_roots() -> list[Path]:
    roots: list[Path] = []
    st = load_state()
    for raw in st.get("extra_dirs") or []:
        p = Path(str(raw))
        if p.is_dir():
            roots.append(p)
    env = os.environ.get("LYGO_SKILLS_DIRS", "")
    for part in env.split(os.pathsep):
        p = Path(part.strip()) if part.strip() else None
        if p and p.is_dir():
            roots.append(p)
    home = Path.home()
    for cand in (
        home / ".agents" / "skills",
        home / ".openclaw" / "skills",
        home / ".openclaw" / "workspace" / "skills",
        home / ".grok" / "skills",
        home / ".clawhub" / "skills",
    ):
        if cand.is_dir():
            roots.append(cand)
    return roots


def catalog() -> list[dict[str, Any]]:
    ensure()
    seen: dict[str, dict[str, Any]] = {}
    layers = [
        (WORKSPACE / "skills", "workspace"),
        (INSTALLED, "clawhub"),
    ]
    for r in extra_roots():
        layers.append((r, "extra"))
    layers.append((BUNDLED, "bundled"))
    enabled = set(str(x) for x in load_state().get("enabled") or [])
    for root, source in layers:
        for sk in _walk_skills(root, source):
            slug = sk["slug"]
            if slug in seen:
                continue
            sk["enabled"] = slug in enabled
            sk["champion"] = slug.startswith("champion-")
            seen[slug] = sk
    rows = list(seen.values())
    rows.sort(key=lambda x: (0 if x.get("champion") else 1, x.get("slug") or ""))
    return rows


def list_skills() -> dict[str, Any]:
    rows = catalog()
    slim = [
        {
            "slug": r["slug"],
            "description": r.get("description"),
            "source": r.get("source"),
            "enabled": r.get("enabled"),
            "champion": r.get("champion"),
            "dir": r.get("dir"),
        }
        for r in rows
    ]
    return {
        "ok": True,
        "n": len(slim),
        "enabled": [r["slug"] for r in slim if r.get("enabled")],
        "skills": slim,
        "clawhub": CLAW_HUB,
        "note": "Full SKILL.md is not in the system prompt. Call skill_read when invoking a skill.",
    }


def read_skill(slug: str) -> dict[str, Any]:
    slug = (slug or "").strip()
    if not slug:
        return {"ok": False, "error": "empty"}
    for r in catalog():
        if r["slug"] == slug or r["slug"].endswith("/" + slug) or slug in {r["slug"], Path(r["dir"]).name}:
            if gate_prompt((r.get("body") or "")[:4000]).get("verdict") == "QUARANTINE":
                return {"ok": False, "error": "p0_blocked", "slug": r["slug"]}
            return {
                "ok": True,
                "slug": r["slug"],
                "description": r.get("description"),
                "source": r.get("source"),
                "enabled": r.get("enabled"),
                "text": r.get("body") or "",
                "path": r.get("path"),
            }
    aliases = {c["champion_id"].lower(): c["slug"] for c in CHAMPIONS}
    aliases.update({c["slug"].replace("champion-", ""): c["slug"] for c in CHAMPIONS})
    hit = aliases.get(slug.lower())
    if hit:
        return read_skill(hit)
    return {"ok": False, "error": "missing", "slug": slug}


def set_enabled(slug: str, on: bool) -> dict[str, Any]:
    st = load_state()
    en = [str(x) for x in st.get("enabled") or []]
    slug = (slug or "").strip()
    found = None
    for r in catalog():
        if r["slug"] == slug or Path(r["dir"]).name == slug:
            found = r["slug"]
            break
    if not found:
        aliases = {c["champion_id"].lower(): c["slug"] for c in CHAMPIONS}
        found = aliases.get(slug.lower()) or slug
    if on:
        if found not in en:
            en.append(found)
    else:
        en = [x for x in en if x != found]
    st["enabled"] = en
    save_state(st)
    return {"ok": True, "slug": found, "enabled": on, "enabled_list": en}


def add_root(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_dir():
        return {"ok": False, "error": "not_dir"}
    st = load_state()
    dirs = [str(x) for x in st.get("extra_dirs") or []]
    s = str(p.resolve())
    if s not in dirs:
        dirs.append(s)
    st["extra_dirs"] = dirs
    save_state(st)
    return {"ok": True, "extra_dirs": dirs, "added": s}


def prompt_catalog(cap: int = 2800) -> str:
    rows = [r for r in catalog() if r.get("enabled")]
    if not rows:
        return (
            "SKILLS: none enabled. Operator can turn on Δ9 champions in the Skills panel "
            "(LYRΔ, Δ9RA, ΣRΛΘ, ARKOS, KAIROS, ÆTHERIS, ΣCENΔR, SANCORA, SEPHRAEL, "
            "OMNIΣIREN, Lightfather, VΩLARIS, ZETAΔ9, JUSTICAE, ΣEIDŌN)."
        )
    lines = [
        "ENABLED SKILLS (OpenClaw-compatible). Name+description only. "
        "Call skill_read before following a skill. Do not invent skill bodies."
    ]
    used = len(lines[0])
    for r in rows:
        line = f"- {r['slug']}: {r.get('description') or ''}"
        if used + len(line) + 1 > cap:
            lines.append(f"- … {len(rows)} enabled; skill_list for the rest")
            break
        lines.append(line)
        used += len(line) + 1
    return "\n".join(lines)


def match_invoked(user_text: str) -> list[str]:
    t = (user_text or "").lower()
    hits: list[str] = []
    for c in CHAMPIONS:
        keys = {c["slug"], c["champion_id"].lower(), c["slug"].replace("champion-", "")}
        keys.add(c["champion_id"].replace("Δ", "d").replace("Σ", "s").replace("Λ", "l").lower())
        if any(k and k in t for k in keys):
            hits.append(c["slug"])
    m = re.search(r"(?:/skill|skill_read|invoke|summon|align with)\s+([a-zA-Z0-9._ΔΣΛΩÆ-]{2,40})", user_text or "", re.I)
    if m:
        hits.append(m.group(1))
    # unique preserve
    out: list[str] = []
    for h in hits:
        if h not in out:
            out.append(h)
    return out[:3]


def _http_json(url: str) -> Any:
    from web_tools import _blocked, _get

    why = _blocked(url)
    if why:
        return {"ok": False, "error": why}
    code, raw, ctype = _get(url)
    if code != 200:
        return {"ok": False, "error": f"http_{code}"}
    try:
        return json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"ok": False, "error": "not_json", "ctype": ctype}


def clawhub_search(q: str) -> dict[str, Any]:
    q = (q or "").strip()[:120]
    if not q:
        url = f"{CLAW_HUB}/api/v1/skills?limit=8&sort=downloads&nonSuspiciousOnly=true"
    else:
        url = f"{CLAW_HUB}/api/v1/search?" + urlencode({"q": q, "limit": "8", "nonSuspiciousOnly": "true"})
    data = _http_json(url)
    if isinstance(data, dict) and data.get("ok") is False:
        return data
    items = []
    if isinstance(data, dict):
        items = data.get("items") or data.get("results") or data.get("skills") or []
        if not items and isinstance(data.get("skill"), dict):
            items = [data]
    elif isinstance(data, list):
        items = data
    rows = []
    for it in items[:8]:
        if not isinstance(it, dict):
            continue
        sk = it.get("skill") if isinstance(it.get("skill"), dict) else it
        slug = sk.get("slug") or it.get("slug") or ""
        owner = ""
        if isinstance(it.get("owner"), dict):
            owner = it["owner"].get("handle") or ""
        elif isinstance(sk.get("owner"), dict):
            owner = sk["owner"].get("handle") or ""
        rows.append(
            {
                "slug": slug,
                "display": sk.get("displayName") or sk.get("name") or slug,
                "summary": (sk.get("summary") or sk.get("description") or it.get("summary") or "")[:240],
                "owner": owner,
                "url": f"{CLAW_HUB}/{owner}/skills/{slug}" if owner else f"{CLAW_HUB}/skills/{slug}",
            }
        )
    return {"ok": True, "q": q, "hits": rows, "class": "RESOURCE"}


def clawhub_inspect(slug: str) -> dict[str, Any]:
    slug = (slug or "").strip().lstrip("@")
    if not slug or not ID_RE.match(slug.replace("/", "-")):
        return {"ok": False, "error": "bad_slug"}
    data = _http_json(f"{CLAW_HUB}/api/v1/skills/{quote(slug, safe='/-')}")
    if isinstance(data, dict) and data.get("ok") is False:
        return data
    if not isinstance(data, dict):
        return {"ok": False, "error": "bad_payload"}
    mod = data.get("moderation") or {}
    if mod.get("isMalwareBlocked"):
        return {"ok": False, "error": "malware_blocked", "slug": slug}
    return {"ok": True, "slug": slug, "data": json.dumps(data, default=str)[:8000], "moderation": mod, "class": "RESOURCE"}


def clawhub_install(slug: str) -> dict[str, Any]:
    slug = (slug or "").strip().lstrip("@")
    if not slug:
        return {"ok": False, "error": "empty"}
    insp = clawhub_inspect(slug)
    if not insp.get("ok"):
        return insp
    from web_tools import _blocked, CTX, UA, TIMEOUT
    import urllib.error
    import urllib.request

    url = f"{CLAW_HUB}/api/v1/download?" + urlencode({"slug": slug})
    why = _blocked(url)
    if why:
        return {"ok": False, "error": why}
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/zip,application/json,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as resp:
            ctype = resp.headers.get("Content-Type") or ""
            raw = resp.read(MAX_ZIP + 1)
            code = resp.status
    except urllib.error.HTTPError as e:
        code, raw, ctype = e.code, (e.read() or b"")[:4000], ""
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    if code != 200:
        return {"ok": False, "error": f"http_{code}", "detail": raw[:200].decode("utf-8", errors="replace")}
    if "json" in (ctype or "").lower() or raw[:1] in (b"{", b"["):
        return {"ok": False, "error": "github_handoff", "hint": "this skill is GitHub-backed; clone SKILL.md yourself into workspace/skills", "detail": raw[:400].decode("utf-8", errors="replace")}
    if len(raw) > MAX_ZIP:
        return {"ok": False, "error": "too_large"}
    dest = INSTALLED / slug.replace("/", "--")
    dest.mkdir(parents=True, exist_ok=True)
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        # maybe a single SKILL.md
        if b"---" in raw[:80]:
            (dest / "SKILL.md").write_bytes(raw)
            return {"ok": True, "slug": slug, "path": str(dest), "files": 1}
        return {"ok": False, "error": "not_zip"}
    n = 0
    for info in zf.infolist():
        name = info.filename.replace("\\", "/")
        if name.endswith("/") or ".." in name.split("/") or name.startswith("/"):
            continue
        low = name.lower()
        if low.endswith((".exe", ".dll", ".bat", ".cmd", ".ps1", ".msi", ".scr")):
            continue
        if info.file_size > 400_000:
            continue
        target = dest / Path(name).name if "/" not in name.strip("/") else dest.joinpath(*Path(name).parts[-3:])
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(info)[:400_000])
            n += 1
        except OSError:
            continue
        if n >= 40:
            break
    if not list(dest.rglob("SKILL.md")) and not list(dest.rglob("skill.md")):
        return {"ok": False, "error": "no_skill_md"}
    origin = dest / ".clawhub-origin.json"
    origin.write_text(json.dumps({"slug": slug, "source": "clawhub", "ts": time.time()}, indent=2), encoding="utf-8")
    set_enabled(slug.replace("/", "--"), True)
    return {"ok": True, "slug": slug, "path": str(dest), "files": n, "enabled": True}
