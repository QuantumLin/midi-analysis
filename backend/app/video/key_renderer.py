"""Key overlay: "TONART" + the current key, e.g. "d-Moll". After a modulation the label
reads "MODULATION →" in full neon and the panel glows brighter for a few seconds."""

from app.analysis.key import KeyAnalysis
from app.video.labels import Language, key_name, text
from app.video.neon import Color
from app.video.neon_overlay import NeonOverlay, flash_strength

MODULATION_HIGHLIGHT_SECONDS = 3.0
MODULATION_GLOW = 1.8


class KeyRenderer(NeonOverlay):
    def __init__(self, width: int, height: int, color: Color, language: Language, keys: KeyAnalysis):
        self.language = language
        self.keys = keys
        probe = NeonOverlay(width, height, color, 0, 0)
        names = [key_name(s.key, language) for s in keys.segments] or ["C"]
        content_width = max(
            max(probe.value_width(n) for n in names),
            probe.label_width(f"{text('modulation', language)} →"),
            320 * probe.u,
        )
        super().__init__(width, height, color, content_width, probe.header_height)

    def state(self, time: float):
        index = next((i for i, s in enumerate(self.keys.segments) if s.start <= time < s.end), None)
        if index is None:
            return None
        segment = self.keys.segments[index]
        since = time - segment.start
        modulated = index > 0 and since < MODULATION_HIGHLIGHT_SECONDS
        strength = max(flash_strength(since), MODULATION_GLOW) if modulated else 1.0
        return (segment.key, modulated, strength)

    def render(self, time: float) -> bytes:
        return self.render_state(self.state(time))

    def draw(self, state):
        key, modulated, strength = state
        canvas = self.new_canvas()
        label = f"{text('modulation', self.language)} →" if modulated else text("key", self.language)
        self.draw_header(canvas, label, key_name(key, self.language), strength, label_accent=modulated)
        return canvas
