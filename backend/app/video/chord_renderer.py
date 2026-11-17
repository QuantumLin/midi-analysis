"""Chord overlay: "AKKORD" + the current chord in neon; it flashes on every chord change."""

from app.video.labels import Language, display_accidentals, text
from app.video.neon import Color
from app.video.neon_overlay import NeonOverlay, flash_strength


class ChordRenderer(NeonOverlay):
    def __init__(self, width: int, height: int, color: Color, language: Language, chord_names: list[str]):
        self.language = language
        probe = NeonOverlay(width, height, color, 0, 0)  # for measurements only
        names = [display_accidentals(n) for n in chord_names] or ["C"]
        content_width = max(
            max(probe.value_width(n) for n in names),
            probe.label_width(text("chord", language)),
            320 * probe.u,
        )
        super().__init__(width, height, color, content_width, probe.header_height)

    def state(self, chord_name: str | None, seconds_since_change: float):
        return None if chord_name is None else (chord_name, flash_strength(seconds_since_change))

    def render(self, chord_name: str | None, seconds_since_change: float = 1.0) -> bytes:
        return self.render_state(self.state(chord_name, seconds_since_change))

    def draw(self, state):
        name, strength = state
        canvas = self.new_canvas()
        self.draw_header(canvas, text("chord", self.language), display_accidentals(name), strength)
        return canvas
