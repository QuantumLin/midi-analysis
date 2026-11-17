"""Fonts for text in rendered videos.

The display font is Orbitron (SIL Open Font License, see assets/OFL.txt), shipped with
the app so videos look the same everywhere. Characters it lacks (♯ ♭ → ·) fall back to
DejaVu Sans, which the Docker image installs (fonts-dejavu-core).
"""

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DISPLAY_FONT = Path(__file__).parent / "assets" / "Orbitron.ttf"
_FALLBACK_CANDIDATES = {
    True: ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"),
    False: ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf"),
}

Font = ImageFont.FreeTypeFont | ImageFont.ImageFont


@lru_cache(maxsize=64)
def load_display_font(size: int, weight: int = 700) -> Font:
    """Orbitron at `weight` (400-900)."""
    font = ImageFont.truetype(str(DISPLAY_FONT), size)
    font.set_variation_by_axes([weight])
    return font


@lru_cache(maxsize=32)
def load_font(size: int, bold: bool = False) -> Font:
    """Plain sans-serif (fallback for characters the display font lacks)."""
    for name in _FALLBACK_CANDIDATES[bold]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


@lru_cache(maxsize=256)
def display_font_has(char: str) -> bool:
    """True if Orbitron has a glyph for `char` (compares against its 'missing glyph' box)."""
    font = load_display_font(48)

    def render(c: str) -> bytes:
        image = Image.new("L", (96, 96))
        ImageDraw.Draw(image).text((8, 8), c, font=font, fill=255)
        return image.tobytes()

    return char.isspace() or render(char) != render("￿")
