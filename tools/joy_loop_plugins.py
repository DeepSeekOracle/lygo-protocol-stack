"""Optional Joy Loop plugins — drop Python modules in data/joy_loop/plugins/."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "data" / "joy_loop" / "plugins"


def load_plugins(bus: Any) -> list[str]:
    import os

    if os.environ.get("LYGO_JOY_PLUGINS_ENABLED", "").lower() not in ("1", "true", "yes"):
        return []
    loaded: list[str] = []
    if not PLUGIN_DIR.is_dir():
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        example = PLUGIN_DIR / "README.txt"
        if not example.is_file():
            example.write_text(
                "Place plugin .py files here with def register(bus): ...\n", encoding="utf-8"
            )
        return loaded
    for path in sorted(PLUGIN_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if not spec or not spec.loader:
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            fn = getattr(mod, "register", None)
            if callable(fn):
                fn(bus)
                loaded.append(path.stem)
        except Exception:
            continue
    return loaded