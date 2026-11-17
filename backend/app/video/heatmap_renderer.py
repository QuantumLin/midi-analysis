"""Keyboard heatmap as a glowing bar: the 88 keys from A0 (left) to C8 (right) as a
continuous colour distribution. The more often a range has been played so far, the
hotter it glows (dark glass -> accent colour -> white-hot); keys held right now flare up.
Small marks under the bar show where each C sits (C1 ... C8).
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from app.analysis.keyboard_activity import KEY_COUNT
from app.midi.pitch import LOWEST_PIANO_KEY
from app.video.neon import PANEL_FILL, Color, centered_frame, colorize, core_color, draw_text

HEAT_GAMMA = 0.55  # lifts rarely played keys so they stay visible next to the busiest one
HELD_BOOST = 0.3  # held keys glow above the hottest played key
SMOOTHING_SIGMA = 0.6  # in keys: a slight blend, single keys stay visible
SMOOTHING_RADIUS = 2
BAR_WIDTH_SHARE = 0.9  # of the frame width
SUPERSAMPLING = 4
GLOW_RADIUS = 0.15  # in bar heights: a subtle halo that keeps the bar crisp


class HeatmapRenderer:
    def __init__(self, width: int, height: int, color: Color):
        self.width, self.height = width, height
        u = height / 1080
        self.color = np.array(color, dtype=np.float32)
        self.core = np.array(core_color(color), dtype=np.float32)
        self.bar_width = round(width * BAR_WIDTH_SHARE)
        self.bar_height = max(6, round(44 * u))
        self.margin = round(self.bar_height * 0.8)  # room for the glow
        offsets = np.arange(-SMOOTHING_RADIUS, SMOOTHING_RADIUS + 1)
        kernel = np.exp(-0.5 * (offsets / SMOOTHING_SIGMA) ** 2)
        self.kernel = kernel / kernel.sum()
        self.label_size = max(8, round(22 * u))
        canvas_height = self.bar_height + 2 * self.margin + round(46 * u)
        self.size = (self.bar_width + 2 * self.margin, canvas_height)
        self.bar_box = (self.margin, self.margin, self.margin + self.bar_width, self.margin + self.bar_height)

        # Column -> fractional key position, for a smooth distribution along the bar.
        columns = (np.arange(self.bar_width) + 0.5) / self.bar_width * KEY_COUNT - 0.5
        self.column_keys = np.clip(columns, 0, KEY_COUNT - 1)
        self.shape_alpha = self._rounded_bar_alpha()  # (bar_height, bar_width) 0..1
        self.background = self._static_layer(u)

    def render(self, press_counts: np.ndarray, held: np.ndarray, max_count: int) -> bytes:
        heat = (press_counts / max_count) ** HEAT_GAMMA if max_count > 0 else np.zeros(KEY_COUNT)
        # Smooth across neighbouring keys: a distribution, not a barcode of white/black keys.
        heat = np.convolve(np.pad(heat, SMOOTHING_RADIUS, mode="edge"), self.kernel, mode="valid")
        if heat.max() > 0:
            heat = heat / heat.max()  # the hottest region stays at full intensity
        heat = np.where(held, np.maximum(heat, 1.0) + HELD_BOOST, heat)  # held keys: white-hot
        column_heat = np.interp(self.column_keys, np.arange(KEY_COUNT), heat).astype(np.float32)

        rgb, alpha = self._ramp(column_heat)
        bar = np.zeros((self.bar_height, self.bar_width, 4), dtype=np.float32)
        bar[..., :3] = rgb[None, :, :]
        bar[..., 3] = alpha[None, :] * self.shape_alpha
        bar_image = Image.fromarray((bar * [1, 1, 1, 255] + 0.5).clip(0, 255).astype(np.uint8), "RGBA")

        canvas = self.background.copy()
        glow = Image.new("RGBA", self.size, (0, 0, 0, 0))
        glow.paste(bar_image, self.bar_box[:2])
        glow = glow.convert("RGBa").filter(ImageFilter.GaussianBlur(self.bar_height * GLOW_RADIUS)).convert("RGBA")
        canvas.alpha_composite(glow)
        canvas.alpha_composite(bar_image, self.bar_box[:2])
        return centered_frame(canvas, self.width, self.height)

    def _ramp(self, heat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """heat 0 -> dark glass, 0.6 -> accent colour, >= 1 -> white-hot core colour."""
        dark = np.array(PANEL_FILL, dtype=np.float32)
        h = heat[:, None]
        low = dark + (self.color - dark) * np.clip(h / 0.6, 0, 1)
        high = self.color + (self.core - self.color) * np.clip((h - 0.6) / 0.6, 0, 1)
        rgb = np.where(h <= 0.6, low, high)
        alpha = np.where(heat <= 0, 0.55, np.clip(0.6 + heat * 0.5, 0, 1))
        return rgb, alpha

    def _rounded_bar_alpha(self) -> np.ndarray:
        s = SUPERSAMPLING
        big = Image.new("L", (self.bar_width * s, self.bar_height * s))
        ImageDraw.Draw(big).rounded_rectangle(
            [(0, 0), (big.width - 1, big.height - 1)], radius=self.bar_height * s // 2, fill=255
        )
        small = big.resize((self.bar_width, self.bar_height), Image.Resampling.LANCZOS)
        return np.asarray(small, dtype=np.float32) / 255

    def _static_layer(self, u: float) -> Image.Image:
        """Marks and labels for every C under the bar."""
        layer = Image.new("RGBA", self.size, (0, 0, 0, 0))
        marks = Image.new("L", self.size)
        draw = ImageDraw.Draw(marks)
        tick_top = self.bar_box[3] + round(8 * u)
        for key in range(KEY_COUNT):
            pitch = LOWEST_PIANO_KEY + key
            if pitch % 12 != 0:
                continue
            x = self.margin + (key + 0.5) / KEY_COUNT * self.bar_width
            draw.line([(x, tick_top), (x, tick_top + round(10 * u))], fill=255, width=max(1, round(2 * u)))
            draw_text(marks, x, tick_top + round(14 * u) + self.label_size, f"C{pitch // 12 - 1}", self.label_size, 600)
        layer.alpha_composite(colorize(marks, core_color(tuple(int(c) for c in self.color)), 0.55))
        return layer
