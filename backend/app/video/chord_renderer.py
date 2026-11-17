"""Draws the chord text field: the current chord name in a rounded, semi-transparent box.

The box size is fixed for the whole video (sized for the longest chord name), so it
doesn't jump around when the chord changes. Each distinct chord is rendered once and
cached; frames between chord changes reuse the same bytes.
"""

from PIL import Image, ImageDraw

from app.video.fonts import load_font

BOX_COLOR = (0, 0, 0)
BOX_ALPHA = 0.55
SUPERSAMPLING = 4  # Pillow draws shapes without anti-aliasing; render large, then downscale.


class ChordRenderer:
    def __init__(self, width: int, height: int, color: tuple[int, int, int], chord_names: list[str]):
        self.width = width
        self.height = height
        self.color = color
        self.font_size = round(height * 0.12)
        self._cache: dict[str | None, bytes] = {None: bytes(width * height * 4)}

        font = load_font(self.font_size * SUPERSAMPLING, bold=True)
        longest = max((font.getlength(name) for name in chord_names), default=font.getlength("C"))
        padding_x, padding_y = 0.6 * self.font_size, 0.35 * self.font_size
        self.box_width = min(width, round(longest / SUPERSAMPLING + 2 * padding_x))
        self.box_height = min(height, round(self.font_size * 1.2 + 2 * padding_y))

    def render(self, chord_name: str | None) -> bytes:
        if chord_name not in self._cache:
            self._cache[chord_name] = self._draw(chord_name)
        return self._cache[chord_name]

    def _draw(self, chord_name: str) -> bytes:
        s = SUPERSAMPLING
        box = Image.new("RGBa", (self.box_width * s, self.box_height * s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(box)
        alpha = round(255 * BOX_ALPHA)
        # "RGBa" is premultiplied, so the box colour is scaled by its alpha.
        draw.rounded_rectangle(
            [(0, 0), (box.width - 1, box.height - 1)],
            radius=round(0.3 * self.font_size * s),
            fill=(*(round(c * BOX_ALPHA) for c in BOX_COLOR), alpha),
        )
        draw.text(
            (box.width / 2, box.height / 2),
            chord_name,
            font=load_font(self.font_size * s, bold=True),
            fill=(*self.color, 255),
            anchor="mm",
        )
        box = box.resize((self.box_width, self.box_height), Image.Resampling.LANCZOS)

        frame = Image.new("RGBa", (self.width, self.height), (0, 0, 0, 0))
        frame.paste(box, ((self.width - self.box_width) // 2, (self.height - self.box_height) // 2))
        return frame.convert("RGBA").tobytes()
