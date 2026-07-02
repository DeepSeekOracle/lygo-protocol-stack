"""Stack integration — anchor SLM, P7, consensus; update link archive + queue."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from lygo_anchor import MultiAnchor  # noqa: E402
from lygo_anchor_config import AnchorProfile  # noqa: E402

ARCHIVE = ROOT / "docs" / "LYGO_PUBLIC_LINK_ARCHIVE.json"
SIGNATURE = "Δ9Φ963-STACK-ANCHOR-v1"


class AnchorOrchestrator:
    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or ROOT
        self.profile = AnchorProfile.load()
        self.multi = MultiAnchor(self.profile, self.repo_root)

    def enqueue(self, event_type: str, payload: dict, payload_id: str | None = None) -> Path:
        paths = self.profile.resolve_paths(self.repo_root)
        paths["queue"].mkdir(parents=True, exist_ok=True)
        pid = payload_id or f"{event_type}_{int(time.time())}"
        job = {
            "signature": SIGNATURE,
            "event_type": event_type,
            "payload_id": pid,
            "payload": payload,
            "enqueued_at": time.time(),
        }
        path = paths["queue"] / f"{pid}.json"
        path.write_text(json.dumps(job, indent=2), encoding="utf-8")
        return path

    def process_job(self, job_path: Path) -> dict[str, Any]:
        job = json.loads(job_path.read_text(encoding="utf-8"))
        et = job.get("event_type", "GENERIC")
        pid = job.get("payload_id", "unknown")
        payload = job.get("payload", {})
        if et == "CONSENSUS":
            result = self.multi.anchor_consensus(payload)
        elif et == "P7_BIOMETRIC":
            result = self.multi.anchor_payload(pid, payload, "P7_BIOMETRIC")
        elif et == "SLM_MERGE":
            result = self.multi.anchor_payload(pid, payload, "SLM_MERGE")
        elif et == "MEMORY":
            result = self.multi.anchor_memory(pid, payload)
        else:
            result = self.multi.anchor_payload(pid, payload, et)
        receipt = {
            "event_type": et,
            "payload_id": pid,
            "success": result.success,
            "url": result.url,
            "service": result.service,
            "content_sha256": result.content_sha256,
        }
        if self.profile.auto_append_link_archive and result.success:
            self._append_permaweb_link(pid, result.url, et)
        if self.profile.ble_enabled and result.content_sha256:
            self._ble_touch(result.content_sha256)
        job_path.unlink(missing_ok=True)
        return receipt

    def drain_queue(self, max_jobs: int = 32) -> list[dict]:
        paths = self.profile.resolve_paths(self.repo_root)
        q = paths["queue"]
        if not q.is_dir():
            return []
        done = []
        for job_path in sorted(q.glob("*.json"))[:max_jobs]:
            try:
                done.append(self.process_job(job_path))
            except Exception as exc:
                done.append({"payload_id": job_path.stem, "success": False, "error": str(exc)})
        return done

    def on_consensus(self, consensus: dict) -> dict[str, Any]:
        from dataclasses import asdict

        pid = consensus.get("proposal_id") or f"consensus_{int(time.time())}"
        self.enqueue("CONSENSUS", consensus, pid)
        r = self.multi.anchor_consensus(consensus)
        return asdict(r)

    def on_p7_snapshot(self, bio_state: dict) -> dict[str, Any]:
        pid = f"p7_{int(time.time())}"
        r = self.multi.anchor_payload(pid, bio_state, "P7_BIOMETRIC")
        return {"payload_id": pid, "url": r.url, "service": r.service, "success": r.success}

    def on_slm_merge(self, merge_report: dict) -> dict[str, Any]:
        pid = f"slm_{merge_report.get('root_hash', '')[:12] or int(time.time())}"
        r = self.multi.anchor_payload(pid, merge_report, "SLM_MERGE")
        return {"payload_id": pid, "url": r.url, "service": r.service, "success": r.success}

    def _append_permaweb_link(self, entry_id: str, url: str, role: str) -> None:
        if not ARCHIVE.is_file():
            return
        data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        entries = data.setdefault("entries", [])
        aid = f"permaweb-{entry_id}"[:64]
        existing = next((e for e in entries if e.get("id") == aid), None)
        if existing:
            existing.setdefault("urls", {})["permaweb"] = url
        else:
            entries.append(
                {
                    "id": aid,
                    "title": f"Permaweb anchor — {entry_id}",
                    "role": f"anchor-{role.lower()}",
                    "urls": {"permaweb": url},
                    "since": time.strftime("%Y-%m-%d"),
                }
            )
        data.setdefault("growth_log", []).append(
            {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": f"anchor {entry_id}", "refs": [aid]}
        )
        ARCHIVE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _ble_touch(self, content_sha256: str) -> None:
        try:
            from ble_mesh_bouncer import LygoBleMeshBouncer
            import asyncio

            b = LygoBleMeshBouncer()
            asyncio.run(b.broadcast_state_hash(content_sha256))
        except Exception:
            pass


_orchestrator: AnchorOrchestrator | None = None


def get_orchestrator() -> AnchorOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AnchorOrchestrator()
    return _orchestrator