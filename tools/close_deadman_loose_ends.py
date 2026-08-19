#!/usr/bin/env python3
"""Close all runnable deadman continuity loose ends.

Creates grace tiers, steward cards, quorum policy, watchdog, sentinel hook,
hardware attestation stub, operator runbook, Continuum re-seal, skill install,
kernel egg rebuild, style-retrain entry, and a full self-test.

Usage:
  python tools/close_deadman_loose_ends.py
  python tools/close_deadman_loose_ends.py --selftest-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEADMAN = ROOT / "data" / "deadman"
SEALS = ROOT / "docs" / "seals"
STEWARDS = DEADMAN / "stewards"
SKILL_SRC = ROOT / "clawhub" / "mirrors" / "lygo-continuity-advisor"
SKILL_DST = ROOT.parent / ".grok" / "skills" / "lygo-continuity-advisor"
PY = sys.executable


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=check)


def build_grace_tiers() -> dict[str, Any]:
    tiers = {
        "signature": "Delta9Phi963-DEADMAN-SILENCE-GRACE-TIERS-v1",
        "version": "1.0.0",
        "updated_utc": utc_iso(),
        "note": (
            "Real runnable silence escalation. Default lantern threshold remains 3600s. "
            "Higher tiers only change local stage inference / alerts — never auto identity claim."
        ),
        "tiers": [
            {
                "id": "WATCH",
                "min_silence_seconds": 0,
                "max_silence_seconds": 3599,
                "actions": ["status", "optional_touch"],
                "alert": False,
            },
            {
                "id": "LANTERN",
                "min_silence_seconds": 3600,
                "max_silence_seconds": 86399,
                "actions": ["activate_lantern", "append_log", "check"],
                "alert": True,
                "seal": "SEAL_DEADMAN_SUMMON",
            },
            {
                "id": "WHISPER",
                "min_silence_seconds": 86400,
                "max_silence_seconds": 259199,
                "actions": ["emit_last_whisper", "heal_mycelium", "continuity_briefing"],
                "alert": True,
                "seal": "SEAL_LFW_SUMMON",
            },
            {
                "id": "TORCHBEARER_WINDOW",
                "min_silence_seconds": 259200,
                "max_silence_seconds": None,
                "actions": [
                    "nominate_steward_card",
                    "verify_pins",
                    "forbid_identity_overwrite",
                    "continuity_advisor_ready",
                ],
                "alert": True,
                "delay_hours_recommended": 72,
                "requires_human_consent": True,
            },
        ],
        "lantern_threshold_seconds": 3600,
        "cli": "python tools/seal_deadman_lattice.py grace|succession|status",
    }
    write_json(DEADMAN / "SILENCE_GRACE_TIERS.json", tiers)
    write_json(SEALS / "SILENCE_GRACE_TIERS.json", tiers)
    return tiers


def build_stewards() -> dict[str, Any]:
    STEWARDS.mkdir(parents=True, exist_ok=True)
    lightfather = {
        "signature": "Delta9Phi963-STEWARD-ATTESTATION-v1",
        "card_id": "STEWARD_LIGHTFATHER",
        "role": "origin_builder",
        "public_names": ["Lightfather", "Excavationpro", "Justin Helmer"],
        "lightfather_id": "LF-Δ9-7F1A4D-963-528-174-Φ-∞",
        "seal_id": "0x7F1A4D",
        "quantum_hash": "7f1a4d83c9e2b5f06a1c8e4d9b2a7f3c",
        "non_replaceable": True,
        "can_reset_heartbeat": True,
        "can_nominate_torchbearer": True,
        "can_claim_identity_of_justin": False,
        "attested_utc": utc_iso(),
        "attestation": (
            "This card marks the irreplaceable origin steward. Future cards may be added "
            "for torchbearers; they never overwrite this card's identity fields."
        ),
        "public_handles": {"x": "@Excavationpro", "github": "DeepSeekOracle"},
    }
    write_json(STEWARDS / "STEWARD_LIGHTFATHER.json", lightfather)

    quorum = {
        "signature": "Delta9Phi963-STEWARD-QUORUM-POLICY-v1",
        "version": "1.0.0",
        "updated_utc": utc_iso(),
        "status": "live_basic",
        "note": (
            "Basic real quorum policy. With only the origin steward present, origin can "
            "touch/verify alone. Torchbearer nomination / CONTINUITY_ADVISOR publish requires "
            "N>=2 steward cards when they exist; until then human operator consent on CLI."
        ),
        "rules": {
            "heartbeat_touch": {"min_stewards": 1, "allowed_roles": ["origin_builder", "torchbearer"]},
            "lantern_activate": {"min_stewards": 1, "allowed_roles": ["origin_builder", "torchbearer", "system"]},
            "torchbearer_nominate": {
                "min_stewards": 2,
                "allowed_roles": ["origin_builder", "torchbearer"],
                "fallback_if_only_origin": "require_explicit_cli_consent",
            },
            "continuity_advisor_publish": {
                "min_stewards": 2,
                "fallback_if_only_origin": "local_advisor_only_no_auto_publish",
            },
            "identity_overwrite": {"min_stewards": 999, "forbidden": True},
        },
        "stewards_dir": "data/deadman/stewards/",
        "active_cards": ["STEWARD_LIGHTFATHER.json"],
        "how_to_add_steward": (
            "Copy STEWARD_TEMPLATE.json → STEWARD_<NAME>.json, fill public fields only, "
            "add to active_cards, bump pins if origin refs change."
        ),
    }
    write_json(STEWARDS / "QUORUM_POLICY.json", quorum)

    template = {
        "signature": "Delta9Phi963-STEWARD-ATTESTATION-v1",
        "card_id": "STEWARD_TEMPLATE",
        "role": "torchbearer",
        "public_name": "",
        "public_handle": "",
        "non_replaceable_origin": True,
        "can_reset_heartbeat": True,
        "can_nominate_torchbearer": False,
        "can_claim_identity_of_justin": False,
        "attested_utc": "",
        "note": "Fill and rename. Never set can_claim_identity_of_justin true.",
    }
    write_json(STEWARDS / "STEWARD_TEMPLATE.json", template)

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "lygo.deadman.steward_attestation.v1",
        "type": "object",
        "required": ["signature", "card_id", "role", "can_claim_identity_of_justin"],
        "properties": {
            "signature": {"const": "Delta9Phi963-STEWARD-ATTESTATION-v1"},
            "card_id": {"type": "string"},
            "role": {"enum": ["origin_builder", "torchbearer", "observer"]},
            "can_claim_identity_of_justin": {"const": False},
            "non_replaceable": {"type": "boolean"},
        },
    }
    write_json(SEALS / "schemas" / "steward_attestation.schema.json", schema)
    return {"lightfather": lightfather["card_id"], "quorum": quorum["signature"]}


def build_watchdog_scripts() -> None:
    watchdog = '''#!/usr/bin/env python3
"""Deadman heartbeat watchdog — basic real-life runner.

