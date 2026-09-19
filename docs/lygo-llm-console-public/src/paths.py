from __future__ import annotations

import os
from pathlib import Path

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

DEFAULT_PORT = 9641
LLAMA_PORT = 11441
EMBED_PORT = 11442


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


def stack_root() -> Path | None:
    env = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if env:
        p = Path(env)
        if p.is_dir():
            return p
    # GamePC default
    return None
