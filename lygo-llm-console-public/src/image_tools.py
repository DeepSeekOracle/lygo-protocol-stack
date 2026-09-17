"""Image limbs: save, inspect, page thumbnail. No extra pip."""
from __future__ import annotations

import base64
import struct
from pathlib import Path
from typing import Any

from paths import WORKSPACE
from web_tools import _blocked, _get


def _in_ws(p: Path) -> Path:
    try:
        p.resolve().relative_to(WORKSPACE.resolve())
        return p
    except ValueError:
        return WORKSPACE / p.name


def image_info(path: str) -> dict[str, Any]:
    p = _in_ws(Path(path) if Path(path).is_absolute() else WORKSPACE / path)
    if not p.is_file():
        return {"ok": False, "error": "missing"}
    raw = p.read_bytes()[:32]
    kind = "unknown"
    w = h = 0
    if raw[:8] == b"\x89PNG\r\n\x1a\n" and len(raw) >= 24:
        kind = "png"
        w, h = struct.unpack(">II", raw[16:24])
    elif raw[:2] == b"\xff\xd8":
        kind = "jpeg"
    elif raw[:6] in (b"GIF87a", b"GIF89a"):
        kind = "gif"
        if len(raw) >= 10:
            w, h = struct.unpack("<HH", raw[6:10])
    return {"ok": True, "path": str(p), "kind": kind, "bytes": p.stat().st_size, "width": w, "height": h}


def image_save(b64: str, path: str | None = None) -> dict[str, Any]:
    s = (b64 or "").strip()
    if "," in s and s.lower().startswith("data:"):
        s = s.split(",", 1)[1]
    try:
        data = base64.b64decode(s)
    except Exception:
        return {"ok": False, "error": "bad_base64"}
    if len(data) > 8_000_000:
        return {"ok": False, "error": "too_large"}
    dest = WORKSPACE / "images" / (path or "upload.bin")
    dest = _in_ws(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    info = image_info(str(dest))
    info["saved"] = True
    return info


def image_list() -> dict[str, Any]:
    root = WORKSPACE / "images"
    root.mkdir(parents=True, exist_ok=True)
    names = [p.name for p in root.iterdir() if p.is_file()][:80]
    return {"ok": True, "dir": str(root), "files": names}


def page_thumbnail(url: str) -> dict[str, Any]:
    why = _blocked(url)
    if why:
        return {"ok": False, "error": why}
    shot = "https://image.thum.io/get/width/1024/noanimate/" + url
    code, raw, ctype = _get(shot)
    if code != 200 or not raw or len(raw) < 80:
        return {"ok": False, "error": f"thumb_{code}", "ctype": ctype}
    dest = WORKSPACE / "images" / "page-thumb.jpg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    return {"ok": True, "path": str(dest), "bytes": len(raw), "source": shot, "class": "RESOURCE"}
