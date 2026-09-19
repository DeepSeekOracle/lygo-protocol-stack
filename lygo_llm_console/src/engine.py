from __future__ import annotations

import ctypes
import json
import os
import signal
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import atomicio
import perf
from paths import ENGINE_DIR, LOGS, PID_PATH, console_limits, ensure_dirs, engine_dir

ENGINE_LOCK = threading.Lock()
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JobObjectExtendedLimitInformation = 9

FORBIDDEN_SNIP = "projects\\ollama\\lib\\ollama"


def binary_forbidden(path: Path) -> bool:
    s = str(path).replace("/", "\\").lower()
    return FORBIDDEN_SNIP in s


def resolve_binary() -> Path | None:
    # engine_dir() names a proven GPU backend build when one is active (backends.py),
    # and the shipped engine otherwise.
    cands = [
        engine_dir() / "llama-server.exe",
        ENGINE_DIR / "llama-server.exe",
        Path(r"U:\LYGO\projects\lygo-llm\engine\llama-server.exe"),
        Path(r"F:\LYGO\projects\lygo-llm\engine\llama-server.exe"),
    ]
    for c in cands:
        if c.is_file() and not binary_forbidden(c):
            return c
    return None


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def available_ram_bytes() -> int:
    st = MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)) == 0:
        return 0
    return int(st.ullAvailPhys)


def ram_ok(model_bytes: int, headroom: int = 2 * 1024**3) -> bool:
    avail = available_ram_bytes()
    if avail <= 0:
        return True
    return avail >= int(model_bytes) + headroom


def _clean_env() -> dict[str, str]:
    keys = ("PATH", "SystemRoot", "COMSPEC", "PATHEXT", "TEMP", "TMP", "USERNAME", "USERPROFILE", "WINDIR", "NUMBER_OF_PROCESSORS")
    env = {k: os.environ[k] for k in keys if k in os.environ}
    return env


def _assign_job(pid: int) -> Any:
    k32 = ctypes.windll.kernel32
    try:
        handle = k32.CreateJobObjectW(None, None)
        if not handle:
            return None
        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", ctypes.c_uint32),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", ctypes.c_uint32),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", ctypes.c_uint32),
                ("SchedulingClass", ctypes.c_uint32),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [("a", ctypes.c_uint64), ("b", ctypes.c_uint64), ("c", ctypes.c_uint64),
                        ("d", ctypes.c_uint64), ("e", ctypes.c_uint64), ("f", ctypes.c_uint64)]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        k32.SetInformationJobObject(handle, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info))
        proc = k32.OpenProcess(0x1F0FFF, False, pid)
        if proc:
            k32.AssignProcessToJobObject(handle, proc)
            k32.CloseHandle(proc)
        return handle
    except Exception:
        return None


@dataclass
class Runner:
    port: int
    gguf: str
    kind: str
    proc: subprocess.Popen
    api_key: str
    job: Any = None
    alias: str = ""
    log_path: str = ""
    log_handle: Any = None
    launch_sig: str = ""


_runners: dict[int, Runner] = {}

# Boots of one port are serialised per port, and _runners / engine.pid.json are guarded by one
# registry lock. ENGINE_LOCK is left exactly as it was: callers hold it around a status
# snapshot, and holding it across a 120 s boot wait would freeze them.
_REGISTRY_LOCK = threading.RLock()
_PORT_LOCKS: dict[int, threading.RLock] = {}
_PORT_LOCKS_GUARD = threading.Lock()


def _port_lock(port: int) -> threading.RLock:
    with _PORT_LOCKS_GUARD:
        lock = _PORT_LOCKS.get(int(port))
        if lock is None:
            lock = _PORT_LOCKS[int(port)] = threading.RLock()
        return lock


DEFAULT_LOG_KEEP_BYTES = 5 * 1024 * 1024
LOG_KEEP_ENV = "LYGO_ENGINE_LOG_MAX_BYTES"


def _log_keep_bytes() -> int:
    """Newest bytes of each server log to keep; LYGO_ENGINE_LOG_MAX_BYTES=0 disables rotation."""
    raw = os.environ.get(LOG_KEEP_ENV, "").strip()
    if raw:
        try:
            return max(0, int(float(raw)))
        except ValueError:
            pass
    return DEFAULT_LOG_KEEP_BYTES


