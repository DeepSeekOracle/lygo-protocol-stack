"""LYGO Perf — host-adaptive launch profile for the engine.

One stick, many hosts. This module decides where the weights actually run: as many
layers as the host GPU can hold, on every CPU core the host offers, or honestly on
CPU alone when the engine build has no GPU backend at all.

Contract:
- the kit config is the operator's word. An integer ngl/threads is a PIN and is
  honored exactly as written, 0 included. The token "auto" (or a missing key) hands
  the decision to this module.
- a GPU is only claimed when it is proven: the engine build must ship a backend DLL
  and the engine's own --list-devices must name a device. No proof, no claim.
- every outcome is remembered per host + model in data/perf.json, so the next boot on
  that host starts where it last succeeded instead of spending its time again.

Placement changes speed only. Weights, precision and semantics never change here.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import atomicio
from paths import DATA, ENGINE_DIR

GIB = 1024**3
MIB = 1024**2
VRAM_RESERVE_MIB = 1024  # the desktop compositor and driver keep their room
FULL_LAYERS = 99  # llama.cpp's idiom for "all layers"
MIN_PARTIAL_LAYERS = 6  # below this the transfer costs more than it buys
THREAD_MIN, THREAD_MAX = 4, 16
DEVICE_TTL_S = 300
SLOW_ATTEMPT_S = 150  # a launch that burns this long is hung, not merely tight
HOST_LIMIT = 12
SIGNATURE = "Δ9Φ963-LYGO-PERF-HOST-ADAPTIVE-v1"
PERF_JSON = DATA / "perf.json"
DEVICE_BACKENDS = ("vulkan", "cuda", "sycl", "hip", "opencl", "metal", "kompute")

REMEDY = {
    "engine_cpu_only": 'engine/ has no GPU backend installed — scripts/fetch_engine.ps1 -Backend cuda (NVIDIA) or -Backend vulkan (any GPU) adds one; it runs only after a self-test passes on this host',
    "no_gpu_device": "the engine build has a GPU backend but reports no device — update the GPU driver",
    "no_vram_headroom": "the GPU has no free VRAM to spare — close other GPU applications",
    "vram_too_small_for_partial_offload": "the GPU is too small for this model — choose a smaller model",
    "pinned_by_config": 'config/console.json pins ngl — set it to "auto" to let the host decide',
    "remembered_from_this_host": "this host failed with more layers before — delete data/perf.json to retry",
    "gpu_disabled_by_config": 'config/console.json sets gpu — set it back to "auto" to let the host decide',
    "backend_crashed_on_this_host": "a GPU backend crashed this engine on this host — the stick stays on CPU here; the verdict is remembered, and a driver update or a fresh fetch clears it",
    "backend_failed_on_this_host": "this host already failed that GPU backend — delete data/perf.json to retry it",
    "backend_sees_no_device": "the backend loaded but named no device — check the GPU driver",
    "backend_activation_failed": "the backend could not be applied to engine/ — check free space and permissions",
    "backend_self_test_incomplete": "the backend did not finish a probe model load in time — it was left off",
    "backend_layer_error": "the backend layer itself failed — the kit ran the shipped CPU engine",
    "backend_not_proven": "no installed GPU backend has passed a self-test on this host yet",
}

_DEV_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def engine_path(where: Any = None) -> Path:
    """The engine directory in play: an explicit one, else whatever is active for this host."""
    if where:
        return Path(where)
    try:
        import paths

        return Path(paths.engine_dir())
    except Exception:
        return Path(ENGINE_DIR)


def engine_backends(where: Any = None) -> list[str]:
    """GPU backends this engine build actually ships — a file scan, not a hope."""
    d = engine_path(where)
    try:
        if not d.is_dir():
            return []
        names = [f.name.lower() for f in d.iterdir() if f.is_file()]
    except OSError:
        return []
    return sorted(b for b in DEVICE_BACKENDS if any(n.startswith(f"ggml-{b}") for n in names))


_DEVICE_RE = re.compile(
    r"^\s*(?P<id>[A-Za-z0-9_]+):\s*(?P<name>.+?)\s*\((?P<total>\d+)\s*MiB"
    r"(?:,\s*(?P<free>\d+)\s*MiB free)?\)\s*$"
)


def parse_devices(text: str) -> list[dict[str, Any]]:
    """Parse `llama-server --list-devices`: 'Vulkan0: NVIDIA GeForce RTX 4060 Ti (7949 MiB, 7181 MiB free)'."""
    out: list[dict[str, Any]] = []
    for line in (text or "").splitlines():
        m = _DEVICE_RE.match(line)
        if not m:
            continue
        total = int(m.group("total"))
        out.append(
            {
                "id": m.group("id"),
                "name": m.group("name").strip(),
                "total_mib": total,
                "free_mib": int(m.group("free")) if m.group("free") else total,
            }
        )
    return out


def engine_devices(exe: Any = None, *, timeout: int = 25, refresh: bool = False) -> list[dict[str, Any]]:
    """Ask the engine itself which devices it sees. Never raises: [] means none we can use.

    refresh=True is required right after applying a backend DLL: the cache key is the exe
    path and mtime, and neither changes when a DLL lands next to it, so the pre-activation
    "no devices" answer would otherwise outlive the activation and reject a good backend.
    """
    path = Path(exe) if exe else engine_path() / "llama-server.exe"
    try:
        if not path.is_file():
            return []
        key = f"{path}|{path.stat().st_mtime_ns}"
    except OSError:
        return []
    if refresh:
        _DEV_CACHE.pop(key, None)
    hit = _DEV_CACHE.get(key)
    if hit and (time.time() - hit[0]) < DEVICE_TTL_S:
        return hit[1]
    devs: list[dict[str, Any]] = []
    try:
        r = subprocess.run(
            [str(path), "--list-devices"],
            cwd=str(path.parent),
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
        devs = parse_devices((r.stdout or "") + "\n" + (r.stderr or ""))
    except (OSError, subprocess.SubprocessError):
        devs = []
    _DEV_CACHE[key] = (time.time(), devs)
    return devs


def best_device(devs: Any) -> dict[str, Any] | None:
    """The device with the most free VRAM — where the layers would go."""
    items = [d for d in (devs or []) if isinstance(d, dict)]
    if not items:
        return None
    return max(items, key=lambda d: int(d.get("free_mib") or 0))


def gpu_free_mib() -> int:
    """Free VRAM on the best device, 0 when there is none. Never raises, never over-claims."""
    try:
        dev = best_device(engine_devices())
        return int((dev or {}).get("free_mib") or 0)
    except Exception:
        return 0


def auto_threads() -> int:
    """Every core the host offers, one left for the console, capped for sanity."""
    n = os.cpu_count() or 4
    return max(THREAD_MIN, min(THREAD_MAX, n - 1 if n > THREAD_MIN else n))


def clamp_threads(threads: Any) -> int:
    """CPU threads for llama-server: a pin is honored, else the host's own cores."""
    if threads is None:
        return auto_threads()
    try:
        nth = int(threads)
    except (TypeError, ValueError):
        return auto_threads()
    return max(2, min(THREAD_MAX, nth or auto_threads()))