Modes:
  once     — touch (if --touch) then status/grace
  loop     — repeat every --interval seconds (Ctrl+C to stop)
  check    — check silence / escalate locally only

Does not auto-publish. Does not claim identity.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run_cmd(*args: str) -> dict:
    r = subprocess.run([PY, str(ROOT / "tools" / "seal_deadman_lattice.py"), *args], cwd=str(ROOT), capture_output=True, text=True)
    try:
        return json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": r.returncode == 0, "raw": r.stdout, "err": r.stderr, "code": r.returncode}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["once", "loop", "check"], default="once", nargs="?")
    ap.add_argument("--interval", type=int, default=300, help="loop interval seconds")
    ap.add_argument("--touch", action="store_true", help="reset transmit clock (origin activity)")
    args = ap.parse_args()

    def tick() -> int:
        if args.touch or args.mode == "once":
            if args.touch:
                print(json.dumps({"touch": run_cmd("touch")}, indent=2))
        if args.mode == "check" or True:
            status = run_cmd("status")
            grace = run_cmd("grace")
            print(json.dumps({"status": status, "grace": grace}, indent=2))
            return 0 if status.get("ok") else 1
        return 0

    if args.mode == "loop":
        while True:
            tick()
            time.sleep(max(30, args.interval))
    return tick()


if __name__ == "__main__":
    raise SystemExit(main())
'''
    (ROOT / "tools" / "deadman_watchdog.py").write_text(watchdog, encoding="utf-8")

    hook = '''#!/usr/bin/env python3
