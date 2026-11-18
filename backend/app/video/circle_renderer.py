"""Circle-of-fifths overlay: 12 major keys on the outer ring, their relative minors inside.

- the current chord's position glows brightly, its name stands in the centre
- a glowing trail connects the last TRAIL_LENGTH positions (older parts fainter)
- every position visited so far glows according to how often it was visited, so by the
  end of the piece the circle shows the piece's harmonic "fingerprint"
"""

import math
from collections import Counter

from PIL import Image, ImageDraw

from app.analysis.circle_of_fifths import POSITIONS, CirclePosition, CircleStep
from app.video.labels import Language, display_accidentals, text
from app.video.neon import PANEL_FILL, Color, add_neon, colorize, draw_text, fitting_size
from app.video.neon_overlay import NeonOverlay, flash_strength

TRAIL_LENGTH = 6
VISIT_LEVELS = 4  # brightness steps of the fingerprint
DOT_WEIGHT = 700


class CircleRenderer(NeonOverlay):
    def __init__(self, width: int, height: int, color: Color, language: Language, steps: list[CircleStep],
                 chord_names: list[str]):  # fmt: skip
        self.language = language
        self.steps = steps
        self.chord_names = [display_accidentals(n) for n in chord_names]
        probe = NeonOverlay(width, height, color, 0, 0)
        u = probe.u
        self.diameter = 640 * u
        self.label_gap = 22 * u
        super().__init__(width, height, color, self.diameter, probe.label_size + self.label_gap + self.diameter)

        self.cx = self.center_x
        self.cy = self.top + self.label_size + self.label_gap + self.diameter / 2
        self.outer_radius, self.inner_radius = self.diameter / 2 - 42 * u, self.diameter / 2 - 136 * u
        self.dot_radius = {"major": 36 * u, "minor": 30 * u}
        self.name_size = {"major": max(8, round(26 * u)), "minor": max(8, round(22 * u))}
        self.center_size = max(12, round(84 * u))
        self.trail_width = max(2, round(5 * u))
        visits = Counter(step.position for step in steps)
        self.max_visits = max(visits.values(), default=1)
        self.base = self._base_layer()

    # --- geometry ----------------------------------------------------------------------------

    def point(self, position: CirclePosition) -> tuple[float, float]:
        radius = self.outer_radius if position.ring == "major" else self.inner_radius
        angle = 2 * math.pi * position.index / POSITIONS - math.pi / 2  # index 0 at the top
        return self.cx + radius * math.cos(angle), self.cy + radius * math.sin(angle)

    @staticmethod
    def all_positions() -> list[CirclePosition]:
        return [CirclePosition(ring, i) for ring in ("major", "minor") for i in range(POSITIONS)]  # type: ignore[arg-type]

    def _dot(self, mask: Image.Image, position: CirclePosition, fill: int | None = 255, outline: int | None = None,
             scale: float = 1.0) -> None:  # fmt: skip
        x, y = self.point(position)
        r = self.dot_radius[position.ring] * scale
        ImageDraw.Draw(mask).ellipse([(x - r, y - r), (x + r, y + r)], fill=fill, outline=outline,
                                     width=max(1, round(2 * self.u)))  # fmt: skip

    def _name(self, mask: Image.Image, position: CirclePosition) -> None:
        x, y = self.point(position)
        size = self.name_size[position.ring]
        draw_text(mask, x, y + size * 0.36, position.name, size, DOT_WEIGHT)

    # --- layers ------------------------------------------------------------------------------

    def _base_layer(self) -> Image.Image:
        """Panel, faint guide rings, dot outlines and names: the same in every frame."""
        canvas = self.new_canvas()
        self.draw_header(canvas, text("circle_of_fifths", self.language), None)
        rings = self.new_mask()
        draw = ImageDraw.Draw(rings)
        for radius in (self.outer_radius, self.inner_radius):
            draw.ellipse([(self.cx - radius, self.cy - radius), (self.cx + radius, self.cy + radius)], outline=255,
                         width=max(1, round(self.u)))  # fmt: skip
        canvas.alpha_composite(colorize(rings, self.color, 0.18))
        outlines, names = self.new_mask(), self.new_mask()
        for position in self.all_positions():
            self._dot(outlines, position, fill=None, outline=255)
            self._name(names, position)
        add_neon(canvas, outlines, self.color, radius=3 * self.u, strength=0.3, core_alpha=0.45)
        add_neon(canvas, names, self.color, radius=2 * self.u, strength=0.2, core_alpha=0.6)
        return canvas

    def state(self, step_index: int | None, time: float):
        """step_index: the chord shown at `time` (see render.chord_at), None = no chord now."""
        played = [s for s in self.steps if s.start <= time]
        visits = Counter(s.position for s in played)
        levels = tuple(
            math.ceil(visits[p] / self.max_visits * VISIT_LEVELS) if visits[p] else 0 for p in self.all_positions()
        )
        trail: list[CirclePosition] = []
        for step in reversed(played):
            if not trail or trail[0] != step.position:
                trail.insert(0, step.position)
            if len(trail) == TRAIL_LENGTH:
                break
        if step_index is None:
            return (None, tuple(trail), levels, "", 1.0)
        step = self.steps[step_index]
        return (step.position, tuple(trail), levels, self.chord_names[step_index], flash_strength(time - step.start))

    def draw(self, state):
        current, trail, levels, name, strength = state
        canvas = self.base.copy()

        fingerprint = self.new_mask()
        for position, level in zip(self.all_positions(), levels):
            if level:
                self._dot(fingerprint, position, fill=round(255 * level / VISIT_LEVELS * 0.55), scale=0.82)
        add_neon(canvas, fingerprint, self.color, radius=6 * self.u, strength=0.5, core_alpha=0.6)

        lines = self.new_mask()
        draw = ImageDraw.Draw(lines)
        for k, (a, b) in enumerate(zip(trail, trail[1:])):
            brightness = round(255 * (k + 1) / max(len(trail) - 1, 1))
            draw.line([self.point(a), self.point(b)], fill=brightness, width=self.trail_width)
        add_neon(canvas, lines, self.color, radius=8 * self.u, strength=0.9)

        if current is not None:
            dot = self.new_mask()
            self._dot(dot, current, scale=1.08)
            add_neon(canvas, dot, self.color, radius=16 * self.u, strength=max(strength, 1.3))
            label = self.new_mask()
            self._name(label, current)
            canvas.alpha_composite(colorize(label, PANEL_FILL))  # dark name on the bright dot

            size = fitting_size(name, self.center_size, 800, max_width=1.6 * (self.inner_radius - self.dot_radius["minor"]))
            center = self.new_mask()
            draw_text(center, self.cx, self.cy + size * 0.36, name, size, 800)
            add_neon(canvas, center, self.color, radius=size * 0.22, strength=strength)
        return canvas
