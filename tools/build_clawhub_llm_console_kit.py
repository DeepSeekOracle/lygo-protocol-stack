#!/usr/bin/env python3
"""Build the ClawHub skill's operator kit: a SANITISED, UNPACKED public console tree.

Two lanes, two artifacts, one rule each:

* `tools/pack_lygo_llm_console_public.py` packs the site zip for chatagent.ca.
* this tool builds `clawhub/mirrors/lygo-llm-console/kit` — the tree the ClawHub package ships
  UNPACKED, so a registry reviewer can read every file that would run instead of trusting a hash
  inside an archive (the 1.2.0 zip drew four HIGH "referenced artifact was not completely
  inspected / embedded NUL bytes" findings for exactly that reason).

Rules:
  * include list only — a new file in the kit is a decision, never an accident;
  * the source tree is never modified: the steward's absolute paths are rewritten in the COPY,
    by an explicit patch table that REFUSES to build when a pattern it expects has moved;
  * every shipped text file is scanned after patching, and the build refuses on a survivor;
  * `kit/KIT_SHA256SUMS.txt` + `kit/PUBLIC_KIT.json` are written so `scripts/verify_kit.py` can
    check the tree it unpacked, file by file, and so the exclusions are visible.

Usage:
    python tools/build_clawhub_llm_console_kit.py            # build into the mirror
    python tools/build_clawhub_llm_console_kit.py --check    # scan only, write nothing
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
SRC = STACK / "lygo_llm_console"
CONSOLE_VERSION_FILE = SRC / "VERSION"
DEST = STACK / "clawhub" / "mirrors" / "lygo-llm-console" / "kit"

INCLUDE_DIRS = ("src", "portal", "web_portal", "prompts", "skills", "config")
INCLUDE_TOOLS = ("resolve_ports.py", "doorbell.py")
INCLUDE_SCRIPTS = ("fetch_engine.ps1",)
INCLUDE_FILES = (
    "VERSION",
    "HARDENING.md",
    "MODELS.md",
    "SKILLS.md",
    "PUBLIC_PORTAL.md",
    "READ_DISCLAIMER_FIRST.md",
    "INSTALL.bat",
    "LYGO_LLM_CONSOLE.bat",
    "LYGO_LLM_CONSOLE_STOP.bat",
    "LICENSE",
    "LICENSING.md",
    "NOTICE",
    "TRADEMARKS.md",
)

# Files that exist in the kit but are authored here (never copied): the public README, the
# channel/credit cards, the manifest and the checksum list.
AUTHORED = ("README.md", "CHANNEL.txt", "CREDIT.txt", "PUBLIC_KIT.json", "KIT_SHA256SUMS.txt")

SKIP_DIRS = {"__pycache__", "data", "engine", "save", "models", "installer", "docs", "workspace"}
SKIP_SUFFIX = {
    ".pyc", ".pyo", ".exe", ".dll", ".so", ".pdb", ".o", ".rmeta", ".bin", ".gguf", ".wav", ".mp3",
    ".zip", ".7z", ".rar", ".msi", ".db", ".sqlite", ".log", ".bak", ".mangled", ".iss", ".img", ".iso",
}
SKIP_NAMES = {
    "api.json", "admin.json", "local.json", ".lygo_llm_token", ".llama_api_key", "engine.pid.json",
    "registry.json", "memory.jsonl",
}
TEXT_SUFFIX = {
    ".py", ".md", ".txt", ".json", ".jsonl", ".js", ".css", ".html", ".bat", ".ps1", ".sh", ".example",
    ".yml", ".yaml", ".toml", ".svg",
}

# --- what must never reach the kit ------------------------------------------------------------
FORBIDDEN = (
    r"I:\E Drive",
    r"C:\Users\justi",
    r"D:\LYGO_CANON",
    r"U:\LYGO",
    r"F:\LYGO",
    r"D:\chatagent",
    r"10.0.0.209",
    r"gitea.pass",
    r"LYGO_SERVER_KEYS",
    "supporter-codes",
)
KEY_SHAPES = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}"
    r"|AKIA[0-9A-Z]{12,}|xox[baprs]-[A-Za-z0-9-]{10,}|nvapi-[A-Za-z0-9_\-]{20,})"
)
PEM_HEAD = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")

# --- the patch table: the steward's machine, rewritten out of the copy ------------------------
# Every entry is (file, old, new) and must MATCH, or the build stops: a pattern that has moved
# means the source drifted and this table is no longer describing the tree it patches.
PATCHES: tuple[tuple[str, str, str], ...] = (
    (
        "src/engine.py",
        """    cands = [
        engine_dir() / "llama-server.exe",
        ENGINE_DIR / "llama-server.exe",
        Path(r"U:\\LYGO\\projects\\lygo-llm\\engine\\llama-server.exe"),
        Path(r"F:\\LYGO\\projects\\lygo-llm\\engine\\llama-server.exe"),
    ]""",
        """    cands = [
        engine_dir() / "llama-server.exe",
        ENGINE_DIR / "llama-server.exe",
    ]""",
    ),
    (
        "src/registry.py",
        """KNOWN_VAULTS = (
    r"I:\\LYGO_MODELS",
    r"U:\\LYGO\\models",
    r"F:\\LYGO\\models",
    r"E:\\LYGO_BUILDER_KEY\\product\\models\\cas",
)""",
        """# Public kit: no absolute vault letters are baked in. A stranger's machine has no other kit's
