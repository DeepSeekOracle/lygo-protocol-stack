#!/usr/bin/env python3
"""Build the PUBLIC LYGO LLM Console zip. Never pack vaults, tokens, or engine blobs."""
from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
SRC = STACK / "lygo_llm_console"
STAGE = STACK / "docs" / "lygo-llm-console-public"
CHAT_DIST = Path(r"D:\chatagent\data\lygo-full-skills\dist")
STACK_DIST = STACK / "docs" / "lygo-full-skills" / "dist"
ZIP_NAME = "lygo-llm-console-public.zip"

SKIP_DIR = {"__pycache__", "data", "engine", "save"}
SKIP_FILE = {
    ".lygo_llm_token",
    ".llama_api_key",
    "local.json",
    "admin.json",
    "engine.pid.json",
    "registry.json",
    "memory.jsonl",
    "hello.txt",
}
ADMIN_MARKERS = (
    "LYGO_SERVER_KEYS",
    "LYGO_BUILDER_KEY",
    "10.0.0.209",
    "gitea.pass",
    "GamePC",
)


def _copy_tree() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    for p in SRC.rglob("*"):
        rel = p.relative_to(SRC)
        if any(part in SKIP_DIR for part in rel.parts):
            continue
        if p.name in SKIP_FILE:
            continue
        if p.suffix.lower() in {".exe", ".dll", ".so"}:
            continue
        dest = STAGE / rel
        if p.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel.parts and rel.parts[0] == "workspace" and p.suffix.lower() in {".md", ".jsonl", ".txt"}:
            # Public kit seeds workspace from prompts/ on INSTALL — never pack steward SOUL/MEMORY.
            continue
        if p.suffix.lower() in {".md", ".txt", ".json"}:
            try:
                body = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                body = ""
            if any(m in body for m in ADMIN_MARKERS) and "prompts" not in rel.parts:
                continue
        shutil.copy2(p, dest)


def _patch_public() -> None:
    paths = STAGE / "src" / "paths.py"
    t = paths.read_text(encoding="utf-8")
    t = t.replace(
        """    cand = Path(r"I:\\E Drive\\lygo-protocol-stack")
    if cand.is_dir():
        return cand
    return None""",
        "    return None",
    )
    paths.write_text(t, encoding="utf-8")

    eng = STAGE / "src" / "engine.py"
    e = eng.read_text(encoding="utf-8")
    e = e.replace(
        """    cands = [
        ENGINE_DIR / "llama-server.exe",
        Path(r"U:\\LYGO\\projects\\lygo-llm\\engine\\llama-server.exe"),
        Path(r"F:\\LYGO\\projects\\lygo-llm\\engine\\llama-server.exe"),
    ]""",
        """    cands = [
        ENGINE_DIR / "llama-server.exe",
    ]""",
    )
    eng.write_text(e, encoding="utf-8")

    bat = STAGE / "LYGO_LLM_CONSOLE.bat"
    b = bat.read_text(encoding="utf-8")
    if "I:\\E Drive" in b or "U:\\LYGO" in b or "F:\\LYGO" in b:
        raise SystemExit("public BAT still contains steward paths")
    bat.write_text(b, encoding="utf-8")

    (STAGE / "CHANNEL.txt").write_text(
        "LYGO_LLM_CONSOLE_PUBLIC\nNot the admin tree. No vaults.\nSteward: Justin Helmer / Excavationpro / Lightfather\n",
        encoding="utf-8",
    )
    (STAGE / "CREDIT.txt").write_text(
        "LYGO LLM Console (public kit)\n"
        "Mark: LYGO — project family of Justin Helmer (Excavationpro / Lightfather).\n"
        "Credits: Justin Helmer; LYGO AI agents; ggml-org llama.cpp (operator-supplied binary).\n"
        "Dual ledgers / Haven Star Chart remain CANON. This kit is RESOURCE.\n"
        "Donate: https://www.paypal.com/paypalme/ExcavationPro\n",
        encoding="utf-8",
    )
    readme = STAGE / "README.md"
    extra = (
        "\n\n## Public kit\n\nThis zip is the **public** channel. "
        "Run **INSTALL.bat** first (seeds Soul / Identity / Memory for this user). "
        "It is not the steward admin tree. Write roots stay inside this folder until you Add Workspace access. "
        "Place ggml-org `llama-server.exe` in `engine/` (CPU Windows zip) or let INSTALL fetch it. "
        "Page: https://chatagent.ca/lygo-llm-console.html\n"
    )
    readme.write_text(readme.read_text(encoding="utf-8") + extra, encoding="utf-8")
    loc = STAGE / "config" / "local.json.example"
    loc.write_text(
        '{\n  "scan_roots": ["./models", "%USERPROFILE%/.ollama/models"],\n'
        '  "comment": "Public kit. Do not add steward vaults."\n}\n',
        encoding="utf-8",
    )


def _zip() -> tuple[Path, str]:
    for d in (CHAT_DIST, STACK_DIST):
        d.mkdir(parents=True, exist_ok=True)
    out = CHAT_DIST / ZIP_NAME
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in STAGE.rglob("*"):
            if p.is_file():
                z.write(p, Path("lygo-llm-console-public") / p.relative_to(STAGE))
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    (CHAT_DIST / (ZIP_NAME + ".sha256")).write_text(sha + "  " + ZIP_NAME + "\n", encoding="utf-8")
    shutil.copy2(out, STACK_DIST / ZIP_NAME)
    shutil.copy2(CHAT_DIST / (ZIP_NAME + ".sha256"), STACK_DIST / (ZIP_NAME + ".sha256"))
    return out, sha


def main() -> int:
    _copy_tree()
    _patch_public()
    # forbid tokens in staged source
    blob = ""
    for p in (STAGE / "src").rglob("*.py"):
        blob += p.read_text(encoding="utf-8", errors="ignore")
    for bad in ("run_cmd", r"C:\Users\justi", "Data Vault", "LYGO_SERVER_KEYS", "gitea.pass", r"I:\E Drive"):
        if bad in blob:
            raise SystemExit(f"public kit src contains forbidden token {bad}")
    ws = STAGE / "workspace"
    if ws.is_dir():
        for p in ws.rglob("*"):
            if p.is_file() and p.name != ".gitkeep" and p.suffix.lower() in {".md", ".jsonl"}:
                raise SystemExit(f"public kit packed workspace identity {p}")
    out, sha = _zip()
    print(out)
    print(sha)
    print("bytes", out.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