def _open_engine_log(port: int) -> Any:
    """Open this port's server log for append, dropping all but the newest LOG_KEEP bytes.

    The log is the only record of why a launch failed, so it is rotated rather than deleted:
    the tail survives, the head does not. Left alone it grew without bound across restarts.
    """
    path = LOGS / f"llama-server-{port}.log"
    keep = _log_keep_bytes()
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    if keep and size > keep:
        try:
            with open(path, "r+b") as fh:
                fh.seek(size - keep)
                tail = fh.read(keep)
                fh.seek(0)
                fh.write(tail)
                fh.truncate()
        except OSError:
            pass
    return open(path, "ab", buffering=0)


def _close_log(handle: Any) -> None:
    """Close a server log handle exactly once: on Windows the open handle locks the log file."""
    if handle is None:
        return
    try:
        handle.close()
    except Exception:
        pass


def _log_note(message: str) -> None:
    """Best-effort one-liner into save/logs/engine.log - why the engine refused to do something."""
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with open(LOGS / "engine.log", "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except OSError:
        pass


def kill_tree(pid: int) -> None:
    """Kill pid and everything it spawned (taskkill /T /F; job objects only cover our own jobs)."""
    if not pid:
        return
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(int(pid))], capture_output=True, timeout=20)
            return
        except Exception:
            pass
    try:
        os.kill(int(pid), signal.SIGTERM)
    except Exception:
        pass


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def process_image_name(pid: int) -> str | None:
    """Full image path of a live pid, or None when it cannot be queried (gone, or access denied)."""
    if os.name != "nt" or not pid or int(pid) <= 0:
        return None
    try:
        k32 = ctypes.windll.kernel32
        handle = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not handle:
            return None
        try:
            size = ctypes.c_uint32(32768)
            buf = ctypes.create_unicode_buffer(int(size.value))
            if not k32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return None
            return buf.value or None
        finally:
            k32.CloseHandle(handle)
    except Exception:
        return None


def pid_is_our_engine(pid: int) -> bool:
    """True only when pid is alive AND its image really is our llama-server.exe.

    A recorded pid is a guess: the process may have exited, the file may be stale from a
    previous boot, or Windows may have reused the number for something else entirely.
    """
    image = process_image_name(pid)
    return bool(image) and Path(image).name.lower() == "llama-server.exe"


def kill_pid(pid: int) -> bool:
    """Kill a pid recorded in the pid file, but only after proving it is really our engine.

    Killing a pid read off disk blind is how a console takes down a browser or the shell that
    started it; when ownership cannot be verified the kill is skipped and the reason is logged.
    """
    if not pid_is_our_engine(pid):
        image = process_image_name(pid)
        _log_note(f"refused to kill pid {pid}: not a verified llama-server.exe (image={image or 'unqueryable'})")
        return False
    kill_tree(pid)
    return True


def kill_recorded_pids() -> dict[str, Any]:
    """Stop every engine pid in engine.pid.json, skipping any pid we cannot verify.

    This is the safe consumer of the pid file: it exists so a stop path never has to trust a
    pid it read off the stick. Entries that fail verification are reported, never killed.
    """
    try:
        blob = json.loads(atomicio.read_text(PID_PATH))
    except Exception:
        return {"ok": True, "checked": 0, "killed": [], "skipped": []}
    killed: list[int] = []
    skipped: list[dict[str, Any]] = []
    for key, entry in (blob.items() if isinstance(blob, dict) else []):
        try:
            pid = int((entry or {}).get("pid") or 0)
        except (AttributeError, TypeError, ValueError):
            pid = 0
        if not pid:
            continue
        if kill_pid(pid):
            killed.append(pid)
        else:
            skipped.append({"port": key, "pid": pid, "reason": "unverified_pid"})
    return {"ok": True, "checked": len(killed) + len(skipped), "killed": killed, "skipped": skipped}


