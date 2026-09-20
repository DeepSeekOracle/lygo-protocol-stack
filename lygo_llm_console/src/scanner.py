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
            if "config.json" in filenames and (
                "model.safetensors.index.json" in filenames
                or any(fn.endswith(".safetensors") for fn in filenames)
            ):
                from colibri import looks_like_colibri_model, model_card

                if looks_like_colibri_model(base):
                    models.append(model_card(base))
                    dirnames[:] = []
                    continue
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
                if (h.get("kind") or "") == "mmproj" and _model_beside(p):
                    # A projector is a sidecar, not a model: registering it as one put "gemma4-12b-mmproj"
                    # in the picker and left the model beside it looking blind.
                    continue
                models.append(_from_header(h, p))
        if truncated:
            break
    return {"models": models, "scan_truncated": truncated, "seconds": round(time.time() - t0, 3)}


def _model_beside(projector: Path) -> Path | None:
    """The chat model a projector file belongs to, when it sits in the same folder."""
    stem = projector.stem
    names: list[str] = []
    if stem.lower().endswith("-mmproj"):
        names.append(stem[: -len("-mmproj")] + ".gguf")
    if stem.lower().startswith("mmproj-"):
        names.append(stem[len("mmproj-") :] + ".gguf")
    for name in names:
        cand = projector.parent / name
        if cand.is_file():
            return cand
    return None


def _projector_beside(model: Path) -> Path | None:
    """The projector that belongs to a model file, when it sits in the same folder."""
    stem = model.stem
    if stem.lower().endswith("-mmproj"):
        return None
    for name in (stem + "-mmproj.gguf", "mmproj-" + stem + ".gguf"):
        cand = model.parent / name
        if cand.is_file():
            return cand
    try:
        for cand in sorted(model.parent.glob("*mmproj*.gguf")):
            if cand.is_file() and stem.lower() in cand.name.lower():
                return cand
    except OSError:
        return None
    return None


def _from_header(h: dict[str, Any], path: Path) -> dict[str, Any]:
    try:
        nbytes = path.stat().st_size
    except OSError:
        nbytes = 0
    kind = h.get("kind") or "chat"
    beside = _projector_beside(path) if kind == "chat" else None
    return {
        "id": h.get("name") or path.stem,
        "path": str(path),
        "kind": kind,
        "ctx": h.get("ctx"),
        "n_gpu_layers": 0,
        "mmproj": str(beside) if beside else None,
        "source": "gguf",
        "bytes": nbytes,
        "runnable": bool(h.get("ok")) and h.get("status") == "ok",
        "status": h.get("status"),
        "meta_truncated": h.get("meta_truncated"),
        "architecture": h.get("architecture"),
    }
