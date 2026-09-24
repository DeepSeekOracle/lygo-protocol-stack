"""D9 for pytest: a full run stops the live console on purpose (the suite boots and shuts one down),
so a green run used to leave the operator's console dead with nothing saying who did it.

This restores it at the end of the session. Set LYGO_NO_ENSURE=1 to keep the suite from starting
anything (CI, or a run on a machine that must not spawn a model).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
_WAS_UP = False


def pytest_sessionstart(session):  # noqa: ARG001 - pytest's hook signature
    """Remember whether a console was serving when the run began: the suite stops one on purpose, so
    only a console that was up may be put back. A run on a machine that never had one must not spend
    minutes cold-booting a 12B at the end of a green suite."""
    global _WAS_UP
    scripts = str(KIT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        import ensure_console

        _WAS_UP = bool(ensure_console.health(ensure_console._read_port(KIT)[0]))
    except Exception:  # noqa: BLE001
        _WAS_UP = False


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001 - pytest's hook signature
    if os.environ.get("LYGO_NO_ENSURE", "").strip().lower() in {"1", "true", "yes"}:
        print("\nconsole: not re-checked (LYGO_NO_ENSURE set)")
        return
    scripts = str(KIT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        import ensure_console

        _ok, line = ensure_console.ensure(KIT, quiet=True, restore_only=not _WAS_UP)
        print("\nconsole: " + line)
    except Exception as exc:  # noqa: BLE001 - never fail a finished suite over the helper
        print(f"\nconsole: not checked ({type(exc).__name__}: {exc})")
