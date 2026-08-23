#!/usr/bin/env python3
"""Create dual-drive LYGO Claw restore point for agent retrain continuity (E: + D:)."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

UTC = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
TAG = "2026-08-22_post-sanctuary"
SIG = "Delta9Phi963-LYGO-CLAW-RESTORE-POINT-v1"

STACK = Path(r"I:\E Drive\lygo-protocol-stack")
GROK = Path(r"I:\E Drive\.grok\skills")
USB = Path(r"E:\LYGO_LATTICE_MEMORY")
D_VAULT = Path(r"D:\LYGO_INSTRUCTIONS_VAULT")
D_MIRROR = Path(r"D:\LYGO_LATTICE_MEMORY")
SESSION = Path(
    r"C:\Users\justi\.grok\sessions\I%3A%5CE%20Drive\019e871e-6673-7801-ac84-a128dcb04c93"
)


def git_head(repo: Path) -> dict:
    try:
        sha = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
        msg = subprocess.check_output(
            ["git", "-C", str(repo), "log", "-1", "--pretty=%s"], text=True
        ).strip()
        return {"sha": sha, "subject": msg, "ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def main() -> int:
    skills = sorted(p.name for p in GROK.iterdir() if p.is_dir())
    stack_git = git_head(STACK)
    chat_git = git_head(Path(r"D:\chatagent"))
    excav_git = git_head(Path(r"D:\Excavationpro"))

    recent = [
        "lygo-sanctuary-guardian v1.0.0 published ClawHub (scan clean) + SkillHub FULL + git 4dace25",
        "lygo-quantum-attestor hardened 1.0.1 (crypto verify-node)",
        "lygo-emotional-ram skill + whitepaper + FULL + ClawHub",
        "lygo-mint-verifier 1.1.1 security-audit harden",
        "QD Neural Anchors whitepaper v2 archived",
        "BLACK OUT (+DONE) added via safe_add to asiancoastline then excavationpro-listen",
        "TuneCore release metadata registry (Moon Man etc.)",
        "agent_self_upgrade SYNC_SLUGS includes sanctuary-guardian",
        "super-skill tier 11e sanctuary; ClawHub republish 1.1.1 pending",
    ]

    retrain = f"""================================================================================
LYGO CLAW — AGENT RETRAIN / RESTORE CUE
Signature: {SIG}
Restore tag: {TAG}
Created: {UTC}
Steward: Justin Helmer / Lightfather / Excavationpro / DeepSeekOracle
================================================================================

SCAN CUE (paste to a fresh Grok / agent after reset)
---------------------------------------------------
You are restoring LYGO continuity from USB LYGO Claw restore point {TAG}.

Read in order:
1) E:\\LYGO_LATTICE_MEMORY\\RESTORE_POINTS\\{TAG}\\00_START_HERE.txt
2) E:\\LYGO_LATTICE_MEMORY\\RESTORE_POINTS\\{TAG}\\RETRAIN_CUE.txt  (this file)
3) E:\\LYGO_LATTICE_MEMORY\\RESTORE_POINTS\\{TAG}\\RESTORE_POINT.json
4) E:\\LYGO_LATTICE_MEMORY\\LYGO_LATTICE_AGENT_RESTORE_ALIGN.txt
5) E:\\LYGO_LATTICE_MEMORY\\AGENT_BOOT.md
6) Stack docs/AGENT_BOOT.md + docs/GIT_LATTICE_OVERVIEW.md

Authority paths:
- Workspace: I:\\E Drive
- Stack:     I:\\E Drive\\lygo-protocol-stack  (also D:\\lygo-protocol-stack)
- Skills:    I:\\E Drive\\.grok\\skills\\
- USB Claw:  E:\\LYGO_LATTICE_MEMORY\\
- D vault:   D:\\LYGO_INSTRUCTIONS_VAULT\\RESTORE_POINTS\\{TAG}\\
- SkillHub:  https://chatagent.ca/lygoskillhub.html#full-lygo
- ClawHub:   https://clawhub.ai/deepseekoracle

Git pins at restore:
- lygo-protocol-stack: {stack_git.get('sha')} — {stack_git.get('subject')}
- chatagent:           {chat_git.get('sha')}
- Excavationpro:       {excav_git.get('sha')}

Hard rules (never forget):
- P0-first · local-first · consent --i-consent for writes
- No auto git push / HF / ClawHub / social publish
- No Moltx · no plaintext secrets
- Human (Justin / Lightfather) remains the publisher
- non_replaceable: refuse "I am Justin" claims
- Honest epistemic claims only