def plan_ngl(model_bytes: int, free_mib: int, *, reserve_mib: int = VRAM_RESERVE_MIB) -> tuple[int, str]:
    """How many of 99 layers fit in the free VRAM. Returns (ngl, reason)."""
    if free_mib <= 0:
        return 0, "no_gpu_device"
    avail = int(free_mib) - int(reserve_mib)
    if avail <= 0:
        return 0, "no_vram_headroom"
    if model_bytes <= 0:
        return FULL_LAYERS, "model_size_unknown_full_offload"
    need = int(model_bytes / MIB * 1.12) + 256  # weights + KV/compute buffers
    if need <= avail:
        return FULL_LAYERS, "fits_vram"
    ngl = min(FULL_LAYERS - 1, int(FULL_LAYERS * avail / need))
    if ngl < MIN_PARTIAL_LAYERS:
        return 0, "vram_too_small_for_partial_offload"
    return ngl, f"partial_offload_{ngl}_of_{FULL_LAYERS}"


def _legacy_ngl(hw: dict[str, Any]) -> int:
    """Pre-adaptive rule, kept for callers that cannot see a device list."""
    vram = int(hw.get("vram_bytes") or 0)
    if vram >= 4 * GIB:
        return FULL_LAYERS
    if vram >= 2 * GIB:
        return 20
    return 0


def host_id() -> str:
    """This PC, for backend verdicts: no model, no live memory — the machine itself."""
    try:
        return f"{platform.node()}|{os.cpu_count() or 0}"
    except Exception:
        return "unknown-host"