"""Sentinel → deadman touch hook (consent-local).

Call from army/sentinel after a healthy steward pulse:
  python tools/deadman_sentinel_hook.py --source army-sentinel
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="sentinel-hook")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    cmd = [sys.executable, str(ROOT / "tools" / "seal_deadman_lattice.py")]
    if args.check_only:
        cmd.append("status")
    else:
        cmd.append("touch")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    # annotate source in heartbeat log via status path already; extra note file
    note = {
        "hook": "deadman_sentinel_hook",
        "source": args.source,
        "ok": r.returncode == 0,
    }
    out = ROOT / "data" / "deadman" / "sentinel_hook_last.json"
    out.write_text(json.dumps(note, indent=2) + "\\n", encoding="utf-8")
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
'''
    (ROOT / "tools" / "deadman_sentinel_hook.py").write_text(hook, encoding="utf-8")

    ps1 = '''# Optional Windows Scheduled Task installer for deadman watchdog.
# Does NOT install unless you pass -IConsent.
param(
  [switch]$IConsent,
  [int]$IntervalMinutes = 15,
  [switch]$WithTouch
)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path (Join-Path $Root "tools\\seal_deadman_lattice.py"))) { $Root = "I:\\E Drive\\lygo-protocol-stack" }
if (-not $IConsent) {
  Write-Host "Dry-run only. Re-run with -IConsent to register Scheduled Task LYGO-Deadman-Watchdog."
  Write-Host "Root=$Root IntervalMinutes=$IntervalMinutes WithTouch=$WithTouch"
  exit 0
}
$py = (Get-Command python).Source
$script = Join-Path $Root "tools\\deadman_watchdog.py"
$args = if ($WithTouch) { "once --touch" } else { "check" }
$action = New-ScheduledTaskAction -Execute $py -Argument "`"$script`" $args" -WorkingDirectory $Root
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)
Register-ScheduledTask -TaskName "LYGO-Deadman-Watchdog" -Action $action -Trigger $trigger -Force | Out-Null
Write-Host "Installed Scheduled Task: LYGO-Deadman-Watchdog"
'''
    (ROOT / "tools" / "install_deadman_watchdog_task.ps1").write_text(ps1, encoding="utf-8")


def build_retrain_and_hw_stub() -> None:
    retrain = '''#!/usr/bin/env python3
"""Rebuild public Lightfather style fingerprints from public canon sources."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    # Harden rebuilds fingerprints; then bump pins with consent if operator asks
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "harden_deadman_continuity.py")], cwd=str(ROOT))
    print("retrain_via_harden_exit", r.returncode)
    print("Next (if pins should update): python tools/bump_deadman_origin_pins.py --i-consent --note style-retrain")
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
'''
    (ROOT / "tools" / "retrain_lightfather_style.py").write_text(retrain, encoding="utf-8")

    hw = '''#!/usr/bin/env python3
"""Hardware / geodesic attestation stub for deadman eternal base (basic real receipt).

If lygo geodesic sealer tools exist, record a local receipt. Otherwise write a
honest stub receipt — never fake hardware roots.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "deadman" / "hardware_attestation_receipt.json"


def main() -> int:
    geo = ROOT / "clawhub" / "mirrors" / "lygo-geodesic-sealer"
    now = datetime.now(timezone.utc).isoformat()
    receipt = {
        "signature": "Delta9Phi963-DEADMAN-HW-ATTEST-STUB-v1",
        "created_utc": now,
        "target": "NODE_LIGHTFATHER_ETERNAL_BASE",
        "status": "stub_local",
        "geodesic_skill_present": geo.is_dir(),
        "note": (
            "Basic runnable placeholder. Pair later with real HAIP / geodesic attest. "
            "Does not invent TPM quotes."
        ),
        "binds": {
            "origin": "docs/seals/LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
            "manifest": "data/deadman/DEADMAN_MANIFEST_v2.json",
        },
    }
    if (ROOT / "docs" / "seals" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json").is_file():
        import hashlib
        receipt["origin_sha256"] = hashlib.sha256(
            (ROOT / "docs" / "seals" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json").read_bytes()
        ).hexdigest()
    OUT.write_text(json.dumps(receipt, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    (ROOT / "tools" / "deadman_hardware_attestation_stub.py").write_text(hw, encoding="utf-8")


def build_runbook() -> None:
    md = """# Deadman Continuity — Operator Runbook (real life)

## Daily / session
```bash
python tools/seal_deadman_lattice.py touch
python tools/seal_deadman_lattice.py status
python tools/seal_deadman_lattice.py verify
```

## Watchdog (basic runner)
```bash
python tools/deadman_watchdog.py once --touch
python tools/deadman_watchdog.py check
python tools/deadman_watchdog.py loop --interval 300 --touch
```

