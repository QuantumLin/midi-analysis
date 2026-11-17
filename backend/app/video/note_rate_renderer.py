"""Notes-per-second field: big live value, plus total and record so far.
Right after a new record, the second line reads "Neuer Rekord: 29 Noten/s" in the accent colour."""

from app.analysis.note_rate import NoteRateRecord
from app.video.fonts import load_font
from app.video.labels import Language, text
from app.video.overlay_box import LABEL_ALPHA, OverlayCanvas, fill, text_width

RECORD_HIGHLIGHT_SECONDS = 2.0
WHITE = (255, 255, 255)


class NoteRateRenderer:
    def __init__(
        self,
        width: int,
        height: int,
        color: tuple[int, int, int],
        language: Language,
        max_rate: int,
        max_total: int,
        records: list[NoteRateRecord],
    ):
        self.color = color
        self.language = language
        self.records = records
        self.big = round(height * 0.12)
        self.small = round(height * 0.04)

        big_width = text_width("8" * len(str(max_rate)), self.big) + text_width(
            " " + text("notes_per_second", language), self.small
        )
        detail_width = max(
            text_width(self._details(max_total, max_rate), self.small, bold=False),
            text_width(f"{text('new_record', language)}: {max_rate} {text('notes_per_second', language)}", self.small),
        )
        self.canvas = OverlayCanvas(
            width,
            height,
            box_width=round(max(big_width, detail_width) + 1.2 * self.big),
            box_height=round(self.big * 1.1 + self.small * 1.4 + 0.8 * self.big),
            radius=round(0.3 * self.big),
        )
        self._last: tuple | None = None
        self._last_frame = self.canvas.empty

    def render(self, time: float, rate: int, total: int, best_so_far: int) -> bytes:
        record = next((r for r in self.records if 0 <= time - r.time < RECORD_HIGHLIGHT_SECONDS), None)
        state = (rate, total, best_so_far, record.value if record else None)
        if state != self._last:  # consecutive frames are often identical
            self._last, self._last_frame = state, self._draw(*state)
        return self._last_frame

    def _details(self, total: int, best: int) -> str:
        return f"{text('total', self.language)} {total}  ·  {text('record', self.language)} {best}"

    def _draw(self, rate: int, total: int, best: int, new_record: int | None) -> bytes:
        box, draw = self.canvas.draw()
        big_font, small_font = load_font(self.big, bold=True), load_font(self.small)
        unit = " " + text("notes_per_second", self.language)

        # Value and unit share a baseline and are centred together.
        value_width = big_font.getlength(str(rate))
        start_x = (box.width - value_width - small_font.getlength(unit)) / 2
        baseline = 0.4 * self.big + self.big * 0.95
        draw.text((start_x, baseline), str(rate), font=big_font, fill=fill(self.color), anchor="ls")
        draw.text((start_x + value_width, baseline), unit, font=small_font, fill=fill(WHITE, LABEL_ALPHA), anchor="ls")

        details_y = baseline + self.small * 1.2
        if new_record is not None:
            draw.text(
                (box.width / 2, details_y),
                f"{text('new_record', self.language)}: {new_record} {text('notes_per_second', self.language)}",
                font=load_font(self.small, bold=True),
                fill=fill(self.color),
                anchor="mt",
            )
        else:
            draw.text(
                (box.width / 2, details_y),
                self._details(total, best),
                font=small_font,
                fill=fill(WHITE, LABEL_ALPHA),
                anchor="mt",
            )
        return self.canvas.frame(box)
