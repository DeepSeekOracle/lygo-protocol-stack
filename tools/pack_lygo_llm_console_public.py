#!/usr/bin/env python3
"""Build the PUBLIC LYGO LLM Console zip — the download offered on chatagent.ca.

Never pack vaults, tokens, personal media, or engine blobs.

Two lanes, one rule each:
  * this tool packs the SITE zip (the full download a visitor gets);
  * `tools/build_clawhub_llm_console_kit.py` builds the ClawHub kit, UNPACKED.

They share one table of what the steward's machine looks like in the source
(`PATCHES`, imported from the kit builder) so the two public copies cannot drift apart in
what they disclose.

What changed here, and why it was worth rewriting:
  * the old copy loop skipped `data/ engine/ save/`, token files and executables, and then copied
    EVERYTHING else. Measured 2026-09-26 on console 1.5.6: that is 509 files / 296 MB, of which
    296 MB is `workspace/` — the steward's songs, generated images and a Rust `target/` tree whose
    object files have the steward's absolute path baked in binary. A public download must not be
    that, and a scanner reads every byte of an archive it cannot explain.
  * it also copied `installer/` (47 Inno Setup scripts naming the vault and the canon drive),
    `tests/` (fixtures plus the paths of credential files), and `scripts/` (bench/seal tools
    hardcoding a photo directory and the USB kit).
  * its final gate scanned only `src/**/*.py`, so `registry.py` and `server.py` kept their
    `U:\\LYGO` / `F:\\LYGO` model-root candidates and shipped them.

So: an explicit exclusion set, the shared patch table applied to the COPY (must-match: a moved
pattern means the source drifted and this tool stops), and a scan of every text file that is
actually about to be zipped, refusing on any survivor.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
SRC = STACK / "lygo_llm_console"
STAGE = STACK / "docs" / "lygo-llm-console-public"
CHAT_DIST = Path(r"D:\chatagent\data\lygo-full-skills\dist")
STACK_DIST = STACK / "docs" / "lygo-full-skills" / "dist"
ZIP_NAME = "lygo-llm-console-public.zip"

# Nothing below the kit root that is not needed to RUN the console. Every exclusion is a decision.
SKIP_DIR = {
    "__pycache__",
    "data",          # operator state: tokens, registry, memory
    "engine",        # llama-server binaries and weights
    "save",          # sessions and receipts
    "workspace",     # the steward's own identity, notes, songs, images, rust target tree
    "installer",     # Inno Setup scripts naming the vault/canon drives
    "tests",         # fixtures (binary) and the paths of credential files
    ".pytest_cache",
}
# ...except the few files the runtime and the documented workflow actually call. Measured, not assumed:
# LYGO_LLM_CONSOLE.bat and LYGO_LLM_CONSOLE_STOP.bat run `tools\resolve_ports.py` and start
# `tools\doorbell.py`; src/install.py tells the operator to run `scripts\fetch_engine.ps1`.
ALLOW_TOOLS = {"resolve_ports.py", "doorbell.py"}
ALLOW_SCRIPTS = {"fetch_engine.ps1", "fetch_colibri.ps1"}
# UI assets the portal loads by name. A 40 KB logo is not a leak; anything bigger belongs on a CDN.
ALLOW_BIN_SUFFIX = {".png", ".jpg", ".jpeg", ".webp", ".ico", ".gif"}
ALLOW_BIN_DIRS = {"portal", "web_portal"}
MAX_BIN = 400 * 1024
SKIP_FILE = {
    ".lygo_llm_token",
    ".llama_api_key",
    "local.json",
    "admin.json",
    "api.json",          # provider keys for the console's cloud brains — never public
    "engine.pid.json",
    "registry.json",
    "memory.jsonl",
    "hello.txt",
}
# Editor/agent leftovers: a `.bak` beside a live config is how a key file survives a rename.
SKIP_NAME = re.compile(r"(\.bak(-|$)|\.mangled|\.orig$|~$|\.save$)")
SKIP_SUFFIX = {".exe", ".dll", ".so", ".o", ".rmeta", ".pdb", ".gguf", ".wav", ".mp3", ".png", ".jpg"}

# Read by tools/scrub_public_audit.py: keep the names.
ADMIN_MARKERS = (
    "LYGO_SERVER_KEYS",
    "LYGO_BUILDER_KEY",
    "10.0.0.209",
    "gitea.pass",
    "GamePC",
)

# The steward's machine, as a path. Docs carrying any of these are dropped unless they are in the
# patch table (a product document we deliberately rewrite); code carrying one must be patched.
STEWARD_PAT = (
    r"I:\E Drive",
    r"C:\Users\justi",
    r"D:\LYGO_CANON",
    r"U:\LYGO",
    r"F:\LYGO",
    r"D:\chatagent",
    r"E:\LYGO_BUILDER_KEY",
    r"I:\LYGO_SERVER_KEYS",
    "10.0.0.209",
    "Data Vault",
    "gitea.pass",
)
KEY_SHAPES = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}"
    r"|AKIA[0-9A-Z]{12,}|xox[baprs]-[A-Za-z0-9-]{10,}|nvapi-[A-Za-z0-9_\-]{20,})"
)
PEM_HEAD = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
TEXT_EXT = {".py", ".md", ".txt", ".json", ".jsonl", ".js", ".css", ".html", ".bat", ".ps1", ".sh",
            ".iss", ".yml", ".yaml", ".toml", ".example", ".svg"}

# One table for both public lanes: the steward's absolute paths, rewritten in the COPY.
sys.path.insert(0, str(STACK / "tools"))
from build_clawhub_llm_console_kit import CONSOLE_VERSION_FILE, PATCHES  # noqa: E402  (lane-shared)

PATCHED_FILES = {rel for rel, old, new in PATCHES if old != new}


def _marker_hit(body: str) -> str | None:
    for m in ADMIN_MARKERS:
        if m in body:
            return m
    for p in STEWARD_PAT:
        if p in body:
            return p
    return None


def _copy_tree() -> tuple[int, list[str]]:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    dropped: list[str] = []
    kept = 0
    for p in sorted(SRC.rglob("*")):
        rel = p.relative_to(SRC)
        if any(part in SKIP_DIR for part in rel.parts):
            continue
        if p.name in SKIP_FILE:
            dropped.append(f"{rel} (skip list)")
            continue
        if SKIP_NAME.search(p.name):
            dropped.append(f"{rel} (editor/agent leftover)")
            continue
        if rel.parts[0] == "tools" and not (len(rel.parts) == 2 and rel.name in ALLOW_TOOLS):
            dropped.append(f"{rel} (dev tool, not called at runtime)")
            continue
        if rel.parts[0] == "scripts" and not (len(rel.parts) == 2 and rel.name in ALLOW_SCRIPTS):
            dropped.append(f"{rel} (steward-side tool)")
            continue
        if p.suffix.lower() in SKIP_SUFFIX:
            if (p.suffix.lower() in ALLOW_BIN_SUFFIX and rel.parts[0] in ALLOW_BIN_DIRS
                    and p.stat().st_size <= MAX_BIN):
                pass  # a portal asset, below the cap: keep it and let the scan read it
            else:
                dropped.append(f"{rel} (binary/weight)")
                continue
        dest = STAGE / rel
        if p.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        if p.suffix.lower() in {".md", ".txt", ".json"} and rel.as_posix() not in PATCHED_FILES:
            try:
                body = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                body = ""
            hit = _marker_hit(body)
            if hit and "prompts" not in rel.parts:
                dropped.append(f"{rel} (names the steward's machine: {hit})")
                continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        kept += 1
    return kept, dropped


def _patch_copy() -> None:
    """Apply the shared table to the staged copy. A pattern that no longer matches is drift."""
    missing: list[str] = []
    for rel, old, new in PATCHES:
        if old == new:
            continue
        f = STAGE / rel
        if not f.is_file():
            missing.append(f"{rel} (not staged)")
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for o, n in ((old.replace("\n", "\r\n"), new.replace("\n", "\r\n")), (old, new)):
            if o in text:
                f.write_text(text.replace(o, n, 1), encoding="utf-8")
                break
        else:
            missing.append(f"{rel} (pattern moved)")
    if missing:
        print("REFUSING: the shared patch table no longer matches the console tree — source drifted:")
        for m in sorted(set(missing)):
            print("   " + m)
        raise SystemExit(3)


def _write_extras() -> None:
    (STAGE / "CHANNEL.txt").write_text(
        "LYGO_LLM_CONSOLE_PUBLIC\nNot the admin tree. No vaults. No personal media.\n"
        "Steward: Justin Helmer / Excavationpro / Lightfather\n",
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
        "Place ggml-org `llama-server.exe` in `engine/` (CPU Windows zip) or let INSTALL fetch it "
        "(`powershell -File scripts\\fetch_engine.ps1`). "
        "Not included, on purpose: models and engine binaries, the test suite, the installer and "
        "release tooling, and any personal workspace. "
        "Page: https://chatagent.ca/lygo-llm-console.html\n"
    )
    if readme.is_file():
        readme.write_text(readme.read_text(encoding="utf-8") + extra, encoding="utf-8")
    else:
        # The source README named the steward's drives, so it was dropped. A public download still
        # needs a README that says what it is and what it will not do.
        readme.write_text(
            "# LYGO LLM Console - public kit\n\n"
            "A local, sovereign LLM runtime and agent portal. Not Ollama, and not the steward's\n"
            "admin tree: no vaults, no keys, no model weights, no personal workspace.\n\n"
            "## Run it\n\n"
            "1. `INSTALL.bat` - seeds **your** Soul / Identity / Memory and checks python.\n"
            "2. Put ggml-org CPU `llama-server.exe` in `engine/`, or run\n"
            "   `powershell -File scripts\\fetch_engine.ps1`.\n"
            "3. `LYGO_LLM_CONSOLE.bat` - the launcher resolves its own folder (`%~dp0`), so it runs\n"
            "   *this* copy wherever you unpacked it, and it refuses a second console on the same\n"
            "   ports. Stop it with `LYGO_LLM_CONSOLE_STOP.bat`.\n"
            "4. Open http://127.0.0.1:9641/ and pick a model.\n\n"
            "Default bind is loopback (`127.0.0.1`); a LAN bind needs `--lan --i-consent`. Run it as a\n"
            "normal, unprivileged user.\n\n"
            "## What it can and cannot do\n\n"
            "Can: scan drives for GGUF, boot a local llama.cpp server on a private loopback port,\n"
            "serve a browser portal, run allowlisted limbs (files, memory, search, fetch, RAG over\n"
            "your own corpus, images when a projector is registered), gate every generation through\n"
            "the LYGO P0 check, and speak a subset of the OpenAI HTTP shape on `/v1/*`.\n\n"
            "Cannot: reach the steward's drives, vaults or keys; publish anything; require Ollama;\n"
            "write outside this folder's `workspace/` and `save/` unless you widen it in config.\n"
            "The shell and Python limbs run code as *your* user - this is not a sandbox.\n\n"
            "Page: https://chatagent.ca/lygo-llm-console.html\n"
            "Source: https://github.com/DeepSeekOracle/lygo-protocol-stack\n",
            encoding="utf-8",
        )
    loc = STAGE / "config" / "local.json.example"
    if loc.parent.is_dir():
        loc.write_text(
            '{\n  "scan_roots": ["./models", "%USERPROFILE%/.ollama/models"],\n'
            '  "comment": "Public kit. Do not add steward vaults."\n}\n',
            encoding="utf-8",
        )


def _is_text(p: Path) -> bool:
    """Text if the suffix says so, if it has no suffix, or if there is no NUL byte up front."""
    if p.suffix.lower() in TEXT_EXT or p.suffix == "" or p.name.startswith("."):
        return True
    try:
        return b"\x00" not in p.open("rb").read(4096)
    except OSError:
        return False


def _scan_stage() -> list[str]:
    findings: list[str] = []
    for p in sorted(STAGE.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(STAGE).as_posix()
        is_asset = (p.suffix.lower() in ALLOW_BIN_SUFFIX
                    and p.relative_to(STAGE).parts[0] in ALLOW_BIN_DIRS
                    and p.stat().st_size <= MAX_BIN)
        if not _is_text(p) and not is_asset:
            findings.append(f"{rel}: not a text artifact in a public download")
            continue
        if is_asset:
            # A PNG can still carry an absolute path in a text chunk. Cheap to check, so check.
            blob = p.read_bytes()
            for pat in STEWARD_PAT:
                if pat.encode("utf-8") in blob:
                    findings.append(f"{rel}: names the steward's machine ({pat}) in binary content")
            continue
        body = p.read_text(encoding="utf-8", errors="ignore")
        for pat in STEWARD_PAT:
            if pat in body:
                findings.append(f"{rel}: names the steward's machine ({pat})")
        m = KEY_SHAPES.search(body)
        if m:
            findings.append(f"{rel}: key-shaped string {m.group(0)[:6]}...")
        if PEM_HEAD.search(body):
            findings.append(f"{rel}: PEM private-key header")
    return findings


def _zip() -> tuple[Path, str]:
    for d in (CHAT_DIST, STACK_DIST):
        d.mkdir(parents=True, exist_ok=True)
    out = CHAT_DIST / ZIP_NAME
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(STAGE.rglob("*")):
            if p.is_file():
                z.write(p, Path("lygo-llm-console-public") / p.relative_to(STAGE))
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    (CHAT_DIST / (ZIP_NAME + ".sha256")).write_text(f"{sha}  {ZIP_NAME}\n", encoding="utf-8")
    shutil.copy2(out, STACK_DIST / ZIP_NAME)
    shutil.copy2(CHAT_DIST / (ZIP_NAME + ".sha256"), STACK_DIST / (ZIP_NAME + ".sha256"))
    return out, sha


def main(argv: list[str]) -> int:
    check = "--check" in argv
    version = CONSOLE_VERSION_FILE.read_text(encoding="utf-8").splitlines()[0].strip()
    kept, dropped = _copy_tree()
    _patch_copy()
    _write_extras()
    findings = _scan_stage()
    print(f"console release : {version}")
    print(f"files staged    : {kept}")
    print(f"excluded        : {len(dropped)} file(s) beyond the directory exclusions")
    for d in dropped[:12]:
        print("   - " + d)
    if len(dropped) > 12:
        print(f"   ... and {len(dropped) - 12} more")
    if findings:
        print(f"\nREFUSED — {len(findings)} finding(s) in the staged public tree:")
        for f in findings[:40]:
            print("   " + f)
        return 1
    if check:
        print("\n--check: nothing written. The staged tree is clean.")
        return 0
    out, sha = _zip()
    print(f"\n{out}")
    print(sha)
    print("bytes", out.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