def stop_runner(runner: Runner | None, timeout_s: float = 8.0) -> None:
    if runner is None:
        return
    proc = runner.proc
    if proc.poll() is None:
        try:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            proc.wait(timeout=timeout_s)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        try:
            proc.wait(timeout=5)
        except Exception:
            # A killed parent can still leave children behind, and the job object below is no
            # help once the console itself already sits in a job: walk the tree as a fallback.
            kill_tree(proc.pid)
    if runner.job:
        try:
            ctypes.windll.kernel32.CloseHandle(runner.job)
        except Exception:
            pass
        runner.job = None
    # The log handle is ours, not the server's: leaving it open is what locked the log file
    # (no delete/rename on Windows) and leaked one handle per restart.
    _close_log(getattr(runner, "log_handle", None))
    runner.log_handle = None
    with _REGISTRY_LOCK:
        _runners.pop(runner.port, None)
    _write_pids()


def stop_port(port: int) -> None:
    with _port_lock(port):
        with _REGISTRY_LOCK:
            r = _runners.get(int(port))
        stop_runner(r)


def clamp_ctx(ctx: int | None, ctx_max: int | None = None) -> int:
    """Context window: model-native (else the config default), capped by the config ctx_max."""
    lim = console_limits()
    cap = max(512, int(ctx_max if ctx_max is not None else lim["ctx_max"]))
    return max(512, min(int(ctx or lim["ctx_default"]), cap))


def clamp_threads(threads: int | None) -> int:
    """CPU threads: a pin when given, else every core the host offers; always 2..16."""
    lim = console_limits()
    nth = threads if threads is not None else lim["threads"]
    return perf.clamp_threads(nth)


KV_TYPES = ("f16", "q8_0", "q4_0")


def clean_kv_type(value: object) -> str:
    """A KV cache type the engine actually accepts, else '' (= let llama.cpp decide).

    Only these three are ever sent: a typo from config must not become an invalid launch argument,
    because a rejected flag means no brain at all rather than a slower one.
    """
    t = str(value or "").strip().lower()
    return t if t in KV_TYPES else ""