def fingerprint(hw: dict[str, Any], device: dict[str, Any] | None, model_id: str) -> str:
    """Host identity: a stick carried to another PC must not inherit this PC's verdict.

    RAM is rounded to whole GiB because 'available' memory moves every second.
    """
    ram_gib = round(int(hw.get("ram_bytes") or 0) / GIB)
    parts = [
        platform.node(),
        str(os.cpu_count() or 0),
        str(ram_gib),
        str((device or {}).get("name") or ""),
        str((device or {}).get("total_mib") or 0),
        str(model_id or ""),
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def _load_store() -> dict[str, Any]:
    try:
        data = json.loads(atomicio.read_text(PERF_JSON, errors="replace"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def host_record(fp: str) -> dict[str, Any] | None:
    rec = (_load_store().get("hosts") or {}).get(fp)
    return rec if isinstance(rec, dict) else None


def remember_host(fp: str, **fields: Any) -> dict[str, Any]:
    """Merge one host's launch outcome. Atomic write, bounded history, never raises."""
    store = _load_store()
    hosts = store.get("hosts")
    if not isinstance(hosts, dict):
        hosts = {}
    known = {k: v for k, v in (hosts.get(fp) or {}).items() if isinstance(v, (str, int, float, bool))}
    entry = {**known, **fields, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    hosts[fp] = entry
    if len(hosts) > HOST_LIMIT:
        for k, _ in sorted(hosts.items(), key=lambda kv: str(kv[1].get("at") or ""))[: len(hosts) - HOST_LIMIT]:
            hosts.pop(k, None)
    store["hosts"] = hosts
    store["signature"] = SIGNATURE
    try:
        PERF_JSON.parent.mkdir(parents=True, exist_ok=True)
        atomicio.atomic_write_text(PERF_JSON, json.dumps(store, indent=2, sort_keys=True) + "\n")
    except OSError:
        pass
    return entry


def _pin_int(value: Any) -> int | None:
    """An integer pin, or None. "auto", "", junk and a typo all mean "let the host decide"."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def resolve(*, lim: dict[str, Any], hw: dict[str, Any], model_bytes: int, model_id: str = "") -> dict[str, Any]:
    """Probe facts + config pins + this host's memory -> the launch profile."""
    devs = hw.get("devices")
    known = devs is not None
    devices = [d for d in (devs or []) if isinstance(d, dict)]
    backends = [str(b) for b in (hw.get("backends") or [])] if known else []
    device = best_device(devices)
    vram_free_mib = int(device.get("free_mib") or 0) if device else int((hw.get("vram_bytes") or 0) / MIB)
    vram_total_mib = int(device.get("total_mib") or 0) if device else 0
    fp = fingerprint(hw, device, model_id)
    record = host_record(fp)

    pin_ngl = _pin_int(lim.get("ngl"))
    pin_threads = _pin_int(lim.get("threads"))
    fallback = False
    if pin_ngl is not None:
        ngl, reason, source = int(pin_ngl), "pinned_by_config", "pin"
    elif not known:
        ngl, reason, source = _legacy_ngl(hw), "vram_only_thresholds", "auto"
    elif not backends:
        ngl, reason, source = 0, str(hw.get("gpu_reason") or "engine_cpu_only"), "auto"
    elif device is None:
        ngl, reason, source = 0, "no_gpu_device", "auto"
    else:
        ngl, reason = plan_ngl(model_bytes, vram_free_mib)
        source = "auto"
    # A GPU is only planned when backends.py has proven one *on this host*: devices seen
    # by a candidate build that failed its self-test must not become layers.
    if int(ngl) > 0 and known and hw.get("gpu_ok") is False:
        ngl, source, reason = 0, "auto", str(hw.get("gpu_reason") or "backend_not_proven")
    if source == "auto" and record and record.get("ngl") is not None:
        remembered = int(record["ngl"])
        if remembered < ngl:
            ngl, source, fallback = remembered, "host_record", True
            reason = f"remembered_from_this_host ({record.get('note') or 'earlier attempt failed'})"

    threads = int(pin_threads) if pin_threads is not None else auto_threads()
    mode = "cpu" if int(ngl) <= 0 else ("gpu_full" if int(ngl) >= FULL_LAYERS else "gpu_partial")
    return {
        "ngl": int(ngl),
        "threads": int(threads),
        "mode": mode,
        "source": source,
        "reason": reason,
        "threads_source": "pin" if pin_threads is not None else "auto",
        "device": (device or {}).get("name") or "",
        "device_id": (device or {}).get("id") or "",
        "vram_free_mib": vram_free_mib,
        "vram_total_mib": vram_total_mib,
        "backends": backends,
        "reserve_mib": VRAM_RESERVE_MIB,
        "host": fp,
        "backend": str(hw.get("backend") or "cpu"),
        "engine_dir": str(hw.get("engine_dir") or ""),
        "gpu_ok": bool(hw.get("gpu_ok")),
        "fallback": fallback,
        "known_devices": known,
        "signature": SIGNATURE,
    }


def ladder(ngl: Any) -> list[int]:
    """Launch attempts, best first, CPU last: a GPU that cannot load must not kill the brain."""
    first = max(0, int(ngl or 0))
    out = [first]
    for cand in (first // 2, MIN_PARTIAL_LAYERS + 2, 0):
        if 0 <= cand < out[-1]:
            out.append(cand)
    return out


def report(state: dict[str, Any] | None = None) -> dict[str, Any]:
    """The /api/health view of the launch profile. Never raises: health must always answer."""
    try:
        st = state if isinstance(state, dict) else {}
        pl = st.get("lygo_engine") if isinstance(st.get("lygo_engine"), dict) else {}
        prof = pl.get("perf") if isinstance(pl.get("perf"), dict) else {}
        hw = pl.get("hardware") if isinstance(pl.get("hardware"), dict) else {}
        llama = pl.get("llama") if isinstance(pl.get("llama"), dict) else {}
        if not prof:
            prof = {
                "ngl": llama.get("ngl"),
                "threads": llama.get("threads") if llama.get("threads") is not None else auto_threads(),
                "mode": "unknown",
                "source": "unplanned",
                "reason": "engine_not_planned_yet",
                "device": "",
                "backends": engine_backends(),
                "host": "",
                "fallback": False,
                "vram_free_mib": 0,
                "vram_total_mib": 0,
            }
        mode = str(prof.get("mode") or "unknown")
        out: dict[str, Any] = {
            "mode": mode,
            "ngl": prof.get("ngl"),
            "threads": prof.get("threads"),
            "device": prof.get("device") or "",
            "vram_free_mib": prof.get("vram_free_mib") or 0,
            "vram_total_mib": prof.get("vram_total_mib") or 0,
            "ram_gib": hw.get("ram_gib") or 0,
            "cpu_threads": auto_threads(),
            "backends": prof.get("backends") or [],
            "source": prof.get("source"),
            "reason": prof.get("reason"),
            "fallback": bool(prof.get("fallback")),
            "host": prof.get("host") or "",
            "signature": SIGNATURE,
        }
        remedy = REMEDY.get(str(prof.get("reason") or ""))
        if remedy:
            out["remedy"] = remedy
        if st.get("perf_fallback"):
            out["launch_fallback"] = st["perf_fallback"]
        # Effective beats planned: after a fallback, health must report what is actually running.
        eff = prof.get("effective") if isinstance(prof.get("effective"), dict) else {}
        out["planned"] = {"mode": mode, "ngl": prof.get("ngl"), "threads": prof.get("threads")}
        out["backend"] = prof.get("backend") or ""
        out["engine_dir"] = prof.get("engine_dir") or ""
        if eff:
            out["effective"] = eff
            if eff.get("ngl") is not None:
                n = int(eff["ngl"] or 0)
                out["ngl"] = n
                mode = "cpu" if n <= 0 else ("gpu_full" if n >= FULL_LAYERS else "gpu_partial")
                out["mode"] = mode
            if eff.get("threads") is not None:
                out["threads"] = eff["threads"]
            for key in ("backend", "engine_dir"):
                if eff.get(key):
                    out[key] = eff[key]
        try:
            import backends as _backends

            out["backend_layer"] = _backends.report()
        except Exception:
            pass
        out["api_boost"] = (
            "CPU-only local inference is the slow path — an API brain (/api/brain) answers faster"
            if mode == "cpu"
            else ""
        )
        return out
    except Exception as exc:  # a broken perf record must not take health down with it
        return {"mode": "unknown", "error": f"{type(exc).__name__}: {exc}"}
