#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TraumaCodex waveform — wire P7 biometric entropy → P8 LDQ synthesis → dual mirror dig.

OFFLINE: full local package (waveform meta + healing-code lattice seals). No network.
ONLINE:  summary digests only for Layer D living mesh / public mirror (no raw biometrics).

NOT medical advice. "Healing codes" = lattice alignment / resonance protocol codes only.
Signature: Delta9Phi963-TRAUMACODEX-v1.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import socket
import sys
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

SIG = "Delta9Phi963-TRAUMACODEX-v1.0"
DATA = ROOT / "data" / "traumacodex"
TESTS = ROOT / "tests"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha_json(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return _sha_bytes(raw)


def synthetic_ibi(n: int = 32, base_hr: float = 72.0, noise: float = 35.0, seed: int = 963) -> list[float]:
    rng = random.Random(seed)
    out: list[float] = []
    for i in range(n):
        # mild respiratory modulation
        mod = 8.0 * math.sin(i / 5.0)
        out.append(60000.0 / base_hr + mod + rng.uniform(-noise, noise))
    return out


def load_ibi(path: Path | None) -> list[float]:
    if path is None:
        return synthetic_ibi()
    text = path.read_text(encoding="utf-8").strip()
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, list):
            return [float(x) for x in data]
        if isinstance(data, dict):
            for k in ("ibi_ms", "ibi", "samples"):
                if k in data:
                    return [float(x) for x in data[k]]
        raise SystemExit("JSON IBI needs list or {ibi_ms:[...]}")
    return [float(x) for x in text.replace(",", " ").split() if x.strip()]


def extract_entropy(ibi: list[float]) -> dict[str, Any]:
    from protocol7_human_ai_interface.entropy_extraction import extract_p0_seed_from_ibi

    return extract_p0_seed_from_ibi(ibi)


