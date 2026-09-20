"""Live console + model facts.

The model cannot inspect its own weights, so the console tells it. These values are injected into
the system prompt and returned by whoami / kernel_status, so "what model are you?" has a real
answer instead of "I have no tool that reports my own backing weights".

Nothing here touches secrets.
"""
from __future__ import annotations

import platform
import sys
from typing import Any

import version
from paths import DEFAULT_PORT, KIT_ROOT, LLAMA_PORT

# Same one file as server.BUILD: the model is told the release the operator is actually running.
_FALLBACK_BUILD = version.stamp()


def _server_module() -> Any:
    return sys.modules.get("server")


def _state() -> dict[str, Any]:
    m = _server_module()
    st = getattr(m, "STATE", None) if m else None
    return st if isinstance(st, dict) else {}


def console_build() -> str:
    m = _server_module()
    return str(getattr(m, "BUILD", None) or _FALLBACK_BUILD)


def selected_model() -> str:
    """The weights actually answering this turn: live STATE first, then the registry."""
    st = _state()
    model = st.get("selected")
    if not model:
        try:
            from registry import load as reg_load

            model = (reg_load() or {}).get("selected")
        except Exception:
            model = None
    return str(model or "no model selected")


def engine_name() -> str:
    st = _state()
    return str(st.get("engine") or "llama.cpp")


def limb_names() -> list[str]:
    try:
        from tools import TOOLS_SCHEMA
    except Exception:
        return []
    out = []
    for t in TOOLS_SCHEMA:
        name = (t.get("function") or {}).get("name")
        if name:
            out.append(str(name))
    return out


def brain_mode() -> dict[str, Any]:
    try:
        import brain_router
        from cloud_api import public_status

        st = public_status()
        return {
            "mode": brain_router.mode_of(st),
            "label": brain_router.label_of(st),
            "api_ready": bool(st.get("enabled")) and bool(st.get("has_key")),
        }
    except Exception as e:  # console modules not loaded (tests, CLI)
        return {"mode": "local", "label": "local engine", "error": str(e)[:80]}


def cloud_info() -> dict[str, Any]:
    try:
        from cloud_api import public_status

        st = public_status()
        return {
            "mode": str(st.get("mode") or ""),
            "model": str(st.get("model") or ""),
            "label": str(st.get("label") or "API"),
            "url": str(st.get("url") or ""),
            "active": bool(st.get("active")),
            "ready": bool(st.get("enabled")) and bool(st.get("has_key")),
        }
    except Exception as e:  # console modules not loaded (tests, CLI)
        return {"mode": "", "model": "", "label": "API", "url": "", "active": False, "ready": False, "error": str(e)[:80]}


def answering(brain: str | None = None) -> dict[str, str]:
    """Who generates the tokens this turn — the brain switch decides, the model never guesses.

    When the API brain is active the answering model/engine is the cloud one, and the local GGUF is
    only a standby; reporting the local weights then is a lie the model will happily repeat.

    `brain` is the effective brain for this request when the caller knows it (a per-request switch
    can differ from the saved mode); otherwise the saved mode is used.
    """
    ci = cloud_info()
    local = selected_model()
    mode = (brain or "").strip() or str(ci.get("mode") or "")
    if mode == "api" and ci.get("ready"):
        host = ""
        url = str(ci.get("url") or "")
        if url:
            host = " " + url.split("/v1")[0].rstrip("/")
        label = str(ci.get("label") or "API")
        model = str(ci.get("model") or "cloud model")
        return {
            "model": model,
            "engine": f"{label} API{host}",
            "brain": "api",
            "brain_label": f"{label}/{model}",
            "standby": local,
        }
    return {
        "model": local,
        "engine": engine_name(),
        "brain": "local",
        "brain_label": f"local engine ({local})",
        "standby": "",
    }


def facts(brain: str | None = None) -> dict[str, Any]:
    names = limb_names()
    a = answering(brain)
    st = _state()
    port = int(st.get("engine_port") or LLAMA_PORT)
    return {
        "ok": True,
        "build": console_build(),
        "system": __import__("surface").report(local_ready=(_state().get("brain") == "ready")),
        "engine": a["engine"],
        "engine_port": port,
        "model": a["model"],
        "brain": a["brain"],
        "brain_label": a["brain_label"],
        "standby_model": a.get("standby") or selected_model(),
        "local_engine": f"{engine_name()} :{port}",
        "portal": f"http://127.0.0.1:{DEFAULT_PORT}/",
        "kit": str(KIT_ROOT),
        "host": platform.node(),
        "n_limbs": len(names),
        "limbs": names,
    }


def system_roles() -> str:
    """The three systems and what each one is, in the compact form the prompt window can carry.

    surface.ROLES is the operator's full wording for humans; surface.ROLES_BRIEF is the same three
    roles quoted short, because the identity block must leave room for history and the answer.
    """
    _s = __import__("surface")
    return " . ".join(_s.LABELS[i] + " = " + _s.ROLES_BRIEF[i] for i in _s.ORDER)


def prompt_block(brain: str | None = None) -> str:
    f = facts(brain)
    return (
        "=== RUNTIME (measured live by the console — this is who you are; never guess or deny it) ===\n"
        f"- Surface: LYGO LLM Console (FULL), build {f['build']}, {f['portal']} on host {f['host']}\n"
        f"- System: {f['system']['label']} ({f['system']['id']}) - one of three systems; roles below\n"
        f"- Roles: {system_roles()}\n"
        f"- Model answering this turn: {f['model']} — brain in use now: {f['brain_label']} ({f['brain']})\n"
        f"- Engine answering: {f['engine']}\n"
        f"- Local standby engine (booted and ready): {f['local_engine']} holding {f['standby_model']}\n"
        f"- Kit folder: {f['kit']}\n"
        f"- Limbs wired: {f['n_limbs']}\n"
        "When the operator asks what model, engine, or build you are running, state the model that "
        "answers this turn. If the API brain fails mid-turn the console answers from the local standby "
        "engine instead — say plainly that the handoff happened if you notice it.\n"
        "You have no reason to say you cannot tell."
    )


def limb_catalog(cap: int = 2200) -> str:
    """Name + intent for every wired limb, so the agent knows what it can actually call.

    Core limbs are listed first so the ones that matter (web_search, list_dir, whoami …) are never
    the ones cut off by the budget. This rides in an 8k-token engine window next to soul/identity/
    memory, so it stays compact.
    """
    try:
        from tools import TOOLS_SCHEMA
    except Exception:
        return ""
    try:
        from tools import CORE_NAMES as _core
    except Exception:
        _core = set()
    rows: list[tuple[str, str]] = []
    for t in TOOLS_SCHEMA:
        fn = t.get("function") or {}
        name = fn.get("name")
        if not name:
            continue
        desc = str(fn.get("description") or "").split(".")[0].strip()[:44]
        rows.append((str(name), desc))
    rows.sort(key=lambda r: (0 if r[0] in _core else 1, r[0]))
    lines = ["=== LIMBS (tools you can call) ==="]
    used = len(lines[0]) + 1
    for name, desc in rows:
        line = f"- {name}: {desc}" if desc else f"- {name}"
        if used + len(line) + 1 > cap:
            lines.append(f"- …{len(rows)} wired in total (skill_list for skills)")
            break
        lines.append(line)
        used += len(line) + 1
    lines.append("Call one instead of saying you cannot look something up.")
    return "\n".join(lines)
