"""Font lookup for text in rendered videos."""

from functools import lru_cache

from PIL import ImageFont

# DejaVu ships in the Docker image (fonts-dejavu-core); the others are fallbacks for local runs.
_CANDIDATES = {
    True: ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"),
    False: ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf"),
}


@lru_cache(maxsize=32)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in _CANDIDATES[bold]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)
