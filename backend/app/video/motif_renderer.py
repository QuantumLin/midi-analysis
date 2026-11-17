"""Motif overlay: "MOTIV A" + how often it has been heard ("6. MAL"), below it "ERSTES
AUFTRETEN" or "KEHRT ZURÜCK". It appears while a motif is played (plus a short hold) and
flashes at every new appearance; otherwise the frame is empty."""

from app.analysis.motifs import Motif
from app.video.labels import Language, motif_count, text
from app.video.neon import Color, add_neon, draw_text, text_width
from app.video.neon_overlay import LABEL_TRACKING, LABEL_WEIGHT, NeonOverlay, flash_strength

HOLD_SECONDS = 1.0  # stays visible this long after the motif ended
FOOTER_TRACKING = LABEL_TRACKING * 0.6


class MotifRenderer(NeonOverlay):
    def __init__(self, width: int, height: int, color: Color, language: Language, motifs: list[Motif]):
        self.language = language
        self.motifs = motifs
        probe = NeonOverlay(width, height, color, 0, 0)
        self.footer_gap = 30 * probe.u
        counts = [motif_count(o.number, language) for m in motifs for o in m.occurrences] or ["1"]
        footers = [text("first_appearance", language), text("returns", language)]
        content_width = max(
            max(probe.value_width(c) for c in counts),
            max(text_width(f.upper(), probe.small_size, LABEL_WEIGHT, FOOTER_TRACKING) for f in footers),
            probe.label_width(f"{text('motif', language)} A"),
            420 * probe.u,
        )
        super().__init__(width, height, color, content_width, probe.header_height + self.footer_gap + probe.small_size)

    def state(self, time: float):
        """The latest motif appearance playing at `time` (label, number, glow), or None."""
        current = None
        for motif in self.motifs:
            for occurrence in motif.occurrences:
                if occurrence.start <= time < occurrence.end + HOLD_SECONDS:
                    if current is None or occurrence.start > current[1].start:
                        current = (motif, occurrence)
        if current is None:
            return None
        motif, occurrence = current
        return (motif.label, occurrence.number, flash_strength(time - occurrence.start))

    def render(self, time: float) -> bytes:
        return self.render_state(self.state(time))

    def draw(self, state):
        label, number, strength = state
        canvas = self.new_canvas()
        value_baseline = self.draw_header(
            canvas, f"{text('motif', self.language)} {label}", motif_count(number, self.language), strength
        )
        footer = text("first_appearance" if number == 1 else "returns", self.language)
        mask = self.new_mask()
        baseline = value_baseline + self.footer_gap + self.small_size * 0.8
        draw_text(mask, self.center_x, baseline, footer.upper(), self.small_size, LABEL_WEIGHT, FOOTER_TRACKING)
        add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=0.3, core_alpha=0.75)
        return canvas
