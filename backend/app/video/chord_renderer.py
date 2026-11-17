"""Chord text field: the current chord name in the shared overlay box.

The box size is fixed for the whole video (sized for the longest chord name), so it
doesn't jump when the chord changes. Each distinct chord is rendered once and cached.
"""

from app.video.fonts import load_font
from app.video.labels import display_accidentals
from app.video.overlay_box import OverlayCanvas, fill, text_width


class ChordRenderer:
    def __init__(self, width: int, height: int, color: tuple[int, int, int], chord_names: list[str]):
        self.color = color
        self.font_size = round(height * 0.12)
        longest = max((text_width(display_accidentals(n), self.font_size) for n in chord_names), default=0)
        longest = max(longest, text_width("C", self.font_size))
        self.canvas = OverlayCanvas(
            width,
            height,
            box_width=round(longest + 1.2 * self.font_size),
            box_height=round(1.9 * self.font_size),
            radius=round(0.3 * self.font_size),
        )
        self._cache: dict[str | None, bytes] = {None: self.canvas.empty}

    def render(self, chord_name: str | None) -> bytes:
        if chord_name not in self._cache:
            box, draw = self.canvas.draw()
            draw.text(
                (box.width / 2, box.height / 2),
                display_accidentals(chord_name),
                font=load_font(self.font_size, bold=True),
                fill=fill(self.color),
                anchor="mm",
            )
            self._cache[chord_name] = self.canvas.frame(box)
        return self._cache[chord_name]
