import mido

from app.analysis.achievements import (
    DISPLAY_SECONDS,
    MAX_DELAY_SECONDS,
    Achievement,
    find_achievements,
    schedule,
)
from app.midi.parser import parse_midi
from tests.midi_factory import build_midi, chord_events

# Times in the factory are beats; at 120 BPM one beat is 0.5 s.


def achievements(events) -> list[Achievement]:
    return find_achievements(parse_midi(build_midi(events)))


def kinds(found: list[Achievement]) -> list[tuple[str, int]]:
    return [(a.kind, a.value) for a in found]


def sequence(pitches: list[int], start: float, step_beats: float, velocity: int = 80):
    events = []
    for k, pitch in enumerate(pitches):
        events += chord_events([pitch], start + k * step_beats, step_beats * 0.9, velocity)
    return events


def test_big_chord_first_and_new_records_only():
    events = chord_events([48, 52, 55, 60, 64, 67], 0, 1)  # 6 notes
    events += chord_events([48, 52, 55, 60, 64, 67], 10, 1)  # same size again: nothing new
    events += chord_events([36, 43, 48, 52, 55, 60, 64, 67], 20, 1)  # 8 notes
    assert kinds(achievements(events)) == [("big_chord", 6), ("big_chord", 8)]


def test_fast_run():
    scale = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79]
    found = achievements(sequence(scale, 0, 0.2))  # 0.1 s per note
    assert kinds(found) == [("run", 12)]
    assert abs(found[0].seconds - 1.1) < 0.01


def test_slow_or_jumping_lines_are_no_run():
    assert achievements(sequence([60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79], 0, 1)) == []  # too slow
    assert achievements(sequence([60, 72, 61, 73, 62, 74, 63, 75, 64, 76, 65, 77], 0, 0.2)) == []  # zigzag


def test_trill():
    found = achievements(sequence([60, 62] * 6, 0, 0.2))
    assert kinds(found) == [("trill", 12)]


def test_leap_needs_free_hands():
    leap = chord_events([36], 0, 0.5) + chord_events([72], 0.6, 0.5)  # released, then 3 octaves up
    assert kinds(achievements(leap)) == [("leap", 36)]
    held = chord_events([36], 0, 2) + chord_events([72], 0.6, 0.5)  # bass still held: two hands
    assert achievements(held) == []


def test_fortissimo_only_when_rare():
    quiet = sequence([60, 62, 64, 65] * 10, 0, 2)
    loud_moment = chord_events([60, 64, 67], 100, 1, velocity=120)
    assert kinds(achievements(quiet + loud_moment)) == [("fortissimo", 120)]
    always_loud = sequence([60, 62, 64, 65] * 5, 0, 2, velocity=120)
    assert achievements(always_loud) == []


def test_extremes_range_and_milestones():
    events = chord_events([24], 8, 1) + chord_events([100], 16, 1)  # C1, then E7: 76 semitones
    found = kinds(achievements(events))
    assert ("low", 24) in found and ("high", 100) in found
    assert ("range", 6) in found and ("range", 5) not in found  # both crossed at once: only 6

    many = sequence([60, 64, 67, 72] * 130, 0, 0.5)  # 520 notes
    assert ("milestone", 500) in kinds(achievements(many))


def test_schedule_never_overlaps_and_drops_late_pop_ups():
    raw = [
        Achievement(10.0, "milestone", 500),
        Achievement(10.5, "big_chord", 6),  # waits for the first one
        Achievement(11.0, "leap", 30),  # would come far too late
    ]
    shown = schedule(raw)
    assert kinds(shown) == [("milestone", 500), ("big_chord", 6)]
    assert shown[1].time >= shown[0].end
    assert shown[1].time - 10.5 <= MAX_DELAY_SECONDS
    assert abs(shown[0].end - shown[0].time - DISPLAY_SECONDS) < 1e-9


def test_empty_file():
    assert find_achievements(parse_midi(build_midi([(0, mido.MetaMessage("text", text="x"))]))) == []
