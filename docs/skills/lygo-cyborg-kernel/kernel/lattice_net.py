#!/usr/bin/env python3
"""
LYGO Cyborg lattice network limb — HTTPS + optional git/HF connect.

FULL unlocked channel: joins public lattice surfaces, star chart feed/meta/data,
optional stack git clone/pull, optional Hugging Face dataset snapshot.

Signature: Delta9Phi963-CYBORG-KERNEL-v1.1.0
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SIG = "Delta9Phi963-CYBORG-KERNEL-v1.1.0"
VERSION = "1.1.0"
UA = "LYGO-Cyborg-Kernel/1.1.0 (+https://chatagent.ca; +https://clawhub.ai/deepseekoracle)"

PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack"
GIT_REPO = "https://github.com/DeepSeekOracle/lygo-protocol-stack.git"
HF_DATASET = "DeepSeekOracle/lygo-protocol-stack"
CHATAGENT = "https://chatagent.ca"

LATTICE_ENDPOINTS: list[dict[str, str]] = [
    {
        "id": "immutable_anchors",
        "url": f"{PAGES}/network_builder/IMMUTABLE_ANCHORS.json",
        "role": "link_ledger",
        "level": "required",
    },
    {
        "id": "haven_star_feed",
        "url": f"{PAGES}/haven_star_chart/haven_star_chart_feed.json",
        "role": "star_ledger",
        "level": "required",
    },
    {
        "id": "haven_star_meta",
        "url": f"{PAGES}/haven_star_chart/haven_star_chart_meta.json",
        "role": "star_meta",
        "level": "required",
    },
    {
        "id": "haven_star_data",
        "url": f"{PAGES}/haven_star_chart/haven_star_chart_data.json",
        "role": "star_registry",
        "level": "required",
    },
    {
        "id": "haven_star_queue",
        "url": f"{PAGES}/haven_star_chart/haven_star_chart_queue.json",
        "role": "star_queue",
        "level": "soft",
    },
    {
        "id": "haven_star_ui",
        "url": f"{PAGES}/HavenStarChart.html",
        "role": "star_ui",
        "level": "required",
    },
    {
        "id": "skillhub",
        "url": f"{CHATAGENT}/lygoskillhub.html",
        "role": "skillhub",
        "level": "required",
    },
    {
        "id": "continuum_portal",
        "url": f"{CHATAGENT}/lygo-continuum.html",
        "role": "continuum",
        "level": "soft",
    },
    {
        "id": "clawhub_publisher",
        "url": "https://clawhub.ai/deepseekoracle",
        "role": "skills",
        "level": "soft",
    },
    {
        "id": "hf_dataset",
        "url": f"https://huggingface.co/datasets/{HF_DATASET}",
        "role": "hf_mirror",
        "level": "soft",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def https_ok(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme == "https" and bool(p.netloc)
    except Exception:
        return False


def http_get(url: str, timeout: float = 25.0, max_bytes: int = 8_000_000) -> dict[str, Any]:
    if not https_ok(url):
        return {"ok": False, "status": 0, "error": "https_only", "bytes": 0}
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(max_bytes + 1)
            truncated = len(body) > max_bytes
            if truncated:
                body = body[:max_bytes]
            return {
                "ok": 200 <= resp.status < 400,
                "status": resp.status,
                "error": None,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "body": body,
                "truncated": truncated,
            }
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": str(e), "bytes": 0}
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e), "bytes": 0}


def parse_json(body: bytes | None) -> Any:
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8", errors="replace"))
    except Exception:
        return None


def summarize_feed(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    entries = data.get("entries") or []
    counts: dict[str, int] = {}
    latest = None
    for e in entries:
        if not isinstance(e, dict):
            continue
        st = str(e.get("status") or "unknown")
        counts[st] = counts.get(st, 0) + 1
        latest = e
    return {
        "entry_count": data.get("entry_count") or len(entries),
        "chain_valid": data.get("chain_valid"),
        "chain_root": data.get("chain_root"),
        "updated_utc": data.get("updated_utc"),
        "signature": data.get("signature"),
        "status_counts": counts,
        "latest_entry": {
            "node_id": (latest or {}).get("node_id"),
            "node_name": (latest or {}).get("node_name"),
            "status": (latest or {}).get("status"),
            "event_type": (latest or {}).get("event_type"),
            "event_utc": (latest or {}).get("event_utc"),
        }
        if latest
        else None,
    }


def summarize_chart(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    cosmos = data.get("cosmos") if isinstance(data.get("cosmos"), dict) else {}
    return {
        "node_count": data.get("node_count"),
        "link_count": data.get("link_count"),
        "registry_sha256": data.get("registry_sha256"),
        "generated_utc": data.get("generated_utc"),
        "galaxy_count": cosmos.get("galaxy_count"),
        "nebula_count": cosmos.get("nebula_count"),
        "cluster_count": cosmos.get("cluster_count"),
        "signature": data.get("signature"),
    }


def lattice_pulse(timeout: float = 25.0) -> dict[str, Any]:
    endpoints_out: list[dict[str, Any]] = []
    req_fail = 0
    soft_fail = 0
    feed = anchors = chart = meta = None

    for ep in LATTICE_ENDPOINTS:
        r = http_get(ep["url"], timeout=timeout)
        item: dict[str, Any] = {
            "id": ep["id"],
            "role": ep["role"],
            "level": ep["level"],
            "url": ep["url"],
            "ok": r["ok"],
            "status": r.get("status"),
            "bytes": r.get("bytes"),
            "sha256": r.get("sha256"),
            "error": r.get("error"),
        }
        if r.get("ok") and r.get("body") and ep["id"].endswith((".json",)) is False:
            # json endpoints by id
            pass
        if r.get("ok") and r.get("body") and ep["url"].endswith(".json"):
            data = parse_json(r["body"])
            if ep["id"] == "haven_star_feed":
                feed = summarize_feed(data)
                item["summary"] = feed
            elif ep["id"] == "immutable_anchors":
                if isinstance(data, dict):
                    anchors = {
                        "signature": data.get("signature"),
                        "version": data.get("version"),
                        "updated_utc": data.get("updated_utc"),
                        "categories": list((data.get("immutable_anchors") or {}).keys())
                        if isinstance(data.get("immutable_anchors"), dict)
                        else [],
                    }
                    item["summary"] = anchors
            elif ep["id"] == "haven_star_data":
                chart = summarize_chart(data)
                item["summary"] = chart
            elif ep["id"] == "haven_star_meta":
                if isinstance(data, dict):
                    meta = {k: data.get(k) for k in list(data.keys())[:12]}
                    item["summary"] = meta

        if not r.get("ok"):
            if ep["level"] == "required":
                req_fail += 1
            else:
                soft_fail += 1
        endpoints_out.append(item)

    live = req_fail == 0
    score = 100
    score -= req_fail * 18
    score -= soft_fail * 4
    score = max(0, min(100, score))
    if feed and feed.get("chain_valid") is True:
        score = min(100, score + 5)
    if chart and chart.get("node_count"):
        score = min(100, score + 5)

    return {
        "signature": SIG,
        "version": VERSION,
        "command": "lattice_pulse",
        "ok": live,
        "live": live,
        "score": score,
        "ready_for_star_ops": live and score >= 60,
        "updated_utc": utc_now(),
        "required_fail": req_fail,
        "soft_fail": soft_fail,
        "star_feed": feed,
        "star_chart": chart,
        "star_meta": meta,
        "anchors": anchors,
        "endpoints": endpoints_out,
        "ui": {
            "star_chart": f"{PAGES}/HavenStarChart.html",
            "skillhub_full": f"{CHATAGENT}/lygoskillhub.html#full-lygo",
            "continuum": f"{CHATAGENT}/lygo-continuum.html",
        },
    }


def resolve_stack_root(explicit: str | None = None) -> Path | None:
    cands: list[Path] = []
    if explicit:
        cands.append(Path(explicit))
    env = (os.environ.get("LYGO_STACK_ROOT") or "").strip()
    if env:
        cands.append(Path(env))
    cands.extend(
        [
            Path(r"D:\lygo-protocol-stack"),
            Path(r"I:\E Drive\lygo-protocol-stack"),
            Path.home() / "lygo-protocol-stack",
            Path.cwd() / "lygo-protocol-stack",
        ]
    )
    for c in cands:
        try:
            if (c / "docs" / "haven_star_chart").is_dir() or (
                c / "tools" / "kernel_egg_catalog.py"
            ).is_file():
                return c.resolve()
        except OSError:
            continue
    return None


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 600) -> dict[str, Any]:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "stdout": (p.stdout or "")[-4000:],
            "stderr": (p.stderr or "")[-2000:],
            "cmd": cmd,
        }
    except FileNotFoundError as e:
        return {"ok": False, "code": 127, "error": f"not_found:{e}", "cmd": cmd}
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": 124, "error": "timeout", "cmd": cmd}
    except Exception as e:
        return {"ok": False, "code": 1, "error": str(e), "cmd": cmd}


def git_connect(
    dest: str | None = None,
    *,
    pull: bool = True,
    clone_if_missing: bool = True,
) -> dict[str, Any]:
    """Clone or pull lygo-protocol-stack. Requires git on PATH."""
    if not shutil.which("git"):
        return {"ok": False, "error": "git_not_on_path", "signature": SIG}

    root = resolve_stack_root(dest)
    out: dict[str, Any] = {
        "signature": SIG,
        "command": "git_connect",
        "repo": GIT_REPO,
        "utc": utc_now(),
    }

    if root and (root / ".git").is_dir():
        out["path"] = str(root)
        out["action"] = "pull" if pull else "exists"
        if pull:
            r = _run(["git", "pull", "--ff-only"], cwd=root, timeout=300)
            out["result"] = r
            out["ok"] = r["ok"]
        else:
            out["ok"] = True
        return out

    if not clone_if_missing:
        return {**out, "ok": False, "error": "stack_missing", "hint": "set LYGO_STACK_ROOT or pass --dest"}

    target = Path(dest) if dest else Path.cwd() / "lygo-protocol-stack"
    if target.exists() and not (target / ".git").is_dir():
        return {**out, "ok": False, "error": "path_exists_not_git", "path": str(target)}

    out["path"] = str(target.resolve())
    out["action"] = "clone"
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    r = _run(["git", "clone", "--depth", "1", GIT_REPO, str(target)], timeout=600)
    out["result"] = r
    out["ok"] = r["ok"]
    if r["ok"]:
        os.environ["LYGO_STACK_ROOT"] = str(target.resolve())
        out["LYGO_STACK_ROOT"] = os.environ["LYGO_STACK_ROOT"]
    return out


def hf_connect(dest: str | None = None) -> dict[str, Any]:
    """
    Pull HF dataset snapshot of the stack mirror if huggingface-cli/hf available.
    Falls back to documenting URL if CLI missing.
    """
    out: dict[str, Any] = {
        "signature": SIG,
        "command": "hf_connect",
        "dataset": HF_DATASET,
        "url": f"https://huggingface.co/datasets/{HF_DATASET}",
        "utc": utc_now(),
    }
    cli = shutil.which("hf") or shutil.which("huggingface-cli")
    if not cli:
        out["ok"] = False
        out["error"] = "hf_cli_missing"
        out["hint"] = "pip install huggingface_hub[cli]  OR  use git_connect"
        return out

    target = Path(dest) if dest else Path.cwd() / "hf-lygo-protocol-stack"
    target.mkdir(parents=True, exist_ok=True)
    # try modern `hf download`
    if Path(cli).name.lower().startswith("hf"):
        cmd = [
            cli,
            "download",
            HF_DATASET,
            "--repo-type",
            "dataset",
            "--local-dir",
            str(target),
        ]
    else:
        cmd = [
            cli,
            "download",
            HF_DATASET,
            "--repo-type",
            "dataset",
            "--local-dir",
            str(target),
        ]
    r = _run(cmd, timeout=900)
    out["path"] = str(target.resolve())
    out["result"] = r
    out["ok"] = r["ok"]
    return out


def star_chart_snapshot(timeout: float = 25.0) -> dict[str, Any]:
    """Fetch and summarize live Star Chart surfaces for agents."""
    pulse = lattice_pulse(timeout=timeout)
    feed_url = f"{PAGES}/haven_star_chart/haven_star_chart_feed.json"
    data_url = f"{PAGES}/haven_star_chart/haven_star_chart_data.json"
    fr = http_get(feed_url, timeout=timeout)
    dr = http_get(data_url, timeout=timeout)
    feed_data = parse_json(fr.get("body")) if fr.get("ok") else None
    chart_data = parse_json(dr.get("body")) if dr.get("ok") else None

    nodes_sample = []
    if isinstance(chart_data, dict):
        for n in (chart_data.get("nodes") or [])[:8]:
            if isinstance(n, dict):
                nodes_sample.append(
                    {
                        "id": n.get("id"),
                        "name": n.get("name"),
                        "kind": n.get("kind"),
                        "layer": n.get("layer"),
                    }
                )

    return {
        "signature": SIG,
        "command": "star_chart",
        "ok": pulse.get("ok") and fr.get("ok"),
        "utc": utc_now(),
        "live_score": pulse.get("score"),
        "ui": f"{PAGES}/HavenStarChart.html",
        "feed": summarize_feed(feed_data) if feed_data else pulse.get("star_feed"),
        "chart": summarize_chart(chart_data) if chart_data else pulse.get("star_chart"),
        "nodes_sample": nodes_sample,
        "how_to_use": [
            "Read feed chain_valid + entry_count before proposing",
            "Dry-run propose presence with cyborg_star.py propose",
            "Live chart write requires human steward + haven gate --i-consent on stack",
        ],
        "pulse_ok": pulse.get("ok"),
    }


def build_presence_proposal(
    agent_id: str,
    display_name: str,
    *,
    kind: str = "lattice",
    note: str = "LYGO cyborg presence",
) -> dict[str, Any]:
    """Dry-run Star Chart style presence proposal (JSON only — no live write)."""
    aid = "".join(c if c.isalnum() or c in "_-" else "_" for c in agent_id)[:48]
    node_id = f"NODE_CYBORG_{aid.upper()[:16]}"
    return {
        "schema": "lygo.star_chart.presence_proposal.v1",
        "dry_run": True,
        "live_write": False,
        "created_utc": utc_now(),
        "agent_id": agent_id,
        "proposal": {
            "id": node_id,
            "kind": kind,
            "name": display_name[:80],
            "equation": "Δ9 · Continuum · lattice presence",
            "glyph": "🦾",
            "tone": "cyborg-kernel",
            "tags": ["LYGO", "CYBORG", "CONTINUUM", "AGENT"],
            "connections": [],
            "urls": {
                "skillhub": f"{CHATAGENT}/lygoskillhub.html#full-lygo",
                "continuum": f"{CHATAGENT}/lygo-continuum.html",
                "star_chart": f"{PAGES}/HavenStarChart.html",
            },
            "layer": "agent",
            "meta": {"note": note, "source": "lygo-cyborg-kernel"},
        },
        "next_live_steps": [
            "Human steward reviews proposal JSON",
            "On stack: python tools/haven_star_chart_gate.py proposal.json",
            "If ACCEPT: submit with --i-consent (never auto from cyborg alone)",
        ],
        "signature": SIG,
    }


def auto_connect(
    dest: str | None = None,
    *,
    use_git: bool = True,
    use_hf: bool = False,
    timeout: float = 25.0,
) -> dict[str, Any]:
    """Full connect: pulse lattice → git (default) → optional HF → star snapshot."""
    pulse = lattice_pulse(timeout=timeout)
    git_r = None
    hf_r = None
    if use_git:
        git_r = git_connect(dest, pull=True, clone_if_missing=True)
    if use_hf:
        hf_r = hf_connect(dest)
    star = star_chart_snapshot(timeout=timeout)
    stack = resolve_stack_root(dest)
    return {
        "signature": SIG,
        "version": VERSION,
        "command": "auto_connect",
        "ok": bool(pulse.get("ok")),
        "utc": utc_now(),
        "lattice_live": pulse.get("live"),
        "score": pulse.get("score"),
        "stack_root": str(stack) if stack else None,
        "git": git_r,
        "hf": hf_r,
        "star": {
            "ok": star.get("ok"),
            "feed": star.get("feed"),
            "chart": star.get("chart"),
            "ui": star.get("ui"),
        },
        "talk_hint": "Run: python scripts/cyborg_talk.py  — or  cyborg_talk.py say 'status'",
        "skillhub_full": f"{CHATAGENT}/lygoskillhub.html#full-lygo",
    }
