"""Notes-per-second overlay: big live value, an LED meter (relative to the piece's peak)
and "GESAMT 523 · REKORD 22" below. A new record flashes the panel and replaces the
bottom line with "NEUER REKORD: 29"."""

from PIL import ImageDraw

from app.analysis.note_rate import NoteRateRecord
from app.video.labels import Language, text
from app.video.neon import Color, add_neon, draw_text, text_width
from app.video.neon_overlay import LABEL_TRACKING, LABEL_WEIGHT, NeonOverlay, flash_strength

RECORD_HIGHLIGHT_SECONDS = 2.0
RECORD_GLOW = 1.8
METER_SEGMENTS = 24
UNLIT_ALPHA = 0.16


class NoteRateRenderer(NeonOverlay):
    def __init__(
        self,
        width: int,
        height: int,
        color: Color,
        language: Language,
        max_rate: int,
        max_total: int,
        records: list[NoteRateRecord],
    ):
        self.language = language
        self.records = records
        self.max_rate = max(1, max_rate)
        probe = NeonOverlay(width, height, color, 0, 0)
        self.meter_gap = 26 * probe.u
        self.meter_height = 16 * probe.u
        self.footer_gap = 30 * probe.u
        footer_widths = [
            text_width(s.upper(), probe.small_size, LABEL_WEIGHT, LABEL_TRACKING * 0.6)
            for s in (self._details(max_total, max_rate), self._record_text(max_rate))
        ]
        content_width = max(
            probe.value_width("8" * len(str(max_rate))),
            probe.label_width(text("notes_per_second", language)),
            *footer_widths,
            420 * probe.u,
        )
        content_height = probe.header_height + self.meter_gap + self.meter_height + self.footer_gap + probe.small_size
        super().__init__(width, height, color, content_width, content_height)
        self.content_width = content_width

    def state(self, time: float, rate: int, total: int, best_so_far: int):
        record = next((r for r in self.records if 0 <= time - r.time < RECORD_HIGHLIGHT_SECONDS), None)
        strength = max(flash_strength(time - record.time), RECORD_GLOW) if record else 1.0
        return (rate, total, best_so_far, record.value if record else None, strength)

    def render(self, time: float, rate: int, total: int, best_so_far: int) -> bytes:
        return self.render_state(self.state(time, rate, total, best_so_far))

    def _details(self, total: int, best: int) -> str:
        return f"{text('total', self.language)} {total}  ·  {text('record', self.language)} {best}"

    def _record_text(self, value: int) -> str:
        return f"{text('new_record', self.language)}: {value}"

    def draw(self, state):
        rate, total, best, record, strength = state
        canvas = self.new_canvas()
        value_baseline = self.draw_header(canvas, text("notes_per_second", self.language), str(rate), strength)

        # LED meter: lit segments in full neon, the rest faintly visible.
        meter_top = value_baseline + self.meter_gap
        lit = round(min(rate / self.max_rate, 1.0) * METER_SEGMENTS)
        segment_width = self.content_width / METER_SEGMENTS
        lit_mask, unlit_mask = self.new_mask(), self.new_mask()
        for i in range(METER_SEGMENTS):
            x0 = self.left + i * segment_width + segment_width * 0.12
            x1 = self.left + (i + 1) * segment_width - segment_width * 0.12
            target = lit_mask if i < lit else unlit_mask
            ImageDraw.Draw(target).rounded_rectangle(
                [(x0, meter_top), (x1, meter_top + self.meter_height)], radius=self.meter_height * 0.3, fill=255
            )
        add_neon(canvas, unlit_mask, self.color, radius=1, strength=0, core_alpha=UNLIT_ALPHA)
        add_neon(canvas, lit_mask, self.color, radius=self.meter_height * 0.8, strength=strength)

        footer_baseline = meter_top + self.meter_height + self.footer_gap + self.small_size * 0.8
        mask = self.new_mask()
        footer = self._record_text(record) if record is not None else self._details(total, best)
        draw_text(mask, self.center_x, footer_baseline, footer.upper(), self.small_size, LABEL_WEIGHT,
                  LABEL_TRACKING * 0.6)  # fmt: skip
        if record is not None:
            add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=strength)
        else:
            add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=0.3, core_alpha=0.75)
        return canvas
