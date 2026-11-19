"""User-selectable look of the overlays: display font and glow strength.

The render pipeline activates a Style for the duration of one video (`using(style)`);
the drawing code (neon.py, fonts.py) reads it via `current()`. Video jobs run one at a
time (see jobs.py), so a single active style is enough; the frame threads of one video
all share it.

To add a font: put the .ttf and its licence into assets/fonts/<Folder>/, add a FontSpec
to FONTS and the same font to the frontend (src/assets/fonts, src/utils/style.ts).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

FONT_DIR = Path(__file__).parent / "assets" / "fonts"

FontId = Literal["orbitron", "montserrat", "bebas", "playfair", "pixel", "handwriting"]
GlowLevel = Literal["subtle", "normal", "strong"]


@dataclass(frozen=True, slots=True)
class FontSpec:
    file: Path
    variable: bool  # has a weight axis (otherwise one fixed weight)
    scale: float  # evens out the visual size between fonts (Orbitron = 1)


FONTS: dict[str, FontSpec] = {
    "orbitron": FontSpec(FONT_DIR / "Orbitron" / "Orbitron.ttf", variable=True, scale=1.0),
    "montserrat": FontSpec(FONT_DIR / "Montserrat" / "Montserrat.ttf", variable=True, scale=1.05),
    "bebas": FontSpec(FONT_DIR / "BebasNeue" / "BebasNeue.ttf", variable=False, scale=1.1),
    "playfair": FontSpec(FONT_DIR / "PlayfairDisplay" / "PlayfairDisplay.ttf", variable=True, scale=1.1),
    "pixel": FontSpec(FONT_DIR / "PressStart2P" / "PressStart2P.ttf", variable=False, scale=0.72),
    "handwriting": FontSpec(FONT_DIR / "Caveat" / "Caveat.ttf", variable=True, scale=1.35),
}

# Multiplies the glow around text, meters and borders; the bright core stays the same.
GLOW_FACTORS: dict[str, float] = {"subtle": 0.3, "normal": 1.0, "strong": 1.8}


@dataclass(frozen=True, slots=True)
class Style:
    font: FontId = "orbitron"
    glow: GlowLevel = "normal"

    @property
    def font_spec(self) -> FontSpec:
        return FONTS[self.font]

    @property
    def glow_factor(self) -> float:
        return GLOW_FACTORS[self.glow]


_active = Style()


def current() -> Style:
    return _active


@contextmanager
def using(style: Style) -> Iterator[None]:
    """Activates `style` while the block runs (and restores the previous one after)."""
    global _active
    previous, _active = _active, style
    try:
        yield
    finally:
        _active = previous
