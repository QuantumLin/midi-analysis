import pytest

from app.analysis.chords import ChordMatch, ChordSegment
from app.analysis.harmony import (
    PROGRESSION_HIGHLIGHT_SECONDS,
    HarmonyAnalysis,
    find_progressions,
    roman_numeral,
    split_numeral,
)
from app.analysis.key import Key

C_MAJOR = Key(0, "major")
A_MINOR = Key(9, "minor")
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def chord(name: str) -> ChordMatch:
    root = name[:2] if len(name) > 1 and name[1] in "#b" else name[:1]
    return ChordMatch(NOTE[root], name[len(root) :], NOTE[root])


def segments(names: str, seconds: float = 1.0) -> list[ChordSegment]:
    return [ChordSegment(i * seconds, (i + 1) * seconds, chord(n), ()) for i, n in enumerate(names.split())]


@pytest.mark.parametrize(
    ("name", "key", "numeral"),
    [
        ("C", C_MAJOR, "I"),
        ("Am", C_MAJOR, "vi"),
        ("G7", C_MAJOR, "V7"),
        ("Fmaj7", C_MAJOR, "IVmaj7"),
        ("Dm7", C_MAJOR, "ii7"),
        ("Bdim", C_MAJOR, "vii°"),
        ("Bm7b5", C_MAJOR, "viiø7"),
        ("Bb", C_MAJOR, "♭VII"),
        ("Ab", C_MAJOR, "♭VI"),
        ("Am", A_MINOR, "i"),
        ("G", A_MINOR, "VII"),
        ("E7", A_MINOR, "V7"),
        ("F", A_MINOR, "VI"),
        ("C", A_MINOR, "III"),
        ("Bdim", A_MINOR, "ii°"),
        ("Caug", C_MAJOR, "I+"),
    ],
)
def test_roman_numerals(name, key, numeral):
    assert roman_numeral(chord(name), key) == numeral


def test_chords_without_third_follow_the_key():
    assert roman_numeral(chord("A5"), A_MINOR) == "i"  # power chord on the minor tonic
    assert roman_numeral(chord("C5"), C_MAJOR) == "I"
    assert roman_numeral(chord("Dsus4"), C_MAJOR) == "iisus4"


def test_split_numeral():
    assert split_numeral("♭VIImaj7") == ("♭VII", "maj7")
    assert split_numeral("vii°") == ("vii", "°")
    assert split_numeral("I") == ("I", "")


def ids(hits):
    return [(h.id, h.count) for h in hits]


def test_pop_formula_and_its_repetitions():
    hits = find_progressions(segments("C G Am F C G Am F C G"))
    assert ids(hits) == [("pop", 1), ("pop", 2)]
    assert hits[0].time == 3.0  # complete with its 4th chord
    assert hits[1].time == 7.0


def test_loops_are_found_from_any_chord_and_in_any_key():
    assert ids(find_progressions(segments("Am F C G"))) == [("pop", 1)]  # vi-IV-I-V
    assert ids(find_progressions(segments("E B C#m A"))) == [("pop", 1)]  # in E major


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        ("C Am F G", "fifties"),
        ("Am G F E", "andalusian"),
        ("Dm7 G7 Cmaj7", "two_five_one"),
        ("Bdim E Am", "two_five_one"),
        ("F G Em Am", "royal_road"),
        ("D A Bm F#m G D", "canon"),
        ("Em Am Dm G C", "circle_of_fifths"),
    ],
)
def test_known_progressions(names, expected):
    assert [h.id for h in find_progressions(segments(names))] == [expected]


def test_passing_and_ambiguous_chords_are_ignored():
    # C7 is the same step as C; Gsus4 (ambiguous) and a 0.1 s passing chord are skipped.
    chords = segments("C C7 Gsus4 G Am F")
    chords.insert(3, ChordSegment(2.95, 3.05, chord("Eb"), ()))
    assert ids(find_progressions(chords)) == [("pop", 1)]


def test_nothing_found_in_random_chords():
    assert find_progressions(segments("C E F# Bb D")) == []


def test_highlight_ends_at_the_next_hit():
    hits = find_progressions(segments("C G Am F C G Am F", seconds=0.5))
    assert hits[0].end == hits[1].time
    assert hits[1].end == hits[1].time + PROGRESSION_HIGHLIGHT_SECONDS


def test_chain_collapses_repeats_and_drops_suffixes():
    chords = segments("C C7 G Am Am7 F")
    numerals = [roman_numeral(c.chord, C_MAJOR) for c in chords]
    harmony = HarmonyAnalysis(chords, numerals, [C_MAJOR] * len(chords), [])
    assert harmony.chain_before(5) == ("I", "V", "vi", "IV")
    assert harmony.chain_before(1) == ("I",)
