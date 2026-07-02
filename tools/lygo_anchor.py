#!/usr/bin/env python3
"""
LYGO Anchor — ultimate unified anchoring (local CA + Turbo + web3 + mesh).
Δ9Φ963-ANCHOR-ULTIMATE-v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

import requests

from lygo_anchor_config import AnchorProfile, ROOT

SIGNATURE = "Δ9Φ963-ANCHOR-ULTIMATE-v1"


@dataclass
class AnchorResult:
    success: bool
    id: str
    url: str
    service: str
    size_bytes: int
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    content_sha256: str = ""


class LocalContentAnchor:
    """Sovereign content-addressed store — always succeeds offline."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

    def anchor(self, data: bytes, payload_id: str) -> AnchorResult:
        digest = hashlib.sha256(data).hexdigest()
        path = self.workspace / f"{digest}.json"
        envelope = {
            "signature": SIGNATURE,
            "payload_id": payload_id,
            "content_sha256": digest,
            "size_bytes": len(data),
            "stored_utc": time.time(),
            "payload_b64": None,
        }
        if len(data) <= 512_000:
            import base64

            envelope["payload_b64"] = base64.b64encode(data).decode("ascii")
        path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        return AnchorResult(
            success=True,
            id=digest,
            url=path.as_uri(),
            service="LYGO-Local-CA",
            size_bytes=len(data),
            timestamp=time.time(),
            metadata={"path": str(path)},
            content_sha256=digest,
        )


class ArweaveTurboAnchor:
    """Arweave Turbo / up.arweave.net — free tier under 100 KiB when gateway accepts."""

    def __init__(self, profile: AnchorProfile):
        self.profile = profile

    def upload(self, data: bytes, payload_id: str, tags: list[dict[str, str]] | None = None) -> dict[str, Any]:
        if len(data) > self.profile.free_max_bytes:
            return {"success": False, "error": "exceeds_free_tier", "size": len(data)}
        headers = {
            "Content-Type": "application/octet-stream",
            "X-LYGO-Signature": "Δ9Φ963-PERMAWEB-ANCHOR",
            "X-LYGO-Payload-ID": payload_id,
        }
        last_err = ""
        for url in (self.profile.turbo_data_url, self.profile.turbo_upload_url):
            for attempt in range(3):
                try:
                    resp = requests.post(url, data=data, headers=headers, timeout=45)
                    if resp.status_code in (200, 201, 202):
                        body = resp.json() if resp.text.strip().startswith("{") else {}
                        tx_id = body.get("id") or body.get("txId") or hashlib.sha256(data).hexdigest()[:43]
                        return {
                            "success": True,
                            "id": tx_id,
                            "url": f"{self.profile.arweave_gateway.rstrip('/')}/{tx_id}",
                            "service": "Arweave-Turbo",
                            "timestamp": time.time(),
                            "gateway": url,
                        }
                    last_err = f"{resp.status_code}:{resp.text[:200]}"
                except Exception as exc:
                    last_err = str(exc)
                time.sleep(2**attempt * 0.5)
        return {"success": False, "error": last_err or "turbo_unreachable"}


