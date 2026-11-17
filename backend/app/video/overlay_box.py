"""Shared look of the text overlays: a rounded, semi-transparent box centred in the frame.

The box is drawn once with supersampling (Pillow shapes have no anti-aliasing);
text is drawn per frame at normal size (Pillow text is anti-aliased).
All images use premultiplied alpha ("RGBa") until the final conversion.
"""

from functools import lru_cache

from PIL import Image, ImageDraw

from app.video.fonts import load_font

BOX_COLOR = (0, 0, 0)
BOX_ALPHA = 0.55
LABEL_ALPHA = 0.7  # secondary text (e.g. "Tonart") is slightly transparent
SUPERSAMPLING = 4


@lru_cache(maxsize=8)
def _box(width: int, height: int, radius: int) -> Image.Image:
    s = SUPERSAMPLING
    image = Image.new("RGBa", (width * s, height * s), (0, 0, 0, 0))
    alpha = round(255 * BOX_ALPHA)
    ImageDraw.Draw(image).rounded_rectangle(
        [(0, 0), (image.width - 1, image.height - 1)],
        radius=radius * s,
        fill=(*(round(c * BOX_ALPHA) for c in BOX_COLOR), alpha),
    )
    return image.resize((width, height), Image.Resampling.LANCZOS)


class OverlayCanvas:
    """A box of fixed size; `frame()` draws text lines into it and returns RGBA frame bytes."""

    def __init__(self, frame_width: int, frame_height: int, box_width: int, box_height: int, radius: int):
        self.frame_width, self.frame_height = frame_width, frame_height
        self.box_width, self.box_height = min(box_width, frame_width), min(box_height, frame_height)
        self.radius = radius
        self.empty = bytes(frame_width * frame_height * 4)

    def draw(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        box = _box(self.box_width, self.box_height, self.radius).copy()
        return box, ImageDraw.Draw(box)

    def frame(self, box: Image.Image) -> bytes:
        frame = Image.new("RGBa", (self.frame_width, self.frame_height), (0, 0, 0, 0))
        frame.paste(box, ((self.frame_width - self.box_width) // 2, (self.frame_height - self.box_height) // 2))
        return frame.convert("RGBA").tobytes()


def text_width(text: str, size: int, bold: bool = True) -> float:
    return load_font(size, bold).getlength(text)


def fill(color: tuple[int, int, int], alpha: float = 1.0) -> tuple[int, int, int, int]:
    """Premultiplied RGBa fill for drawing on the box."""
    return (*(round(c * alpha) for c in color), round(255 * alpha))