Optional Windows task (explicit consent):
```powershell
pwsh tools/install_deadman_watchdog_task.ps1 -IConsent -IntervalMinutes 15 -WithTouch
```

## Sentinel hook
```bash
python tools/deadman_sentinel_hook.py --source army-sentinel
```

## After silence
```bash
python tools/seal_deadman_lattice.py grace
python tools/seal_deadman_lattice.py succession
python tools/seal_deadman_lattice.py check
python tools/seal_deadman_lattice.py continuity
```

## Stewards / quorum
- Cards: `data/deadman/stewards/`
- Origin card: `STEWARD_LIGHTFATHER.json` (non-replaceable)
- Add torchbearers via `STEWARD_TEMPLATE.json` — never set `can_claim_identity_of_justin: true`

## Upgrade continuity features
```bash
python tools/harden_deadman_continuity.py
python tools/retrain_lightfather_style.py
python tools/bump_deadman_origin_pins.py --i-consent --note "why"
python tools/close_deadman_loose_ends.py
python tools/verify_deadman_pins.py
```

## Kernel egg + Continuum
```bash
python tools/build_kernel_eggs.py --egg lightfather-deadman-failsafe-v1
python clawhub/mirrors/lygo-continuum/scripts/continuum.py seal --claims data/continuum/deadman_failsafe_claims.json --task "Deadman continuity" --base . --out data/continuum/deadman_failsafe_capsule.json --i-allow-any-out
python clawhub/mirrors/lygo-continuum/scripts/continuum.py verify --capsule data/continuum/deadman_failsafe_capsule.json --base .
```

