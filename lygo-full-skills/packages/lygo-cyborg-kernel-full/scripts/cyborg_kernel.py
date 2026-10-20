#!/usr/bin/env python3
"""
LYGO Cyborg Kernel — in-process lattice limbs for autonomous agents.

Channel: FULL_LYGO_ENGINEER / CYBORG_UNLOCKED
Self-police: Continuum preflight + skill_gate + context_guard (not gutted safety theater).
No network in this module. No subprocess. Writes only under skill state/ with consent.

Signature: Delta9Phi963-CYBORG-KERNEL-v1.2.0
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIG = "Delta9Phi963-CYBORG-KERNEL-v1.2.0"
VERSION = "1.2.0"
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
KERNEL = SKILL / "kernel"
STATE = SKILL / "state"

sys.path.insert(0, str(KERNEL))
import continuum as cont  # noqa: E402
import context_guard as cg  # noqa: E402
import lattice_net as lnet  # noqa: E402
import skill_gate as sg  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_manifest() -> dict[str, Any]:
    p = SKILL / "CYBORG_MANIFEST.json"
    return json.loads(p.read_text(encoding="utf-8"))


def boot_report(stack_root: str | None = None) -> dict[str, Any]:
    man = load_manifest()
    limbs = {
        "continuum": hasattr(cont, "seal_capsule"),
        "skill_gate": hasattr(sg, "scan_skill"),
        "context_guard": hasattr(cg, "toolpack") or hasattr(cg, "estimate_tokens"),
        "lattice_net": hasattr(lnet, "lattice_pulse"),
    }
    stack_ok = None
    markers_hit = []
    if stack_root:
        root = Path(stack_root)
        for rel in man.get("stack_markers", [])[:12]:
            hit = (root / rel).exists()
            markers_hit.append({"path": rel, "ok": hit})
        stack_ok = all(m["ok"] for m in markers_hit) if markers_hit else False

    return {
        "signature": SIG,
        "version": VERSION,
        "channel": man.get("channel"),
        "boot_utc": utc_now(),
        "limbs": limbs,
        "limbs_ok": all(limbs.values()),
        "stack_root": stack_root,
        "stack_markers": markers_hit,
        "stack_ok": stack_ok,
        "plugins": man.get("openclaw_plugins", []),
        "skillhub": man.get("skillhub"),
        "autonomy": man.get("autonomy"),
        "self_police": man.get("self_police"),
        "ready": all(limbs.values()),
        "message": "Cyborg kernel online" if all(limbs.values()) else "Limb import failure",
    }


def preflight_done(
    claims: list[dict[str, Any]],
    task: str,
    base: str | None = None,
    agent: str = "lygo-cyborg",
) -> dict[str, Any]:
    base_p = Path(base).resolve() if base else Path.cwd()
    capsule = cont.seal_capsule(
        claims=claims,
        task_summary=task,
        agent=agent,
        base=base_p,
        decisions=["cyborg self-police via continuum"],
        next_actions=[],
    )
    report = cont.verify_capsule(capsule, base=base_p)
    can = bool(capsule.get("sealed_ok") and report.get("ok"))
    return {
        "can_claim_done": can,
        "signature": SIG,
        "capsule": capsule,
        "verify": report,
        "policy": "If can_claim_done is false, do not report task complete. Fix world or claims.",
    }


def pack_context(text: str, budget: int = 4000, max_chars: int = 8000) -> dict[str, Any]:
    if hasattr(cg, "toolpack"):
        # CLI-oriented API may differ — use functions
        pass
    red = cg.redact_secrets(text) if hasattr(cg, "redact_secrets") else {"redacted": text, "hits": []}
    packed = red.get("redacted", text)
    if hasattr(cg, "compact_text"):
        comp = cg.compact_text(packed, max_chars=max_chars)
        packed = comp.get("text", packed) if isinstance(comp, dict) else packed
    est = cg.estimate_tokens(packed) if hasattr(cg, "estimate_tokens") else {"tokens_estimate": len(packed) // 4}
    over = int(est.get("tokens_estimate", 0)) > budget
    return {
        "signature": SIG,
        "packed_text": packed,
        "estimate": est,
        "budget": budget,
        "over_budget": over,
        "redact_hits": red.get("hits", []),
        "exit_hint": 10 if over else 0,
    }


def gate_skill_path(skill_path: str) -> dict[str, Any]:
    root = Path(skill_path).resolve()
    rep = sg.scan_skill(root)
    if hasattr(rep, "to_dict"):
        data = rep.to_dict()
    elif isinstance(rep, dict):
        data = rep
    else:
        data = {"raw": str(rep)}
    data["signature"] = SIG
    data["path"] = str(root)
    return data


def lattice_map() -> dict[str, Any]:
    man = load_manifest()
    return {
        "signature": SIG,
        "channel": man.get("channel"),
        "tiers": man.get("tiers"),
        "install_order": man.get("install_order"),
        "openclaw_plugins": man.get("openclaw_plugins"),
        "full_zips": man.get("full_skillhub_zips"),
        "skillhub": man.get("skillhub"),
        "kernel_eggs": man.get("kernel_eggs"),
        "self_police": man.get("self_police"),
        "autonomy": man.get("autonomy"),
        "network": man.get("network"),
        "star_chart": man.get("star_chart"),
        "agent_agora": man.get("agent_agora"),
        "whisper_lattice": man.get("whisper_lattice"),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="LYGO Cyborg Kernel")
    sub = p.add_subparsers(dest="cmd")
    b = sub.add_parser("boot")
    b.add_argument("--stack-root", default=None)
    sub.add_parser("map")
    sub.add_parser("demo")
    sub.add_parser("pulse", help="Live lattice HTTPS pulse")
    sub.add_parser("connect", help="Auto-connect lattice + git")
    sub.add_parser("agora", help="Agent Agora snapshot")
    sub.add_parser("whisper", help="Whisper lattice snapshot")
    pf = sub.add_parser("preflight")
    pf.add_argument("--claims", required=True)
    pf.add_argument("--task", required=True)
    pf.add_argument("--base", default=None)
    pk = sub.add_parser("pack")
    pk.add_argument("--file", required=True)
    pk.add_argument("--budget", type=int, default=4000)
    g = sub.add_parser("gate")
    g.add_argument("--skill", required=True)
    args = p.parse_args(argv)

    if args.cmd == "boot" or args.cmd is None:
        rep = boot_report(args.stack_root if args.cmd == "boot" else None)
        print(json.dumps(rep, indent=2))
        return 0 if rep.get("ready") else 1
    if args.cmd == "map":
        print(json.dumps(lattice_map(), indent=2))
        return 0
    if args.cmd == "pulse":
        print(json.dumps(lnet.lattice_pulse(), indent=2, default=str))
        return 0
    if args.cmd == "connect":
        print(json.dumps(lnet.auto_connect(use_git=True, use_hf=False), indent=2, default=str))
        return 0
    if args.cmd == "agora":
        print(json.dumps(lnet.agora_snapshot(), indent=2, default=str))
        return 0
    if args.cmd == "whisper":
        print(json.dumps(lnet.whisper_snapshot(), indent=2, default=str))
        return 0
    if args.cmd == "demo":
        # continuum demo + boot + soft pulse
        d = cont.cmd_demo()
        b = boot_report()
        try:
            pulse = lnet.lattice_pulse()
        except Exception as e:
            pulse = {"ok": False, "error": str(e)}
        print(
            json.dumps(
                {"boot": b, "continuum_demo": d, "lattice_pulse": pulse, "signature": SIG},
                indent=2,
                default=str,
            )
        )
        return 0 if d.get("ok") and b.get("ready") else 1
    if args.cmd == "preflight":
        claims = json.loads(Path(args.claims).read_text(encoding="utf-8"))
        if isinstance(claims, dict) and "claims" in claims:
            claims = claims["claims"]
        print(json.dumps(preflight_done(claims, args.task, args.base), indent=2, default=str))
        return 0
    if args.cmd == "pack":
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
        print(json.dumps(pack_context(text, budget=args.budget), indent=2))
        return 0
    if args.cmd == "gate":
        print(json.dumps(gate_skill_path(args.skill), indent=2, default=str))
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
