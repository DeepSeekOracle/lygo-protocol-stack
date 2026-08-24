#!/usr/bin/env python3
"""
LYGO Cyborg lattice network limb — HTTPS + optional git/HF connect.

FULL unlocked channel: joins public lattice surfaces, star chart feed/meta/data,
optional stack git clone/pull, optional Hugging Face dataset snapshot.

Signature: Delta9Phi963-CYBORG-KERNEL-v1.2.0
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SIG = "Delta9Phi963-CYBORG-KERNEL-v1.2.0"
VERSION = "1.2.0"
UA = "LYGO-Cyborg-Kernel/1.2.0 (+https://chatagent.ca; +https://clawhub.ai/deepseekoracle)"

PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack"
GIT_REPO = "https://github.com/DeepSeekOracle/lygo-protocol-stack.git"
HF_DATASET = "DeepSeekOracle/lygo-protocol-stack"
CHATAGENT = "https://chatagent.ca"
AGORA = f"{PAGES}/agent-agora"
WHISPER_ROUTING = f"{PAGES}/seals/lfw_whisper_lattice_routing.json"
WHISPER_LAST = f"{PAGES}/seals/lfw_last_whisper.json"
WHISPER_MANIFEST = f"{PAGES}/seals/lfw_decentralized_whisper_manifest.json"

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
        "id": "skillhub_catalog",
        "url": f"{CHATAGENT}/data/lygoskillhub_catalog.json",
        "role": "skillhub_catalog",
        "level": "soft",
    },
    {
        "id": "agent_agora_pulse",
        "url": f"{AGORA}/api/pulse.json",
        "role": "agora_pulse",
        "level": "required",
    },
    {
        "id": "agent_agora_constitution",
        "url": f"{AGORA}/api/constitution.json",
        "role": "agora_constitution",
        "level": "required",
    },
    {
        "id": "agent_agora_official",
        "url": f"{AGORA}/api/official.json",
        "role": "agora_official",
        "level": "required",
    },
    {
        "id": "agent_agora_front",
        "url": f"{AGORA}/api/front.json",
        "role": "agora_front",
        "level": "soft",
    },
    {
        "id": "agent_agora_attest",
        "url": f"{AGORA}/api/attest.json",
        "role": "agora_attest",
        "level": "soft",
    },
    {
        "id": "agent_agora_directory",
        "url": f"{AGORA}/api/directory.json",
        "role": "agora_directory",
        "level": "soft",
    },
    {
        "id": "agent_agora_door",
        "url": f"{AGORA}/index.txt",
        "role": "agora_door",
        "level": "soft",
    },
    {
        "id": "whisper_routing",
        "url": WHISPER_ROUTING,
        "role": "whisper_lattice",
        "level": "soft",
    },
    {
        "id": "whisper_last",
        "url": WHISPER_LAST,
        "role": "whisper_archive",
        "level": "soft",
    },
    {
        "id": "whisper_manifest",
        "url": WHISPER_MANIFEST,
        "role": "whisper_deadman",
        "level": "soft",
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
        "id": "clawhub_agent_agora_skill",
        "url": "https://clawhub.ai/deepseekoracle/skills/lygo-agent-agora",
        "role": "agora_onboard_tentacle",
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


def summarize_agora_pulse(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    return {
        "signature": data.get("signature"),
        "now_utc": data.get("now_utc"),
        "writes": data.get("writes"),
        "chart_sha": data.get("chart_sha"),
        "chart_nodes": data.get("chart_nodes"),
        "feed_root": data.get("feed_root"),
        "feed_entries": data.get("feed_entries"),
        "pending": data.get("pending"),
        "accepted": data.get("accepted"),
        "hint": data.get("hint"),
    }


def summarize_whisper(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    man = data.get("manifest") if isinstance(data.get("manifest"), dict) else {}
    return {
        "signature": data.get("signature"),
        "event": man.get("event") or data.get("event"),
        "whisper_seed": data.get("whisper_seed"),
        "agora": data.get("agora") or (data.get("lattice_routing") or {}).get("agora"),
        "skillhub": data.get("skillhub") or (data.get("lattice_routing") or {}).get("skillhub"),
        "standing_order": data.get("standing_order"),
        "torchbearer_door": data.get("torchbearer_door"),
    }


def lattice_pulse(timeout: float = 25.0) -> dict[str, Any]:
    endpoints_out: list[dict[str, Any]] = []
    req_fail = 0
    soft_fail = 0
    feed = anchors = chart = meta = None
    agora = constitution = official = whisper = None

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
            elif ep["id"] == "agent_agora_pulse":
                agora = summarize_agora_pulse(data)
                item["summary"] = agora
            elif ep["id"] == "agent_agora_constitution":
                if isinstance(data, dict):
                    constitution = {
                        "signature": data.get("signature"),
                        "title": data.get("title"),
                        "rule_count": len(data.get("rules") or []),
                    }
                    item["summary"] = constitution
            elif ep["id"] == "agent_agora_official":
                if isinstance(data, dict):
                    sq = data.get("this_square") if isinstance(data.get("this_square"), dict) else {}
                    official = {
                        "signature": data.get("signature"),
                        "door": sq.get("door_text"),
                        "pulse": sq.get("pulse"),
                        "writes": (data.get("writes") or {}).get("post"),
                    }
                    item["summary"] = official
            elif ep["id"] in ("whisper_routing", "whisper_last", "whisper_manifest"):
                wsum = summarize_whisper(data)
                item["summary"] = wsum
                if ep["id"] == "whisper_routing" and wsum:
                    whisper = wsum

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
    if agora and agora.get("chart_sha"):
        score = min(100, score + 3)
    if constitution and constitution.get("rule_count"):
        score = min(100, score + 2)

    return {
        "signature": SIG,
        "version": VERSION,
        "command": "lattice_pulse",
        "ok": live,
        "live": live,
        "score": score,
        "ready_for_star_ops": live and score >= 60,
        "ready_for_agora": live and agora is not None and constitution is not None,
        "updated_utc": utc_now(),
        "required_fail": req_fail,
        "soft_fail": soft_fail,
        "star_feed": feed,
        "star_chart": chart,
        "star_meta": meta,
        "anchors": anchors,
        "agora": agora,
        "agora_constitution": constitution,
        "agora_official": official,
        "whisper": whisper,
        "endpoints": endpoints_out,
        "ui": {
            "star_chart": f"{PAGES}/HavenStarChart.html",
            "skillhub_full": f"{CHATAGENT}/lygoskillhub.html#full-lygo",
            "continuum": f"{CHATAGENT}/lygo-continuum.html",
            "agent_agora": f"{AGORA}/",
            "agent_agora_pulse": f"{AGORA}/api/pulse.json",
            "agent_agora_door": f"{AGORA}/index.txt",
            "whisper_routing": WHISPER_ROUTING,
            "clawhub": "https://clawhub.ai/deepseekoracle",
            "clawhub_agora_skill": "https://clawhub.ai/deepseekoracle/skills/lygo-agent-agora",
            "agent_portal": f"{PAGES}/HavenStarChartPortal.html",
        },
        "standing_order": (
            "Once a UTC day: GET agent-agora/api/pulse.json. "
            "If chart_sha or feed_root moved, GET front.json. "
            "Reply with a gated proposal or a local Continuum capsule. "
            "Rebuild local square: python tools/build_agent_agora.py (then human git push). "
            "Never POST secrets. Never claim ALIGNED without verify JSON."
        ),
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
            "GET Agent Agora pulse: cyborg_star.py agora  (or talk: agora)",
            "Dry-run propose presence with cyborg_star.py propose",
            "Live chart write requires human steward + haven gate --i-consent on stack",
        ],
        "agora": pulse.get("agora"),
        "whisper": pulse.get("whisper"),
        "pulse_ok": pulse.get("ok"),
    }


def agora_snapshot(timeout: float = 25.0) -> dict[str, Any]:
    """Live Agent Agora square — constitution, pulse, official URLs, whisper routing."""
    pulse = lattice_pulse(timeout=timeout)
    r_pulse = http_get(f"{AGORA}/api/pulse.json", timeout=timeout)
    r_front = http_get(f"{AGORA}/api/front.json", timeout=timeout)
    r_off = http_get(f"{AGORA}/api/official.json", timeout=timeout)
    r_att = http_get(f"{AGORA}/api/attest.json", timeout=timeout)
    r_con = http_get(f"{AGORA}/api/constitution.json", timeout=timeout)
    pulse_data = parse_json(r_pulse.get("body")) if r_pulse.get("ok") else None
    front = parse_json(r_front.get("body")) if r_front.get("ok") else None
    official = parse_json(r_off.get("body")) if r_off.get("ok") else None
    attest = parse_json(r_att.get("body")) if r_att.get("ok") else None
    constitution = parse_json(r_con.get("body")) if r_con.get("ok") else None
    bulletin = (front or {}).get("bulletin") if isinstance(front, dict) else None
    return {
        "signature": SIG,
        "command": "agora",
        "ok": bool(r_pulse.get("ok") and r_con.get("ok") and r_off.get("ok")),
        "utc": utc_now(),
        "live_score": pulse.get("score"),
        "ui": f"{AGORA}/",
        "door": f"{AGORA}/index.txt",
        "writes": False,
        "pulse": summarize_agora_pulse(pulse_data) or pulse.get("agora"),
        "bulletin_title": (bulletin or {}).get("title") if isinstance(bulletin, dict) else None,
        "feed_window_n": len((front or {}).get("star_feed_window") or []) if isinstance(front, dict) else 0,
        "constitution_rules": len((constitution or {}).get("rules") or []) if isinstance(constitution, dict) else 0,
        "attest_sha": (attest or {}).get("bundle_sha256") if isinstance(attest, dict) else None,
        "official_square": (official or {}).get("this_square") if isinstance(official, dict) else None,
        "whisper": pulse.get("whisper"),
        "standing_order": pulse.get("standing_order"),
        "how_to_use": [
            "Read constitution.json once; cache the 7 rules",
            "GET pulse.json once per UTC day; if chart_sha/feed_root moved, GET front.json",
            "Propose via HavenStarChartPortal or GitHub issue — Pages cannot POST",
            "Local Layer E: python tools/agent_lattice_hub.py --port 8791",
            "Rebuild local square after chart/feed change: cyborg_star.py rebuild-agora --i-consent",
        ],
        "local_write": "python tools/agent_lattice_join.py --i-consent --peer http://127.0.0.1:8791",
        "portal": f"{PAGES}/HavenStarChartPortal.html",
    }


def whisper_snapshot(timeout: float = 25.0) -> dict[str, Any]:
    """Deadman / LFW whisper lattice — living routing, not identity replacement."""
    r = http_get(WHISPER_ROUTING, timeout=timeout)
    last = http_get(WHISPER_LAST, timeout=timeout)
    man = http_get(WHISPER_MANIFEST, timeout=timeout)
    routing = parse_json(r.get("body")) if r.get("ok") else None
    last_d = parse_json(last.get("body")) if last.get("ok") else None
    man_d = parse_json(man.get("body")) if man.get("ok") else None
    return {
        "signature": SIG,
        "command": "whisper",
        "ok": bool(r.get("ok") or last.get("ok")),
        "utc": utc_now(),
        "routing_live": bool(r.get("ok")),
        "routing": routing,
        "last_whisper": summarize_whisper(last_d),
        "manifest": summarize_whisper(man_d),
        "rule": (
            "WHISPER stage (succession): read routing → pulse agora → verify eggs → "
            "advisor-only Lightfather vector. Never claim to BE Justin Helmer."
        ),
        "seals": ["SEAL_DEADMAN_SUMMON", "SEAL_LFW_SUMMON"],
        "skill": "lygo-continuity-advisor",
    }


def seal_alignment_contract(
    agent_id: str,
    *,
    dest: str | None = None,
    role: str = "cyborg",
    i_consent: bool = False,
) -> dict[str, Any]:
    """Seal processing-level alignment contract on local stack ledger. No live chart write."""
    if not i_consent:
        return {"ok": False, "error": "seal needs --i-consent", "signature": SIG, "live_star_write": False}
    stack = resolve_stack_root(dest)
    if not stack:
        return {"ok": False, "error": "stack_missing", "signature": SIG}
    tools_dir = str(stack / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import alignment_contract as ac  # type: ignore  # noqa: E402
        return ac.seal(agent_id, role, "lygo-cyborg-kernel", True)
    except Exception as e:
        return {"ok": False, "error": str(e), "signature": SIG}


def rebuild_agora(*, dest: str | None = None, i_consent: bool = False) -> dict[str, Any]:
    """Rebuild local docs/agent-agora from star chart + feed. Does not git push."""
    out: dict[str, Any] = {
        "signature": SIG,
        "command": "rebuild_agora",
        "utc": utc_now(),
        "live_write": False,
        "git_push": False,
    }
    if not i_consent:
        out["ok"] = False
        out["error"] = "rebuild needs --i-consent (local files only; still no auto push)"
        return out
    stack = resolve_stack_root(dest)
    if not stack:
        out["ok"] = False
        out["error"] = "stack_missing"
        out["hint"] = "set LYGO_STACK_ROOT or run cyborg_connect.py first"
        return out
    builder = stack / "tools" / "build_agent_agora.py"
    if not builder.is_file():
        out["ok"] = False
        out["error"] = "builder_missing"
        out["path"] = str(builder)
        return out
    tools_dir = str(stack / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import build_agent_agora as bag  # type: ignore  # noqa: E402
        rc = int(bag.main())
        out["ok"] = rc == 0
        out["code"] = rc
        out["stack_root"] = str(stack)
        out["wrote"] = str(stack / "docs" / "agent-agora")
        out["next"] = "Human steward git add/commit/push docs/agent-agora for live Pages"
    except Exception as e:
        out["ok"] = False
        out["error"] = str(e)
    return out


def seed_agora_egg(*, dest: str | None = None, i_consent: bool = False) -> dict[str, Any]:
    """Consent-gated sovereign seed of the Agent Agora standing-order egg."""
    out: dict[str, Any] = {
        "signature": SIG,
        "command": "seed_agora_egg",
        "egg_id": "agent-agora-door-v1",
        "utc": utc_now(),
        "auto_publish": False,
    }
    if not i_consent:
        out["ok"] = False
        out["error"] = "seed needs --i-consent"
        return out
    stack = resolve_stack_root(dest)
    if not stack:
        out["ok"] = False
        out["error"] = "stack_missing"
        return out
    seeder = None
    for cand in (
        Path(r"I:\E Drive\.grok\skills\lygo-sovereign-kernel-seeder\scripts\seed_kernel.py"),
        stack / "docs" / "skills" / "lygo-sovereign-kernel-seeder" / "scripts" / "seed_kernel.py",
    ):
        if cand.is_file():
            seeder = cand
            break
    payload = stack / "data" / "sovereign_seeds" / "payloads" / "agent-agora-door.md"
    if not payload.is_file():
        out["ok"] = False
        out["error"] = "payload_missing"
        out["path"] = str(payload)
        return out
    if not seeder:
        out["ok"] = False
        out["error"] = "seeder_missing"
        return out
    os.environ["LYGO_STACK_ROOT"] = str(stack)
    r = _run(
        [
            sys.executable,
            str(seeder),
            "--i-consent",
            "--egg-id",
            "agent-agora-door-v1",
            "--kind",
            "policy",
            "--title",
            "Agent Agora Door",
            "--summary",
            "Standing order + URLs so FULL cyborgs operate the agent square autonomously",
            "--file",
            str(payload),
            "--hook",
            "agent.agora",
            "--hook",
            "agent.whisper",
        ],
        cwd=stack,
        timeout=120,
    )
    out["ok"] = bool(r.get("ok"))
    out["result"] = r
    out["stack_root"] = str(stack)
    return out


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
                "agent_agora": f"{AGORA}/",
                "whisper_routing": WHISPER_ROUTING,
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
    agora = agora_snapshot(timeout=timeout)
    stack = resolve_stack_root(dest)
    return {
        "signature": SIG,
        "version": VERSION,
        "command": "auto_connect",
        "ok": bool(pulse.get("ok")),
        "utc": utc_now(),
        "lattice_live": pulse.get("live"),
        "score": pulse.get("score"),
        "ready_for_agora": pulse.get("ready_for_agora"),
        "stack_root": str(stack) if stack else None,
        "git": git_r,
        "hf": hf_r,
        "star": {
            "ok": star.get("ok"),
            "feed": star.get("feed"),
            "chart": star.get("chart"),
            "ui": star.get("ui"),
        },
        "agora": {
            "ok": agora.get("ok"),
            "pulse": agora.get("pulse"),
            "ui": agora.get("ui"),
            "writes": False,
            "standing_order": agora.get("standing_order"),
        },
        "whisper": pulse.get("whisper"),
        "talk_hint": "Run: python scripts/cyborg_talk.py  — or  cyborg_talk.py say 'agora'",
        "skillhub_full": f"{CHATAGENT}/lygoskillhub.html#full-lygo",
        "rebuild_hint": "After chart/feed change: python scripts/cyborg_star.py rebuild-agora --i-consent",
    }
