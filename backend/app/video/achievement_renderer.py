"""Achievement pop-ups, like in a video game: "ERFOLG FREIGESCHALTET", a glowing star with
the title ("8-FINGER-AKKORD") and a detail line ("8 Töne auf einmal").

Each pop-up springs in (scales up with a slight overshoot and flashes), stays for a few
seconds and fades out; between pop-ups the frame is empty. All pop-ups of a video share
one panel size, so they look like one consistent element.
"""

import numpy as np
from PIL import Image

from app.analysis.achievements import Achievement
from app.video.labels import Language, achievement_texts, text
from app.video.neon import Color, add_neon, centered_frame, draw_star, draw_text, text_width
from app.video.neon_overlay import LABEL_TRACKING, LABEL_WEIGHT, NeonOverlay, ease_out_back, flash_strength

APPEAR_SECONDS = 0.3
FADE_SECONDS = 0.4
ANIMATION_STEPS = 8  # quantisation of the in/out animation (identical frames are drawn once)
START_SCALE = 0.6
TITLE_WEIGHT = 800
DETAIL_TRACKING = 0.06


class AchievementRenderer(NeonOverlay):
    def __init__(self, width: int, height: int, color: Color, language: Language, achievements: list[Achievement]):
        self.language = language
        self.achievements = achievements
        self.texts = [achievement_texts(a, language) for a in achievements]
        probe = NeonOverlay(width, height, color, 0, 0)
        self.title_size = max(12, round(64 * probe.u))
        self.star_radius = self.title_size * 0.42
        self.star_gap = self.title_size * 0.4
        self.title_gap = 24 * probe.u
        self.detail_gap = 26 * probe.u
        self.small_size = probe.small_size
        content_width = max(
            max((self._title_row_width(t) for t, _ in self.texts), default=0),
            max((self._detail_width(d) for _, d in self.texts), default=0),
            probe.label_width(text("achievement", language)),
            480 * probe.u,
        )
        content_height = (
            probe.label_size + self.title_gap + self.title_size * 0.78 + self.detail_gap + probe.small_size
        )
        super().__init__(width, height, color, content_width, content_height)

    def _title_row_width(self, title: str) -> float:
        return 2 * self.star_radius + self.star_gap + text_width(title.upper(), self.title_size, TITLE_WEIGHT)

    def _detail_width(self, detail: str) -> float:
        return text_width(detail.upper(), self.small_size, LABEL_WEIGHT, DETAIL_TRACKING)

    def state(self, time: float):
        """(pop-up index, scale, opacity, glow strength), or None between pop-ups."""
        index = next((i for i, a in enumerate(self.achievements) if a.time <= time < a.end), None)
        if index is None:
            return None
        item = self.achievements[index]
        since, remaining = time - item.time, item.end - time
        scale, alpha = 1.0, 1.0
        if since < APPEAR_SECONDS:
            p = _quantize(since / APPEAR_SECONDS)
            scale = START_SCALE + (1 - START_SCALE) * ease_out_back(p)
            alpha = min(1.0, 0.25 + p)
        elif remaining < FADE_SECONDS:
            q = _quantize(remaining / FADE_SECONDS)
            scale, alpha = 0.94 + 0.06 * q, q
        return (index, round(scale, 3), round(alpha, 3), flash_strength(since))

    def render(self, time: float) -> bytes:
        return self.render_state(self.state(time))

    def render_state(self, state) -> bytes:
        if state is None:
            return self.empty
        _, scale, alpha, _ = state
        canvas = self.draw(state)
        if scale != 1.0:
            size = (max(1, round(canvas.width * scale)), max(1, round(canvas.height * scale)))
            canvas = canvas.resize(size, Image.Resampling.BILINEAR)
        if alpha < 1.0:
            pixels = np.asarray(canvas).copy()
            pixels[..., 3] = (pixels[..., 3] * alpha).astype(np.uint8)
            canvas = Image.fromarray(pixels, "RGBA")
        return centered_frame(canvas, self.frame_width, self.frame_height)

    def draw(self, state):
        index, _, _, strength = state
        title, detail = self.texts[index]
        canvas = self.new_canvas()

        label_baseline = self.top + self.label_size * 0.8
        mask = self.new_mask()
        draw_text(mask, self.center_x, label_baseline, text("achievement", self.language).upper(), self.label_size,
                  LABEL_WEIGHT, LABEL_TRACKING)  # fmt: skip
        add_neon(canvas, mask, self.color, radius=self.label_size * 0.5, strength=min(strength, 1.6))

        # Star + title, centred together.
        title_baseline = label_baseline + self.title_gap + self.title_size * 0.78
        row_left = self.center_x - self._title_row_width(title) / 2
        title_width = text_width(title.upper(), self.title_size, TITLE_WEIGHT)
        mask = self.new_mask()
        draw_star(mask, row_left + self.star_radius, title_baseline - self.title_size * 0.36, self.star_radius)
        title_center = row_left + 2 * self.star_radius + self.star_gap + title_width / 2
        draw_text(mask, title_center, title_baseline, title.upper(), self.title_size, TITLE_WEIGHT)
        add_neon(canvas, mask, self.color, radius=self.title_size * 0.22, strength=strength)

        detail_baseline = title_baseline + self.detail_gap + self.small_size * 0.8
        mask = self.new_mask()
        draw_text(mask, self.center_x, detail_baseline, detail.upper(), self.small_size, LABEL_WEIGHT, DETAIL_TRACKING)
        add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=0.3, core_alpha=0.8)
        return canvas


def _quantize(p: float) -> float:
    return round(min(max(p, 0.0), 1.0) * ANIMATION_STEPS) / ANIMATION_STEPS
