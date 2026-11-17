import numpy as np
import pytest

from app.analysis.spectrum import MAX_DB, MIN_DB, HEADROOM_DB, compute_spectrum, quantize
from app.midi.models import MidiData
from app.midi.parser import parse_midi
from app.midi.pitch import pitch_to_frequency
from tests.midi_factory import build_midi, chord_events

FPS = 20
BINS = 512


def level_at(spectrum, frame: int, hz: float) -> float:
    return float(np.interp(np.log(hz), np.log(spectrum.frequencies), spectrum.levels_db[frame]))


def test_frequency_of_a4_is_440():
    assert pitch_to_frequency(69) == pytest.approx(440.0)
    assert pitch_to_frequency(81) == pytest.approx(880.0)


def test_note_shows_fundamental_and_harmonics():
    # A3 (220 Hz) from 0 to 1 s.
    spectrum = compute_spectrum(parse_midi(build_midi(chord_events([57], 0, 2))), FPS, BINS)
    frame = 5  # 0.25 s

    peak_bin = int(np.argmax(spectrum.levels_db[frame]))
    assert spectrum.frequencies[peak_bin] == pytest.approx(220, rel=0.03)
    # The attack (frame 0) is the loudest moment and is normalised to the headroom; it then decays.
    assert spectrum.levels_db.max() == pytest.approx(MAX_DB - HEADROOM_DB, abs=0.01)
    assert spectrum.levels_db[frame].max() < MAX_DB - HEADROOM_DB
    # Harmonics are present but quieter than the fundamental; between partials it is quieter still.
    fundamental, second, third = (level_at(spectrum, frame, hz) for hz in (220, 440, 660))
    assert fundamental > second > third > MIN_DB + 10
    assert level_at(spectrum, frame, 330) < third - 10
    # Nothing far below the fundamental.
    assert level_at(spectrum, frame, 50) == pytest.approx(MIN_DB)


def test_level_falls_after_note_end_with_ballistics():
    spectrum = compute_spectrum(parse_midi(build_midi(chord_events([57], 0, 2) + chord_events([57], 8, 0.1))), FPS, BINS)
    # The note ends at 1.0 s; compare 0.95 s with 1.25 s.
    during = level_at(spectrum, 19, 220)
    after = level_at(spectrum, 25, 220)
    assert after < during - 5
    # Ballistics limit the fall to 36 dB/s: at most ~10.8 dB in 0.3 s.
    assert after >= during - 36 * 0.3 - 0.5


def test_frame_count_matches_duration():
    spectrum = compute_spectrum(parse_midi(build_midi(chord_events([60], 0, 4))), FPS, BINS)
    assert spectrum.levels_db.shape == (41, BINS)  # 2 s at 20 fps, frames 0..40


def test_silence_gives_floor_level():
    spectrum = compute_spectrum(MidiData(duration=1.0), FPS, BINS)
    assert np.all(spectrum.levels_db == MIN_DB)


def test_quantize_maps_range_to_bytes():
    assert quantize(np.array([MIN_DB, MAX_DB, -100.0])).tolist() == [0, 255, 0]