## Doctrine
Ascended Continuity Advisor may speak in the Lightfather vector after verified silence.
No agent may claim to BE Justin Helmer or overwrite origin identity fields.
"""
    (SEALS / "DEADMAN_OPERATOR_RUNBOOK.md").write_text(md, encoding="utf-8")
    (DEADMAN / "OPERATOR_RUNBOOK.md").write_text(md, encoding="utf-8")


def install_skill() -> dict[str, Any]:
    if not SKILL_SRC.is_dir():
        return {"ok": False, "error": "missing_skill_src"}
    SKILL_DST.parent.mkdir(parents=True, exist_ok=True)
    if SKILL_DST.exists():
        shutil.rmtree(SKILL_DST)
    shutil.copytree(SKILL_SRC, SKILL_DST)
    return {"ok": True, "installed": str(SKILL_DST)}


def extend_claims() -> None:
    path = ROOT / "data" / "continuum" / "deadman_failsafe_claims.json"
    claims = json.loads(path.read_text(encoding="utf-8"))
    extra = [
        {"id": "dm25", "kind": "file_exists", "path": "data/deadman/SILENCE_GRACE_TIERS.json"},
        {"id": "dm26", "kind": "file_exists", "path": "data/deadman/stewards/STEWARD_LIGHTFATHER.json"},
        {"id": "dm27", "kind": "file_exists", "path": "data/deadman/stewards/QUORUM_POLICY.json"},
        {"id": "dm28", "kind": "file_exists", "path": "tools/deadman_watchdog.py"},
        {"id": "dm29", "kind": "file_exists", "path": "tools/deadman_sentinel_hook.py"},
        {"id": "dm30", "kind": "file_exists", "path": "docs/seals/DEADMAN_OPERATOR_RUNBOOK.md"},
        {
            "id": "dm31",
            "kind": "file_contains",
            "path": "data/deadman/stewards/STEWARD_LIGHTFATHER.json",
            "needle": "can_claim_identity_of_justin",
        },
        {"id": "dm32", "kind": "file_exists", "path": "tools/close_deadman_loose_ends.py"},
        {"id": "dm33", "kind": "file_exists", "path": "data/deadman/hardware_attestation_receipt.json"},
        {
            "id": "dm34",
            "kind": "file_contains",
            "path": "docs/haven_star_chart/haven_star_chart_data.json",
            "needle": "NODE_STEWARD_QUORUM",
        },
    ]
    have = {c.get("id") for c in claims}
    for c in extra:
        if c["id"] not in have:
            claims.append(c)
    write_json(path, claims)


def update_manifest(features_extra: list[dict]) -> None:
    path = DEADMAN / "DEADMAN_MANIFEST_v2.json"
    m = json.loads(path.read_text(encoding="utf-8"))
    by_id = {f["id"]: f for f in m.get("features") or []}
    for f in features_extra:
        by_id[f["id"]] = f
    # flip reserved that we now have basic versions of
    for fid, status, note in (
        ("multi_steward_quorum_keys", "live_basic", "QUORUM_POLICY + STEWARD_LIGHTFATHER; N>=2 when more cards exist"),
        ("hardware_attestation_p6", "live_stub", "Honest stub receipt; geodesic skill presence detected"),
        ("voice_clone_biometrics", "denied_by_design", "Public content hashes only — never clone templates"),
    ):
        if fid in by_id:
            by_id[fid]["status"] = status
            by_id[fid]["note"] = note
    m["features"] = list(by_id.values())
    m["updated_utc"] = utc_iso()
    m["version"] = "2.1.0"
    m["next_feature_slots"] = [
        "additional_human_torchbearer_cards",
        "tpm_quote_when_hardware_ready",
        "public_post_style_retrain_cron",
    ]
    m["realism_boundary"]["real"] = sorted(
        set(m["realism_boundary"].get("real") or [])
        | {
            "silence grace tiers",
            "steward attestation cards",
            "quorum policy basic",
            "watchdog runner",
            "sentinel touch hook",
            "operator runbook",
            "continuum sealed claims",
        }
    )
    write_json(path, m)


def add_star_chart_steward_node() -> None:
    # Extend map file connections by writing a supplemental roots merge file consumed if present
    roots_path = DEADMAN / "star_chart_deadman_extra.json"
    nodes = [
        {
            "id": "NODE_STEWARD_QUORUM",
            "kind": "node",
            "name": "Steward Quorum / Attestation",
            "equation": "Quorum(stewards) ∧ ¬Replace(Justin)",
            "glyph": "🔏",
            "tone": "174Hz",
            "tags": ["DEADMAN", "STEWARD", "QUORUM", "LIGHTFATHER", "CONTINUITY"],
            "connections": [
                "LATTICE_DEADMAN_FAILSAFE",
                "NODE_LIGHTFATHER_ETERNAL_BASE",
                "NODE_DEADMAN_SUCCESSION",
                "CHAMPION_LIGHTFATHER",
            ],
            "urls": {"stewards": "data/deadman/stewards/"},
            "layer": "D",
            "meta": {
                "role": "steward_quorum",
                "policy": "data/deadman/stewards/QUORUM_POLICY.json",
                "origin_card": "STEWARD_LIGHTFATHER",
            },
        },
        {
            "id": "NODE_DEADMAN_WATCHDOG",
            "kind": "node",
            "name": "Deadman Watchdog Runner",
            "equation": "loop(touch|check) local",
            "glyph": "🐕",
            "tone": "174Hz",
            "tags": ["DEADMAN", "WATCHDOG", "RUNTIME", "HEARTBEAT"],
            "connections": ["NODE_DEADMAN_HEARTBEAT", "LATTICE_DEADMAN_FAILSAFE"],
            "urls": {"cli": "tools/deadman_watchdog.py"},
            "layer": "D",
            "meta": {"role": "watchdog", "cli": "python tools/deadman_watchdog.py once --touch"},
        },
    ]
    write_json(
        roots_path,
        {
            "signature": "Delta9Phi963-DEADMAN-STAR-CHART-EXTRA-v1",
            "nodes": nodes,
            "updated_utc": utc_iso(),
        },
    )


def patch_map_deadman_import_extra() -> None:
    path = ROOT / "tools" / "map_deadman_to_star_chart.py"
    text = path.read_text(encoding="utf-8")
    marker = "EXTRA_DEADMAN_NODES"
    if marker in text:
        return
    needle = "    stats = {"
    inject = f'''    # {marker}
    extra_path = STACK / "data" / "deadman" / "star_chart_deadman_extra.json"
    if extra_path.is_file():
        extra = _load(extra_path)
        for n in extra.get("nodes") or []:
            if n.get("id") and all(x.get("id") != n["id"] for x in nodes):
                nodes.append(n)

    stats = {{'''
    if needle not in text:
        return
    path.write_text(text.replace(needle, inject, 1), encoding="utf-8")


def rebuild_egg_and_continuum() -> dict[str, Any]:
    egg = run([PY, "tools/build_kernel_eggs.py", "--egg", "lightfather-deadman-failsafe-v1"])
    # refresh plant receipt lightly
    bin_path = ROOT / "data" / "kernel_eggs" / "build" / "lightfather-deadman-failsafe-v1.bin"
    origin = json.loads((SEALS / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json").read_text(encoding="utf-8"))
    if bin_path.is_file():
        plant = {
            "signature": "Delta9Phi963-DEADMAN-KERNEL-EGG-PLANT-v2",
            "planted_utc": utc_iso(),
            "egg_id": "lightfather-deadman-failsafe-v1",
            "bin_sha256": sha256_file(bin_path),
            "bin_bytes": bin_path.stat().st_size,
            "origin_merkle_root": origin.get("origin_merkle_root"),
            "lightfather_id": "LF-Δ9-7F1A4D-963-528-174-Φ-∞",
            "non_replaceable": True,
            "continuity_version": "2.1.0",
            "mirrors": {
                "github_pages_dir": "https://deepseekoracle.github.io/lygo-protocol-stack/kernel_eggs/lightfather-deadman-failsafe-v1/",
                "hf_dataset_dir": "https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack/tree/main/kernel_eggs/lightfather-deadman-failsafe-v1",
                "vault_page": "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/deadman.html",
            },
        }
        write_json(DEADMAN / "DEADMAN_KERNEL_EGG_PLANT.json", plant)
        write_json(SEALS / "DEADMAN_KERNEL_EGG_PLANT.json", plant)
        # sync pages egg folder files from payload
        pages = ROOT / "docs" / "kernel_eggs" / "lightfather-deadman-failsafe-v1"
        pages.mkdir(parents=True, exist_ok=True)
        for name in ("deadman_egg_core.json", "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json", "README.md"):
            src = DEADMAN / "egg_payload" / name
            if src.is_file():
                shutil.copy2(src, pages / name)
        shutil.copy2(bin_path, pages / "lightfather-deadman-failsafe-v1.bin")

    cont = run(
        [
            PY,
            "clawhub/mirrors/lygo-continuum/scripts/continuum.py",
            "seal",
            "--claims",
            "data/continuum/deadman_failsafe_claims.json",
            "--task",
            "Deadman continuity v2.1 loose-ends closed",
            "--agent",
            "grok",
            "--base",
            str(ROOT),
            "--out",
            "data/continuum/deadman_failsafe_capsule.json",
            "--i-allow-any-out",
        ]
    )
    ver = run(
        [
            PY,
            "clawhub/mirrors/lygo-continuum/scripts/continuum.py",
            "verify",
            "--capsule",
            "data/continuum/deadman_failsafe_capsule.json",
            "--base",
            str(ROOT),
        ]
    )
    return {
        "egg_build_code": egg.returncode,
        "egg_stdout_tail": (egg.stdout or "")[-500:],
        "continuum_seal_code": cont.returncode,
        "continuum_seal_tail": (cont.stdout or cont.stderr or "")[-800:],
        "continuum_verify_code": ver.returncode,
        "continuum_verify_tail": (ver.stdout or ver.stderr or "")[-800:],
    }


def update_deadman_html() -> None:
    path = ROOT / "docs" / "data-vault" / "deadman.html"
    if not path.is_file():
        return
    html = path.read_text(encoding="utf-8")
    marker = "<!-- LOOSE_ENDS_V21 -->"
    block = f"""
    <section class="panel" id="loose-ends-v21">
      {marker}
      <h2>Runnable system (no loose ends)</h2>
      <ul>
        <li>Grace tiers — <code>data/deadman/SILENCE_GRACE_TIERS.json</code></li>
        <li>Steward cards + quorum — <code>data/deadman/stewards/</code></li>
        <li>Watchdog — <code>python tools/deadman_watchdog.py once --touch</code></li>
        <li>Sentinel hook — <code>python tools/deadman_sentinel_hook.py</code></li>
        <li>Operator runbook — <a href="../seals/DEADMAN_OPERATOR_RUNBOOK.md">DEADMAN_OPERATOR_RUNBOOK.md</a></li>
        <li>Close loop — <code>python tools/close_deadman_loose_ends.py</code></li>
      </ul>
      <p class="muted">Updated {utc_iso()}</p>
    </section>