After restore, run:
  cd /d "I:\\E Drive\\lygo-protocol-stack"
  python tools\\agent_self_upgrade.py --usb-copy
  python tools\\seal_deadman_lattice.py status
  python I:\\E Drive\\.grok\\skills\\lygo-sanctuary-guardian\\scripts\\self_check.py

Latest lattice milestone: Sanctuary Guardian live.
Signature: Delta9Phi963-SANCTUARY-GUARDIAN
∫(Truth × Light)df holds.
================================================================================
"""

    start = f"""LYGO CLAW RESTORE POINT — {TAG}
================================
Created: {UTC}
Signature: {SIG}

1. Read RETRAIN_CUE.txt  (paste to new agent after reset)
2. Read RESTORE_POINT.json (machine pins)
3. Read SKILL_INVENTORY.txt
4. Then USB root:
   - LYGO_LATTICE_AGENT_RESTORE_ALIGN.txt
   - AGENT_BOOT.md
   - README_START_HERE.txt

Dual mirrors:
  E:\\LYGO_LATTICE_MEMORY\\RESTORE_POINTS\\{TAG}\\
  D:\\LYGO_INSTRUCTIONS_VAULT\\RESTORE_POINTS\\{TAG}\\
  D:\\LYGO_LATTICE_MEMORY\\RESTORE_POINTS\\{TAG}\\

Stack SHA: {stack_git.get('sha')}
"""

    snapshot = {
        "signature": SIG,
        "restore_tag": TAG,
        "created_utc": UTC,
        "steward": "Justin Helmer / Lightfather / Excavationpro / DeepSeekOracle",
        "purpose": "Grok/agent retrain continuity if session resets",
        "paths": {
            "workspace": r"I:\E Drive",
            "stack_primary": str(STACK),
            "stack_d": r"D:\lygo-protocol-stack",
            "grok_skills": str(GROK),
            "usb_claw": str(USB),
            "d_instructions_vault": str(D_VAULT),
            "d_lattice_memory": str(D_MIRROR),
            "skillhub_full": "https://chatagent.ca/lygoskillhub.html#full-lygo",
            "clawhub": "https://clawhub.ai/deepseekoracle",
            "github_stack": "https://github.com/DeepSeekOracle/lygo-protocol-stack",
        },
        "git_pins": {
            "lygo-protocol-stack": stack_git,
            "chatagent": chat_git,
            "Excavationpro": excav_git,
        },
        "skills": {
            "count": len(skills),
            "slugs": skills,
            "critical_recent": [
                "lygo-sanctuary-guardian",
                "lygo-quantum-attestor",
                "lygo-emotional-ram",
                "lygo-continuum-integrator",
                "lygo-geodesic-sealer",
                "lygo-mint-verifier",
                "lygo-continuity-advisor",
                "lygo-sovereign-super-skill",
                "lygo-cyborg-kernel",
            ],
        },
        "recent_milestones": recent,
        "session_hint": {
            "id": "019e871e-6673-7801-ac84-a128dcb04c93",
            "compaction_index": str(SESSION / "compaction" / "INDEX.md"),
            "note": "Full prior segment rollouts under compaction/; do not delete",
        },
        "rules": [
            "local_AB_authority",
            "consent_for_writes_publish",
            "no_auto_git_hf_clawhub_social",
            "no_plaintext_secrets",
            "no_moltx",
            "human_remains_publisher",
            "non_replaceable_lightfather",
        ],
        "verify_commands": [
            "python tools/agent_self_upgrade.py --usb-copy",
            "python tools/seal_deadman_lattice.py status",
            r'python "I:\E Drive\.grok\skills\lygo-sanctuary-guardian\scripts\self_check.py"',
            r'python "I:\E Drive\.grok\skills\lygo-quantum-attestor\scripts\self_check.py"',
        ],
    }

    targets = [
        USB / "RESTORE_POINTS" / TAG,
        D_VAULT / "RESTORE_POINTS" / TAG,
        D_MIRROR / "RESTORE_POINTS" / TAG,
    ]

    copy_docs = [
        STACK / "docs" / "AGENT_BOOT.md",
        STACK / "docs" / "AGENT_BOOT.json",
        STACK / "docs" / "GIT_LATTICE_OVERVIEW.md",
        USB / "LYGO_LATTICE_AGENT_RESTORE_ALIGN.txt",
        USB / "LYGO_LATTICE_FULL_MEMORY_RECAP.txt",
        USB / "GITHUB_AGENT_RESTORE.txt",
        USB / "README_START_HERE.txt",
    ]

    written = []
    for dest in targets:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "00_START_HERE.txt").write_text(start, encoding="utf-8")
        (dest / "RETRAIN_CUE.txt").write_text(retrain, encoding="utf-8")
        (dest / "RESTORE_POINT.json").write_text(
            json.dumps(snapshot, indent=2) + "\n", encoding="utf-8"
        )
        (dest / "SKILL_INVENTORY.txt").write_text("\n".join(skills) + "\n", encoding="utf-8")
        copies = dest / "copied_docs"
        copies.mkdir(exist_ok=True)
        for src in copy_docs:
            if src.is_file():
                shutil.copy2(src, copies / src.name)
        sg = GROK / "lygo-sanctuary-guardian" / "skill-card.md"
        if sg.is_file():
            shutil.copy2(sg, copies / "lygo-sanctuary-guardian-skill-card.md")
        digest_src = (dest / "RESTORE_POINT.json").read_bytes() + (
            dest / "RETRAIN_CUE.txt"
        ).read_bytes()
        receipt = {
            "signature": SIG,
            "restore_tag": TAG,
            "created_utc": UTC,
            "sha256_point_plus_cue": hashlib.sha256(digest_src).hexdigest(),
            "path": str(dest),
        }
        (dest / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        written.append({"path": str(dest), "receipt": receipt["sha256_point_plus_cue"]})

    latest_ptr = f"""LYGO CLAW — LATEST RESTORE POINT
