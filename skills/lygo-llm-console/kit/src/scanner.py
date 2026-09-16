from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from gguf_header import parse_gguf_header
from ollama_import import import_cas_tree

SKIP_DIR = {"windows", "$recycle.bin", "node_modules", ".git", "system volume information"}


def _expand(root: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(root)))


def scan_roots(roots: list[str], wall_s: float = 25.0) -> dict[str, Any]:
    t0 = time.time()
    models: list[dict[str, Any]] = []
    truncated = False
    seen: set[str] = set()

    for raw in roots:
        root = _expand(raw)
        if not root.exists():
            continue
        # Ollama CAS
        if (root / "manifests").is_dir() and (root / "blobs").is_dir():
            for rec in import_cas_tree(root):
                key = rec.get("path") or rec.get("id")
                if key in seen:
                    continue
                seen.add(str(key))
                models.append(rec)
            continue
        if root.is_file() and root.suffix.lower() == ".gguf":
            h = parse_gguf_header(root)
            models.append(_from_header(h, root))
            continue
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if time.time() - t0 > wall_s:
                truncated = True
                break
            dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIR]
            base = Path(dirpath)
            if "model.safetensors.index.json" in filenames or any(
                fn.endswith(".safetensors") for fn in filenames
            ):
                models.append(
                    {
                        "id": base.name,
                        "path": str(base),
                        "kind": "archive",
                        "status": "UNSUPPORTED_FORMAT",
                        "reason": "safetensors_hf",
                        "runnable": False,
                        "source": "disk",
                    }
                )
                dirnames[:] = []
                continue
            for fn in filenames:
                if time.time() - t0 > wall_s:
                    truncated = True
                    break
                if not fn.lower().endswith(".gguf"):
                    continue
                p = base / fn
                key = str(p)
                if key in seen:
                    continue
                seen.add(key)
                h = parse_gguf_header(p)
                models.append(_from_header(h, p))
        if truncated:
            break
    return {"models": models, "scan_truncated": truncated, "seconds": round(time.time() - t0, 3)}


def _from_header(h: dict[str, Any], path: Path) -> dict[str, Any]:
    try:
        nbytes = path.stat().st_size
    except OSError:
        nbytes = 0
    return {
        "id": h.get("name") or path.stem,
        "path": str(path),
        "kind": h.get("kind") or "chat",
        "ctx": h.get("ctx"),
        "n_gpu_layers": 0,
        "mmproj": None,
        "source": "gguf",
        "bytes": nbytes,
        "runnable": bool(h.get("ok")) and h.get("status") == "ok",
        "status": h.get("status"),
        "meta_truncated": h.get("meta_truncated"),
        "architecture": h.get("architecture"),
    }
