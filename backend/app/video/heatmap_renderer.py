"""Keyboard heatmap: an 88-key piano along the bottom of the frame whose keys glow the
more often they have been pressed so far; keys held right now light up brightly.

Drawing uses a label map (pixel -> key index) built once; each frame only computes
88 colours and maps them onto the pixels with one numpy lookup.
"""

import numpy as np

from app.analysis.keyboard_activity import KEY_COUNT
from app.midi.pitch import LOWEST_PIANO_KEY, is_black_key

WHITE_KEY_COUNT = 52
KEY_ASPECT = 5.6  # white key length / width
MAX_HEIGHT_SHARE = 0.4  # of the frame height
BLACK_WIDTH, BLACK_LENGTH = 0.6, 0.62  # relative to a white key
TRANSPARENT = KEY_COUNT  # label of pixels between keys

UNPLAYED_WHITE = ((255, 255, 255), 0.12)
UNPLAYED_BLACK = ((16, 16, 16), 0.75)
HEAT_GAMMA = 0.5  # lifts rarely used keys so they stay visible next to the busiest key


class HeatmapRenderer:
    def __init__(self, width: int, height: int, color: tuple[int, int, int]):
        self.width, self.height = width, height
        self.color = np.array(color, dtype=np.float32)
        self.labels = keyboard_labels(width, height)
        self.top = height - self.labels.shape[0]
        self.black = np.array([is_black_key(LOWEST_PIANO_KEY + k) for k in range(KEY_COUNT)])

    def render(self, press_counts: np.ndarray, held: np.ndarray, max_count: int) -> bytes:
        palette = self._palette(press_counts, held, max_count)
        frame = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        frame[self.top :] = palette[self.labels]
        return frame.tobytes()

    def _palette(self, counts: np.ndarray, held: np.ndarray, max_count: int) -> np.ndarray:
        """RGBA (uint8) per key, plus a transparent last entry for the gaps."""
        heat = (counts / max_count) ** HEAT_GAMMA if max_count > 0 else np.zeros(KEY_COUNT)
        heat = heat[:, None].astype(np.float32)
        played = (counts > 0)[:, None]

        white_rgb = np.where(played, self.color, np.float32(UNPLAYED_WHITE[0]))
        white_alpha = np.where(played, 0.22 + 0.7 * heat, UNPLAYED_WHITE[1])
        black_base = np.array(UNPLAYED_BLACK[0], dtype=np.float32)
        black_rgb = np.where(played, black_base + (self.color - black_base) * (0.35 + 0.65 * heat), black_base)
        black_alpha = np.where(played, 0.85, UNPLAYED_BLACK[1])

        is_black = self.black[:, None]
        rgb = np.where(is_black, black_rgb, white_rgb)
        alpha = np.where(is_black, black_alpha, white_alpha)
        # Held keys: bright, tinted towards white.
        rgb = np.where(held[:, None], self.color + (255 - self.color) * 0.55, rgb)
        alpha = np.where(held[:, None], 1.0, alpha)

        palette = np.zeros((KEY_COUNT + 1, 4), dtype=np.uint8)
        palette[:KEY_COUNT, :3] = np.clip(rgb + 0.5, 0, 255)
        palette[:KEY_COUNT, 3] = np.clip(alpha * 255 + 0.5, 0, 255)[:, 0]
        return palette


def keyboard_labels(width: int, height: int) -> np.ndarray:
    """Pixel -> key index (0 = A0) for a keyboard spanning the full width; TRANSPARENT in gaps."""
    white_width = width / WHITE_KEY_COUNT
    key_height = max(1, min(round(white_width * KEY_ASPECT), round(height * MAX_HEIGHT_SHARE)))
    gap = max(1, round(width / 1920))
    labels = np.full((key_height, width), TRANSPARENT, dtype=np.int16)

    white_index = 0
    black_keys: list[tuple[int, float]] = []
    for key in range(KEY_COUNT):
        if is_black_key(LOWEST_PIANO_KEY + key):
            black_keys.append((key, white_index * white_width))  # centred on the boundary
            continue
        left = round(white_index * white_width)
        right = round((white_index + 1) * white_width) - gap
        labels[:, left:right] = key
        white_index += 1

    black_width = white_width * BLACK_WIDTH
    black_height = round(key_height * BLACK_LENGTH)
    for key, boundary in black_keys:
        left = round(boundary - black_width / 2)
        right = round(boundary + black_width / 2)
        labels[:black_height, max(0, left - gap) : right + gap] = TRANSPARENT  # thin gap around black keys
        labels[: black_height - gap, max(0, left) : right] = key
    return labels
