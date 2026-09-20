from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from paths import CONSOLE_JSON, KIT_ROOT, LOGS, REGISTRY_PATH, SAVE, ensure_dirs
from atomicio import atomic_write_text, read_text as read_file_text

SIGNATURE = "Δ9Φ963-LYGO-LLM-CONSOLE-REG-v1"

# Load outcome of the last load(), so a caller (the server, a CLI) can tell the operator that the
# model list was recovered from the backup instead of silently coming back empty. A torn
# registry.json used to make every model disappear with no error at all.
LOAD_STATUS: dict[str, Any] = {"recovered": False, "source": "", "reason": "", "at": 0.0}


def registry_backup_path() -> Path:
    """registry.json.bak beside the live file (computed live: tests patch REGISTRY_PATH)."""
    return REGISTRY_PATH.with_name(REGISTRY_PATH.name + ".bak")


def kit_storage_roots() -> list[Path]:
    """Storage this kit C A R R I E S with it: the kit folder, and any root it declares by env.

    Deliberately narrower than the scanner's roots. The scanner may look at a vault on the machine it
    is plugged into (and should - that is how the operator's own models get imported), but a file that
    lives outside the kit is not something the stick holds.
    """
    roots = [Path(KIT_ROOT)]
    for env_name in ("LYGO_BUILDER_KEY_ROOT", "LYGO_USB_ROOT", "LYGO_STACK_ROOT"):
        declared = os.environ.get(env_name, "").strip()
        if declared:
            roots.append(Path(os.path.expandvars(declared)))
    roots.extend(_declared_in_config())
    # A vault named by the machine counts only when it is on the SAME DRIVE as the kit. LYGO_MODELS
    # points at the PC's vault; a stick that called the PC's vault its own would advertise models it
    # does not carry, which is the exact lie this helper exists to stop.
    vault = os.environ.get("LYGO_MODELS", "").strip()
    if vault:
        try:
            if Path(os.path.expandvars(vault)).drive.lower() == Path(KIT_ROOT).drive.lower():
                roots.append(Path(os.path.expandvars(vault)))
        except (OSError, ValueError):
            pass
    out: list[Path] = []
    for r in roots:
        try:
            out.append(r.resolve())
        except OSError:
            continue
    return out


