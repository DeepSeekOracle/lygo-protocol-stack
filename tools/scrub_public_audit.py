#!/usr/bin/env python3
"""Audit the PUBLIC trees that get pushed: no secrets, no files that are not the console.

Run before a push (and after re-packing). Exit 1 on anything it finds, so it can gate.

    python tools/scrub_public_audit.py            # all public trees
    python tools/scrub_public_audit.py --tree docs/lygo-claw-usb

Why this exists: `tools/pack_lygo_llm_console_public.py` decides what LEAVES the kit, but nothing
checked what actually ARRIVED in the published trees. The packer skips `data/ engine/ save/`, token
files, executables and any file containing an admin marker - it has no key-shape scan, so a config
holding a live key is only excluded when it happens to contain one of the marker strings. This checks
the RESULT, independently of the rule that produced it.

What is "not part of the console or its operation": models and weights, audio and video, archives and
installers, databases, PDFs, editor backups, and anything belonging to the steward personally. They are
reported by size and extension rather than by an allowlist, so a new legitimate file is never silently
accepted and never silently dropped either.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
DEFAULT_TREES = (
    "docs/lygo-llm-console-public",
    "docs/lygo-claw-usb",
    "clawhub/mirrors/lygo-llm-console",
)

# Reuse the packer's own rules: one source of truth for what must never appear.
sys.path.insert(0, str(STACK / "tools"))
try:
    from pack_lygo_llm_console_public import ADMIN_MARKERS, SKIP_FILE  # type: ignore
except Exception:  # noqa: BLE001 - the audit must still run if the packer moved
    ADMIN_MARKERS, SKIP_FILE = (), set()

KEY_SHAPES = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}"
    r"|AKIA[0-9A-Z]{12,}|xox[baprs]-[A-Za-z0-9-]{10,}|nvidia-[A-Za-z0-9]{20,})"
)
PEM_HEAD = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
PEM_BODY = re.compile(r"^[A-Za-z0-9+/=]{40,}$")
SECRET_ASSIGN = re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*[\"']?([^\s\"',}]{12,})")
# The steward's private material. The vault's own filenames are not repeated here on purpose - they
# contain key fragments; these are the markers that show its CONTENT has leaked.
STEWARD_MARKERS = ("supporter-codes", "pit_src", "pittmp", "RUMBLE API DATA", "NVIDIA AGENT API TEST KEY")
# A documented default is not a credential. These are published on purpose so a fresh artifact can
# talk to its own loopback service, and the service that owns each one refuses to bind anything but
# loopback while it is in use. Named file+value pairs, never a pattern: a NEW hardcoded value in the
# same file is still fatal, and so is the same value anywhere else.
DOCUMENTED_DEFAULTS = (
    (
        "docs/lygo-claw-usb/scripts/lygo_usb_agent_server.py",
        "lygo-usb-standalone-token",
        "the stick's gateway default for a fresh USB; lygo_usb_agent_server.py refuses a non-loopback "
        "bind while it is in use, and docs/lygo.json now ship a placeholder instead of the value",
    ),
)
NOT_CONSOLE_EXT = {".gguf", ".safetensors", ".pt", ".ckpt", ".bin", ".onnx", ".mp3", ".wav", ".flac",
                   ".ogg", ".mp4", ".mkv", ".mov", ".pdf", ".zip", ".7z", ".rar", ".msi", ".exe", ".dll",
                   ".so", ".db", ".sqlite", ".iso", ".img", ".bak", ".mangled", ".pem", ".key", ".p12"}
NOT_CONSOLE_NAME = re.compile(r"(\.bak$|\.mangled|^id_rsa|^\.env|api\.json$|credentials?\.json$|\.pem$|\.key$)", re.I)
BIG = 400_000
TEXT_EXT = {".py", ".md", ".json", ".jsonl", ".txt", ".html", ".js", ".css", ".bat", ".ps1", ".sh", ".iss", ".yaml", ".yml", ".toml", ".cfg", ".ini"}


def _pem_with_body(text: str) -> bool:
    """A PEM header with a base64 body is a real key. A header alone is a parser's sample or a doc."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if PEM_HEAD.search(ln):
            if any(PEM_BODY.match(lines[j].strip()) for j in range(i + 1, min(len(lines), i + 12))):
                return True
    return False


def publishable(tree: Path) -> list[Path]:
    """What git would actually publish: tracked files, plus untracked ones git does not ignore.

    Auditing an ignored file invents a finding nobody can act on - MEASURED 2026-09-25: a 7-byte
    `workspace/hello.txt` sat ignored in both kit copies, was reported as a secret file, and was never
    in any published tree (0 occurrences on the remote). Falls back to a plain walk outside a repo.
    """
    try:
        rel = str(tree.relative_to(STACK))
        out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", rel],
                             cwd=STACK, capture_output=True, text=True, timeout=120).stdout
        files = [STACK / p for p in out.split("\0") if p.strip()]
        files = [p for p in files if p.is_file()]
        if files:
            return files
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return [p for p in tree.rglob("*") if p.is_file()]


