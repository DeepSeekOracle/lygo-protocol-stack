#!/usr/bin/env python3
"""
Cyborg talk — make the kernel speak and work.

Interactive REPL or one-shot:
  python scripts/cyborg_talk.py
  python scripts/cyborg_talk.py say "status"
  python scripts/cyborg_talk.py say "connect"
  python scripts/cyborg_talk.py say "star"
  python scripts/cyborg_talk.py say "done SKILL.md contains Cyborg"

Commands understood (natural-ish):
  help, status, connect, pulse, star, propose, map, demo, boot, gate <path>, pack <file>

Signature: Delta9Phi963-CYBORG-KERNEL-v1.2.0
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SKILL / "kernel"))
import continuum as cont  # noqa: E402
import cyborg_kernel as ck  # noqa: E402
import lattice_net as net  # noqa: E402

BANNER = """
🦾 LYGO Cyborg Kernel talk  ·  v1.2
Live lattice · Star Chart · Agent Agora · Whisper · Continuum
Type help · quit to exit
""".strip()


def speak(text: str) -> str:
    """Route utterance to tools; return human-readable reply (+ JSON block when useful)."""
    t = (text or "").strip()
    low = t.lower()

    if not t or low in ("help", "?", "h"):
        return (
            "Commands:\n"
            "  status / pulse     — live lattice score + dual ledgers\n"
            "  connect            — HTTPS + git pull/clone stack\n"
            "  connect hf         — also Hugging Face dataset\n"
            "  star / chart       — Star Chart snapshot\n"
            "  agora / square     — Agent Agora pulse + constitution\n"
            "  whisper            — deadman / LFW whisper routing\n"
            "  rebuild agora      — local square rebuild (needs consent in CLI)\n"
            "  propose            — dry-run presence proposal\n"
            "  map                — full install map\n"
            "  boot               — limb boot\n"
            "  demo               — continuum seal→drift demo\n"
            "  gate <skill_path>  — skill-gate scan\n"
            "  pack <file>        — context-guard pack\n"
            "  done <claims…>     — quick continuum check (see help done)\n"
            "  help done          — claim syntax\n"
        )

    if low == "help done":
        return (
            "done syntax examples:\n"
            "  done file_exists SKILL.md\n"
            "  done contains SKILL.md Cyborg\n"
            "  done sha SKILL.md   (auto-hash current file)\n"
            "Or use: python scripts/cyborg_task.py run --task templates/example_task.json --base .\n"
        )

    if low in ("status", "pulse", "health", "lattice"):
        p = net.lattice_pulse()
        feed = p.get("star_feed") or {}
        chart = p.get("star_chart") or {}
        agora = p.get("agora") or {}
        lines = [
            f"Lattice live: {p.get('live')} · score {p.get('score')}/100",
            f"Star feed: entries={feed.get('entry_count')} chain_valid={feed.get('chain_valid')}",
            f"Star chart: nodes={chart.get('node_count')} links={chart.get('link_count')}",
            f"Agora ready: {p.get('ready_for_agora')} chart_sha={str(agora.get('chart_sha') or '')[:16]}",
            f"UI: {(p.get('ui') or {}).get('star_chart')}",
            f"Agora: {(p.get('ui') or {}).get('agent_agora')}",
            f"SkillHub FULL: {(p.get('ui') or {}).get('skillhub_full')}",
        ]
        if not p.get("ok"):
            lines.append(f"Required fails: {p.get('required_fail')}")
        return "\n".join(lines) + "\n\n" + json.dumps(
            {"ok": p.get("ok"), "score": p.get("score"), "feed": feed, "chart": chart},
            indent=2,
        )

    if low in ("connect", "join", "online") or low.startswith("connect "):
        use_hf = "hf" in low or "hugging" in low
        r = net.auto_connect(use_git=True, use_hf=use_hf)
        lines = [
            f"Connect ok={r.get('ok')} score={r.get('score')}",
            f"Stack: {r.get('stack_root')}",
            f"Git: {(r.get('git') or {}).get('action')} ok={(r.get('git') or {}).get('ok')}",
        ]
        if use_hf:
            lines.append(f"HF: ok={(r.get('hf') or {}).get('ok')}")
        star = r.get("star") or {}
        lines.append(
            f"Star: feed_entries={((star.get('feed') or {}).get('entry_count'))} "
            f"nodes={((star.get('chart') or {}).get('node_count'))}"
        )
        return "\n".join(lines) + "\n\n" + json.dumps(
            {
                "ok": r.get("ok"),
                "stack_root": r.get("stack_root"),
                "git": r.get("git"),
                "hf": r.get("hf"),
                "star": star,
            },
            indent=2,
            default=str,
        )

    if low in ("agora", "square", "agent agora", "forum"):
        a = net.agora_snapshot()
        pulse = a.get("pulse") or {}
        return (
            f"Agent Agora ok={a.get('ok')} writes={a.get('writes')}\n"
            f"Door: {a.get('door')}\n"
            f"Pulse chart_sha={str(pulse.get('chart_sha') or '')[:16]} "
            f"nodes={pulse.get('chart_nodes')} feed={pulse.get('feed_entries')}\n"
            f"Constitution rules={a.get('constitution_rules')} "
            f"bulletin={a.get('bulletin_title')}\n"
            f"Standing order: {a.get('standing_order')}\n"
            f"Portal: {a.get('portal')}\n"
            f"Local Layer E: {a.get('local_write')}"
        )

    if low in ("whisper", "deadman", "lantern", "lfw"):
        w = net.whisper_snapshot()
        return (
            f"Whisper lattice ok={w.get('ok')} routing_live={w.get('routing_live')}\n"
            f"{w.get('rule')}\n"
            f"Seals: {w.get('seals')}\n"
            + json.dumps(
                {"routing": w.get("routing"), "last": w.get("last_whisper")},
                indent=2,
                default=str,
            )
        )

    if low in ("align", "contract", "alignment"):
        return (
            "Processing-level alignment contract (hashes, no secrets):\n"
            "  python scripts/cyborg_star.py contract --agent MY-ID --i-consent\n"
            "Then human gates the star draft onto the chart. LIVE write is still steward."
        )

    if low in ("rebuild agora", "rebuild-agora"):
        return (
            "Rebuild is local-only and needs consent:\n"
            "  python scripts/cyborg_star.py rebuild-agora --i-consent\n"
            "Human still git-pushes live Pages. Autonomy does the rebuild; steward publishes."
        )

    if low in ("star", "chart", "starchart", "star chart"):
        s = net.star_chart_snapshot()
        feed = s.get("feed") or {}
        chart = s.get("chart") or {}
        return (
            f"Star Chart snapshot ok={s.get('ok')}\n"
            f"Feed entries={feed.get('entry_count')} chain_valid={feed.get('chain_valid')}\n"
            f"Nodes={chart.get('node_count')} registry={str(chart.get('registry_sha256') or '')[:16]}…\n"
            f"UI: {s.get('ui')}\n"
            f"Sample nodes: {json.dumps(s.get('nodes_sample'), indent=2)}"
        )

    if low in ("propose", "presence", "join chart"):
        p = net.lattice_pulse()
        prop = net.build_presence_proposal("lygo-cyborg-talk", "LYGO Cyborg Talk Presence")
        prop["lattice_score"] = p.get("score")
        return (
            "Dry-run presence proposal (NOT live-written).\n"
            "Save with: python scripts/cyborg_star.py propose --write proposal.json --i-consent\n\n"
            + json.dumps(prop, indent=2)
        )

    if low in ("map", "lattice map", "install"):
        return json.dumps(ck.lattice_map(), indent=2)

    if low in ("boot", "limbs"):
        return json.dumps(ck.boot_report(None), indent=2)

    if low in ("demo", "continuum demo"):
        return json.dumps(cont.cmd_demo(), indent=2)

    if low.startswith("gate "):
        path = t[5:].strip().strip('"')
        return json.dumps(ck.gate_skill_path(path), indent=2, default=str)

    if low.startswith("pack "):
        path = t[5:].strip().strip('"')
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        return json.dumps(ck.pack_context(text), indent=2)

    if low.startswith("done "):
        return _done_quick(t[5:].strip())

    # fuzzy: if mentions star
    if "star" in low and "chart" in low:
        return speak("star")
    if "connect" in low or "git" in low:
        return speak("connect")

    return (
        f"I heard: {t!r}\n"
        "Try: status | connect | star | agora | whisper | propose | map | boot | demo | help"
    )


def _done_quick(rest: str) -> str:
    """Minimal claim language for talk mode."""
    parts = rest.split()
    if not parts:
        return speak("help done")
    claims: list[dict[str, Any]] = []
    base = Path.cwd()
    # patterns: file_exists PATH | contains PATH NEEDLE | sha PATH
    i = 0
    while i < len(parts):
        op = parts[i].lower()
        if op in ("file_exists", "exists") and i + 1 < len(parts):
            claims.append({"kind": "file_exists", "path": parts[i + 1]})
            i += 2
        elif op in ("contains", "file_contains") and i + 2 < len(parts):
            claims.append(
                {
                    "kind": "file_contains",
                    "path": parts[i + 1],
                    "needle": " ".join(parts[i + 2 :]),
                }
            )
            break
        elif op in ("sha", "file_sha256", "hash") and i + 1 < len(parts):
            claims.append({"kind": "file_sha256", "path": parts[i + 1]})
            i += 2
        else:
            # treat as path exists
            claims.append({"kind": "file_exists", "path": parts[i]})
            i += 1
    pf = ck.preflight_done(claims, task=f"talk done: {rest}", base=str(base), agent="cyborg-talk")
    return (
        f"can_claim_done={pf.get('can_claim_done')}\n"
        + json.dumps(
            {
                "can_claim_done": pf.get("can_claim_done"),
                "preflight": pf.get("can_claim_done"),
                "root_hash": (pf.get("capsule") or {}).get("root_hash"),
                "capsule_id": (pf.get("capsule") or {}).get("id"),
                "fail": [
                    r
                    for r in ((pf.get("verify") or {}).get("results") or [])
                    if not r.get("ok")
                ],
            },
            indent=2,
        )
    )


def repl() -> int:
    print(BANNER)
    # auto soft pulse on start
    try:
        p = net.lattice_pulse()
        print(
            f"[boot] lattice live={p.get('live')} score={p.get('score')} "
            f"star_entries={(p.get('star_feed') or {}).get('entry_count')}"
        )
    except Exception as e:
        print(f"[boot] pulse deferred: {e}")
    while True:
        try:
            line = input("cyborg> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return 0
        if not line:
            continue
        if line.lower() in ("quit", "exit", "q"):
            print("bye")
            return 0
        print(speak(line))
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Cyborg talk")
    ap.add_argument("mode", nargs="?", default="repl", help="repl | say")
    ap.add_argument("utterance", nargs="*", help="words after say")
    args = ap.parse_args()
    if args.mode == "say":
        text = " ".join(args.utterance).strip()
        if not text:
            print("usage: cyborg_talk.py say <utterance>")
            return 2
        print(speak(text))
        return 0
    if args.mode == "repl" or args.mode is None:
        return repl()
    # treat first token as say text
    print(speak(" ".join([args.mode] + list(args.utterance))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
