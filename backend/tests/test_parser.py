import mido
import pytest

from app.midi.parser import MidiParseError, parse_midi
from tests.midi_factory import build_midi, chord_events


def test_converts_ticks_to_seconds_using_tempo():
    data = build_midi(chord_events([60], start=1, length=2))  # 120 BPM: beat = 0.5 s
    midi = parse_midi(data)

    assert len(midi.notes) == 1
    note = midi.notes[0]
    assert note.pitch == 60
    assert note.velocity == 80
    assert note.start == pytest.approx(0.5)
    assert note.end == pytest.approx(1.5)
    assert midi.duration == pytest.approx(1.5)


def test_note_on_with_zero_velocity_ends_note():
    data = build_midi(
        [
            (0, mido.Message("note_on", note=64, velocity=90)),
            (1, mido.Message("note_on", note=64, velocity=0)),
        ]
    )
    (note,) = parse_midi(data).notes
    assert note.end == pytest.approx(0.5)


def test_sustain_pedal_extends_released_notes():
    data = build_midi(
        [
            (0, mido.Message("control_change", control=64, value=127)),
            *chord_events([60], start=0, length=1),
            (4, mido.Message("control_change", control=64, value=0)),
        ]
    )
    (note,) = parse_midi(data).notes
    assert note.end == pytest.approx(2.0)  # sound lasts until pedal-up
    assert note.key_end == pytest.approx(0.5)  # key was released after one beat


def test_percussion_is_kept_separate():
    data = build_midi(chord_events([60], 0, 1) + chord_events([36], 0, 1, channel=9))
    midi = parse_midi(data)
    assert [n.pitch for n in midi.notes] == [60]
    assert [n.pitch for n in midi.percussion_notes] == [36]


def test_invalid_data_raises_parse_error():
    with pytest.raises(MidiParseError):
        parse_midi(b"definitely not a midi file")