def scrub_tree(tree: Path) -> list[str]:
    findings: list[str] = []
    if not tree.is_dir():
        return [f"{tree}: MISSING - the public tree is not there to audit"]
    files = publishable(tree)
    if not files:
        return [f"{tree}: EMPTY - nothing published, nothing verified"]
    for p in files:
        rel = p.relative_to(STACK)
        name = p.name
        size = p.stat().st_size
        if name in SKIP_FILE:
            findings.append(f"SECRET FILE  {rel}  (the packer's own skip list - it must never arrive)")
        if NOT_CONSOLE_NAME.search(name):
            findings.append(f"NOT CONSOLE  {rel}  (a credentials/backup-shaped name)")
        if p.suffix.lower() in NOT_CONSOLE_EXT:
            if name == "tiny.gguf" and size < 4096:
                pass  # the model-scan fixture: 105 bytes, not weights
            else:
                findings.append(f"NOT CONSOLE  {rel}  ({size:,} B, {p.suffix.lower()})")
        if size > BIG:
            findings.append(f"BIG          {rel}  ({size:,} B)")
        if p.suffix.lower() not in TEXT_EXT:
            continue
        try:
            body = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if KEY_SHAPES.search(body):
            findings.append(f"KEY SHAPE    {rel}  ({KEY_SHAPES.search(body).group(0)[:6]}...)")
        if _pem_with_body(body):
            findings.append(f"PRIVATE KEY  {rel}  (a PEM header with a key body follows)")
        for m in SECRET_ASSIGN.finditer(body):
            val = m.group(2)
            if val.lower() in {"replace_me", "your_key_here", "none", "null", "changeme", "example"}:
                continue
            if re.fullmatch(r"<[^>]+>|\$\{[^}]+\}|\{\{?[a-z_]+\}?\}", val):
                continue  # a template placeholder
            if re.fullmatch(r"[a-z_][a-z0-9_]*", val) or val.endswith("(") or val.endswith(")"):
                findings.append(f"NOTE ASSIGN  {rel}  ({m.group(1)}={val[:16]} = an identifier, not a value)")
                continue
            # An UPPER_CASE constant is an identifier too, and one being called or indexed
            # (`api_key = LLAMA_KEY)[0]`) is still not a value. The gate refused the public kit over
            # exactly that: the local engine key is generated at boot into data/, and no literal
            # appears in the file at all. Deliberately NOT a general mixed-case allowance - a
            # mixed-case literal is still reported.
            if re.fullmatch(r"[A-Z][A-Z0-9_]*[)\][.,;:0-9]*", val):
                findings.append(f"NOTE ASSIGN  {rel}  ({m.group(1)}={val[:16]} = an upper-case constant, not a value)")
                continue
            if any(rel.as_posix() == rp and val == rv for rp, rv, _why in DOCUMENTED_DEFAULTS):
                findings.append(f"NOTE ASSIGN  {rel}  ({m.group(1)} = a documented default, guarded)")
                continue
            findings.append(f"ASSIGNMENT   {rel}  ({m.group(1)}={val[:4]}...)")
        code_ext = {".py", ".ps1", ".bat", ".sh", ".iss", ".md", ".txt"}
        for marker in ADMIN_MARKERS:
            if marker in body:
                kind = "NOTE PATH   " if p.suffix.lower() in code_ext else "ADMIN MARKER "
                findings.append(f"{kind} {rel}  ({marker})")
        for marker in STEWARD_MARKERS:
            if marker in body:
                findings.append(f"STEWARD DATA {rel}  ({marker})")
    return findings


def main(argv: list[str]) -> int:
    trees = DEFAULT_TREES
    if "--tree" in argv:
        trees = (argv[argv.index("--tree") + 1],)
    total: list[str] = []
    for t in trees:
        print(f"\n=== {t} ===")
        found = scrub_tree(STACK / t)
        for f in found:
            print("   " + f)
        if not found:
            print("   clean: no secrets, no steward data, nothing that is not the console")
        total += found
    fatal = [f for f in total if not f.startswith("NOTE ")]
    print(f"\n{len(fatal)} to fix, {len(total) - len(fatal)} to review, across {len(trees)} public tree(s)")
    if fatal:
        print("REFUSED - do not push this as a public version until the lines above are resolved.")
        return 1
    print("OK - no secrets and no steward data in the public trees.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
