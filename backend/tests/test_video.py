import json
import subprocess
import time
import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.analysis.chords import ChordMatch, ChordSegment
from app.analysis.spectrum import MIN_DB, log_frequencies
from app.main import app
from app.midi.parser import parse_midi
from app.video.chord_renderer import ChordRenderer
from app.video.options import VideoOptions
from app.video.render import chord_at, render_video
from app.video.spectrum_renderer import SpectrumRenderer
from tests.midi_factory import build_midi, chord_events

WIDTH, HEIGHT = 320, 180
WHITE = (255, 255, 255)


def as_image(frame: bytes) -> np.ndarray:
    return np.frombuffer(frame, dtype=np.uint8).reshape(HEIGHT, WIDTH, 4)


def segment(name_root: int, start: float, end: float) -> ChordSegment:
    return ChordSegment(start, end, ChordMatch(name_root, "", name_root), ())


# --- options -------------------------------------------------------------------------


def test_options_validation():
    options = VideoOptions.create("spectrum", "prores", 1920, 1080, 30, "#4da3ff", True)
    assert options.color == (0x4D, 0xA3, 0xFF)
    for bad in [(1921, 1080, 30, "#ffffff"), (1920, 1080, 29, "#ffffff"), (1920, 1080, 30, "red"), (100, 100, 30, "#ffffff")]:
        with pytest.raises(ValueError):
            VideoOptions.create("spectrum", "prores", *bad, True)


# --- chord display timing ------------------------------------------------------------


def test_chord_at_holds_through_short_gaps_only():
    chords = [segment(0, 1.0, 2.0), segment(7, 2.5, 3.0)]  # C, then G after a 0.5 s gap

    def name(time):
        chord = chord_at(chords, time)
        return chord.chord.name if chord else None

    assert name(0.5) is None
    assert name(1.5) == "C"
    assert name(2.2) == "C"  # held through the gap
    assert name(2.7) == "G"
    assert name(4.9) == "G"  # held 2 s after the last chord ...
    assert name(5.1) is None  # ... then hidden


# --- frame renderers -----------------------------------------------------------------


def test_spectrum_frame_draws_peak_where_the_note_is():
    frequencies = log_frequencies(512)
    levels = np.full(512, MIN_DB)
    levels[np.argmin(np.abs(frequencies - 1000))] = -3.0  # one loud bin at 1 kHz
    renderer = SpectrumRenderer(WIDTH, HEIGHT, WHITE, show_grid=False)
    image = as_image(renderer.render(levels, frequencies))

    peak_column = int(np.argmax((image[..., 3] > 128).sum(axis=0)))
    expected = np.log(1000 / 20) / np.log(20000 / 20) * WIDTH
    assert abs(peak_column - expected) <= 3
    assert image[: HEIGHT // 2, : WIDTH // 4, 3].max() == 0  # top-left stays transparent


def test_spectrum_grid_adds_labels_and_lines():
    frequencies = log_frequencies(512)
    silent = np.full(512, MIN_DB)
    plain = as_image(SpectrumRenderer(WIDTH, HEIGHT, WHITE, show_grid=False).render(silent, frequencies))
    grid = as_image(SpectrumRenderer(WIDTH, HEIGHT, WHITE, show_grid=True).render(silent, frequencies))
    assert (grid[..., 3] > 0).sum() > (plain[..., 3] > 0).sum() * 3


def test_chord_frame_has_centered_box_with_text():
    renderer = ChordRenderer(WIDTH, HEIGHT, (255, 200, 0), "de", ["C", "Am7"])
    empty = as_image(renderer.render(None))
    frame = as_image(renderer.render("Am7"))

    assert empty.max() == 0
    alpha = frame[..., 3]
    assert alpha[HEIGHT // 2, WIDTH // 2] > 0 and alpha[0, 0] == 0 and alpha[-1, -1] == 0
    # Neon core: the accent colour mixed with white -> bright, warm pixels.
    text_pixels = (frame[..., 0] > 230) & (frame[..., 1] > 200) & (frame[..., 2] < 200) & (alpha > 200)
    assert text_pixels.sum() > 20
    # Same box size for every chord, so the field doesn't jump.
    assert (as_image(renderer.render("C"))[..., 3] > 0).sum() == (alpha > 0).sum()


# --- full render -----------------------------------------------------------------------


def probe(path) -> dict:
    output = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=codec_name,pix_fmt,width,height,nb_read_frames", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    return json.loads(output)["streams"][0]


@pytest.mark.parametrize("kind", ["spectrum", "chords", "key", "note_rate", "heatmap"])
def test_render_prores_with_alpha(tmp_path, kind):
    midi = parse_midi(build_midi(chord_events([60, 64, 67], 0, 2)))  # 1 s
    options = VideoOptions.create(kind, "prores", WIDTH, HEIGHT, 24, "#ffffff", True)
    progress = []
    path = render_video(midi, options, tmp_path / "out", progress.append)

    info = probe(path)
    assert path.suffix == ".mov"
    assert info["codec_name"] == "prores" and info["pix_fmt"] == "yuva444p12le"
    assert (info["width"], info["height"]) == (WIDTH, HEIGHT)
    assert int(info["nb_read_frames"]) == 25  # 0..1 s at 24 fps
    assert progress[-1] == 1.0


def test_render_png_sequence_zip(tmp_path):
    midi = parse_midi(build_midi(chord_events([60, 64, 67], 0, 1)))  # 0.5 s
    options = VideoOptions.create("chords", "png", WIDTH, HEIGHT, 24, "#ffffff", True)
    path = render_video(midi, options, tmp_path / "out", lambda _: None, frame_prefix="song_chords")

    assert path.suffix == ".zip"
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert len(names) == 13 and names[0] == "song_chords_000000.png"
        assert archive.read(names[0])[:8] == b"\x89PNG\r\n\x1a\n"
    assert not (tmp_path / "out_frames").exists()  # temporary frames cleaned up


# --- API -------------------------------------------------------------------------------


def test_video_api_job_lifecycle():
    client = TestClient(app)
    midi = build_midi(chord_events([60, 64, 67], 0, 1))
    response = client.post(
        "/api/videos",
        files={"file": ("My Song (1).mid", midi, "audio/midi")},
        data={"kind": "chords", "format": "prores", "width": WIDTH, "height": HEIGHT, "fps": 24},
    )
    assert response.status_code == 202
    job = response.json()

    deadline = time.monotonic() + 30
    while job["status"] in ("queued", "running") and time.monotonic() < deadline:
        time.sleep(0.1)
        job = client.get(f"/api/videos/{job['id']}").json()

    assert job["status"] == "done", job
    assert job["file_name"] == "My_Song_1_chords.mov"
    download = client.get(f"/api/videos/{job['id']}/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "video/quicktime"
    assert len(download.content) == job["size_bytes"]


def test_video_api_rejects_bad_options_and_unknown_jobs():
    client = TestClient(app)
    midi = build_midi(chord_events([60], 0, 1))
    response = client.post(
        "/api/videos", files={"file": ("a.mid", midi, "audio/midi")}, data={"kind": "spectrum", "fps": 29}
    )
    assert response.status_code == 400
    assert client.get("/api/videos/does-not-exist").status_code == 404
