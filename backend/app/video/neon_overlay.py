"""Base for the neon text overlays (chord, key, notes per second).

Every overlay is a glass panel of fixed size (so it never jumps) with an uppercase,
letter-spaced label on top and a big glowing value below. Subclasses draw their content
for a hashable "state" (what is shown at a moment); the render pipeline draws each run
of identical states only once.
"""

from PIL import Image

from app.video.neon import Color, add_neon, centered_frame, draw_text, neon_panel, text_width
from app.video.style import current

LABEL_TRACKING = 0.22
LABEL_WEIGHT = 600
VALUE_WEIGHT = 800
FLASH_SECONDS = 0.45  # chord change / event flash
FLASH_BOOST = 1.3


class NeonOverlay:
    def __init__(self, frame_width: int, frame_height: int, color: Color, content_width: float, content_height: float):
        self.frame_width, self.frame_height = frame_width, frame_height
        self.color = color
        u = frame_height / 1080
        self.u = u
        self.label_size = max(8, round(28 * u))
        self.value_size = max(16, round(110 * u))
        self.small_size = max(8, round(30 * u))
        self.pad = round(44 * u)
        self.margin = round(64 * u)  # room for the glow (and the flash aura) around the panel
        self.panel = neon_panel(
            width=round(content_width + 2 * self.pad),
            height=round(content_height + 2 * self.pad),
            margin=self.margin,
            radius=round(30 * u),
            border=max(1, round(3 * u)),
            color=color,
            glow=current().glow_factor,
        )
        self.left = self.margin + self.pad  # content origin inside the canvas
        self.top = self.margin + self.pad
        self.center_x = self.panel.width / 2
        self.empty = bytes(frame_width * frame_height * 4)

    # Shared measurements for subclasses.
    def label_width(self, text: str) -> float:
        return text_width(text.upper(), self.label_size, LABEL_WEIGHT, LABEL_TRACKING)

    def value_width(self, text: str) -> float:
        return text_width(text, self.value_size, VALUE_WEIGHT)

    @property
    def header_height(self) -> float:
        """Label plus big value."""
        return self.label_size + 22 * self.u + self.value_size * 0.78

    def render_state(self, state) -> bytes:
        """RGBA frame bytes for a state; None = nothing shown (transparent)."""
        if state is None:
            return self.empty
        return centered_frame(self.draw(state), self.frame_width, self.frame_height)

    def draw(self, state) -> Image.Image:
        raise NotImplementedError

    def hide_frame(self) -> None:
        """No glass panel and no glowing border: only the glowing content is drawn.
        The canvas keeps its size, so the layout stays the same."""
        self.panel = Image.new("RGBA", self.panel.size, (0, 0, 0, 0))

    # Drawing helpers.
    def new_canvas(self) -> Image.Image:
        return self.panel.copy()

    def new_mask(self) -> Image.Image:
        return Image.new("L", self.panel.size)

    def draw_header(self, canvas: Image.Image, label: str, value: str | None, strength: float = 1.0,
                    label_accent: bool = False) -> float:  # fmt: skip
        """Label + big value (None: the subclass draws the value); returns the value's baseline."""
        label_baseline = self.top + self.label_size * 0.8
        mask = self.new_mask()
        draw_text(mask, self.center_x, label_baseline, label.upper(), self.label_size, LABEL_WEIGHT, LABEL_TRACKING)
        add_neon(canvas, mask, self.color, radius=self.label_size * 0.5,
                 strength=strength if label_accent else 0.35, core_alpha=1.0 if label_accent else 0.8)  # fmt: skip

        value_baseline = label_baseline + 22 * self.u + self.value_size * 0.78
        if value is None:
            return value_baseline
        mask = self.new_mask()
        draw_text(mask, self.center_x, value_baseline, value, self.value_size, VALUE_WEIGHT)
        add_neon(canvas, mask, self.color, radius=self.value_size * 0.22, strength=strength)
        return value_baseline


def flash_strength(seconds_since_event: float) -> float:
    """1.0 normally; up to 1 + FLASH_BOOST right after an event, fading out (quantised)."""
    if not 0 <= seconds_since_event < FLASH_SECONDS:
        return 1.0
    remaining = 1 - seconds_since_event / FLASH_SECONDS
    return 1.0 + round(FLASH_BOOST * remaining * 5) / 5


def ease_out_back(p: float) -> float:
    """0 -> 1 with a small overshoot near the end (a "pop")."""
    c1 = 1.70158
    return 1 + (c1 + 1) * (p - 1) ** 3 + c1 * (p - 1) ** 2
