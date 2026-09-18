from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

KIT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = KIT_ROOT / "src"
VENDOR_P0 = SRC_ROOT / "vendor" / "p0"
PORTAL = KIT_ROOT / "portal"
CONFIG = KIT_ROOT / "config"
ENGINE_DIR = KIT_ROOT / "engine"
DATA = KIT_ROOT / "data"
SAVE = KIT_ROOT / "save"
WORKSPACE = KIT_ROOT / "workspace"
RECEIPTS = SAVE / "receipts"
MYCELIUM = SAVE / "mycelium"
LOGS = SAVE / "logs"
NOTEPAD = SAVE / "notepad"
SKILLS = KIT_ROOT / "skills"
SKILLS_SAVE = SAVE / "skills"
REGISTRY_PATH = SAVE / "registry.json"
CONSOLE_JSON = CONFIG / "console.json"
LOCAL_JSON = CONFIG / "local.json"
TOKEN_PATH = DATA / ".lygo_llm_token"
LLAMA_KEY_PATH = DATA / ".llama_api_key"
PID_PATH = DATA / "engine.pid.json"
ACTIVE_ENGINE_JSON = DATA / "perf_active.json"


def engine_dir() -> Path:
    """The engine directory to launch: an activated GPU backend build, else engine/.

    backends.py writes that record only after a backend has been proven on this host;
    a stale, half-removed or unreadable record falls back to the shipped engine instead
    of failing the boot.
    """
    try:
        rec = json.loads(ACTIVE_ENGINE_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ENGINE_DIR
    cand = Path(str((rec or {}).get("engine_dir") or ""))
    try:
        if str(cand) and (cand / "llama-server.exe").is_file():
            return cand
    except OSError:
        pass
    return ENGINE_DIR

def _port_from_env(name: str, default: int) -> int:
    """Ports are env-overridable so a USB stick can run *beside* a desktop console.

    LYGO_CONSOLE_PORT / LYGO_LLAMA_PORT / LYGO_EMBED_PORT / LYGO_COLIBRI_PORT — the USB
    LYGO CLAW sets 9651/11451/11452/11453 so it never fights the desktop 9641/11441/11442/11443.
    A junk value falls back to the default rather than crashing the boot.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        val = int(raw)
    except ValueError:
        return default
    return val if 0 < val < 65536 else default


DEFAULT_PORT = _port_from_env("LYGO_CONSOLE_PORT", 9641)
LLAMA_PORT = _port_from_env("LYGO_LLAMA_PORT", 11441)
EMBED_PORT = _port_from_env("LYGO_EMBED_PORT", 11442)
COLIBRI_PORT = _port_from_env("LYGO_COLIBRI_PORT", 11443)


_CFG_CACHE: dict[str, Any] | None = None


def console_cfg() -> dict[str, Any]:
    """Merged config/console.json + config/local.json (local wins). Cached, never raises.

    One reader for the whole kit: the limits a USB stick ships in its own config are the
    operator's contract, so no module may hard-code a desktop value beside this.
    """
    global _CFG_CACHE
    if _CFG_CACHE is None:
        cfg: dict[str, Any] = {}
        for p in (CONSOLE_JSON, LOCAL_JSON):
            try:
                if p.is_file():
                    d = json.loads(p.read_text(encoding="utf-8"))
                    if isinstance(d, dict):
                        cfg = {**cfg, **d}
            except (OSError, ValueError):
                pass
        _CFG_CACHE = cfg
    return _CFG_CACHE


AUTO_TOKENS = ("auto", "hardware", "")


def _cfg_int(key: str) -> int | None:
    """Config integer. An explicit number is a pin (0 included); "auto"/absent means
    the host decides — see perf.py."""
    v = console_cfg().get(key)
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, str) and v.strip().lower() in AUTO_TOKENS:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _cfg_str(key: str, default: str = "") -> str:
    """Config text value, lowercased. Absent or junk means the default."""
    v = console_cfg().get(key)
    if isinstance(v, str) and v.strip():
        return v.strip().lower()
    return default


def console_limits() -> dict[str, Any]:
    """Engine launch limits from the kit config.

    Operator intent beats the hardware auto-plan: an integer ngl/threads is a pin and is
    honored even at 0, because CPU-only is a real choice. The token "auto" (what the kit
    ships) hands the choice to perf.py, so one stick uses the GPU on a tower and the CPU on
    a laptop.
    ctx_default only fills in for a model that declares no native context; ctx_max caps it.
    gpu = auto|off — "off" never touches a GPU backend (see backends.py), "auto" proves
    one on this host before using it.
    """
    return {
        "ngl": _cfg_int("ngl"),
        "threads": _cfg_int("threads"),
        "ctx_default": _cfg_int("ctx_default") or 4096,
        "ctx_max": _cfg_int("ctx_max") or 8192,
        "gpu": _cfg_str("gpu", "auto"),
        "source": "console.json" if console_cfg() else "defaults",
    }



def ensure_dirs() -> None:
    for p in (
        DATA,
        SAVE,
        WORKSPACE,
        RECEIPTS,
        MYCELIUM,
        LOGS,
        NOTEPAD,
        NOTEPAD / "notes",
        SKILLS_SAVE,
        SKILLS_SAVE / "installed",
        WORKSPACE / "skills",
        ENGINE_DIR,
    ):
        p.mkdir(parents=True, exist_ok=True)


# --- portable root resolution --------------------------------------------------
# The kit travels: desktop I:\E Drive\lygo-protocol-stack, USB E:\LYGO_BUILDER_KEY,
# packaging target D:\LYGO_CONSOLE. A baked-in drive letter is therefore only ever the
# LAST resort, and resolution never goes quiet: every candidate is recorded by
# resolution_log() and stack_root_status() always returns a root plus the reason.

STACK_ROOT_ENV: tuple[str, ...] = ("LYGO_STACK_ROOT", "LYGO_STACK")
STACK_MARKERS: tuple[str, ...] = ("LYGO_STACK_ROOT_POINTER.md",)
STACK_MARKER_DIRS: tuple[str, ...] = ("protocol0_byte_entropy_filter", "lygo_llm_console")
DRIVE_SCAN_LETTERS: str = "IEDCFUV"
STACK_DRIVE_TEMPLATES: tuple[str, ...] = (
    "{d}:\\E Drive\\lygo-protocol-stack",
    "{d}:\\lygo-protocol-stack",
    "{d}:\\LYGO\\lygo-protocol-stack",
)

_RESOLUTION_LOG: list[dict[str, str]] = []


def _record(kind: str, source: str, path: Any, verdict: str, reason: str = "") -> dict[str, str]:
    row = {"kind": kind, "source": source, "path": str(path or ""), "verdict": verdict, "reason": reason}
    _RESOLUTION_LOG.append(row)
    if os.environ.get("LYGO_PATHS_DEBUG", "").strip():
        print(f"[paths] stack-root {source} = {row['path']} -> {verdict} ({reason})", file=sys.stderr)
    return row


def resolution_log() -> list[dict[str, str]]:
    """Every candidate the last stack-root resolution considered, in order, with its verdict."""
    return [dict(r) for r in _RESOLUTION_LOG]


def _stack_marker(root: Path) -> str:
    """A reason string when root really is the protocol stack, else ''."""
    for name in STACK_MARKERS:
        if (root / name).is_file():
            return f"marker {name}"
    for name in STACK_MARKER_DIRS:
        if (root / name).is_dir():
            return f"subdir {name}"
    return ""


def _as_path(raw: str) -> Path | None:
    try:
        return Path(raw)
    except (OSError, ValueError):
        return None


def _stack_candidates() -> list[tuple[Path, str, str]]:
    out: list[tuple[Path, str, str]] = []
    for name in STACK_ROOT_ENV:
        raw = os.environ.get(name, "").strip()
        if raw:
            p = _as_path(raw)
            if p is not None:
                out.append((p, f"env:{name}", "env"))
    parent = KIT_ROOT.parent
    out.append((parent, "kit-relative:KIT_ROOT.parent", "kit"))
    out.append((KIT_ROOT / "lygo-protocol-stack", "kit-relative:KIT_ROOT/lygo-protocol-stack", "kit"))
    out.append((parent / "lygo-protocol-stack", "kit-relative:KIT_ROOT.parent/lygo-protocol-stack", "kit"))
    if parent.parent != parent:
        out.append((parent.parent, "kit-relative:KIT_ROOT.parent.parent", "kit"))
    here = (KIT_ROOT.drive or "")[:1].upper()
    letters = ([here] if here else []) + [c for c in DRIVE_SCAN_LETTERS if c != here]
    for letter in letters:
        for tpl in STACK_DRIVE_TEMPLATES:
            cand = tpl.format(d=letter)
            p = _as_path(cand)
            if p is not None:
                out.append((p, f"drive-scan:{cand}", "drive-letter"))
    return out


def stack_root_status() -> dict[str, Any]:
    """Resolve the protocol-stack root and say exactly what happened.

    Order: LYGO_STACK_ROOT/LYGO_STACK -> KIT_ROOT-relative -> raw drive letters LAST.
    Never returns None: with nothing verified the best existing candidate is returned with
    a reason naming the markers that were missing.
    """
    del _RESOLUTION_LOG[:]
    best: Path | None = None
    best_source = ""
    for path, source, kind in _stack_candidates():
        try:
            is_dir = path.is_dir()
        except OSError:
            is_dir = False
        if not is_dir:
            _record(kind, source, path, "skipped", "not a directory")
            continue
        marker = _stack_marker(path)
        if marker:
            _record(kind, source, path, "won", marker)
            return {
                "root": str(path),
                "verified": True,
                "source": source,
                "reason": f"{source} verified by {marker}",
                "candidates": resolution_log(),
            }
        _record(kind, source, path, "exists-unverified", "no stack marker")
        if best is None:
            best, best_source = path, source
    if best is not None:
        reason = (
            "no verified stack root: none of "
            f"{'/'.join(STACK_MARKERS)} or {'/'.join(STACK_MARKER_DIRS)} present; "
            f"kept best existing candidate {best_source}"
        )
        _record("fallback", best_source, best, "best-effort", reason)
        return {
            "root": str(best),
            "verified": False,
            "source": best_source,
            "reason": reason,
            "candidates": resolution_log(),
        }
    fallback = KIT_ROOT.parent
    reason = f"no stack root anywhere on this host; unverified default {fallback} (never None)"
    _record("fallback", "kit-relative:KIT_ROOT.parent", fallback, "hard-fallback", reason)
    return {
        "root": str(fallback),
        "verified": False,
        "source": "kit-relative:KIT_ROOT.parent (unverified default)",
        "reason": reason,
        "candidates": resolution_log(),
    }


def stack_root() -> Path:
    """The protocol-stack root. Never None - stack_root_status() carries the reason."""
    return Path(str(stack_root_status()["root"]))
