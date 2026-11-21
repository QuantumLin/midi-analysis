"""Draws one spectrum-analyzer frame (RGBA, transparent background).

The curve and its fill are rasterised directly with numpy: for every pixel column
the curve height is known, so anti-aliased coverage can be computed analytically
(fill: distance below the curve; line: perpendicular distance to the curve).
That is both fast and smooth, without a drawing library in the hot loop.

Curve and grid are each a single colour, so compositing reduces to blending two
constant colours by a per-pixel ratio, and without grid only alpha changes per frame.
"""

import numpy as np
from PIL import Image, ImageDraw

from app.analysis.spectrum import MAX_DB, MAX_HZ, MIN_DB, MIN_HZ
from app.video.fonts import load_font
from app.video.options import SpectrumStyle

GRID_FREQUENCIES = (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000)
GRID_DB_STEP = 12
BAR_COUNT = 72
GRID_COLOR = (255, 255, 255)
GRID_LINE_ALPHA = 0.16
GRID_LABEL_ALPHA = 0.7
FILL_ALPHA_TOP = 0.45  # fill opacity right below the plot top ...
FILL_ALPHA_BOTTOM = 0.08  # ... fading towards the bottom


class SpectrumRenderer:
    def __init__(
        self,
        width: int,
        height: int,
        color: tuple[int, int, int],
        show_grid: bool,
        display_style: SpectrumStyle = "curve",
    ):
        if display_style not in ("curve", "centered_bars"):
            raise ValueError("Spectrum style must be 'curve' or 'centered_bars'.")
        self.width = width
        self.height = height
        self.color = np.array(color, dtype=np.float32)
        self.display_style = display_style
        scale = height / 1080
        self.half_line = np.float32(max(1.5, 3.0 * scale) / 2 + 0.5)

        if show_grid:  # room for labels: dB on the right, Hz at the bottom
            self.left, self.right = round(24 * scale), width - round(72 * scale)
            self.top, self.bottom = round(24 * scale), height - round(56 * scale)
        else:
            self.left, self.right = 0, width
            self.top, self.bottom = round(height * 0.04), height

        columns = np.arange(self.left, self.right) + 0.5
        fraction = (columns - self.left) / (self.right - self.left)
        self.column_log_hz = np.log(MIN_HZ) + fraction * (np.log(MAX_HZ) - np.log(MIN_HZ))

        # Only rows that can contain curve or fill are computed per frame.
        self.row_start = max(0, int(self.top - self.half_line))
        rows = np.arange(self.row_start, self.bottom, dtype=np.float32) + 0.5
        self.rows = rows[:, None]
        fill_fraction = np.clip((rows - self.top) / (self.bottom - self.top), 0, 1)
        self.fill_alpha = (FILL_ALPHA_TOP + (FILL_ALPHA_BOTTOM - FILL_ALPHA_TOP) * fill_fraction)[:, None]

        # Static part of every frame (uint8 RGBA) and the grid alpha inside the plot region.
        grid = self._grid_layer(scale) if show_grid else None
        self.base = np.zeros((height, width, 4), dtype=np.uint8)
        self.base[..., :3] = color
        if grid is not None:
            self.base[...] = grid
        region = (slice(self.row_start, self.bottom), slice(self.left, self.right))
        self.region = region
        self.grid_alpha = self.base[region][..., 3].astype(np.float32) / 255 if grid is not None else None

    def render(self, levels_db: np.ndarray, bin_frequencies: np.ndarray) -> bytes:
        """levels_db: one spectrum frame over bin_frequencies. Returns raw RGBA bytes."""
        alpha = (
            self._centered_bars_alpha(levels_db, bin_frequencies)
            if self.display_style == "centered_bars"
            else self._curve_alpha(levels_db, bin_frequencies)
        )
        frame = self.base.copy()
        target = frame[self.region]

        if self.grid_alpha is None:
            target[..., 3] = alpha * 255 + 0.5
        else:
            # Curve (colour c, alpha a) over grid (white, alpha g): blend colours by the
            # share the grid contributes, out_alpha = a + g * (1 - a).
            grid_share = self.grid_alpha * (1 - alpha)
            out_alpha = alpha + grid_share
            t = np.divide(grid_share, out_alpha, out=np.ones_like(out_alpha), where=out_alpha > 0)
            for channel in range(3):
                c = self.color[channel]
                target[..., channel] = c + (GRID_COLOR[channel] - c) * t + 0.5
            target[..., 3] = out_alpha * 255 + 0.5
        return frame.tobytes()

    def _curve_alpha(self, levels_db: np.ndarray, bin_frequencies: np.ndarray) -> np.ndarray:
        levels = np.interp(self.column_log_hz, np.log(bin_frequencies), levels_db)
        normalized = (levels - MIN_DB) / (MAX_DB - MIN_DB)
        curve_y = (self.bottom - normalized * (self.bottom - self.top)).astype(np.float32)
        slope_factor = 1 / np.sqrt(1 + np.gradient(curve_y) ** 2)

        offset = self.rows - curve_y[None, :]  # > 0 below the curve
        fill = np.clip(offset + 0.5, 0, 1) * self.fill_alpha
        line = np.clip(self.half_line - np.abs(offset) * slope_factor[None, :], 0, 1)
        return line + fill * (1 - line)  # line over fill, same colour

    def _centered_bars_alpha(self, levels_db: np.ndarray, bin_frequencies: np.ndarray) -> np.ndarray:
        fractions = (np.arange(BAR_COUNT, dtype=np.float64) + 0.5) / BAR_COUNT
        bar_log_hz = np.log(MIN_HZ) + fractions * (np.log(MAX_HZ) - np.log(MIN_HZ))
        levels = np.interp(bar_log_hz, np.log(bin_frequencies), levels_db)
        normalized = np.clip((levels - MIN_DB) / (MAX_DB - MIN_DB), 0, 1)

        spacing = (self.right - self.left) / BAR_COUNT
        half_width = max(1.0, spacing * 0.18) / 2
        center_y = (self.top + self.bottom) / 2
        columns = np.arange(self.left, self.right, dtype=np.float32) + 0.5
        alpha = np.zeros((self.rows.shape[0], self.right - self.left), dtype=np.float32)

        for index, value in enumerate(normalized):
            center_x = self.left + (index + 0.5) * spacing
            first = max(0, int(np.floor(center_x - half_width - 0.5)) - self.left)
            last = min(len(columns), int(np.ceil(center_x + half_width + 0.5)) - self.left)
            horizontal = np.clip(half_width + 0.5 - np.abs(columns[first:last] - center_x), 0, 1)
            half_length = value * (self.bottom - self.top) / 2
            vertical = np.clip(half_length + 0.5 - np.abs(self.rows[:, 0] - center_y), 0, 1)
            region = alpha[:, first:last]
            np.maximum(region, vertical[:, None] * horizontal[None, :], out=region)

        return alpha

    def _grid_layer(self, scale: float) -> np.ndarray:
        """Static grid with labels as uint8 RGBA."""
        image = Image.new("RGBA", (self.width, self.height), (*GRID_COLOR, 0))
        draw = ImageDraw.Draw(image)
        font = load_font(max(10, round(18 * scale)))
        line = (*GRID_COLOR, round(255 * GRID_LINE_ALPHA))
        label = (*GRID_COLOR, round(255 * GRID_LABEL_ALPHA))
        line_width = max(1, round(scale))

        log_min, log_span = np.log(MIN_HZ), np.log(MAX_HZ) - np.log(MIN_HZ)
        for hz in GRID_FREQUENCIES:
            x = self.left + (np.log(hz) - log_min) / log_span * (self.right - self.left)
            x = min(round(x), self.right - 1)
            draw.line([(x, self.top), (x, self.bottom)], fill=line, width=line_width)
            text = f"{hz // 1000}k" if hz >= 1000 else str(hz)
            anchor = "lt" if hz == GRID_FREQUENCIES[0] else "rt" if hz == GRID_FREQUENCIES[-1] else "mt"
            draw.text((x, self.bottom + 10 * scale), text, font=font, fill=label, anchor=anchor)

        for db in range(int(MAX_DB), int(MIN_DB) - 1, -GRID_DB_STEP):
            y = round(self.top + (MAX_DB - db) / (MAX_DB - MIN_DB) * (self.bottom - self.top))
            draw.line([(self.left, y), (self.right, y)], fill=line, width=line_width)
            draw.text((self.right + 10 * scale, y), f"{db} dB", font=font, fill=label, anchor="lm")

        return np.asarray(image, dtype=np.uint8)
