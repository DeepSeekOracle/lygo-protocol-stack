"""TPM 2.0 interface — Keylime-ready stub with platform probes."""

from __future__ import annotations

import platform
import shutil
import subprocess
from typing import Any


def _try_keylime() -> bool:
    try:
        import keylime  # noqa: F401

        return True
    except ImportError:
        return False


def _windows_tpm_present() -> bool:
    if platform.system() != "Windows":
        return False
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        return False
    script = (
        "Get-Tpm -ErrorAction SilentlyContinue | "
        "Select-Object -ExpandProperty TpmPresent"
    )
    try:
        cp = subprocess.run(
            [ps, "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=15,
        )
        out = (cp.stdout or "").strip().lower()
        return out == "true"
    except (subprocess.TimeoutExpired, OSError):
        return False


def _linux_tpm_present() -> bool:
    for path in ("/dev/tpm0", "/dev/tpmrm0"):
        try:
            with open(path, "rb"):
                return True
        except OSError:
            continue
    return shutil.which("tpm2_getcap") is not None


def check_tpm() -> bool:
    """Return True if TPM 2.0 appears present or Keylime is installed."""
    if _try_keylime():
        return True
    if platform.system() == "Windows":
        return _windows_tpm_present()
    if platform.system() == "Linux":
        return _linux_tpm_present()
    return False


def read_pcr_stub(indices: tuple[int, ...] = (0, 1, 7)) -> dict[str, str]:
    """PCR values — hardware path pending Keylime; software placeholder for dev."""
    import hashlib
    import uuid

    seed = f"tpm-pcr-stub|{uuid.getnode()}|{platform.node()}"
    out: dict[str, str] = {}
    for i in indices:
        digest = hashlib.sha256(f"{seed}|pcr{i}".encode()).hexdigest()
        out[f"pcr{i}"] = digest
    return out


def tpm_status() -> dict[str, Any]:
    return {
        "tpm_present": check_tpm(),
        "keylime_installed": _try_keylime(),
        "platform": platform.system(),
        "mode": "hardware" if check_tpm() and _try_keylime() else "stub",
    }