# vault, and this kit resolves its own storage by env, kit-relative path, or the operator's own
# declared scan_roots. The tuple stays, empty, so every caller is unchanged.
KNOWN_VAULTS: tuple[str, ...] = ()""",
    ),
    (
        "src/server.py",
        """    extras.extend(
        [
            Path(r"I:\\LYGO_MODELS"),
            Path(r"D:\\LYGO_MODEL_VAULT"),
            Path(r"D:\\LYGO_MODEL_VAULT\\cas"),
            Path(r"U:\\LYGO\\models"),
            Path(r"F:\\LYGO\\models"),
            Path(r"E:\\LYGO_BUILDER_KEY\\product\\models\\cas"),
        ]
    )""",
        """    # Public kit: no baked-in vault letters. Declared env roots above and the operator's
    # config/console.json scan_roots are the only candidates, so a kit on an unknown machine looks
    # in its own folder and where its operator pointed it.""",
    ),
    (
        "src/paths.py",
        """# The kit travels: desktop I:\\E Drive\\lygo-protocol-stack, USB E:\\LYGO_BUILDER_KEY,
# packaging target D:\\LYGO_CONSOLE. A baked-in drive letter is therefore only ever the
# LAST resort, and resolution never goes quiet: every candidate is recorded by
# resolution_log() and stack_root_status() always returns a root plus the reason.""",
        """# The kit travels: a desktop checkout, a USB stick, a packaging target. A baked-in drive letter
# is therefore only ever the LAST resort, and resolution never goes quiet: every candidate is
# recorded by resolution_log() and stack_root_status() always returns a root plus the reason.""",
    ),
    (
        "src/paths.py",
        """STACK_DRIVE_TEMPLATES: tuple[str, ...] = (
    "{d}:\\\\E Drive\\\\lygo-protocol-stack",
    "{d}:\\\\lygo-protocol-stack",
    "{d}:\\\\LYGO\\\\lygo-protocol-stack",
)""",
        """STACK_DRIVE_TEMPLATES: tuple[str, ...] = (
    "{d}:\\\\lygo-protocol-stack",
    "{d}:\\\\LYGO\\\\lygo-protocol-stack",
)""",
    ),
    (
        "src/chat_loop.py",
        """# "check this photo <path>" where the path was drive I:, folder "E Drive", YOUTUBE LYGO VIDEOS,""",
        """# "check this photo <path>" where the path had a drive letter and folders with spaces in them,""",
    ),
    (
        "src/chat_loop.py",
        """# it ("I:\\E Drive\\..."), which every inline path pattern truncates.""",
        """# it (a path with a space in it), which every inline path pattern truncates.""",
    ),
    (
        "src/repair_paths.py",
        """The kit travels between drives: I:\\\\E Drive\\\\lygo-protocol-stack (desktop) ->
E:\\\\LYGO_BUILDER_KEY\\\\lygo_llm_console (USB) -> D:\\\\LYGO_CONSOLE (packaged). Absolute""",
        """The kit travels between drives: a desktop checkout, a USB kit folder, a packaged folder on
another drive. Absolute""",
    ),
    (
        "src/repair_paths.py",
        """    D:\\\\E Drive\\\\LYRA LOCAL while the real folder stayed on I: - a read root that exists nowhere""",
        """    a folder under the origin drive while the real folder stayed where it was - a root that
    exists nowhere""",
    ),
    (
        "src/admin_map.py",
        """# \"has a lygo_llm_console child\" test and {usb} expanded to the stack, reporting success.""",
        """# \"has a lygo_llm_console child\" test and {usb} expanded to the stack, reporting success.""",
    ),
    (
        "src/admin_map.py",
        """# The old code tried E:\\ and then fell back to KIT_ROOT.parent, so the desktop kit
# silently accepted the WRONG tree - I:\\E Drive\\lygo-protocol-stack passed the loose""",
        """# The old code tried one drive and then fell back to KIT_ROOT.parent, so the desktop kit
# silently accepted the WRONG tree - the stack checkout passed the loose""",
    ),
    (
        "src/skills_mod.py",
        """this kit (which is what the core is on the default GamePC layout).""",
        """this kit (which is what the core is on the default desktop layout).""",
    ),
    (
        "HARDENING.md",
        """- BAT: `I:\\E Drive\\lygo-protocol-stack\\lygo_llm_console\\LYGO_LLM_CONSOLE.bat` (Desktop trampoline OK).""",
        """- BAT: `LYGO_LLM_CONSOLE.bat` in the kit root (drive-portable, `%~dp0`; a desktop shortcut is fine).""",
    ),
    (
        "portal/index.html",
        """placeholder="C:\\  or  D:\\chatagent  or any folder\"""",
        """placeholder="any folder, e.g. D:\\models\"""",
    ),
    (
        "skills/champions/champion-lyra-architect/SKILL.md",
        """**Charter file:** `workspace/LYRA_ARCHITECT.md` (distilled from `I:\\E Drive\\LYRA_CORE`""",
        """**Charter file:** `workspace/LYRA_ARCHITECT.md` (distilled from the LYRA core tree""",
    ),
    (
        "src/admin_map.py",
        """# Was a baked-in Path(r"D:\\chatagent"): on any host without D:, self_check reported""",
        """# Was a baked-in absolute path: on any host without that drive, self_check reported""",
    ),
    (
        "src/vendor/p0/NOTICE.txt",
        """This copy exists so the stream runtime (U:\\LYGO\\projects\\lygo-llm) can fail-closed""",
        """This copy exists so the kit runtime can fail-closed""",
    ),
)