def spawn_runner(
    *,
    port: int,
    gguf: Path,
    kind: str,
    mmproj: Path | None,
    ctx: int,
    ngl: int,
    alias: str,
    api_key: str,
    threads: int | None = None,
    mmap: bool = True,
    flash_attn: bool = False,
    kv_type: str = "",
    batch: int = 0,
    ubatch: int = 0,
    skip_ram_gate: bool = False,
    ctx_max: int | None = None,
) -> Runner:
    exe = resolve_binary()
    if exe is None:
        raise FileNotFoundError("llama-server.exe missing under engine/")
    if binary_forbidden(exe):
        raise PermissionError("forbidden_ollama_nested_binary")
    gguf = Path(gguf)
    if not gguf.is_file():
        raise FileNotFoundError(str(gguf))
    try:
        model_bytes = gguf.stat().st_size
    except OSError:
        model_bytes = 0
    if not skip_ram_gate and not ram_ok(model_bytes):
        raise MemoryError(
            json.dumps({"brain": "ram_refused", "avail": available_ram_bytes(), "need": model_bytes + 2 * 1024**3})
        )
    ctx = clamp_ctx(ctx, ctx_max)
    ngl = int(ngl or 0)
    nth = clamp_threads(threads)
    ensure_dirs()
    LOGS.mkdir(parents=True, exist_ok=True)
    # Identifies the launch exactly, so a later boot of the same port with the same arguments can
    # reuse the live server instead of killing and restarting it. The api key is deliberately not
    # part of the string (it is compared in memory instead).
    kv_type = clean_kv_type(kv_type)
    launch_sig = "|".join(
        str(x).lower()
        for x in (exe, gguf, kind, ctx, ngl, nth, alias, mmproj, mmap, flash_attn, kv_type, batch, ubatch)
    )
    argv = [
        str(exe),
        "-m",
        str(gguf),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "-c",
        str(ctx),
        "-ngl",
        str(ngl),
        "-t",
        str(nth),
        "-np",
        "1",
        "--jinja",
        "--metrics",
        "--alias",
        alias or gguf.stem,
        "--api-key",
        api_key,
    ]
    if not mmap:
        # This engine build dropped --no-mmap in favour of -lm/--load-mode (verified against the
        # shipped llama-server --help): the old flag aborted the launch with "invalid argument".
        argv.extend(["-lm", "none"])
    if flash_attn:
        # lygo_engine.plan() decides this (console.json "flash_attn"). Passing it here is what
        # keeps that plan honest: it used to advertise flash attention and never send the flag.
        argv.extend(["-fa", "on"])
    if kv_type:
        # Quantised KV cache: q8_0 halves and q4_0 quarters the KV memory, which is what buys a
        # larger context on a small GPU. Never sent unless the plan asked for it.
        argv.extend(["-ctk", kv_type, "-ctv", kv_type])
    if batch:
        # Prefill batching, clamped: a silly value must not become an unbootable engine.
        argv.extend(["-b", str(max(256, min(8192, int(batch))))])
    if ubatch:
        argv.extend(["-ub", str(max(64, min(4096, int(ubatch))))])
    if kind == "embed":
        argv.append("--embedding")
    if mmproj and Path(mmproj).is_file() and kind == "chat":
        argv.extend(["--mmproj", str(mmproj)])
    # Serialise boots per port: two threads that both saw "no runner yet" used to Popen two
    # servers on the same port and keep whichever registered last.
    with _port_lock(port):
        with _REGISTRY_LOCK:
            live = _runners.get(port)
        if (
            live is not None
            and live.launch_sig == launch_sig
            and live.api_key == api_key
            and live.proc.poll() is None
            and _health(port, api_key)
        ):
            return live
        stop_port(port)
        proc: subprocess.Popen | None = None
        runner: Runner | None = None
        log_f = _open_engine_log(port)
        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(exe.parent),
                env=_clean_env(),
                stdout=log_f,
                stderr=subprocess.STDOUT,
                creationflags=CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
            )
            job = _assign_job(proc.pid)
            runner = Runner(
                port=port,
                gguf=str(gguf),
                kind=kind,
                proc=proc,
                api_key=api_key,
                job=job,
                alias=alias,
                log_path=str(log_f.name),
                log_handle=log_f,
                launch_sig=launch_sig,
            )
            with _REGISTRY_LOCK:
                _runners[port] = runner
            _write_pids()
            deadline = time.time() + 120
            while time.time() < deadline:
                if proc.poll() is not None:
                    raise RuntimeError(f"llama-server exited {proc.returncode}")
                if _health(port, api_key):
                    return runner
                time.sleep(3)
            raise TimeoutError("timeout")
        except BaseException:
            # Every failure and timeout path unwinds through here: stop_runner owns the process,
            # its job object and the log handle, so a failed launch leaves nothing running and
            # nothing locked on the stick.
            if runner is not None:
                stop_runner(runner)
            else:
                if proc is not None:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                _close_log(log_f)
            raise


def _health(port: int, api_key: str) -> bool:
    url = f"http://127.0.0.1:{port}/health"
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            return 200 <= resp.status < 300
    except Exception:
        pass
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def _write_pids() -> None:
    """Mirror the live runners into engine.pid.json, atomically.

    A plain write_text tore the file for whoever read it mid-write (the launcher, tools), which
    left the port sweep as the only safety net; atomicio swaps the file whole. A failure here is
    swallowed on purpose: refusing to stop a server because the pid file is unwritable would be
    worse than the stale file this exists to prevent.
    """
    with _REGISTRY_LOCK:
        blob: dict[str, dict[str, Any]] = {}
        for p, r in _runners.items():
            pid = getattr(getattr(r, "proc", None), "pid", None)
            if pid:
                blob[str(p)] = {
                    "pid": pid,
                    "gguf": getattr(r, "gguf", ""),
                    "kind": getattr(r, "kind", ""),
                }
    try:
        PID_PATH.parent.mkdir(parents=True, exist_ok=True)
        atomicio.atomic_write_text(PID_PATH, json.dumps(blob, indent=2))
    except OSError as exc:
        _log_note(f"pid file write failed ({type(exc).__name__})")


def ollama_port_open() -> bool:
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=1)
        return True
    except Exception:
        return False


def runner_for(port: int) -> Runner | None:
    with _REGISTRY_LOCK:
        return _runners.get(port)
