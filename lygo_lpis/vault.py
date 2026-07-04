"""P1 prompt vault — manifests + content shards (no secrets in repo)."""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any, Optional

SIGNATURE = "Δ9Φ963-LPIS-VAULT-v1"


def vault_root() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "prompt_vault"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:64]


class PromptVault:
    def __init__(self, root: Optional[Path] = None):
        self.root = root or vault_root()
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest = self.root / "vault_manifest.jsonl"

    def ingest(
        self,
        source: str,
        *,
        file_path: Optional[Path] = None,
        url: Optional[str] = None,
        model: str = "unknown",
        version: str = "1.0",
    ) -> dict[str, Any]:
        if file_path and file_path.is_file():
            content = file_path.read_text(encoding="utf-8", errors="replace")
            prov = str(file_path)
        elif url:
            with urllib.request.urlopen(url, timeout=120) as resp:
                content = resp.read().decode("utf-8", errors="replace")
            prov = url
        else:
            return {"ok": False, "error": "file_path or url required"}

        prompt_id = f"prompt_{_slug(source)}_{hashlib.sha256(content.encode()).hexdigest()[:8]}"
        digest = hashlib.sha256(content.encode()).hexdigest()
        body_path = self.root / f"{prompt_id}.txt"
        body_path.write_text(content, encoding="utf-8")
        record = {
            "signature": SIGNATURE,
            "id": prompt_id,
            "source": source,
            "model": model,
            "version": version,
            "provenance": prov,
            "sha256": digest,
            "chars": len(content),
            "ingested_utc": time.time(),
            "path": str(body_path.relative_to(self.root.parent.parent)).replace("\\", "/"),
        }
        meta_path = self.root / f"{prompt_id}.json"
        meta_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        with self.manifest.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        return {"ok": True, "prompt_id": prompt_id, "sha256": digest, "chars": len(content)}

    def load(self, prompt_id: str) -> Optional[dict[str, Any]]:
        meta = self.root / f"{prompt_id}.json"
        if not meta.is_file():
            return None
        record = json.loads(meta.read_text(encoding="utf-8"))
        body = self.root / f"{prompt_id}.txt"
        if body.is_file():
            record["content"] = body.read_text(encoding="utf-8", errors="replace")
        return record

    def list_ids(self) -> list[str]:
        return sorted(p.stem for p in self.root.glob("prompt_*.json"))