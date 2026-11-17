from app.analysis.motifs import MIN_OCCURRENCES, MOTIF_NOTES, find_motifs
from app.midi.parser import parse_midi
from app.video.labels import motif_count, ordinal_en
from tests.midi_factory import build_midi, chord_events

# Times in beats; at 120 BPM one beat is 0.5 s.
THEME = [(67, 1), (69, 0.5), (72, 0.5), (71, 1), (67, 0.5), (64, 0.5), (65, 1), (62, 1)]  # (pitch, beats)


def phrase(notes: list[tuple[int, float]], start: float, transpose: int = 0):
    events, t = [], start
    for pitch, beats in notes:
        events += chord_events([pitch + transpose], t, beats * 0.9)
        t += beats
    return events, t


def song(*parts) -> list:
    """parts: lists of (pitch, beats) played one after another, a beat of rest in between."""
    events, t = [], 0.0
    for notes, transpose in parts:
        new, t = phrase(notes, t, transpose)
        events += new
        t += 1
    return events


FILLERS = [
    [(60, 0.5), (66, 1), (61, 0.5), (70, 2)],
    [(63, 1), (75, 0.5), (59, 1.5), (68, 1)],
    [(74, 2), (58, 0.5), (73, 1), (57, 0.5)],
]


def motifs_of(events):
    return find_motifs(parse_midi(build_midi(events)))


def test_finds_a_recurring_theme_also_transposed():
    events = song((THEME, 0), (FILLERS[0], 0), (THEME, 0), (FILLERS[1], 0), (THEME, 5), (FILLERS[2], 0))
    motifs = motifs_of(events)
    assert len(motifs) == 1
    motif = motifs[0]
    assert motif.label == "A"
    assert motif.length == len(THEME)  # extended from the minimum length to the whole theme
    assert [o.number for o in motif.occurrences] == [1, 2, 3]
    first = motif.occurrences[0]
    assert first.start == 0.0 and abs(first.end - 5.9 * 0.5) < 1e-6  # last note starts at beat 5, lasts 0.9


def test_accompaniment_below_the_melody_is_ignored():
    events = song((THEME, 0), (FILLERS[0], 0), (THEME, 0), (FILLERS[1], 0), (THEME, 0))
    events += chord_events([36, 43], 0, 40)  # long bass under everything
    assert motifs_of(events)[0].length == len(THEME)


def test_too_few_repetitions_or_no_shape_is_no_motif():
    assert MIN_OCCURRENCES == 3
    assert motifs_of(song((THEME, 0), (FILLERS[0], 0), (THEME, 0))) == []  # only twice
    scale = [(60 + step, 0.5) for step in (0, 2, 4, 5, 7, 9)]
    repeated_note = [(60, 0.5)] * MOTIF_NOTES
    assert motifs_of(song((scale, 0), (scale, 0), (scale, 0))) == []  # plain scale: no shape
    assert motifs_of(song((repeated_note, 0), (repeated_note, 0), (repeated_note, 0))) == []


def test_a_different_rhythm_is_a_different_motif():
    other_rhythm = [(p, 1.0 if b == 0.5 else 0.5) for p, b in THEME]
    events = song((THEME, 0), (FILLERS[0], 0), (other_rhythm, 0), (FILLERS[1], 0), (THEME, 0))
    assert motifs_of(events) == []


def test_count_texts():
    assert motif_count(6, "de") == "6. Mal"
    assert [ordinal_en(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22, 101)] == [
        "1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "101st"
    ]  # fmt: skip
