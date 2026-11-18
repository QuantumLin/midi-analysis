"""Keyboard bingo overlay: "TASTATUR-BINGO" above a 3x3 card of glass fields.

- open fields are faint; a ticked field lights up (and flashes when it is ticked)
- every completed line is struck through with a glowing line
- after a completed line, "BINGO!" ("2× BINGO!" ...) glows below the card for a few
  seconds; otherwise the number of ticked fields is shown there ("4 / 9")
"""

from PIL import ImageDraw

from app.analysis.bingo import SIZE, BingoCard
from app.video.labels import BINGO_LABELS, Language, bingo_banner, text
from app.video.neon import Color, add_neon, colorize, draw_text, fitting_size
from app.video.neon_overlay import LABEL_WEIGHT, VALUE_WEIGHT, NeonOverlay, flash_strength

BANNER_SECONDS = 3.0
FIELD_WEIGHT = 700
OPEN_ALPHA = 0.35


class BingoRenderer(NeonOverlay):
    def __init__(self, width: int, height: int, color: Color, language: Language, card: BingoCard):
        self.language = language
        self.card = card
        probe = NeonOverlay(width, height, color, 0, 0)
        u = probe.u
        self.cell_width, self.cell_height, self.cell_gap = 270 * u, 116 * u, 16 * u
        self.label_gap, self.footer_gap = 26 * u, 34 * u
        self.field_size = max(8, round(30 * u))
        self.banner_size = max(12, round(80 * u))
        self.grid_size = (SIZE * self.cell_width + (SIZE - 1) * self.cell_gap,
                          SIZE * self.cell_height + (SIZE - 1) * self.cell_gap)  # fmt: skip
        content_width = max(self.grid_size[0], probe.label_width(text("bingo_title", language)))
        content_height = probe.label_size + self.label_gap + self.grid_size[1] + self.footer_gap + self.banner_size * 0.8
        super().__init__(width, height, color, content_width, content_height)
        self.grid_left = self.center_x - self.grid_size[0] / 2
        self.grid_top = self.top + self.label_size + self.label_gap
        self.labels = [BINGO_LABELS[f.id][language] for f in card.fields]

    def cell_box(self, cell: int) -> tuple[float, float, float, float]:
        row, col = divmod(cell, SIZE)
        x = self.grid_left + col * (self.cell_width + self.cell_gap)
        y = self.grid_top + row * (self.cell_height + self.cell_gap)
        return x, y, x + self.cell_width, y + self.cell_height

    def cell_center(self, cell: int) -> tuple[float, float]:
        x0, y0, x1, y1 = self.cell_box(cell)
        return (x0 + x1) / 2, (y0 + y1) / 2

    def state(self, time: float):
        """(ticked per field, completed lines, freshly ticked field, its glow, banner, banner glow)."""
        ticked = self.card.ticked_at(time)
        lines = self.card.lines_at(time)
        fresh = max(
            (i for i, f in enumerate(self.card.fields) if f.time is not None and 0 <= time - f.time < 0.45),
            key=lambda i: self.card.fields[i].time or 0.0,
            default=None,
        )
        cell_glow = flash_strength(time - self.card.fields[fresh].time) if fresh is not None else 1.0
        banner, banner_glow = None, 1.0
        if lines and time - lines[-1].time < BANNER_SECONDS:
            banner = bingo_banner(len(lines), self.language)
            banner_glow = max(flash_strength(time - lines[-1].time), 1.6)
        return (ticked, tuple(line.cells for line in lines), fresh, cell_glow, banner, banner_glow)

    def render(self, time: float) -> bytes:
        return self.render_state(self.state(time))

    def draw(self, state):
        ticked, lines, fresh, cell_glow, banner, banner_glow = state
        canvas = self.new_canvas()
        self.draw_header(canvas, text("bingo_title", self.language), None)

        radius = 16 * self.u
        width = max(1, round(2 * self.u))
        open_cells, ticked_fill, ticked_border = self.new_mask(), self.new_mask(), self.new_mask()
        for cell, is_ticked in enumerate(ticked):
            box = self.cell_box(cell)
            if is_ticked:
                ImageDraw.Draw(ticked_fill).rounded_rectangle(box, radius=radius, fill=255)
                ImageDraw.Draw(ticked_border).rounded_rectangle(box, radius=radius, outline=255, width=width * 2)
            else:
                ImageDraw.Draw(open_cells).rounded_rectangle(box, radius=radius, outline=255, width=width)
        add_neon(canvas, open_cells, self.color, radius=3 * self.u, strength=0.3, core_alpha=OPEN_ALPHA)
        canvas.alpha_composite(colorize(ticked_fill, self.color, 0.22))
        add_neon(canvas, ticked_border, self.color, radius=8 * self.u, strength=1.0)

        open_text, ticked_text, fresh_text = self.new_mask(), self.new_mask(), self.new_mask()
        for cell, is_ticked in enumerate(ticked):
            target = fresh_text if cell == fresh else ticked_text if is_ticked else open_text
            self._field_label(target, cell)
        add_neon(canvas, open_text, self.color, radius=2 * self.u, strength=0.2, core_alpha=OPEN_ALPHA + 0.15)
        add_neon(canvas, ticked_text, self.color, radius=self.field_size * 0.3, strength=1.0)
        add_neon(canvas, fresh_text, self.color, radius=self.field_size * 0.3, strength=cell_glow)

        if lines:
            strikes = self.new_mask()
            for cells in lines:
                ImageDraw.Draw(strikes).line([self.cell_center(cells[0]), self.cell_center(cells[-1])], fill=255,
                                             width=max(2, round(4 * self.u)))  # fmt: skip
            # Faint enough that the field labels underneath stay readable.
            add_neon(canvas, strikes, self.color, radius=8 * self.u, strength=0.6, core_alpha=0.45)

        baseline = self.grid_top + self.grid_size[1] + self.footer_gap + self.banner_size * 0.75
        mask = self.new_mask()
        if banner:
            draw_text(mask, self.center_x, baseline, banner.upper(), self.banner_size, VALUE_WEIGHT)
            add_neon(canvas, mask, self.color, radius=self.banner_size * 0.22, strength=banner_glow)
        else:
            count = f"{sum(ticked)} / {len(ticked)}"
            draw_text(mask, self.center_x, baseline - self.banner_size * 0.2, count, self.small_size, LABEL_WEIGHT)
            add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=0.3, core_alpha=0.75)
        return canvas

    def _field_label(self, mask, cell: int) -> None:
        """The field's label, shrunk to fit; two lines if it would get too small."""
        label = self.labels[cell].upper()
        cx, cy = self.cell_center(cell)
        max_width = self.cell_width - 28 * self.u
        size = fitting_size(label, self.field_size, FIELD_WEIGHT, max_width)
        words = label.split(" ")
        if size < self.field_size * 0.75 and len(words) > 1:
            middle = len(words) // 2
            parts = [" ".join(words[:middle]), " ".join(words[middle:])]
            size = min(fitting_size(p, self.field_size, FIELD_WEIGHT, max_width) for p in parts)
            for k, part in enumerate(parts):
                draw_text(mask, cx, cy + size * (0.36 + (k - 0.5) * 1.1), part, size, FIELD_WEIGHT)
            return
        draw_text(mask, cx, cy + size * 0.36, label, size, FIELD_WEIGHT)