EXCLUDED_WITH_REASON = {
    "tests/": "not shipped on ClawHub: the site zip carries the suite. Its fixtures are generated at test time and their binary leftovers are what a scanner reports as NUL-byte artifacts.",
    "scripts/ (except fetch_engine.ps1)": "bench/bundle/seal tools that name the steward's own drives; they are not needed to run the console.",
    "tools/ (except resolve_ports.py, doorbell.py)": "the two the launcher calls. The rest package, seal and audit the steward's tree.",
    "WHITEPAPER.md": "narrates the steward's own layout and drives; the site links it instead.",
    "BRANDING.md, COMPACTION.md, SESSIONS.md, FULL_LYGO.md, installer/, docs/": "internal build and brand process notes.",
    "config/api.json, config/admin.json, config/local.json, save/, data/, engine/, models/": "credentials, operator state, engine binaries and weights never travel.",
    "workspace/": "the kit seeds a fresh identity from prompts/ on first run; a steward's own SOUL/MEMORY must never ship.",
}

PUBLIC_README = """# LYGO LLM Console — public kit (operator runtime)

This folder is the runtime half of the ClawHub skill **LYGO LLM Console** (`deepseekoracle/lygo-llm-console`).
It ships **unpacked on purpose**: every file that would run is readable here before you run it.

It is the **public** channel. It is not the steward's admin tree, it carries no operator keys, no
vaults and no model weights, and it never launches or requires `ollama.exe`.

## Read this first

1. `VERSION` — the console release this tree is (`1.5.6`).
2. `PUBLIC_KIT.json` — what was copied in, what was left out and why, and a SHA-256 per file.
3. `KIT_SHA256SUMS.txt` — run `python ../scripts/verify_kit.py` to check every file yourself.

## Run it

1. Put official **ggml-org** `llama-server.exe` (Windows CPU build, tag `b10988`) into `engine/`, or
   let `INSTALL.bat` fetch it. The console never uses a nested Ollama copy.
2. `INSTALL.bat` — seeds **your** Soul / Identity / Memory. No steward identity is included.
3. `LYGO_LLM_CONSOLE.bat` — the launcher is drive-portable (`%~dp0`): it runs *this* folder, whatever
   drive it sits on, and refuses to start a second console on the same ports.
4. Open <http://127.0.0.1:9641/> and pick a model.

Run it as a normal, **unprivileged** user. Default bind is loopback (`127.0.0.1`); a LAN bind needs
`--lan --i-consent`.

## What it can do (and what it cannot)

Can: scan drives for GGUF files and read-only Ollama CAS trees, boot a local llama.cpp server on a
private loopback port, serve a browser portal, run allowlisted limbs (files, memory, search, fetch,
RAG over your own corpus, images when a projector is registered), gate every generation through the
LYGO P0 Φ-gate, and speak a subset of the OpenAI HTTP shape on `/v1/*`.

Cannot: reach the steward's drives, vaults or keys; publish anything; call `ollama.exe`; write
outside this kit's `workspace/` and `save/` unless you deliberately widen it in config.

Page: <https://chatagent.ca/lygo-llm-console.html> · ClawHub: <https://clawhub.ai/deepseekoracle/skills/lygo-llm-console>
"""