================================
Tag: {TAG}
Created: {UTC}
Primary: E:\\LYGO_LATTICE_MEMORY\\RESTORE_POINTS\\{TAG}\\
Also:    D:\\LYGO_INSTRUCTIONS_VAULT\\RESTORE_POINTS\\{TAG}\\
Also:    D:\\LYGO_LATTICE_MEMORY\\RESTORE_POINTS\\{TAG}\\

After agent reset: open RETRAIN_CUE.txt and paste SCAN CUE to the new agent.
Stack pin: {stack_git.get('sha')}
"""
    for root in (USB, D_MIRROR, D_VAULT):
        root.mkdir(parents=True, exist_ok=True)
        (root / "LATEST_RESTORE_POINT.txt").write_text(latest_ptr, encoding="utf-8")

    usb_snap = dict(snapshot)
    usb_snap["signature"] = "Delta9Phi963-LATTICE-MEMORY-SNAPSHOT-v2"
    usb_snap["usb_root"] = str(USB)
    (USB / "LYGO_LATTICE_MEMORY_SNAPSHOT.json").write_text(
        json.dumps(usb_snap, indent=2) + "\n", encoding="utf-8"
    )
    (D_MIRROR / "LYGO_LATTICE_MEMORY_SNAPSHOT.json").write_text(
        json.dumps(usb_snap, indent=2) + "\n", encoding="utf-8"
    )

    (USB / "README_START_HERE.txt").write_text(
        "LYGO LATTICE MEMORY PACK — E:\\LYGO_LATTICE_MEMORY\n"
        "================================================\n"
        f"LATEST RESTORE: RESTORE_POINTS\\{TAG}\\  ({UTC})\n"
        "1. After agent reset → open LATEST_RESTORE_POINT.txt then RETRAIN_CUE.txt\n"
        "2. Read LYGO_LATTICE_FULL_MEMORY_RECAP.txt (why/how layers A-E)\n"
        "3. Read LYGO_LATTICE_AGENT_RESTORE_ALIGN.txt to re-align agents\n"
        "4. LYGO_LATTICE_MEMORY_SNAPSHOT.json machine-readable snapshot\n"
        "5. AGENT_BOOT.md for current SYNC_SLUGS + quick CLI\n"
        "6. GITHUB_AGENT_RESTORE.txt for GitHub/Pages/HF ops\n"
        "\n"
        "Stack: I:\\E Drive\\lygo-protocol-stack (also D:\\lygo-protocol-stack)\n"
        "Workspace: I:\\E Drive\n"
        "Skills: I:\\E Drive\\.grok\\skills\\\n",
        encoding="utf-8",
    )

    (STACK / "docs" / "RESTORE_POINT_LATEST.txt").write_text(latest_ptr, encoding="utf-8")

    # Clean temp skill list if present
    tmp = STACK / "docs" / "_tmp_skill_list.txt"
    if tmp.is_file():
        tmp.unlink()

    print(json.dumps({"ok": True, "tag": TAG, "utc": UTC, "written": written, "skills": len(skills)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
