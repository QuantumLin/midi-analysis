"""Export settings for overlay videos."""

import re
from dataclasses import dataclass
from typing import Literal

from app.video.style import FontId, GlowLevel

VideoKind = Literal["spectrum", "chords", "key", "note_rate", "heatmap", "harmony", "achievements", "boss", "circle", "bingo", "wrapped"]
VideoFormat = Literal["prores", "png"]
Language = Literal["de", "en"]
SpectrumStyle = Literal["curve", "centered_bars"]

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
    language: Language = "en"  # texts in the overlays
    show_frame: bool = True  # glass panel with glowing border around the text and game overlays
    font: FontId = "orbitron"  # display font, see style.py
    glow: GlowLevel = "normal"
    scale: float = 1.0  # size of the overlay content within the output frame
    spectrum_style: SpectrumStyle = "curve"

    @staticmethod
    def create(
        kind: VideoKind,
        format: VideoFormat,
        width: int,
        height: int,
        fps: int,
        color: str,
        show_grid: bool,
        language: Language = "en",
        show_frame: bool = True,
        font: FontId = "orbitron",
        glow: GlowLevel = "normal",
        scale: float = 1.0,
        spectrum_style: SpectrumStyle = "curve",
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
        if not 0.25 <= scale <= 1.0:
            raise ValueError("Overlay size must be between 25% and 100%.")
        if spectrum_style not in ("curve", "centered_bars"):
            raise ValueError("Spectrum style must be 'curve' or 'centered_bars'.")
        rgb = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
        return VideoOptions(
            kind, format, width, height, fps, rgb, show_grid, language, show_frame, font, glow, scale, spectrum_style
        )  # type: ignore[arg-type]