def _declared_in_config() -> list[Path]:
    """Roots THIS kit declares in its own config/console.json (absolute entries).

    An arrangement written into the kit's own config travels with the kit; a path that merely exists on
    today's host does not.
    """
    roots: list[Path] = []
    try:
        cfg = json.loads(Path(CONSOLE_JSON).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - a missing or malformed config is not a reason to fail a boot
        return roots
    for r in cfg.get("scan_roots") or []:
        s = os.path.expandvars(os.path.expanduser(str(r)))
        p = Path(s)
        roots.append(p if p.is_absolute() else Path(KIT_ROOT) / s)
    return roots


def reach(rec: dict[str, Any]) -> dict[str, Any]:
    """Can this model run HERE, and does it travel with the kit?

    Two different questions, and a travelling stick needs both answered separately:

      reachable - its files exist on this machine (a fact about now)
      portable  - they sit inside storage the kit carries (a fact about the road)

    A record that is reachable but not portable runs on the machine the stick is plugged into today and
    is gone on the next one. Measured on the stick 2026-09-19: 8 of its 14 records named
    C:\\Users\\justi\\.ollama and even D:\\Ollama blobs - the only vision model among them - so the picker
    was advertising models the stick does not hold. A missing mmproj counts: a record whose projector
    is gone cannot look at a picture either.
    """
    files: list[tuple[str, Path]] = []
    for key in ("path", "mmproj"):
        v = str(rec.get(key) or "").strip()
        if v:
            files.append((key, Path(v)))
    if not files:
        return {"reachable": False, "portable": False, "why": "the record names no model file",
                "missing": [], "outside": []}
    missing = [str(p) for _, p in files if not p.is_file()]
    roots = [str(r).lower() for r in kit_storage_roots()]
    outside: list[str] = []
    for _, p in files:
        try:
            rp = str(p.resolve()).lower()
        except OSError:
            rp = str(p).lower()
        if not any(rp.startswith(r) for r in roots):
            outside.append(str(p))
    why = None
    if missing:
        why = "its file is not on this machine: %s" % missing[0]
    elif outside:
        why = "it lives outside the kit, so it does not travel: %s" % outside[0]
    return {"reachable": not missing, "portable": not missing and not outside, "why": why,
            "missing": missing, "outside": outside}


def selected_vision() -> bool:
    """True when the SELECTED record can actually look at a picture on this machine.

    The vision limbs and an attached photo both need a projector: a chat model with no mmproj, or one
    whose mmproj is not present here, cannot see an image no matter what the picker says.
    """
    data = load()
    sel = data.get("selected")
    rec = next((m for m in data.get("models") or [] if m.get("id") == sel), None)
    if not rec:
        return False
    mp = str(rec.get("mmproj") or "").strip()
    try:
        return bool(mp) and Path(mp).is_file()
    except OSError:
        return False


def load_status() -> dict[str, Any]:
    """What the last load() did — public so callers can surface a recovery."""
    return dict(LOAD_STATUS)


def _log(message: str) -> None:
    """Loud, dependency-free: stderr plus a line in save/logs/registry.log."""
    line = f"[registry] {time.strftime('%Y-%m-%d %H:%M:%S')} {message}"
    try:
        print(line, file=sys.stderr, flush=True)
    except OSError:
        pass
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with (LOGS / "registry.log").open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


# The default main brain is a tool-strong CODER first: this console is an agent, and a coder
# model calls tools far more reliably than a general chat model of the same size. The rest of the
# list is the ordered fallback for hosts that cannot hold the coder.
PREFER_IDS = (
    "qwen2.5-coder:7b",
    "qwen2.5-coder:3b",
    "qwen3-coder:30b",
    "qwen2.5:3b",
    "llama3.1:8b",
    "llama3.2:1b",
)

# RAM-auto brain (console.json "prefer_by_ram"): pick the biggest model this host can really hold
# instead of a fixed favourite, so the same stick behaves right on an 8 GB laptop and a 64 GB tower.
# Weights are NOT the whole story once loaded — context + compute buffers grow them, so require
# factor*weights + headroom to fit in *available* physical RAM (same 2 GB rule engine.ram_ok uses).
RAM_HEADROOM = 2 * 1024**3
RAM_FIT_FACTOR = 1.6


TOOL_RANK_CODER = 3
TOOL_RANK_CHAT = 2
TOOL_RANK_OTHER = 1
_CODER_HINTS = ("coder", "coding", "code-")
_TOOL_HINTS = ("qwen", "llama3", "deepseek", "phi", "gemma4", "nemotron", "bonsai", "mistral")


def tool_rank(m: dict[str, Any]) -> int:
    """How well this model does agentic TOOL CALLING — the console's actual job.

    Deliberately coarse tiers: a coder model first, a modern instruct model second, everything
    else last. Size breaks ties INSIDE a tier and never outranks it — a 9B general chat model is
    not a better agent than a 7B coder.
    """
    mid = str(m.get("id") or "").lower()
    if any(h in mid for h in _CODER_HINTS):
        return TOOL_RANK_CODER
    if any(h in mid for h in _TOOL_HINTS):
        return TOOL_RANK_CHAT
    return TOOL_RANK_OTHER


def _bad_on_this_host() -> set[str]:
    """Ids this host already proved it cannot load. A missing memory module is never fatal."""
    try:
        import model_verdicts

        return model_verdicts.bad_ids()
    except Exception:  # noqa: BLE001
        return set()


def _chats(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bad = _bad_on_this_host()
    return [
        m
        for m in models
        if m.get("kind") == "chat"
        and m.get("runnable")
        and m.get("id")
        and str(m.get("id")) not in bad
    ]


def ranked(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every usable brain, best first: PREFER_IDS order, then tool rank, then size."""
    chats = _chats(models)
    by_id = {m["id"]: m for m in chats}
    out: list[dict[str, Any]] = []
    for pid in PREFER_IDS:
        if pid in by_id and by_id[pid] not in out:
            out.append(by_id[pid])
    rest = [m for m in chats if m not in out]
    rest.sort(key=lambda m: (tool_rank(m), int(m.get("bytes") or 0)), reverse=True)
    return out + rest


def candidates(
    models: list[dict[str, Any]],
    prefer_ram: bool = False,
    avail_bytes: int | None = None,
) -> list[str]:
    """Ordered ids to try as the brain: the default first, then every fallback.

    This is what lets a console that meets a model it cannot load move on to the next brain
    instead of staying dark.
    """
    ids = [str(m["id"]) for m in ranked(models)]
    if prefer_ram:
        chosen = ram_choice(
            models, avail_ram_bytes() if avail_bytes is None else int(avail_bytes)
        )
        if chosen and chosen in ids:
            ids.remove(chosen)
            ids.insert(0, chosen)
    return ids


def avail_ram_bytes() -> int:
    """Available physical RAM, or 0 when it cannot be read (0 = 'unknown', never a refusal)."""
    try:
        from engine import available_ram_bytes

        return int(available_ram_bytes())
    except Exception:
        return 0


def vram_free_mib() -> int:
    """This host's free VRAM (0 when there is none). Lazy + fail-safe: registry stays GPU-agnostic."""
    try:
        import perf

        return int(perf.gpu_free_mib())
    except Exception:
        return 0


def _ram_floor_bytes() -> int:
    """Half of INSTALLED RAM — a deterministic floor under the momentary-free measurement.

    Without this the chosen brain depends on what was running a minute ago (a 14B unload leaves
    the page cache looking busy), which makes the default un-reproducible across boots.
    """
    for getter in ("total_ram_bytes",):
        try:
            mod = __import__("engine")
            if hasattr(mod, getter):
                return int(getattr(mod, getter)()) // 2
        except Exception:
            pass
    try:
        import psutil

        return int(psutil.virtual_memory().total) // 2
    except Exception:
        return 0


def prefer_by_ram() -> bool:
    try:
        from paths import CONSOLE_JSON

        return bool(json.loads(CONSOLE_JSON.read_text(encoding="utf-8")).get("prefer_by_ram"))
    except (OSError, json.JSONDecodeError, ImportError):
        return False


def ram_choice(
    models: list[dict[str, Any]],
    avail_bytes: int,
    headroom: int = RAM_HEADROOM,
    factor: float = RAM_FIT_FACTOR,
    vram_mib: int | None = None,
) -> str | None:
    """Best tool-capable brain this host can actually RUN WELL; None when RAM/sizes are unknown.

    Two properties this gate must have to be worth trusting:

      * deterministic per machine — the budget is max(measured available, half of installed RAM),
        so the default brain cannot swing because another program was running a minute ago;
      * GPU-aware — a model that does not fit VRAM falls back to CPU, which measured ~25x slower
        for prompt eval on this host (80 tok/s CPU vs 3,246 tok/s on a VRAM-resident model). So
        models that fit VRAM fully win over partially-offloaded ones before tool rank matters.
    """
    sized = [m for m in _chats(models) if int(m.get("bytes") or 0) > 0]
    if avail_bytes <= 0 or not sized:
        return None
    budget = max(int(avail_bytes), _ram_floor_bytes())
    fits = [m for m in sized if int(m["bytes"]) * factor + headroom <= budget]
    if not fits:
        # Nothing fits comfortably: the smallest is still the best chance of booting at all.
        return min(sized, key=lambda m: int(m["bytes"]))["id"]
    vram = vram_free_mib() if vram_mib is None else int(vram_mib)
    if vram > 0:
        try:
            import perf

            on_gpu = [m for m in fits if perf.plan_ngl(int(m["bytes"]), vram)[0] >= perf.FULL_LAYERS]
            if on_gpu:
                fits = on_gpu
        except Exception:
            pass
    # Best TOOL model the host can hold; among equals, the biggest. Ranks are coarse on purpose
    # (see tool_rank) — picking a bigger-but-weaker agent would be the wrong trade.
    return max(fits, key=lambda m: (tool_rank(m), int(m["bytes"])))["id"]


def _fits(
    model_id: str,
    models: list[dict[str, Any]],
    avail_bytes: int,
    headroom: int = RAM_HEADROOM,
    factor: float = RAM_FIT_FACTOR,
) -> bool:
    """Would this model fit here? Unknown sizes/RAM return True — never move a human's pin blind."""
    rec = next((m for m in models if m.get("id") == model_id), None)
    size = int((rec or {}).get("bytes") or 0)
    if not rec or size <= 0 or avail_bytes <= 0:
        return True
    return size * factor + headroom <= avail_bytes


def pick_default(
    models: list[dict[str, Any]],
    prefer_ram: bool = False,
    avail_bytes: int | None = None,
) -> str | None:
    """Deterministic default (PREFER_IDS, else smallest). RAM-auto is opt-in via `prefer_ram`.

    Keeping this deterministic matters: callers that want config-driven RAM picking pass
    `prefer_ram=prefer_by_ram()` (registry.upsert does), so plain callers and tests never get a
    surprise model just because console.json happens to enable the flag.
    """
    if prefer_ram:
        chosen = ram_choice(
            models, avail_ram_bytes() if avail_bytes is None else int(avail_bytes)
        )
        if chosen:
            return chosen
    order = ranked(models)
    return str(order[0]["id"]) if order else None


def _present(m: dict[str, Any]) -> bool:
    """Only advertise a model whose weights are really on this machine.

    A stick that walks onto another host must not keep offering a brain that lives in that
    host's home CAS: RAM-auto would pick it and the boot would fail far from home. Records
    for missing files are dropped here and re-added by the next scan once the file is back.
    """
    from pathlib import Path as _Path

    p = str(m.get("path") or "")
    return (not p) or _Path(p).is_file()


def _read_registry(path: Path) -> dict[str, Any] | None:
    """Parsed registry at *path*, or None when the file is absent, torn or not an object."""
    if not path.is_file():
        return None
    try:
        data = json.loads(read_file_text(path))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def load() -> dict[str, Any]:
    """Read registry.json, falling back to registry.json.bak instead of losing every model.

    A yanked stick or a power cut can leave a torn/zero-length registry.json. Returning an empty
    registry there makes all models silently disappear, so the previous good copy is tried and the
    outcome is left in load_status() for the caller to surface. Empty is only ever returned when
    nothing readable exists at all — and both files existing but unreadable is logged loudly.
    """
    data = _read_registry(REGISTRY_PATH)
    if data is not None:
        LOAD_STATUS.update({"recovered": False, "source": str(REGISTRY_PATH), "reason": "", "at": time.time()})
        return data
    bak = registry_backup_path()
    if REGISTRY_PATH.is_file():
        _log(f"registry.json is unreadable (torn or not JSON) — trying {bak.name}")
        recovered = _read_registry(bak)
        if recovered is not None:
            _log(f"RECOVERED {len(recovered.get('models') or [])} models from {bak.name}; "
                 "registry.json is torn and will be rewritten on the next save")
            LOAD_STATUS.update({"recovered": True, "source": str(bak),
                                "reason": "registry.json unreadable, used backup", "at": time.time()})
            return recovered
    if REGISTRY_PATH.is_file() or bak.is_file():
        _log(f"LOUD: registry unreadable and no usable backup at {bak} — "
             "reporting an EMPTY registry (all models disappear until a rescan)")
        LOAD_STATUS.update({"recovered": False, "source": "", "reason": "registry.json and .bak both unreadable",
                            "at": time.time()})
    else:
        LOAD_STATUS.update({"recovered": False, "source": "", "reason": "no registry yet", "at": time.time()})
    return {"signature": SIGNATURE, "selected": None, "models": []}


def save(data: dict[str, Any]) -> None:
    ensure_dirs()
    SAVE.mkdir(parents=True, exist_ok=True)
    data["signature"] = SIGNATURE
    text = json.dumps(data, indent=2)
    # Keep the last known-good file as registry.json.bak before overwriting it: that copy is what
    # load() recovers from when the write itself is interrupted.
    bak = registry_backup_path()
    if REGISTRY_PATH.is_file():
        try:
            prev = read_file_text(REGISTRY_PATH)
            if prev.strip():
                atomic_write_text(bak, prev)
        except OSError:
            pass
    atomic_write_text(REGISTRY_PATH, text)


# A selection an operator made on purpose. Anything else is this machine re-tuning itself.
PINNED_SOURCES = {"manual", "operator", "steward"}
OWNED_SOURCE = "lygo_vault"


def _owned_wins(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """An owned copy must survive a rescan of the store it was imported from.

    The scanner reports whatever store it finds, and an imported CAS is one of them, so its record
    carries that store's path. Once the kit owns a copy in its own vault, a rescan must not hand the
    model back to the foreign store: the vault is what makes this kit standalone. Losing it silently
    is not hypothetical - a refresh run put every owned path back into an Ollama blob folder.
    """
    if str(existing.get("source")) != OWNED_SOURCE:
        return {**existing, **incoming}
    merged = {**existing, **incoming}
    for key in ("path", "gguf", "mmproj"):
        value = existing.get(key)
        if value and Path(str(value)).is_file():
            merged[key] = value
    for key in ("source", "sha256", "bytes", "manifest", "sidecars"):
        if existing.get(key):
            merged[key] = existing[key]
    return merged


def upsert(models: list[dict[str, Any]], selected: str | None = None) -> dict[str, Any]:
    data = load()
    by_id = {m.get("id"): m for m in data.get("models") or [] if m.get("id")}
    for m in models:
        if m.get("id"):
            by_id[m["id"]] = _owned_wins(by_id.get(m["id"]) or {}, m)
    data["models"] = [m for m in by_id.values() if _present(m)]
    want_ram = prefer_by_ram()
    avail = avail_ram_bytes() if want_ram else 0
    if selected:
        data["selected"] = selected
        data["selected_source"] = "manual"
    else:
        pinned = data.get("selected")
        manual = bool(pinned) and data.get("selected_source") in PINNED_SOURCES
        # Re-pick unless a human switched it AND their pick still fits this host: that is what lets
        # the same stick re-tune itself when it walks onto a bigger or smaller machine.
        ids_now = {m.get("id") for m in data["models"]}
        if (
            not pinned
            or not manual
            or pinned not in ids_now
            or (want_ram and not _fits(pinned, data["models"], avail))
        ):
            auto = pick_default(data["models"], prefer_ram=want_ram, avail_bytes=avail)
            if auto:
                data["selected"] = auto
                data["selected_source"] = "ram" if want_ram and avail > 0 else "auto"
    lost = {m.get("id") for m in by_id.values() if not _present(m)}
    if data.get("selected") in lost:
        # The pinned brain's weights left this machine: re-pick here, because the branch above
        # cannot — an explicit `selected=` call sets the pin, and that pin now dangles.
        auto = pick_default(data["models"], prefer_ram=want_ram, avail_bytes=avail)
        if auto:
            data["selected"] = auto
            data["selected_source"] = "ram" if want_ram and avail > 0 else "auto"
    save(data)
    return data


def get(model_id: str) -> dict[str, Any] | None:
    for m in load().get("models") or []:
        if m.get("id") == model_id:
            return m
    return None
