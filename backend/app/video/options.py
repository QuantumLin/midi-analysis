"""Export settings for overlay videos."""

import re
from dataclasses import dataclass
from typing import Literal

VideoKind = Literal["spectrum", "chords", "key", "note_rate", "heatmap", "harmony", "achievements", "motifs", "sections", "boss", "circle", "bingo", "wrapped"]
VideoFormat = Literal["prores", "png"]
Language = Literal["de", "en"]

ALLOWED_FPS = (24, 25, 30, 50, 60)
MIN_WIDTH, MAX_WIDTH = 320, 3840
MIN_HEIGHT, MAX_HEIGHT = 180, 2160
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True, slots=True)
class VideoOptions:
    kind: VideoKind
    format: VideoFormat
    width: int
    height: int
    fps: int
    color: tuple[int, int, int]  # accent colour: curve, text, heat
    show_grid: bool  # spectrum only: frequency/dB grid with labels
    language: Language = "de"  # texts in the overlays

    @staticmethod
    def create(
        kind: VideoKind,
        format: VideoFormat,
        width: int,
        height: int,
        fps: int,
        color: str,
        show_grid: bool,
        language: Language = "de",
    ) -> "VideoOptions":
        """Validates raw values; raises ValueError with a readable message."""
        if not (MIN_WIDTH <= width <= MAX_WIDTH and MIN_HEIGHT <= height <= MAX_HEIGHT):
            raise ValueError(f"Resolution must be between {MIN_WIDTH}x{MIN_HEIGHT} and {MAX_WIDTH}x{MAX_HEIGHT}.")
        if width % 2 or height % 2:
            raise ValueError("Width and height must be even numbers.")
        if fps not in ALLOWED_FPS:
            raise ValueError(f"FPS must be one of {', '.join(map(str, ALLOWED_FPS))}.")
        if not _HEX_COLOR.match(color):
            raise ValueError("Color must be a hex value like #4da3ff.")
        rgb = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
        return VideoOptions(kind, format, width, height, fps, rgb, show_grid, language)  # type: ignore[arg-type]
