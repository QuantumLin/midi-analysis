from app.analysis.sections import find_sections
from app.midi.parser import parse_midi
from app.video.labels import section_count, section_name
from tests.midi_factory import build_midi, chord_events

# Times in beats; at 120 BPM one beat is 0.5 s, so 24 beats are 12 s.
PART_A = [[48, 60, 64, 67], [43, 59, 62, 67], [45, 57, 60, 64], [41, 57, 60, 65]]  # C G Am F, middle register
PART_B = [[63, 75, 79, 82], [68, 80, 84, 87], [70, 82, 86, 89], [66, 78, 82, 85]]  # Eb Ab Bb F#: high, other key


def part(chords: list[list[int]], start: float, beats: float, step: float):
    events, t = [], start
    while t < start + beats:
        for chord in chords:
            events += chord_events(chord, t, step * 0.9)
            t += step
    return events


def sections_of(events):
    return find_sections(parse_midi(build_midi(events)))


def test_a_b_a_form():
    events = part(PART_A, 0, 24, 1) + part(PART_B, 24, 24, 0.5) + part(PART_A, 48, 24, 1)
    sections = sections_of(events)
    assert [(s.label, s.number) for s in sections] == [("A", 1), ("B", 1), ("A", 2)]
    assert abs(sections[1].start - 12) <= 1.5 and abs(sections[2].start - 24) <= 1.5
    assert sections[0].start == 0 and sections[-1].end == 36.0 - 0.05  # last note: beat 72 - 0.1 beats


def test_uniform_piece_is_one_section():
    sections = sections_of(part(PART_A, 0, 60, 1))
    assert [(s.label, s.number) for s in sections] == [("A", 1)]


def test_no_notes():
    assert sections_of([]) == []


def test_section_texts():
    assert section_name("B", "de") == "Teil B" and section_name("B", "en") == "Part B"
    assert section_count(1, "de") == "Neu" and section_count(3, "de") == "zum 3. Mal"
    assert section_count(2, "en") == "2nd time"
