import mido
import pytest

from app.analysis.chords import detect_chords, identify_chord
from app.midi.parser import parse_midi
from tests.midi_factory import build_midi, chord_events


def chord_name(pitches):
    match = identify_chord(pitches)
    return match.name if match else None


@pytest.mark.parametrize(
    ("pitches", "expected"),
    [
        ([60, 64, 67], "C"),
        ([57, 60, 64], "Am"),
        ([55, 59, 62, 65], "G7"),
        ([60, 64, 67, 71], "Cmaj7"),
        ([62, 65, 69, 72], "Dm7"),
        ([59, 62, 65], "Bdim"),
        ([60, 64, 68], "Caug"),
        ([60, 65, 67], "Csus4"),
        ([59, 62, 65, 68], "Bdim7"),
        ([59, 62, 65, 69], "Bm7b5"),
        ([48, 60, 64, 67, 72], "C"),  # doubled notes across octaves
        ([52, 60, 67], "C/E"),  # first inversion
        ([60, 64, 67, 69], "C6"),  # same notes as Am7, the bass decides
        ([57, 60, 64, 67], "Am7"),
        ([40, 47], "E5"),
        ([60, 64, 70], "C7"),  # without fifth
    ],
)
def test_identify_chord(pitches, expected):
    assert chord_name(pitches) == expected


@pytest.mark.parametrize(
    ("pitches", "expected"),
    [
        ([48, 52, 55, 74], "Cadd9"),  # exact match beats "C plus extra tone"
        ([48, 52, 55, 73], "C"),  # C major with a foreign melody note (C#)
        ([48, 52, 55, 73, 78], "C"),  # two foreign tones
        ([45, 52, 57, 60, 70], "Am"),  # foreign A# over Am
        ([45, 52, 57, 60, 71, 77], "Amadd9"),  # B is read as the 9th, F stays foreign
        ([48, 52, 58], "C7"),  # missing fifth
    ],
)
def test_tolerates_extra_tones_and_missing_fifth(pitches, expected):
    assert chord_name(pitches) == expected


def test_too_many_foreign_tones_give_no_chord():
    assert identify_chord([60, 64, 67, 61, 63, 66]) is None  # C major + C#, D#, F#


@pytest.mark.parametrize("pitches", [[], [60], [60, 64], [60, 61, 62]])
def test_unknown_or_too_few_notes_give_no_chord(pitches):
    assert identify_chord(pitches) is None


def test_detects_progression_with_timing():
    progression = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62, 65]]
    events = []
    for i, pitches in enumerate(progression):
        events += chord_events(pitches, start=i * 2, length=2)
    chords = detect_chords(parse_midi(build_midi(events)))

    assert [c.chord.name for c in chords] == ["C", "Am", "F", "G7"]
    assert [c.start for c in chords] == pytest.approx([0.0, 1.0, 2.0, 3.0])
    assert [c.end for c in chords] == pytest.approx([1.0, 2.0, 3.0, 4.0])
    assert chords[0].note_names == ["C4", "E4", "G4"]


def test_repeated_chord_is_merged_and_short_overlaps_ignored():
    events = chord_events([60, 64, 67], start=0, length=1)
    events += chord_events([60, 64, 67], start=1, length=1)
    # A note that briefly overlaps the chord change (shorter than the minimum segment length).
    events += chord_events([62], start=0.95, length=0.1)
    chords = detect_chords(parse_midi(build_midi(events)))

    assert [c.chord.name for c in chords] == ["C"]
    assert chords[0].start == pytest.approx(0.0)
    assert chords[0].end == pytest.approx(1.0)


def test_sustain_pedal_never_released_does_not_blur_chords():
    # Pedal goes down at the start and is never released (seen in real-world files).
    progression = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
    events = [(0, mido.Message("control_change", control=64, value=127))]
    for i, pitches in enumerate(progression):
        events += chord_events(pitches, start=i * 2, length=1.8)
    chords = detect_chords(parse_midi(build_midi(events)))
    assert [c.chord.name for c in chords] == ["C", "Am", "F", "G"]


def test_chord_arpeggiated_into_pedal_is_detected():
    events = [(0, mido.Message("control_change", control=64, value=127))]
    for i, pitch in enumerate([45, 57, 60, 64]):  # A2 A3 C4 E4, each key released quickly
        events += chord_events([pitch], start=i * 0.5, length=0.4)
    events.append((6, mido.Message("control_change", control=64, value=0)))
    chords = detect_chords(parse_midi(build_midi(events)))
    assert [c.chord.name for c in chords] == ["Am"]
    assert chords[0].end == pytest.approx(3.0)


def test_percussion_is_ignored():
    events = chord_events([60, 64, 67], 0, 2) + chord_events([36, 38, 42], 0, 2, channel=9)
    chords = detect_chords(parse_midi(build_midi(events)))
    assert [c.chord.name for c in chords] == ["C"]
