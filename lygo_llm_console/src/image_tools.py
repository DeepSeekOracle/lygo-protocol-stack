"""Image limbs: save, inspect, page thumbnail. No extra pip."""
from __future__ import annotations

import base64
import struct
from pathlib import Path
from typing import Any

from admin_map import read_roots
from paths import WORKSPACE, under_workspace
from web_tools import _blocked, _get


def _in_ws(p: Path) -> Path:
    """Keep a path inside the workspace, for uploads (name-only, never a disk path)."""
    try:
        p.resolve().relative_to(WORKSPACE.resolve())
        return p
    except ValueError:
        return WORKSPACE / p.name


def _allowed_read(p: Path) -> tuple[Path, str | None]:
    """(real_path, refusal) for a read target: the workspace plus the configured read roots.

    Absolute paths elsewhere on the PC are allowed when they sit under a mapped read root
    (config/admin.json -> read_roots) and are not a denied location, which is the same policy the
    other limbs use. Anything else is REFUSED with a reason that names the rule.

    This replaces a silent rewrite: image_info used to bounce an outside path into
    WORKSPACE/<name> and then report "missing", so a real picture on another drive looked absent
    and the model could only answer that the file does not exist.
    """
    from tools import _denied, _under, real_path  # lazy: tools.py is heavy and imports paths
    try:
        rp = real_path(p)
    except Exception:
        return p, "bad_path"
    if _denied(rp):
        return rp, "denied_path"
    roots: list[Path] = [WORKSPACE]
    for extra in tuple(read_roots() or ()):
        try:
            roots.append(Path(extra))
        except (TypeError, ValueError):
            continue
    if _under(rp, tuple(roots)):
        return rp, None
    return rp, "outside_read_roots"


def image_info(path: str) -> dict[str, Any]:
    p, why = _allowed_read(under_workspace(path))
    if why:
        return {"ok": False, "error": why, "path": str(p),
                "read_roots": [str(x) for x in (read_roots() or ())]}
    if not p.is_file():
        return {"ok": False, "error": "missing", "path": str(p)}
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