class Web3StorageAnchor:
    def __init__(self, api_key: str | None):
        self.api_key = api_key or os.environ.get("WEB3_STORAGE_API_KEY")

    def upload(self, data: bytes, name: str = "lygo_anchor.json") -> dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "WEB3_STORAGE_API_KEY_missing"}
        try:
            import tempfile

            with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
                f.write(data)
                temp_path = f.name
            try:
                from web3storagepy import upload as w3_upload  # type: ignore

                result = w3_upload(file=temp_path, token=self.api_key)
                if result.get("STATUS_CODE") == 200:
                    response_data = json.loads(result.get("RESPONSE", "{}"))
                    cid = response_data.get("cid", "")
                    return {
                        "success": True,
                        "cid": cid,
                        "id": cid,
                        "url": f"https://dweb.link/ipfs/{cid}",
                        "service": "web3.storage",
                        "timestamp": time.time(),
                    }
                return {"success": False, "error": str(result)}
            finally:
                os.unlink(temp_path)
        except ImportError:
            return {"success": False, "error": "web3storagepy_not_installed"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


class MultiAnchor:
    def __init__(self, profile: AnchorProfile | None = None, repo_root: Path | None = None):
        self.repo_root = repo_root or ROOT
        self.profile = profile or AnchorProfile.load()
        paths = self.profile.resolve_paths(self.repo_root)
        self.local = LocalContentAnchor(paths["workspace"])
        self.turbo = ArweaveTurboAnchor(self.profile)
        self.web3 = Web3StorageAnchor(os.environ.get("WEB3_STORAGE_API_KEY"))

    def anchor_bytes(self, data: bytes, payload_id: str, description: str = "") -> AnchorResult:
        results: list[AnchorResult] = []
        local_r = self.local.anchor(data, payload_id)
        results.append(local_r)
        mode = self.profile.mode
        if mode in ("turbo", "multi"):
            tr = self.turbo.upload(data, payload_id, self.profile.tags)
            if tr.get("success"):
                results.append(
                    AnchorResult(
                        success=True,
                        id=tr["id"],
                        url=tr["url"],
                        service=tr["service"],
                        size_bytes=len(data),
                        timestamp=tr.get("timestamp", time.time()),
                        metadata=tr,
                        content_sha256=local_r.content_sha256,
                    )
                )
        if mode == "multi" and len(data) >= self.profile.free_max_bytes:
            wr = self.web3.upload(data, payload_id)
            if wr.get("success"):
                results.append(
                    AnchorResult(
                        success=True,
                        id=wr["id"],
                        url=wr["url"],
                        service=wr["service"],
                        size_bytes=len(data),
                        timestamp=wr.get("timestamp", time.time()),
                        metadata=wr,
                        content_sha256=local_r.content_sha256,
                    )
                )
        best = next((r for r in results if r.service != "LYGO-Local-CA" and r.success), local_r)
        best.metadata["description"] = description
        best.metadata["all_services"] = [asdict(r) for r in results]
        self._write_receipt(payload_id, best)
        return best

    def anchor_payload(self, payload_id: str, data: dict, event_type: str = "GENERIC") -> AnchorResult:
        envelope = {
            "type": event_type,
            "payload_id": payload_id,
            "data": data,
            "timestamp": time.time(),
            "version": SIGNATURE,
        }
        raw = json.dumps(envelope, sort_keys=True).encode("utf-8")
        return self.anchor_bytes(raw, payload_id, description=event_type)

    def anchor_light_code(self, light_code: str, metadata: dict | None = None) -> AnchorResult:
        return self.anchor_payload(
            f"light_{hashlib.sha256(light_code.encode()).hexdigest()[:12]}",
            {"light_code": light_code, "metadata": metadata or {}},
            "LIGHT_CODE",
        )

    def anchor_consensus(self, consensus_result: dict) -> AnchorResult:
        pid = consensus_result.get("proposal_id") or hashlib.sha256(
            json.dumps(consensus_result, sort_keys=True).encode()
        ).hexdigest()[:16]
        return self.anchor_payload(f"consensus_{pid}", consensus_result, "CONSENSUS")

    def anchor_memory(self, memory_id: str, data: dict) -> AnchorResult:
        return self.anchor_payload(f"memory_{memory_id}", {"memory_id": memory_id, "data": data}, "MEMORY_FRAGMENT")

    def anchor_merkle_batch(self, leaves: list[dict], batch_id: str | None = None) -> AnchorResult:
        hashes = [hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest() for x in leaves]
        if len(hashes) == 1:
            root = hashes[0]
        else:
            while len(hashes) > 1:
                nxt = []
                for i in range(0, len(hashes), 2):
                    pair = hashes[i] + (hashes[i + 1] if i + 1 < len(hashes) else hashes[i])
                    nxt.append(hashlib.sha256(pair.encode()).hexdigest())
                hashes = nxt
            root = hashes[0]
        bid = batch_id or f"merkle_{root[:16]}"
        return self.anchor_payload(bid, {"merkle_root": root, "count": len(leaves)}, "MERKLE_BATCH")

    def _write_receipt(self, payload_id: str, result: AnchorResult) -> None:
        paths = self.profile.resolve_paths(self.repo_root)
        paths["receipts"].mkdir(parents=True, exist_ok=True)
        receipt = {
            "status": "ANCHOR_RECEIPT",
            "payload_id": payload_id,
            "success": result.success,
            "id": result.id,
            "url": result.url,
            "service": result.service,
            "content_sha256": result.content_sha256,
            "timestamp": result.timestamp,
        }
        (paths["receipts"] / f"anchor_receipt_{payload_id}.json").write_text(
            json.dumps(receipt, indent=2), encoding="utf-8"
        )


# Back-compat alias
LYGOAnchor = MultiAnchor


def verify_tx(tx_id: str, timeout: int = 20) -> dict[str, Any]:
    url = f"https://arweave.net/tx/{tx_id}/status"
    try:
        r = requests.get(url, timeout=timeout)
        return {"ok": r.status_code == 200, "status_code": r.status_code, "body": r.text[:500]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Anchor CLI")
    ap.add_argument("--type", choices=["light_code", "consensus", "memory", "file", "verify"], required=True)
    ap.add_argument("--data", help="JSON string or file path")
    ap.add_argument("--tx-id", help="For --type verify")
    ap.add_argument("--output", help="Write result JSON")
    args = ap.parse_args()
    anchor = MultiAnchor()

    if args.type == "verify":
        out = verify_tx(args.tx_id or "")
    elif args.type == "light_code":
        out = asdict(anchor.anchor_light_code(args.data or ""))
    elif args.type == "consensus":
        data = json.loads(args.data) if args.data else {}
        out = asdict(anchor.anchor_consensus(data))
    elif args.type == "memory":
        data = json.loads(args.data) if args.data else {}
        out = asdict(anchor.anchor_memory("cli_memory", data))
    elif args.type == "file":
        path = Path(args.data or "")
        content = path.read_bytes()
        out = asdict(anchor.anchor_bytes(content, f"file_{path.stem}", str(path)))
    else:
        out = {"error": "unknown"}

    text = json.dumps(out, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0 if out.get("success", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())