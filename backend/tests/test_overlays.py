import numpy as np
import pytest

from app.analysis.key import Key, KeyAnalysis, KeySegment
from app.analysis.keyboard_activity import KEY_COUNT
from app.analysis.note_rate import NoteRateRecord
from app.video.fonts import display_font_has
from app.video.heatmap_renderer import HeatmapRenderer
from app.video.key_renderer import KeyRenderer
from app.video.labels import display_accidentals, key_name
from app.video.neon import text_width
from app.video.neon_overlay import flash_strength
from app.video.note_rate_renderer import NoteRateRenderer

WIDTH, HEIGHT = 640, 360
ACCENT = (0, 229, 255)


def as_image(frame: bytes, width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    return np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 4)


def glow(image: np.ndarray) -> float:
    """Total visible light: colour weighted by alpha."""
    return float((image[..., :3].astype(np.float64).mean(axis=2) * image[..., 3] / 255).sum())


def visible_rows(image: np.ndarray) -> int:
    return int((image[..., 3] > 0).any(axis=1).sum())


# --- labels and fonts --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "shown"),
    [("Bb", "B♭"), ("F#m7", "F♯m7"), ("Bbm7b5/Ab", "B♭m7b5/A♭"), ("Cadd9", "Cadd9"), ("Ebaug", "E♭aug")],
)
def test_display_accidentals(raw, shown):
    assert display_accidentals(raw) == shown


@pytest.mark.parametrize(
    ("key", "de", "en"),
    [
        (Key(2, "minor"), "d-Moll", "D minor"),
        (Key(10, "major"), "B♭-Dur", "B♭ major"),
        (Key(6, "minor"), "f♯-Moll", "F♯ minor"),
    ],
)
def test_key_names(key, de, en):
    assert key_name(key, "de") == de
    assert key_name(key, "en") == en


def test_display_font_and_fallback_glyphs():
    assert display_font_has("D") and display_font_has("7")
    assert not display_font_has("♭")  # drawn with the fallback font
    assert text_width("B♭", 60) > text_width("B", 60)


def test_flash_fades_out():
    assert flash_strength(0.0) > flash_strength(0.2) > flash_strength(0.44) >= 1.0
    assert flash_strength(1.0) == 1.0 and flash_strength(-0.1) == 1.0


# --- key overlay ---------------------------------------------------------------------------


def test_key_overlay_flashes_on_modulation():
    keys = KeyAnalysis(
        overall=Key(0, "major"),
        segments=[KeySegment(0, 10, Key(0, "major")), KeySegment(10, 20, Key(3, "major"))],
    )
    renderer = KeyRenderer(WIDTH, HEIGHT, ACCENT, "de", keys)
    before, just_after, later = (as_image(renderer.render(t)) for t in (5, 10.5, 15))

    assert glow(before) > 0
    assert glow(just_after) > glow(later) * 1.1  # "Modulation →" in full neon plus a stronger glow
    assert renderer.render(25) == renderer.empty  # after the piece
    assert visible_rows(before) == visible_rows(later)  # same panel size


# --- notes per second ------------------------------------------------------------------------


def test_note_rate_overlay_meter_and_record_flash():
    renderer = NoteRateRenderer(WIDTH, HEIGHT, ACCENT, "en", max_rate=30, max_total=999,
                                records=[NoteRateRecord(time=10.0, value=25)])  # fmt: skip
    slow = as_image(renderer.render(5.0, 3, 100, 20))
    fast = as_image(renderer.render(6.0, 28, 100, 20))
    record = as_image(renderer.render(10.2, 28, 150, 28))

    assert glow(fast) > glow(slow)  # more LED segments lit
    assert glow(record) > glow(fast)  # record flash
    assert visible_rows(slow) == visible_rows(record)  # same panel size


# --- heatmap bar -------------------------------------------------------------------------------


def test_heatmap_bar_glows_where_keys_were_played():
    renderer = HeatmapRenderer(WIDTH, HEIGHT, ACCENT)
    counts = np.zeros(KEY_COUNT, dtype=int)
    counts[10] = 1  # rarely played, low register
    counts[50] = 10  # often played
    held = np.zeros(KEY_COUNT, dtype=bool)
    held[70] = True  # held right now
    image = as_image(renderer.render(counts, held, max_count=10))

    rows = np.nonzero(image[..., 3].max(axis=1) > 200)[0]
    bar_row = int(rows[len(rows) // 2])

    def brightness(key: int) -> float:
        left = (WIDTH - renderer.bar_width) // 2
        x = left + int((key + 0.5) / KEY_COUNT * renderer.bar_width)
        pixel = image[bar_row, x].astype(float)
        return pixel[:3].mean() * pixel[3] / 255

    assert brightness(50) > brightness(10) > brightness(30)  # often > rarely > never
    assert brightness(70) >= brightness(50)  # held key flares up
    assert image[0, :, 3].max() == 0 and image[-1, :, 3].max() == 0  # transparent around the bar