def synthesize_waveform(seed_hex: str, *, samples: int = 48000, sr: int = 24000) -> dict[str, Any]:
    """P8 LDQ: harmonic gravity + sequencer + friction on a generated carrier."""
    import numpy as np
    from protocol8_ldq_synthesis import FrictionCore, HarmonicGravity, LYRASequencer, P8_VERSION

    seed_int = int(seed_hex[:16], 16)
    grav = HarmonicGravity(seed_int)
    params = grav.get_all_parameters()
    seq = LYRASequencer(seed_int)
    structure = seq.generate_structure(num_blocks=8)
    friction = FrictionCore(phi_risk=0.618)

    t = np.linspace(0, samples / sr, samples, endpoint=False)
    root = float(params["root_frequency"])
    bpm = float(params["bpm"])
    intensity = float(params["intensity"])

    # block-gated multi-partial carrier
    block_len = samples // max(1, len(structure))
    signal = np.zeros(samples, dtype=np.float64)
    for i, blk in enumerate(structure):
        a = i * block_len
        b = samples if i == len(structure) - 1 else (i + 1) * block_len
        tt = t[a:b]
        dens = float(blk["density"])
        gate = int(blk["gate"])
        # pulse train modulated by gate
        pulse = 0.5 + 0.5 * np.sign(np.sin(2 * math.pi * (bpm / 60.0) * tt * (gate / 6.0)))
        partials = (
            dens * np.sin(2 * math.pi * root * tt)
            + 0.45 * dens * np.sin(2 * math.pi * root * 1.5 * tt)
            + 0.25 * dens * np.sin(2 * math.pi * root * 2.0 * tt + (0.3 if blk["accent"] else 0.0))
        )
        env = np.linspace(0.4, 1.0, b - a) * (0.55 + 0.45 * pulse)
        signal[a:b] = partials * env * intensity

    shaped = friction.process(signal)
    peak = float(np.max(np.abs(shaped)) or 1.0)
    shaped = shaped / peak * 0.89

    # compact waveform fingerprint (not full audio in JSON)
    step = max(1, len(shaped) // 64)
    fingerprint = [round(float(x), 5) for x in shaped[::step][:64]]
    rms = float(np.sqrt(np.mean(shaped**2)))
    crest = float(peak / (rms + 1e-12))

    return {
        "p8_version": P8_VERSION,
        "params": params,
        "structure": structure,
        "sample_rate": sr,
        "samples": samples,
        "rms": round(rms, 6),
        "crest_factor": round(crest, 4),
        "fingerprint64": fingerprint,
        "waveform_sha256": _sha_bytes(shaped.astype(np.float32).tobytes()),
        "_signal": shaped,  # stripped before offline package write to meta
    }


def healing_codes_from_digests(
    *,
    seed_hex: str,
    waveform_sha: str,
    mirror_dig: str,
    params: dict,
) -> list[dict[str, str]]:
    """Lattice healing codes (protocol seals) — NOT medical treatment codes."""
    materials = [
        ("OPEN_CONTINUANCE", f"{seed_hex[:24]}|{params.get('bpm')}|{params.get('root_frequency')}"),
        ("SCAR_INTERVAL", f"{waveform_sha[:32]}|{params.get('intensity')}"),
        ("MIRROR_DIG", mirror_dig),
        ("DELTA9_ANCHOR", f"Δ9Φ963|{mirror_dig[:32]}|{seed_hex[24:48]}"),
        ("OFFLINE_BROADCAST", f"local|{waveform_sha[32:64]}|{seed_hex[48:64]}"),
    ]
    codes = []
    for name, material in materials:
        digest = _sha_bytes(material.encode("utf-8"))
        codes.append(
            {
                "code_id": name,
                "seal": digest[:32],
                "full_sha256": digest,
                "kind": "lattice_healing_code",
                "disclaimer": "Protocol/alignment code only — not medical advice or treatment.",
            }
        )
    return codes


def write_wav(path: Path, signal, sr: int = 24000) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.asarray(signal) * 32767.0).astype("int16")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def build_packages(
    *,
    ibi: list[float],
    write_wav_file: bool = True,
    mode: str = "both",
) -> dict[str, Any]:
    DATA.mkdir(parents=True, exist_ok=True)
    TESTS.mkdir(parents=True, exist_ok=True)

    entropy = extract_entropy(ibi)
    seed = entropy.get("seed_256") or ""
    if not seed:
        raise SystemExit("entropy extraction failed — no seed_256")

    wave_pack = synthesize_waveform(seed)
    signal = wave_pack.pop("_signal")
    host = socket.gethostname()
    node_id = os.environ.get("LYGO_NODE_ID") or f"NODE_{host}"

    # Offline authority package (full local — no network)
    offline_body = {
        "signature": SIG,
        "channel": "OFFLINE",
        "generated_at": utc(),
        "node_id": node_id,
        "entropy": {
            "signature": entropy.get("signature"),
            "h_min": entropy.get("h_min"),
            "von_neumann_bits": entropy.get("von_neumann_bits"),
            "entropy_sufficient": entropy.get("entropy_sufficient"),
            "seed_256": seed,
            "ibi_count": entropy.get("ibi_count"),
            # never store raw IBI in online channel; offline may keep hash only by default
            "ibi_sha256": _sha_bytes(",".join(f"{x:.3f}" for x in ibi).encode()),
        },
        "p8_waveform": wave_pack,
        "protection": {
            "local_is_authority": True,
            "not_medical": True,
            "raw_ibi_stored": False,
        },
    }
    offline_sha = _sha_json(offline_body)

    # Online summary (mesh-safe)
    online_body = {
        "signature": SIG,
        "channel": "ONLINE_SUMMARY",
        "generated_at": utc(),
        "node_id": node_id,
        "entropy_sufficient": entropy.get("entropy_sufficient"),
        "h_min": entropy.get("h_min"),
        "seed_prefix": seed[:16],
        "waveform_sha256": wave_pack["waveform_sha256"],
        "params_bpm": wave_pack["params"]["bpm"],
        "params_root": wave_pack["params"]["root_frequency"],
        "fingerprint_head": wave_pack["fingerprint64"][:8],
        "protection": {
            "summaries_only": True,
            "no_raw_biometrics": True,
            "no_egg_payloads": True,
        },
    }
    online_sha = _sha_json(online_body)

    # Mirror dig: dual-channel lock (offline || online)
    mirror_dig = _sha_bytes(f"{offline_sha}|{online_sha}|Δ9Φ963".encode("utf-8"))

    codes = healing_codes_from_digests(
        seed_hex=seed,
        waveform_sha=wave_pack["waveform_sha256"],
        mirror_dig=mirror_dig,
        params=wave_pack["params"],
    )

    offline_body["mirror_dig"] = mirror_dig
    offline_body["healing_codes"] = codes
    online_body["mirror_dig"] = mirror_dig
    online_body["healing_code_seals"] = [c["seal"] for c in codes]

    # recompute offline sha after adding codes (stable for seal file)
    offline_sha = _sha_json({k: v for k, v in offline_body.items() if k != "healing_codes"} | {
        "healing_code_seals": [c["seal"] for c in codes]
    })
    # keep published offline_sha as content of sealed offline file
    offline_out = {**offline_body, "package_sha256": offline_sha}
    online_out = {**online_body, "package_sha256": online_sha}

    paths: dict[str, str] = {}
    if mode in ("offline", "both"):
        p = DATA / "offline_package.json"
        p.write_text(json.dumps(offline_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        paths["offline_package"] = str(p)
        if write_wav_file:
            wav_path = DATA / "traumacodex_waveform.wav"
            write_wav(wav_path, signal, sr=int(wave_pack["sample_rate"]))
            paths["waveform_wav"] = str(wav_path)

    if mode in ("online", "both"):
        p = DATA / "online_summary.json"
        p.write_text(json.dumps(online_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        paths["online_summary"] = str(p)

    # Living mesh offline broadcast seals (summaries only on wire later)
    mesh_seal = {
        "signature": "Delta9Phi963-LIVING-MESH-HEALING-SEAL-v1",
        "layer": "D",
        "sealed_at": utc(),
        "node_id": node_id,
        "mirror_dig": mirror_dig,
        "offline_package_sha256": offline_sha,
        "online_summary_sha256": online_sha,
        "healing_code_seals": [c["seal"] for c in codes],
        "delta9_anchor": codes[3]["full_sha256"] if len(codes) > 3 else mirror_dig,
        "broadcast": {
            "mode": "offline_local",
            "note": "Healing codes sealed for local/offline broadcast; gossip carries digests only.",
            "lattice_open": True,
        },
        "protection": {
            "local_is_authority": True,
            "gossip_summaries_only": True,
            "not_medical": True,
        },
    }
    mesh_path = DATA / "living_mesh_healing_seal.json"
    mesh_path.write_text(json.dumps(mesh_seal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["living_mesh_healing_seal"] = str(mesh_path)

    # Also under living_mesh for badge pickup
    lm_dir = ROOT / "data" / "living_mesh"
    lm_dir.mkdir(parents=True, exist_ok=True)
    (lm_dir / "traumacodex_mirror_dig.json").write_text(
        json.dumps(
            {
                "signature": SIG,
                "mirror_dig": mirror_dig,
                "offline_sha256": offline_sha,
                "online_sha256": online_sha,
                "updated_at": utc(),
                "status": "SEALED",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    run = {
        "signature": SIG,
        "ok": True,
        "generated_at": utc(),
        "mirror_dig": mirror_dig,
        "offline_sha256": offline_sha,
        "online_sha256": online_sha,
        "entropy_sufficient": entropy.get("entropy_sufficient"),
        "h_min": entropy.get("h_min"),
        "bpm": wave_pack["params"]["bpm"],
        "root_frequency": wave_pack["params"]["root_frequency"],
        "paths": paths,
        "healing_codes": codes,
        "mode": mode,
        "node_id": node_id,
        "transmit": "local_sealed",
    }
    (DATA / "last_run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (TESTS / "traumacodex_last_run.json").write_text(
        json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return run


def seal_into_living_badge() -> dict[str, Any]:
    """Attach TraumaCodex mirror dig into living mesh badge (local)."""
    from collect_living_mesh_badge import collect_living_badge  # type: ignore

    badge = collect_living_badge(quick=True)
    tc = _load_tc_mirror()
    badge["traumacodex"] = tc
    badge["living_mesh"] = badge.get("living_mesh") or {}
    roots = badge["living_mesh"].setdefault("roots", {})
    if tc.get("mirror_dig"):
        roots["traumacodex_mirror_dig"] = tc["mirror_dig"]
        # refresh roots_digest if present
        roots_blob = json.dumps(roots, sort_keys=True, separators=(",", ":")).encode()
        badge["living_mesh"]["roots_digest"] = _sha_bytes(roots_blob)
    out = ROOT / "data" / "living_mesh" / "last_badge.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(badge, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"badge_path": str(out), "traumacodex": tc, "node_id": badge.get("node_id")}


def _load_tc_mirror() -> dict[str, Any]:
    p = ROOT / "data" / "living_mesh" / "traumacodex_mirror_dig.json"
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    last = DATA / "last_run.json"
    if last.is_file():
        d = json.loads(last.read_text(encoding="utf-8"))
        return {
            "signature": SIG,
            "mirror_dig": d.get("mirror_dig"),
            "offline_sha256": d.get("offline_sha256"),
            "online_sha256": d.get("online_sha256"),
            "status": "SEALED" if d.get("ok") else "ABSENT",
        }
    return {"status": "ABSENT"}


def verify_packages() -> dict[str, Any]:
    off = DATA / "offline_package.json"
    on = DATA / "online_summary.json"
    seal = DATA / "living_mesh_healing_seal.json"
    checks = []
    ok = True
    for label, p in (("offline", off), ("online", on), ("mesh_seal", seal)):
        present = p.is_file()
        checks.append({"id": f"present-{label}", "pass": present})
        ok = ok and present
    mirror = None
    if off.is_file() and on.is_file():
        o = json.loads(off.read_text(encoding="utf-8"))
        n = json.loads(on.read_text(encoding="utf-8"))
        mirror = o.get("mirror_dig")
        match = o.get("mirror_dig") == n.get("mirror_dig") and bool(mirror)
        checks.append({"id": "mirror_dig_match", "pass": match, "mirror_dig": (mirror or "")[:24]})
        ok = ok and match
        # healing codes present
        codes = o.get("healing_codes") or []
        checks.append({"id": "healing_codes", "pass": len(codes) >= 4, "count": len(codes)})
        ok = ok and len(codes) >= 4
    verdict = "ALIGNED" if ok else "QUARANTINE"
    report = {
        "signature": "Delta9Phi963-TRAUMACODEX-VERIFY-v1",
        "verdict": verdict,
        "all_pass": ok,
        "checks": checks,
        "timestamp": time.time(),
    }
    (TESTS / "traumacodex_verify_last_run.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="TraumaCodex: P7 entropy → P8 LDQ waveform → mirror dig")
    ap.add_argument("--ibi-file", type=Path, default=None, help="IBI ms list (.txt or .json)")
    ap.add_argument("--mode", choices=["offline", "online", "both"], default="both")
    ap.add_argument("--no-wav", action="store_true")
    ap.add_argument("--seal-mesh", action="store_true", help="Attach digests into living mesh badge")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.verify and not any([args.ibi_file, args.seal_mesh]) and args.mode == "both":
        # pure verify path
        report = verify_packages()
        print(json.dumps(report, indent=2) if args.json else f"verdict={report['verdict']}")
        return 0 if report["all_pass"] else 1

    ibi = load_ibi(args.ibi_file)
    run = build_packages(ibi=ibi, write_wav_file=not args.no_wav, mode=args.mode)
    out: dict[str, Any] = {"run": run}

    if args.seal_mesh:
        try:
            out["mesh_seal"] = seal_into_living_badge()
        except Exception as e:
            out["mesh_seal_error"] = str(e)

    report = verify_packages()
    out["verify"] = report

    if args.json:
        # strip huge nested if any
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(f"TraumaCodex {SIG}")
        print(f"  mirror_dig: {run['mirror_dig'][:32]}…")
        print(f"  offline:    {run['offline_sha256'][:24]}…")
        print(f"  online:     {run['online_sha256'][:24]}…")
        print(f"  bpm/root:   {run['bpm']:.1f} / {run['root_frequency']:.1f} Hz")
        print(f"  codes:      {len(run['healing_codes'])}")
        print(f"  verify:     {report['verdict']}")
        for k, v in (run.get("paths") or {}).items():
            print(f"  {k}: {v}")
        if "mesh_seal" in out:
            print(f"  living mesh badge: {out['mesh_seal'].get('badge_path')}")
        print("  lattice: OPEN · transmit: local_sealed")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