PUBLIC_CHANNEL = """LYGO_LLM_CONSOLE_PUBLIC
Not the admin tree. No vaults, no operator keys, no model weights.
Steward: Justin Helmer / Excavationpro / Lightfather
"""

PUBLIC_CREDIT = """LYGO LLM Console (public kit)
Mark: LYGO — project family of Justin Helmer (Excavationpro / Lightfather).
Credits: Justin Helmer; LYGO AI agents; ggml-org llama.cpp (operator-supplied binary).
Dual ledgers / Haven Star Chart remain CANON. This kit is RESOURCE.
Donate: https://www.paypal.com/paypalme/ExcavationPro
"""


def console_version() -> str:
    line = (SRC / "VERSION").read_text(encoding="utf-8", errors="ignore").splitlines()
    return (line[0] if line else "").strip()


def wanted(rel: Path) -> bool:
    parts = rel.parts
    if not parts:
        return False
    if any(p in SKIP_DIRS for p in parts[:-1]) or parts[0] in SKIP_DIRS:
        return False
    if rel.name in SKIP_NAMES or rel.suffix.lower() in SKIP_SUFFIX:
        return False
    if parts[0] == "tools":
        return len(parts) == 2 and parts[1] in INCLUDE_TOOLS
    if parts[0] == "scripts":
        return len(parts) == 2 and parts[1] in INCLUDE_SCRIPTS
    if parts[0] in INCLUDE_DIRS:
        return rel.suffix.lower() in TEXT_SUFFIX or rel.name == ".gitkeep"
    return False


def scan(body: str, rel: str) -> list[str]:
    hits: list[str] = []
    for token in FORBIDDEN:
        if token in body:
            hits.append(f"{rel}: forbidden path/fragment {token!r}")
    if KEY_SHAPES.search(body):
        hits.append(f"{rel}: key-shaped string {KEY_SHAPES.search(body).group(0)[:6]}...")
    if PEM_HEAD.search(body):
        hits.append(f"{rel}: PEM private-key header")
    return hits


