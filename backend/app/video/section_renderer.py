"""Section overlay: "ABSCHNITT" + the current part ("TEIL B"), below it "NEU" or how often
the part has been heard ("ZUM 3. MAL"). It flashes at every section change; when a part
comes back the panel glows brighter for a few seconds."""

from app.analysis.sections import Section
from app.video.labels import Language, section_count, section_name, text
from app.video.neon import Color, add_neon, draw_text, text_width
from app.video.neon_overlay import LABEL_TRACKING, LABEL_WEIGHT, NeonOverlay, flash_strength

REPEAT_HIGHLIGHT_SECONDS = 3.0
REPEAT_GLOW = 1.8
FOOTER_TRACKING = LABEL_TRACKING * 0.6


class SectionRenderer(NeonOverlay):
    def __init__(self, width: int, height: int, color: Color, language: Language, sections: list[Section]):
        self.language = language
        self.sections = sections
        probe = NeonOverlay(width, height, color, 0, 0)
        self.footer_gap = 30 * probe.u
        names = [section_name(s.label, language) for s in sections] or [section_name("A", language)]
        footers = [section_count(s.number, language) for s in sections] or [section_count(1, language)]
        content_width = max(
            max(probe.value_width(n) for n in names),
            max(text_width(f.upper(), probe.small_size, LABEL_WEIGHT, FOOTER_TRACKING) for f in footers),
            probe.label_width(text("section", language)),
            420 * probe.u,
        )
        super().__init__(width, height, color, content_width, probe.header_height + self.footer_gap + probe.small_size)

    def state(self, time: float):
        section = next((s for s in self.sections if s.start <= time < s.end), None)
        if section is None:
            return None
        since = time - section.start
        repeated = section.number > 1 and since < REPEAT_HIGHLIGHT_SECONDS
        strength = max(flash_strength(since), REPEAT_GLOW) if repeated else flash_strength(since)
        return (section.label, section.number, repeated, strength)

    def render(self, time: float) -> bytes:
        return self.render_state(self.state(time))

    def draw(self, state):
        label, number, repeated, strength = state
        canvas = self.new_canvas()
        value_baseline = self.draw_header(canvas, text("section", self.language), section_name(label, self.language),
                                          strength)  # fmt: skip
        mask = self.new_mask()
        baseline = value_baseline + self.footer_gap + self.small_size * 0.8
        footer = section_count(number, self.language)
        draw_text(mask, self.center_x, baseline, footer.upper(), self.small_size, LABEL_WEIGHT, FOOTER_TRACKING)
        if repeated:
            add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=strength)
        else:
            add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=0.3, core_alpha=0.75)
        return canvas
