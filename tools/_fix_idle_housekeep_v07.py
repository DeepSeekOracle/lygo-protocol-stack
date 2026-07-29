from pathlib import Path

p = Path(r"D:\lygo-protocol-stack\clawhub\mirrors\lygo-ollama-army\ollama_command_center\scripts\army_idle_housekeeping.py")
t = p.read_text(encoding="utf-8")

bad = 'def _external_writes_allowed(cfg: dict) -> bool:\\n    idle = (cfg or {}).get("idle_guardian") or {}\\n    return bool(idle.get("allow_external_memory_write", False))\\n\\n\\ndef main() -> int:'
good = '''def _external_writes_allowed() -> bool:
    idle = _idle_cfg()
    return bool(idle.get("allow_external_memory_write", False))


def main() -> int:'''
if bad in t:
    t = t.replace(bad, good)
    print("fixed external_writes def")
else:
    # try already-broken with real newlines partially
    import re
    t2, n = re.subn(
        r"def _external_writes_allowed\(cfg: dict\) -> bool:.*?def main\(\) -> int:",
        good,
        t,
        count=1,
        flags=re.S,
    )
    t = t2
    print("regex fix", n)

# Fix lyra core discovery
t = t.replace(
    """def _lyra_core() -> Path | None:
    for key in ("LYRA_CORE_ROOT", "LYRA_CORE"):
        raw = os.environ.get(key, "").strip()
        if raw:
            p = Path(raw)
            if (p / "memory").is_dir() or (p / "modules" / "lyra_brain.py").is_file():
                return p
    for candidate in (
        # removed hardcoded LYRA_CORE path
        _stack().parent / "LYRA_CORE",
        Path.home() / "LYRA_CORE",
    ):
        if (candidate / "memory").is_dir():
            return candidate
    return None
""",
    """def _lyra_core() -> Path | None:
    # v0.7.0: only when allow_external_memory_write + explicit LYRA_CORE_ROOT
    if not _external_writes_allowed():
        return None
    raw = (os.environ.get("LYRA_CORE_ROOT") or "").strip()
    if not raw:
        return None
    p = Path(raw)
    if (p / "memory").is_dir() or (p / "modules" / "lyra_brain.py").is_file():
        return p
    return None
""",
)

# Gate external ops
old = """def run_ops(ops: list[str]) -> dict:
    stack = _stack()
    summary: dict = {"ts": _utc(), "ops": {}, "all_ok": True}
    for name in ops:
        fn = OPS.get(name)
"""
new = """def run_ops(ops: list[str]) -> dict:
    stack = _stack()
    summary: dict = {"ts": _utc(), "ops": {}, "all_ok": True}
    external = {"three_brain_index", "self_grow_check", "living_memory_audit"}
    for name in ops:
        if name in external and not _external_writes_allowed():
            detail = {"ok": True, "skipped": "external_memory_write_disabled"}
            summary["ops"][name] = detail
            _log(name, True, detail)
            continue
        fn = OPS.get(name)
"""
if old in t:
    t = t.replace(old, new)
    print("run_ops gated")
else:
    print("run_ops miss")

# DEFAULT_OPS safer
t = t.replace(
    'DEFAULT_OPS = [\n    "memory_sync",\n    "three_brain_index",',
    'DEFAULT_OPS = [\n    "memory_sync",\n    # "three_brain_index",  # requires allow_external_memory_write',
)

p.write_text(t, encoding="utf-8")
print("ok bytes", len(t))
