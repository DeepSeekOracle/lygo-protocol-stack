"""Render monospace text to PNG for vision-model context."""

from __future__ import annotations

import io
from typing import Tuple

from pxpipe_lygo.config import FONT_SIZE, LINE_SPACING, MAX_PNG_HEIGHT, MAX_PNG_WIDTH

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    raise ImportError("pxpipe_lygo requires Pillow: pip install Pillow") from exc


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_text_to_png(text: str) -> Tuple[bytes, int, int]:
    font = _load_font(FONT_SIZE)
    lines = text.splitlines() or [""]
    max_line = max(len(line) for line in lines)
    bbox = font.getbbox("M")
    char_w = max(8, bbox[2] - bbox[0])
    line_h = (bbox[3] - bbox[1]) + LINE_SPACING

    width = min(MAX_PNG_WIDTH, max(120, max_line * char_w + 24))
    height = min(MAX_PNG_HEIGHT, max(80, len(lines) * line_h + 24))

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 12
    for line in lines:
        if y + line_h > height - 8:
            draw.text((12, y), "… [truncated for PNG cap]", font=font, fill=(120, 0, 0))
            break
        draw.text((12, y), line, font=font, fill=(0, 0, 0))
        y += line_h

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue(), width, height