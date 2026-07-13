#!/usr/bin/env python3
"""
LYGO Token Saver Hub — route mundane work to local Ollama (zero pay-to-go tokens).

Integrates army queue, pxpipe shrink, and savings journal.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

SIGNATURE = "Δ9Φ963-TOKEN-SAVER-HUB-v1"

ARMY_ROOT = Path(
    os.environ.get(
        "LYGO_ARMY_ROOT",
        Path.home() / ".grok" / "skills" / "lygo-ollama-army",
    )
)
if not ARMY_ROOT.is_dir():
    ARMY_ROOT = Path(r"I:\E Drive\.grok\skills\lygo-ollama-army")

CC = ARMY_ROOT / "ollama_command_center"
CONFIG = CC / "config" / "army_config.json"
TASKS = CC / "tasks"
RESULTS = CC / "results"
WORKSPACE = CC / "workspace"
JOURNAL = WORKSPACE / "token_saver_journal.jsonl"
STATUS_FILE = WORKSPACE / "token_saver_status.json"

ROUTE_MAP = {
    "summarize": ("classify", "Summarize briefly for LYGO memory. Output JSON: {\"summary\":\"...\",\"class\":\"mundane|action\"}"),
    "draft": ("draft-simple", "Draft a short helpful reply."),
    "classify": ("classify", "Classify and summarize for triage."),
    "triage": ("discord-triage", "Triage message priority and intent."),
    "explore": ("classify", "Explore/skim this text; return compact bullet summary only."),
}

DEFAULT_MODEL = os.environ.get("LYRA_OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def load_config() -> dict:
    if CONFIG.is_file():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def token_saver_cfg(cfg: dict) -> dict:
    return cfg.get("token_saver") or {}


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def stack_root(cfg: dict) -> Path | None:
    raw = (cfg.get("lygo_stack_root") or os.environ.get("LYGO_STACK_ROOT") or "").strip()
    return Path(raw) if raw else None


def ollama_ready() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=4) as resp:
            data = json.loads(resp.read().decode())
        return bool(data.get("models"))
    except Exception:
        return False


def ollama_chat(model: str, prompt: str, system: str = "", num_predict: int = 280) -> str:
    import urllib.error

    body = json.dumps(
        {
            "model": model,
            "messages": (
                ([{"role": "system", "content": system}] if system else [])
                + [{"role": "user", "content": prompt}]
            ),
            "stream": False,
            "options": {"temperature": 0.35, "num_predict": num_predict},
        }
    ).encode()
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        return (data.get("message") or {}).get("content", "")
    except urllib.error.URLError as exc:
        return f"[OLLAMA_ERR] {exc}"


def maybe_shrink(text: str, cfg: dict) -> tuple[str, bool, str]:
    ts_cfg = token_saver_cfg(cfg)
    threshold = int(ts_cfg.get("compress_threshold_chars", 6000))
    if len(text) < threshold:
        return text, False, "under_threshold"

    root = stack_root(cfg)
    if root and (root / "tools" / "pxpipe_lygo_for_agent.py").is_file():
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        try:
            from pxpipe_lygo.agent_helper import maybe_compress_context  # type: ignore

            shrunk = maybe_compress_context(text, target="grok")
            if shrunk and len(shrunk) < len(text) * 0.9:
                return shrunk, True, "pxpipe"
        except Exception:
            pass

    cap = int(ts_cfg.get("truncate_chars", threshold))
    if len(text) > cap:
        return text[:cap] + "\n...[truncated — use --file with pxpipe for full shrink]", True, "truncate"
    return text, False, "none"


def log_savings(
    *,
    route: str,
    chars_in: int,
    chars_out: int,
    compressed: bool,
    mode: str,
    model: str,
) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    saved_est = max(0, estimate_tokens(str(chars_in)) - estimate_tokens(str(chars_out)))
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "signature": SIGNATURE,
        "route": route,
        "mode": mode,
        "model": model,
        "chars_in": chars_in,
        "chars_out": chars_out,
        "tokens_saved_est": saved_est,
        "compressed": compressed,
        "api_avoided": True,
    }
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def journal_totals() -> dict:
    if not JOURNAL.is_file():
        return {"events": 0, "tokens_saved_est": 0}
    events = 0
    saved = 0
    for line in JOURNAL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            blob = json.loads(line)
            events += 1
            saved += int(blob.get("tokens_saved_est", 0))
        except json.JSONDecodeError:
            continue
    return {"events": events, "tokens_saved_est": saved}


def queue_and_wait(role: str, payload: dict, timeout: float = 90.0) -> dict:
    TASKS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    tid = f"token-saver-{uuid4().hex[:12]}"
    (TASKS / f"{tid}.task.json").write_text(
        json.dumps({"id": tid, "role": role, "payload": payload}),
        encoding="utf-8",
    )
    result_path = RESULTS / f"{tid}.result.json"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if result_path.is_file():
            return json.loads(result_path.read_text(encoding="utf-8"))
        time.sleep(1.5)
    return {"error": "timeout", "task_id": tid}


def route_local(
    action: str,
    text: str,
    *,
    sync: bool = True,
    model: str | None = None,
) -> dict:
    cfg = load_config()
    ts_cfg = token_saver_cfg(cfg)
    if not ts_cfg.get("enabled", True):
        return {"error": "token_saver.disabled", "escalate_api": True}

    role, hint = ROUTE_MAP.get(action, ("classify", "Help briefly."))
    model = model or ts_cfg.get("default_model", DEFAULT_MODEL)
    raw_len = len(text)
    shrunk, compressed, shrink_mode = maybe_shrink(text, cfg)

    if not ollama_ready():
        return {
            "error": "ollama_offline",
            "escalate_api": True,
            "hint": "Start Ollama or LYGO_USB_Daemon_Supervisor.ps1",
        }

    prefer_queue = bool(ts_cfg.get("prefer_queue", False))
    if sync and not prefer_queue:
        prompt = f"{hint}\n\n---\n{shrunk}"
        out = ollama_chat(model, prompt, system="LYGO local token saver. Be concise.")
        log_savings(
            route=action,
            chars_in=raw_len,
            chars_out=len(out),
            compressed=compressed,
            mode=f"sync/{shrink_mode}",
            model=model,
        )
        return {
            "route": action,
            "role": role,
            "mode": "sync",
            "model": model,
            "compressed": compressed,
            "shrink_mode": shrink_mode,
            "result": out,
            "tokens_saved_est": max(0, estimate_tokens(text) - estimate_tokens(out)),
        }

    payload = {"text": shrunk, "prompt": shrunk, "subrole": action}
    if action == "draft":
        payload = {"query": shrunk}
    if action == "triage":
        payload = {"content": shrunk, "author": "token-saver", "is_reply": False}

    result = queue_and_wait(role, payload, timeout=float(ts_cfg.get("queue_timeout_seconds", 90)))
    out_text = json.dumps(result.get("result", result))
    log_savings(
        route=action,
        chars_in=raw_len,
        chars_out=len(out_text),
        compressed=compressed,
        mode="queue",
        model=model,
    )
    return {
        "route": action,
        "role": role,
        "mode": "queue",
        "model": model,
        "compressed": compressed,
        "result": result,
        "tokens_saved_est": max(0, estimate_tokens(text) - estimate_tokens(out_text)),
    }


def build_status() -> dict:
    cfg = load_config()
    perf = cfg.get("performance") or {}
    sentinel_path = WORKSPACE / "sentinel_status.json"
    sentinel = {}
    if sentinel_path.is_file():
        sentinel = json.loads(sentinel_path.read_text(encoding="utf-8"))

    vault_mode = "alt" if os.environ.get("XAI_API_KEY_ALT") else ("main" if os.environ.get("XAI_API_KEY") else "no-vault")

    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=4) as resp:
            models = [m.get("name") for m in json.loads(resp.read().decode()).get("models", [])]
    except Exception:
        models = []

    totals = journal_totals()
    report = {
        "signature": SIGNATURE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "enabled": token_saver_cfg(cfg).get("enabled", True),
        "ollama_ok": bool(models),
        "models": models[:6],
        "vault_mode": vault_mode,
        "gateway_port": perf.get("gateway_port", 18789),
        "queue_unique": perf.get("queue_unique_tasks"),
        "sentinel_healthy": sentinel.get("healthy"),
        "lattice": (sentinel.get("lattice") or {}).get("summary"),
        "journal": totals,
        "mode": "local_first",
    }
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Token Saver Hub — local Ollama routing")
    ap.add_argument("--route", choices=sorted(ROUTE_MAP.keys()), help="Mundane task route")
    ap.add_argument("--file", "-f", help="Input file")
    ap.add_argument("--text", "-t", help="Inline text")
    ap.add_argument("--status", action="store_true", help="Print saver status JSON")
    ap.add_argument("--queue", action="store_true", help="Force army queue (async path)")
    ap.add_argument("--model", default=None, help="Ollama model override")
    args = ap.parse_args()

    if args.status:
        print(json.dumps(build_status(), indent=2))
        return 0

    if not args.route:
        ap.error("--route required unless --status")

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
    elif args.text:
        text = args.text
    else:
        ap.error("--file or --text required")

    out = route_local(args.route, text, sync=not args.queue, model=args.model)
    print(json.dumps(out, indent=2))
    return 0 if "error" not in out else 1


if __name__ == "__main__":
    raise SystemExit(main())