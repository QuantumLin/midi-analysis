import numpy as np
import pytest

from app.analysis.key import Key, KeyAnalysis, KeySegment
from app.analysis.keyboard_activity import KEY_COUNT
from app.analysis.note_rate import NoteRateRecord
from app.video.heatmap_renderer import TRANSPARENT, HeatmapRenderer, keyboard_labels
from app.video.key_renderer import KeyRenderer
from app.video.labels import display_accidentals, key_name
from app.video.note_rate_renderer import NoteRateRenderer

WIDTH, HEIGHT = 640, 360
ACCENT = (255, 200, 0)


def as_image(frame: bytes, width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    return np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 4)


def accent_pixels(image: np.ndarray) -> int:
    return int(((image[..., 0] > 200) & (image[..., 1] > 150) & (image[..., 2] < 90) & (image[..., 3] > 150)).sum())


# --- labels ----------------------------------------------------------------------------


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


# --- key field ---------------------------------------------------------------------------


def test_key_field_highlights_modulation_briefly():
    keys = KeyAnalysis(
        overall=Key(0, "major"),
        segments=[KeySegment(0, 10, Key(0, "major")), KeySegment(10, 20, Key(3, "major"))],
    )
    renderer = KeyRenderer(WIDTH, HEIGHT, ACCENT, "de", keys)
    before, just_after, later = (as_image(renderer.render(t)) for t in (5, 10.5, 15))

    assert before[..., 3].max() > 0
    assert accent_pixels(just_after) > accent_pixels(later)  # "Modulation →" is drawn in the accent colour
    assert renderer.render(25) == renderer.canvas.empty  # after the piece


# --- notes per second ----------------------------------------------------------------------


def test_note_rate_field_shows_record_highlight():
    renderer = NoteRateRenderer(WIDTH, HEIGHT, ACCENT, "en", max_rate=30, max_total=999,
                                records=[NoteRateRecord(time=10.0, value=25)])  # fmt: skip
    normal = as_image(renderer.render(5.0, 12, 100, 20))
    record = as_image(renderer.render(10.5, 25, 150, 25))

    assert normal[..., 3].max() > 0
    assert accent_pixels(record) > accent_pixels(normal)
    # Same box size regardless of content.
    assert (normal[..., 3] > 0).any(axis=1).sum() == (record[..., 3] > 0).any(axis=1).sum()


# --- heatmap ---------------------------------------------------------------------------------


def test_keyboard_labels_cover_all_88_keys_at_the_bottom():
    labels = keyboard_labels(1920, 1080)
    present = set(np.unique(labels)) - {TRANSPARENT}
    assert present == set(range(KEY_COUNT))
    assert labels.shape[1] == 1920 and labels.shape[0] < 1080 * 0.4
    # Lowest key on the left, highest on the right.
    bottom_row = labels[-1]
    assert bottom_row[5] == 0 and bottom_row[-5] == KEY_COUNT - 1


def test_heatmap_colours_played_and_held_keys():
    renderer = HeatmapRenderer(WIDTH, HEIGHT, ACCENT)
    counts = np.zeros(KEY_COUNT, dtype=int)
    counts[39] = 10  # middle C, played often
    counts[40] = 1  # C#4, played once
    held = np.zeros(KEY_COUNT, dtype=bool)
    held[43] = True  # E4 held right now
    image = as_image(renderer.render(counts, held, max_count=10))

    def key_pixel(key: int) -> np.ndarray:
        rows, cols = np.nonzero(renderer.labels == key)
        return image[renderer.top + rows[-1], cols[len(cols) // 2]]

    assert key_pixel(39)[3] > key_pixel(0)[3]  # often played > never played
    assert key_pixel(43)[3] == 255  # held: fully opaque
    assert image[: renderer.top, :, 3].max() == 0  # nothing above the keyboard
