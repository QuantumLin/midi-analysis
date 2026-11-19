import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.video.chord_renderer import ChordRenderer
from app.video.fonts import display_font_has, load_display_font
from app.video.neon import text_width
from app.video.options import VideoOptions
from app.video.render import render_video
from app.video.style import FONTS, GLOW_FACTORS, Style, current, using
from app.midi.parser import parse_midi
from tests.midi_factory import build_midi, chord_events

WIDTH, HEIGHT = 640, 360


def light(frame: bytes) -> float:
    image = np.frombuffer(frame, dtype=np.uint8).reshape(HEIGHT, WIDTH, 4)
    return float((image[..., :3].astype(np.float64).mean(axis=2) * image[..., 3] / 255).sum())


@pytest.mark.parametrize("font", list(FONTS))
def test_every_font_draws_text_and_falls_back_for_accidentals(font):
    with using(Style(font)):
        assert display_font_has("A") and display_font_has("ö")
        assert not display_font_has("♭")  # comes from the fallback font
        assert text_width("B♭m7", 60) > text_width("Bm7", 60) > 0
        frame = ChordRenderer(WIDTH, HEIGHT, (0, 229, 255), "de", ["B♭m7"]).render("Bbm7")
        assert light(frame) > 0


def test_fonts_differ():
    widths = set()
    for font in FONTS:
        with using(Style(font)):
            widths.add(round(text_width("Sprungriese", 60)))
    assert len(widths) == len(FONTS)


def test_style_is_restored_after_use():
    assert current() == Style()
    with using(Style("pixel", "strong")):
        assert current().font == "pixel" and load_display_font(40).path.endswith("PressStart2P.ttf")
    assert current() == Style()


def test_glow_levels_change_the_brightness():
    def chord_light(glow: str) -> float:
        with using(Style(glow=glow)):
            return light(ChordRenderer(WIDTH, HEIGHT, (0, 229, 255), "de", ["C"]).render("C"))

    assert chord_light("subtle") < chord_light("normal") < chord_light("strong")
    assert list(GLOW_FACTORS) == ["subtle", "normal", "strong"]


def test_render_pipeline_applies_the_chosen_style(tmp_path):
    """render_video activates font and glow from the options, and restores the default after."""
    midi = parse_midi(build_midi(chord_events([60, 64, 67], 0, 2)))

    def rendered_frame(font: str, glow: str) -> bytes:
        options = VideoOptions.create("chords", "png", WIDTH, HEIGHT, 24, "#00e5ff", True, "de", True, font, glow)
        path = render_video(midi, options, tmp_path / f"{font}-{glow}", lambda _: None)
        with zipfile.ZipFile(path) as archive:
            return archive.read(sorted(archive.namelist())[12])

    default = rendered_frame("orbitron", "normal")
    assert rendered_frame("playfair", "normal") != default
    assert rendered_frame("orbitron", "strong") != default
    assert current() == Style()


def test_api_accepts_known_fonts_only():
    client = TestClient(app)
    midi = build_midi(chord_events([60, 64, 67], 0, 2))
    data = {"kind": "chords", "format": "png", "width": WIDTH, "height": HEIGHT, "fps": 24}
    ok = client.post("/api/videos", files={"file": ("a.mid", midi, "audio/midi")},
                     data={**data, "font": "bebas", "glow": "strong"})  # fmt: skip
    assert ok.status_code == 202
    bad = client.post("/api/videos", files={"file": ("a.mid", midi, "audio/midi")}, data={**data, "font": "comic"})
    assert bad.status_code == 422
