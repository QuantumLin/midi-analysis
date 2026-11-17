"""Key field: "Tonart" + the current key, e.g. "d-Moll"; after a modulation the label
reads "Modulation" (in the accent colour) for a few seconds."""

from app.analysis.key import Key, KeyAnalysis
from app.video.fonts import load_font
from app.video.labels import Language, key_name, text
from app.video.overlay_box import LABEL_ALPHA, OverlayCanvas, fill, text_width

MODULATION_HIGHLIGHT_SECONDS = 3.0
WHITE = (255, 255, 255)


class KeyRenderer:
    def __init__(self, width: int, height: int, color: tuple[int, int, int], language: Language, keys: KeyAnalysis):
        self.color = color
        self.language = language
        self.keys = keys
        self.big = round(height * 0.11)
        self.small = round(height * 0.04)

        names = [key_name(s.key, language) for s in keys.segments] or ["C-Dur"]
        widest = max(
            max(text_width(n, self.big) for n in names),
            text_width(text("modulation", language), self.small),
        )
        self.canvas = OverlayCanvas(
            width,
            height,
            box_width=round(widest + 1.2 * self.big),
            box_height=round(self.big * 1.25 + self.small * 1.4 + 0.8 * self.big),
            radius=round(0.3 * self.big),
        )
        self._cache: dict[tuple[Key, bool], bytes] = {}

    def render(self, time: float) -> bytes:
        segment_index = next((i for i, s in enumerate(self.keys.segments) if s.start <= time < s.end), None)
        if segment_index is None:
            return self.canvas.empty
        segment = self.keys.segments[segment_index]
        modulated = segment_index > 0 and time - segment.start < MODULATION_HIGHLIGHT_SECONDS
        cache_key = (segment.key, modulated)
        if cache_key not in self._cache:
            self._cache[cache_key] = self._draw(segment.key, modulated)
        return self._cache[cache_key]

    def _draw(self, key: Key, modulated: bool) -> bytes:
        box, draw = self.canvas.draw()
        center_x = box.width / 2
        label_y = 0.4 * self.big + self.small / 2
        label = f"{text('modulation', self.language)} →" if modulated else text("key", self.language)
        draw.text(
            (center_x, label_y),
            label,
            font=load_font(self.small, bold=modulated),
            fill=fill(self.color) if modulated else fill(WHITE, LABEL_ALPHA),
            anchor="mm",
        )
        draw.text(
            (center_x, label_y + self.small * 0.7 + self.big * 0.65),
            key_name(key, self.language),
            font=load_font(self.big, bold=True),
            fill=fill(self.color),
            anchor="mm",
        )
        return self.canvas.frame(box)
