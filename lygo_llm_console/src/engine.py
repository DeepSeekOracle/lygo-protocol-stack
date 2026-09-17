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

from paths import ENGINE_DIR, LOGS, PID_PATH, ensure_dirs

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
    cands = [
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


_runners: dict[int, Runner] = {}


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
    if runner.job:
        try:
            ctypes.windll.kernel32.CloseHandle(runner.job)
        except Exception:
            pass
    _runners.pop(runner.port, None)


def stop_port(port: int) -> None:
    r = _runners.get(port)
    stop_runner(r)


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
    skip_ram_gate: bool = False,
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
    ctx = max(512, min(int(ctx or 4096), 8192))
    ngl = int(ngl or 0)
    nth = int(threads or 4)
    nth = max(2, min(16, nth))
    ensure_dirs()
    LOGS.mkdir(parents=True, exist_ok=True)
    log_f = open(LOGS / f"llama-server-{port}.log", "ab", buffering=0)
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
    if mmap:
        pass  # llama.cpp mmaps GGUF from SSD by default — Colibri-style tiering for dense weights
    else:
        argv.append("--no-mmap")
    if kind == "embed":
        argv.append("--embedding")
    if mmproj and Path(mmproj).is_file() and kind == "chat":
        argv.extend(["--mmproj", str(mmproj)])
    stop_port(port)
    proc = subprocess.Popen(
        argv,
        cwd=str(exe.parent),
        env=_clean_env(),
        stdout=log_f,
        stderr=subprocess.STDOUT,
        creationflags=CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
    )
    job = _assign_job(proc.pid)
    runner = Runner(port=port, gguf=str(gguf), kind=kind, proc=proc, api_key=api_key, job=job, alias=alias, log_path=str(log_f.name))
    _runners[port] = runner
    _write_pids()
    deadline = time.time() + 120
    last_err = "timeout"
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"llama-server exited {proc.returncode}")
        if _health(port, api_key):
            return runner
        time.sleep(3)
    stop_runner(runner)
    raise TimeoutError(last_err)


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
    blob = {str(p): {"pid": r.proc.pid, "gguf": r.gguf, "kind": r.kind} for p, r in _runners.items()}
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")


def ollama_port_open() -> bool:
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=1)
        return True
    except Exception:
        return False


def runner_for(port: int) -> Runner | None:
    return _runners.get(port)
