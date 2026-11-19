"""Fonts for text in rendered videos.

The display font is chosen by the user (app/video/style.py); all of them are shipped
with the app under assets/fonts/ (SIL Open Font License, licence next to each font), so
videos look the same everywhere. Characters a font lacks (e.g. ♯ ♭ →) fall back to
DejaVu Sans, which the Docker image installs (fonts-dejavu-core).
"""

from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from app.video.style import FONTS, current

_FALLBACK_CANDIDATES = {
    True: ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"),
    False: ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf"),
}

Font = ImageFont.FreeTypeFont | ImageFont.ImageFont


def load_display_font(size: int, weight: int = 700) -> Font:
    """The active display font at `size` (scaled to even out font sizes) and `weight`
    (400-900; fonts with a single weight ignore it)."""
    return _load(current().font, size, weight)


@lru_cache(maxsize=256)
def _load(font_id: str, size: int, weight: int) -> Font:
    spec = FONTS[font_id]
    font = ImageFont.truetype(str(spec.file), max(1, round(size * spec.scale)))
    if spec.variable:
        axis = font.get_variation_axes()[0]
        font.set_variation_by_axes([min(max(weight, axis["minimum"]), axis["maximum"])])
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


def display_font_has(char: str) -> bool:
    """True if the active display font has a glyph for `char`."""
    return _has(current().font, char)


@lru_cache(maxsize=2048)
def _has(font_id: str, char: str) -> bool:
    """Compares the glyph with the font's 'missing glyph' box (and with nothing at all,
    for fonts whose missing glyph is empty)."""
    font = _load(font_id, 48, 700)

    def render(c: str) -> bytes:
        image = Image.new("L", (96, 96))
        ImageDraw.Draw(image).text((8, 8), c, font=font, fill=255)
        return image.tobytes()

    glyph = render(char)
    return char.isspace() or (glyph != render("￿") and any(glyph))