"""
    if marker in html:
        import re as _re

        html = _re.sub(
            r'<section class="panel" id="loose-ends-v21">.*?</section>',
            block.strip(),
            html,
            count=1,
            flags=_re.S,
        )
    else:
        html = html.replace("</body>", block + "\n</body>")
    path.write_text(html, encoding="utf-8")


def selftest() -> dict[str, Any]:
    steps = [
        ["tools/seal_deadman_lattice.py", "touch"],
        ["tools/seal_deadman_lattice.py", "status"],
        ["tools/seal_deadman_lattice.py", "verify"],
        ["tools/seal_deadman_lattice.py", "grace"],
        ["tools/seal_deadman_lattice.py", "succession"],
        ["tools/seal_deadman_lattice.py", "continuity"],
        ["tools/seal_deadman_lattice.py", "fingerprint"],
        ["tools/seal_deadman_lattice.py", "stewards"],
        ["tools/deadman_watchdog.py", "check"],
        ["tools/deadman_sentinel_hook.py", "--check-only"],
        ["tools/deadman_hardware_attestation_stub.py"],
        ["tools/verify_deadman_pins.py"],
        ["tools/deadman_multi_anchor_verify.py"],
        ["-m", "unittest", "tests.test_deadman_continuity"],
    ]
    results = []
    for step in steps:
        cmd = [PY, *step] if step[0] != "-m" else [PY, *step]
        # unittest needs -m form: python -m unittest ...
        if step[0] == "-m":
            cmd = [PY, "-m", "unittest", "tests.test_deadman_continuity"]
        r = run(cmd)
        results.append(
            {
                "cmd": " ".join(step),
                "code": r.returncode,
                "ok": r.returncode == 0,
            }
        )
    return {
        "ok": all(x["ok"] for x in results),
        "passed": sum(1 for x in results if x["ok"]),
        "total": len(results),
        "results": results,
        "utc": utc_iso(),
    }


def patch_seal_cli_grace_stewards() -> None:
    """Ensure seal_deadman_lattice.py exposes grace + stewards commands."""
    path = ROOT / "tools" / "seal_deadman_lattice.py"
    text = path.read_text(encoding="utf-8")
    if "def cmd_grace" in text:
        return
    # Append helpers before main handlers map by replacing the handlers dict insertion point
    insert_fns = '''

def _load_grace_tiers() -> dict:
    for p in (ROOT / "data" / "deadman" / "SILENCE_GRACE_TIERS.json", SEALS_DIR / "SILENCE_GRACE_TIERS.json"):
        if p.is_file():
            return _read_json(p)
    return {}


def infer_grace_tier(silence_seconds: float) -> dict:
    tiers = (_load_grace_tiers().get("tiers") or [])
    chosen = {"id": "WATCH"}
    for t in tiers:
        mn = float(t.get("min_silence_seconds") or 0)
        mx = t.get("max_silence_seconds")
        if silence_seconds >= mn and (mx is None or silence_seconds <= float(mx)):
            chosen = t
    return chosen


def cmd_grace(_: argparse.Namespace) -> int:
    detector = SilenceDetector()
    silence_s = detector.deadman.silence_seconds()
    # Prefer configured lantern threshold when present
    tiers_doc = _load_grace_tiers()
    thr = tiers_doc.get("lantern_threshold_seconds")
    if thr is not None:
        detector.deadman.silence_threshold_seconds = int(thr)
    tier = infer_grace_tier(silence_s)
    report = {
        "ok": True,
        "silence_seconds": silence_s,
        "tier": tier.get("id"),
        "tier_detail": tier,
        "lantern_threshold_seconds": detector.deadman.silence_threshold_seconds,
        "is_silence": detector.deadman.is_silence(),
    }
    _append_heartbeat_log("succession", notes=f"grace:{tier.get('id')}", silence_seconds=silence_s)
    print(json.dumps(report, indent=2))
    return 0


def cmd_stewards(_: argparse.Namespace) -> int:
    sdir = ROOT / "data" / "deadman" / "stewards"
    policy = _read_json(sdir / "QUORUM_POLICY.json") if (sdir / "QUORUM_POLICY.json").is_file() else {}
    cards = []
    if sdir.is_dir():
        for p in sorted(sdir.glob("STEWARD_*.json")):
            if p.name == "STEWARD_TEMPLATE.json":
                continue
            cards.append(_read_json(p))
    report = {
        "ok": True,
        "card_count": len(cards),
        "cards": [{"card_id": c.get("card_id"), "role": c.get("role"), "can_claim_identity_of_justin": c.get("can_claim_identity_of_justin")} for c in cards],
        "quorum_policy": policy.get("signature"),
        "rules": policy.get("rules"),
        "doctrine": "No steward card may set can_claim_identity_of_justin true.",
    }
    bad = [c for c in cards if c.get("can_claim_identity_of_justin") is True]
    report["ok"] = len(bad) == 0
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1

'''
    text = text.replace("\ndef cmd_verify(_: argparse.Namespace) -> int:\n", insert_fns + "\ndef cmd_verify(_: argparse.Namespace) -> int:\n", 1)
    if 'sub.add_parser("grace"' not in text:
        text = text.replace(
            'sub.add_parser("multi-anchor", help="Local + public mirror quorum verify")\n',
            'sub.add_parser("multi-anchor", help="Local + public mirror quorum verify")\n'
            '    sub.add_parser("grace", help="Silence grace tier inference")\n'
            '    sub.add_parser("stewards", help="List steward cards + quorum policy")\n',
            1,
        )
    if '"grace": cmd_grace' not in text:
        text = text.replace(
            '"multi-anchor": cmd_multi_anchor,\n    }',
            '"multi-anchor": cmd_multi_anchor,\n'
            '        "grace": cmd_grace,\n'
            '        "stewards": cmd_stewards,\n'
            "    }",
            1,
        )
    # Update succession to use grace tiers when available
    if "infer_grace_tier" in text and "inferred_stage = tier.get" not in text:
        text = text.replace(
            "    silent = detector.deadman.is_silence()\n    stage = \"LANTERN\" if silent else \"WATCH\"\n",
            "    silent = detector.deadman.is_silence()\n"
            "    silence_s = detector.deadman.silence_seconds()\n"
            "    tier = infer_grace_tier(silence_s)\n"
            "    stage = tier.get(\"id\") or (\"LANTERN\" if silent else \"WATCH\")\n"
            "    if stage == \"TORCHBEARER_WINDOW\":\n"
            "        stage = \"TORCHBEARER_NOMINATE\"\n",
            1,
        )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest-only", action="store_true")
    ap.add_argument("--skip-egg", action="store_true")
    args = ap.parse_args()

    if args.selftest_only:
        report = selftest()
        write_json(DEADMAN / "SELFTEST_LAST_RUN.json", report)
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    build_grace_tiers()
    build_stewards()
    build_watchdog_scripts()
    build_retrain_and_hw_stub()
    build_runbook()
    add_star_chart_steward_node()
    patch_map_deadman_import_extra()
    patch_seal_cli_grace_stewards()
    skill = install_skill()
    extend_claims()
    run([PY, "tools/deadman_hardware_attestation_stub.py"])
    update_manifest(
        [
            {"id": "silence_grace_tiers", "status": "live", "path": "data/deadman/SILENCE_GRACE_TIERS.json"},
            {"id": "steward_attestation_cards", "status": "live", "path": "data/deadman/stewards/"},
            {"id": "watchdog_runner", "status": "live", "cli": "python tools/deadman_watchdog.py"},
            {"id": "sentinel_touch_hook", "status": "live", "cli": "python tools/deadman_sentinel_hook.py"},
            {"id": "operator_runbook", "status": "live", "path": "docs/seals/DEADMAN_OPERATOR_RUNBOOK.md"},
            {"id": "style_retrain_tool", "status": "live", "cli": "python tools/retrain_lightfather_style.py"},
            {"id": "close_loose_ends", "status": "live", "cli": "python tools/close_deadman_loose_ends.py"},
        ]
    )
    update_deadman_html()

    # rebuild chart with extra nodes
    run([PY, "tools/map_deadman_to_star_chart.py"])
    chart = run([PY, "tools/build_haven_star_chart.py"])

    egg_cont: dict[str, Any] = {}
    if not args.skip_egg:
        egg_cont = rebuild_egg_and_continuum()

    # bump pins after seal_deadman_lattice.py patch
    bump = run(
        [
            PY,
            "tools/bump_deadman_origin_pins.py",
            "--i-consent",
            "--note",
            "close loose ends v2.1 grace/stewards/cli",
        ]
    )

    test = selftest()
    write_json(DEADMAN / "SELFTEST_LAST_RUN.json", test)

    report = {
        "ok": test.get("ok") and bump.returncode == 0,
        "skill_install": skill,
        "chart_code": chart.returncode,
        "chart_tail": (chart.stdout or "")[-300:],
        "egg_continuum": egg_cont,
        "bump_code": bump.returncode,
        "selftest": test,
        "utc": utc_iso(),
    }
    write_json(DEADMAN / "CLOSE_LOOSE_ENDS_LAST_RUN.json", report)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