def build(write: bool) -> int:
    if not SRC.is_dir():
        print(f"REFUSING: no console tree at {SRC}")
        return 2
    version = console_version()
    if not version:
        print("REFUSING: VERSION is empty")
        return 2

    staged: dict[str, bytes] = {}
    missing_patch: list[str] = []

    def add(rel: str, data: bytes) -> None:
        staged[rel] = data

    for name in INCLUDE_FILES:
        p = SRC / name
        if p.is_file():
            add(name, p.read_bytes())

    for root, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d != "__pycache__"]
        for f in files:
            p = Path(root) / f
            rel = p.relative_to(SRC)
            if wanted(rel):
                add(rel.as_posix(), p.read_bytes())

    # the patch table, applied to the COPY only
    for rel, old, new in PATCHES:
        if old == new:
            continue
        data = staged.get(rel)
        text = data.decode("utf-8") if data is not None else None
        if text is None:
            missing_patch.append(rel)
            continue
        # The tree is CRLF; the table is written LF. Try the file's own convention first, so the
        # shipped bytes keep their line endings (a .bat rewritten to LF is a broken .bat).
        replaced = None
        for o, n in ((old.replace("\n", "\r\n"), new.replace("\n", "\r\n")), (old, new)):
            if o in text:
                replaced = text.replace(o, n, 1)
                break
        if replaced is None:
            missing_patch.append(rel)
            continue
        staged[rel] = replaced.encode("utf-8")
    if missing_patch:
        print("REFUSING: the patch table no longer matches the tree — source drifted:")
        for rel in sorted(set(missing_patch)):
            print("   " + rel)
        return 3

    # authored files
    add("README.md", PUBLIC_README.encode("utf-8"))
    add("CHANNEL.txt", PUBLIC_CHANNEL.encode("utf-8"))
    add("CREDIT.txt", PUBLIC_CREDIT.encode("utf-8"))

    findings: list[str] = []
    for rel, data in sorted(staged.items()):
        if Path(rel).suffix.lower() not in TEXT_SUFFIX:
            continue
        findings += scan(data.decode("utf-8", errors="ignore"), rel)

    # every shipped file must be a file the include rules chose, nothing else
    stray = [rel for rel in staged if "\\" in rel]
    findings += [f"{rel}: non-posix path" for rel in stray]

    print(f"console release : {version}")
    print(f"files staged    : {len(staged)}")
    if findings:
        print(f"\nREFUSED — {len(findings)} finding(s) in the public kit:")
        for f in findings[:40]:
            print("   " + f)
        return 1

    manifest = {
        "kit": "lygo-llm-console public kit (ClawHub package, unpacked)",
        "console_release": version,
        "source_tree": str(SRC),
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "packed_as_archive": False,
        "reason_unpacked": "a registry reviewer can read every file that runs; the 1.2.0 zip drew four HIGH analysis-evasion findings for being uninspectable",
        "patched_in_the_copy_only": sorted({rel for rel, _o, _n in PATCHES if _o != _n}),
        "not_shipped": EXCLUDED_WITH_REASON,
        "files": {},
    }
    sums: list[str] = []
    for rel, data in sorted(staged.items()):
        digest = hashlib.sha256(data).hexdigest()
        manifest["files"][rel] = {"sha256": digest, "bytes": len(data)}
        sums.append(f"{digest}  {rel}")
    manifest["file_count"] = len(staged)

    if not write:
        print("\n--check: nothing written. All checks passed.")
        return 0

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    for rel, data in staged.items():
        out = DEST / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    (DEST / "PUBLIC_KIT.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (DEST / "KIT_SHA256SUMS.txt").write_text("\n".join(sorted(sums)) + "\n", encoding="utf-8")
    print(f"\nkit written: {DEST}")
    print(f"files      : {len(staged)} (+2 manifest/checksum)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="scan only, write nothing")
    args = ap.parse_args()
    return build(write=not args.check)


if __name__ == "__main__":
    raise SystemExit(main())
