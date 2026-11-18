"""Neon look shared by all text overlays: glowing text and a dark glass panel with a
glowing border, centred in an otherwise transparent frame.

Text is drawn into a greyscale mask first; the mask is then turned into a stack of
blurred, coloured glow layers plus a bright core (the accent colour mixed with white),
like a neon tube. `strength` scales the glow, which the overlays use to flash on events.
"""

import math
from collections.abc import Iterable
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from app.video.fonts import display_font_has, load_display_font, load_font

Color = tuple[int, int, int]

CORE_WHITE_MIX = 0.55  # neon core: accent colour mixed with this much white
PANEL_FILL = (8, 10, 22)
PANEL_ALPHA = 0.62
SUPERSAMPLING = 4


def mix(a: Color, b: Color, t: float) -> Color:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))  # type: ignore[return-value]


def core_color(color: Color) -> Color:
    return mix(color, (255, 255, 255), CORE_WHITE_MIX)


# --- text with fallback glyphs and letter spacing -------------------------------------------


FALLBACK_SCALE = 0.85
FALLBACK_STROKE = 0.035  # of the size: thickens fallback glyphs (♯ ♭) to match the heavy display font


def _glyph(char: str, size: int, weight: int):
    """(font, stroke width) for one character."""
    if display_font_has(char):
        return load_display_font(size, weight), 0
    stroke = round(size * FALLBACK_STROKE) if weight >= 600 else 0
    return load_font(round(size * FALLBACK_SCALE), bold=weight >= 600), stroke


def _advance(char: str, size: int, weight: int) -> float:
    font, stroke = _glyph(char, size, weight)
    return font.getlength(char) + 2 * stroke


def text_width(text: str, size: int, weight: int = 700, tracking: float = 0.0) -> float:
    return sum(_advance(c, size, weight) for c in text) + tracking * size * max(len(text) - 1, 0)


def fitting_size(text: str, size: int, weight: int, max_width: float, tracking: float = 0.0, minimum: int = 8) -> int:
    """The largest font size <= size at which `text` fits into max_width."""
    while size > minimum and text_width(text, size, weight, tracking) > max_width:
        size -= 1
    return size


def draw_text(
    mask: Image.Image,
    center_x: float,
    baseline: float,
    text: str,
    size: int,
    weight: int = 700,
    tracking: float = 0.0,
) -> None:
    """Draws `text` in white onto an "L" mask, centred on center_x, sitting on `baseline`."""
    draw = ImageDraw.Draw(mask)
    x = center_x - text_width(text, size, weight, tracking) / 2
    for char in text:
        font, stroke = _glyph(char, size, weight)
        draw.text((x + stroke, baseline), char, font=font, fill=255, anchor="ls", stroke_width=stroke, stroke_fill=255)
        x += _advance(char, size, weight) + tracking * size


def draw_star(mask: Image.Image, center_x: float, center_y: float, radius: float, points: int = 5) -> None:
    """Filled star in white onto an "L" mask (anti-aliased by supersampling)."""
    s = SUPERSAMPLING
    size = int(radius * 2) + 4
    big = Image.new("L", (size * s, size * s))
    c = size * s / 2
    corners = []
    for i in range(points * 2):
        r = radius * s * (1.0 if i % 2 == 0 else 0.45)
        angle = math.pi * i / points - math.pi / 2  # first tip points up
        corners.append((c + r * math.cos(angle), c + r * math.sin(angle)))
    ImageDraw.Draw(big).polygon(corners, fill=255)
    small = big.resize((size, size), Image.Resampling.LANCZOS)
    left, top = round(center_x - size / 2), round(center_y - size / 2)
    mask.paste(255, (left, top), small)


# --- glow ---------------------------------------------------------------------------------------


def colorize(mask: Image.Image, color: Color, alpha: float = 1.0) -> Image.Image:
    layer = Image.new("RGBA", mask.size, (*color, 0))
    layer.putalpha(mask.point(lambda v: min(255, round(v * alpha))) if alpha != 1.0 else mask)
    return layer


def add_neon(canvas: Image.Image, mask: Image.Image, color: Color, radius: float, strength: float = 1.0,
             core_alpha: float = 1.0) -> None:  # fmt: skip
    """Composites glowing text (given as mask) onto the RGBA canvas, in place.
    strength > 1 (a flash) adds a wide aura and a whiter core on top of the normal glow."""
    for blur, alpha in ((radius, 0.55), (radius * 0.4, 0.8)):
        glow = mask.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(colorize(glow, color, min(2.5, alpha * strength)))
    if strength > 1:
        aura = mask.filter(ImageFilter.GaussianBlur(radius * 2.5))
        canvas.alpha_composite(colorize(aura, color, min(1.0, 0.6 * (strength - 1)) * 2))
    core = core_color(color) if strength <= 1 else mix(core_color(color), (255, 255, 255), min(0.8, (strength - 1) * 0.5))
    canvas.alpha_composite(colorize(mask, core, core_alpha))


# --- panel ------------------------------------------------------------------------------------


@lru_cache(maxsize=16)
def neon_panel(width: int, height: int, margin: int, radius: int, border: int, color: Color) -> Image.Image:
    """Glass panel with a glowing border, `margin` px of room around it for the glow."""
    s = SUPERSAMPLING
    size = (width + 2 * margin, height + 2 * margin)
    box = [(margin * s, margin * s), ((margin + width) * s - 1, (margin + height) * s - 1)]

    def shape(**kwargs) -> Image.Image:
        big = Image.new("L", (size[0] * s, size[1] * s))
        ImageDraw.Draw(big).rounded_rectangle(box, radius=radius * s, **kwargs)
        return big.resize(size, Image.Resampling.LANCZOS)

    fill_mask = shape(fill=255)
    border_mask = shape(outline=255, width=border * s)

    panel = colorize(fill_mask, PANEL_FILL, PANEL_ALPHA)
    panel.alpha_composite(colorize(border_mask.filter(ImageFilter.GaussianBlur(margin * 0.45)), color, 0.9))
    panel.alpha_composite(colorize(border_mask, core_color(color), 0.95))
    return panel


def centered_frame(canvas: Image.Image, frame_width: int, frame_height: int) -> bytes:
    """Places the canvas in the middle of a transparent frame; returns RGBA bytes."""
    frame = np.zeros((frame_height, frame_width, 4), dtype=np.uint8)
    pixels = np.asarray(canvas)
    h, w = min(pixels.shape[0], frame_height), min(pixels.shape[1], frame_width)
    top, left = (frame_height - h) // 2, (frame_width - w) // 2
    src_top, src_left = (pixels.shape[0] - h) // 2, (pixels.shape[1] - w) // 2
    frame[top : top + h, left : left + w] = pixels[src_top : src_top + h, src_left : src_left + w]
    return frame.tobytes()


def widest(texts: Iterable[str], size: int, weight: int = 700, tracking: float = 0.0) -> float:
    return max((text_width(t, size, weight, tracking) for t in texts), default=0.0)
