"""Song Wrapped end screen: "SONG WRAPPED" and the piece's facts as glass cards in two
columns. Unlike the other overlays it is not synchronised with the piece: it is a clip
of its own (duration()), meant to follow the performance in the edit.

Timeline: the title appears, then one card after another pops in, everything stays for
a few seconds and fades out.
"""

import math

import numpy as np
from PIL import Image

from app.video.labels import Language, text
from app.video.neon import (
    Color,
    add_neon,
    centered_frame,
    draw_text,
    fitting_size,
    neon_panel,
)
from app.video.neon_overlay import LABEL_TRACKING, LABEL_WEIGHT, VALUE_WEIGHT, ease_out_back
from app.video.wrapped import WrappedCard

INTRO_SECONDS = 0.8
CARD_INTERVAL_SECONDS = 1.0
POP_SECONDS = 0.3
HOLD_SECONDS = 4.0
FADE_SECONDS = 0.6
ANIMATION_STEPS = 8
COLUMNS = 2


class WrappedRenderer:
    def __init__(self, width: int, height: int, color: Color, language: Language, cards: list[WrappedCard]):
        self.frame_width, self.frame_height = width, height
        self.color = color
        self.language = language
        self.cards = cards
        u = height / 1080
        self.u = u
        self.card_width, self.card_height, self.gap = round(620 * u), round(150 * u), round(28 * u)
        self.card_margin = round(36 * u)  # room for each card's glow
        self.title_size = max(12, round(92 * u))
        self.title_height = round(150 * u)
        rows = max(1, math.ceil(len(cards) / COLUMNS))
        self.size = (
            COLUMNS * self.card_width + (COLUMNS - 1) * self.gap + 2 * self.card_margin,
            self.title_height + rows * self.card_height + (rows - 1) * self.gap + 2 * self.card_margin,
        )
        self.card_images = [self._card_image(card) for card in cards]
        self.empty = bytes(width * height * 4)

    def duration(self) -> float:
        return INTRO_SECONDS + len(self.cards) * CARD_INTERVAL_SECONDS + HOLD_SECONDS + FADE_SECONDS

    def frame_count(self, fps: int) -> int:
        return max(1, round(self.duration() * fps))

    def card_start(self, index: int) -> float:
        return INTRO_SECONDS + index * CARD_INTERVAL_SECONDS

    def state(self, time: float):
        """(title opacity, scale per card (0 = not shown yet), overall opacity)."""
        if not 0 <= time < self.duration():
            return None
        title = _quantize(time / INTRO_SECONDS)
        scales = []
        for index in range(len(self.cards)):
            since = time - self.card_start(index)
            if since < 0:
                scales.append(0.0)
            elif since < POP_SECONDS:
                scales.append(round(0.6 + 0.4 * ease_out_back(_quantize(since / POP_SECONDS)), 3))
            else:
                scales.append(1.0)
        remaining = self.duration() - time
        opacity = _quantize(remaining / FADE_SECONDS) if remaining < FADE_SECONDS else 1.0
        return (title, tuple(scales), opacity)

    def render(self, time: float) -> bytes:
        return self.render_state(self.state(time))

    def render_state(self, state) -> bytes:
        if state is None:
            return self.empty
        title_opacity, scales, opacity = state
        canvas = Image.new("RGBA", self.size, (0, 0, 0, 0))
        if title_opacity > 0:
            mask = Image.new("L", self.size)
            draw_text(mask, self.size[0] / 2, self.card_margin + self.title_size * 0.8,
                      text("song_wrapped", self.language).upper(), self.title_size, VALUE_WEIGHT, 0.06)  # fmt: skip
            add_neon(canvas, mask, self.color, radius=self.title_size * 0.22, strength=1.0,
                     core_alpha=title_opacity)  # fmt: skip
        for index, scale in enumerate(scales):
            if scale <= 0:
                continue
            image = self.card_images[index]
            if scale != 1.0:
                image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                                     Image.Resampling.BILINEAR)  # fmt: skip
            cx, cy = self._card_center(index)
            canvas.alpha_composite(image, (round(cx - image.width / 2), round(cy - image.height / 2)))
        if opacity < 1.0:
            pixels = np.asarray(canvas).copy()
            pixels[..., 3] = (pixels[..., 3] * opacity).astype(np.uint8)
            canvas = Image.fromarray(pixels, "RGBA")
        return centered_frame(canvas, self.frame_width, self.frame_height)

    def _card_center(self, index: int) -> tuple[float, float]:
        row, col = divmod(index, COLUMNS)
        rows = math.ceil(len(self.cards) / COLUMNS)
        if row == rows - 1 and len(self.cards) % COLUMNS:  # lone card in the last row: centred
            x = self.size[0] / 2
        else:
            x = self.card_margin + col * (self.card_width + self.gap) + self.card_width / 2
        y = self.card_margin + self.title_height + row * (self.card_height + self.gap) + self.card_height / 2
        return x, y

    def _card_image(self, card: WrappedCard) -> Image.Image:
        """One glass card with the title (small, uppercase) and the value (big neon)."""
        image = neon_panel(self.card_width, self.card_height, self.card_margin, round(24 * self.u),
                           max(1, round(3 * self.u)), self.color).copy()  # fmt: skip
        center_x = image.width / 2
        max_width = self.card_width - 2 * 32 * self.u
        title_size = max(8, round(26 * self.u))
        mask = Image.new("L", image.size)
        draw_text(mask, center_x, self.card_margin + 30 * self.u + title_size * 0.8, card.title.upper(), title_size,
                  LABEL_WEIGHT, LABEL_TRACKING)  # fmt: skip
        add_neon(image, mask, self.color, radius=title_size * 0.5, strength=0.35, core_alpha=0.8)
        value_size = fitting_size(card.value, max(12, round(56 * self.u)), VALUE_WEIGHT, max_width)
        mask = Image.new("L", image.size)
        draw_text(mask, center_x, self.card_margin + self.card_height - 34 * self.u, card.value, value_size,
                  VALUE_WEIGHT)  # fmt: skip
        add_neon(image, mask, self.color, radius=value_size * 0.22, strength=1.0)
        return image


def _quantize(p: float) -> float:
    return round(min(max(p, 0.0), 1.0) * ANIMATION_STEPS) / ANIMATION_STEPS
