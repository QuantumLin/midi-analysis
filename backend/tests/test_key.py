import numpy as np
import pytest

from app.analysis.key import ALL_KEYS, Key, detect_keys, key_correlations
from app.midi.models import MidiData
from app.midi.parser import parse_midi
from tests.midi_factory import build_midi, chord_events

# I - IV - V - I in C major and in Eb major, one chord per bar (2 s at 120 BPM).
C_MAJOR_CADENCE = [[48, 60, 64, 67], [53, 60, 65, 69], [43, 59, 62, 67], [48, 60, 64, 67]]
EB_MAJOR_CADENCE = [[51, 63, 67, 70], [56, 63, 68, 72], [46, 62, 65, 70], [51, 63, 67, 70]]
A_MINOR_CADENCE = [[45, 57, 60, 64], [50, 57, 62, 65], [40, 56, 59, 64], [45, 57, 60, 64]]


def progression(chords: list[list[int]], repeats: int, start_beat: float = 0) -> list:
    events = []
    for i, pitches in enumerate(chords * repeats):
        events += chord_events(pitches, start=start_beat + i * 4, length=4)
    return events


def test_major_scale_histogram_correlates_best_with_its_key():
    c_major_scale = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], dtype=float)
    assert ALL_KEYS[int(np.argmax(key_correlations(c_major_scale)))] == Key(0, "major")


def test_detects_c_major_without_modulation():
    analysis = detect_keys(parse_midi(build_midi(progression(C_MAJOR_CADENCE, 3))))
    assert analysis.overall == Key(0, "major")
    assert [s.key for s in analysis.segments] == [Key(0, "major")]
    assert analysis.segments[0].start == 0.0 and analysis.segments[-1].end == pytest.approx(24.0)


def test_detects_a_minor():
    analysis = detect_keys(parse_midi(build_midi(progression(A_MINOR_CADENCE, 3))))
    assert analysis.overall == Key(9, "minor")


def test_detects_modulation_from_c_to_eb_major():
    events = progression(C_MAJOR_CADENCE, 3) + progression(EB_MAJOR_CADENCE, 3, start_beat=48)
    analysis = detect_keys(parse_midi(build_midi(events)))

    assert [s.key for s in analysis.segments] == [Key(0, "major"), Key(3, "major")]
    assert analysis.overall == Key(0, "major")  # equal time in both keys -> the home key
    change = analysis.segments[1].start
    assert 21 <= change <= 27  # the real change is at 24 s; the 8 s window blurs it a little
    assert analysis.key_at(5) == Key(0, "major") and analysis.key_at(40) == Key(3, "major")


def test_overall_key_is_where_the_piece_spends_most_time():
    events = progression(C_MAJOR_CADENCE, 1) + progression(EB_MAJOR_CADENCE, 4, start_beat=16)
    analysis = detect_keys(parse_midi(build_midi(events)))
    assert analysis.overall == Key(3, "major")


def test_empty_piece_has_no_key():
    analysis = detect_keys(MidiData())
    assert analysis.overall is None and analysis.segments == []


@pytest.mark.parametrize(
    ("key", "name", "flats"),
    [
        (Key(0, "major"), "C", False),
        (Key(2, "minor"), "D", True),  # d minor: Bb
        (Key(10, "major"), "Bb", True),
        (Key(6, "major"), "F#", False),
        (Key(1, "minor"), "C#", False),
        (Key(3, "minor"), "Eb", True),
        (Key(9, "minor"), "A", False),
    ],
)
def test_key_spelling(key, name, flats):
    assert key.tonic_name == name
    assert key.prefer_flats is flats
