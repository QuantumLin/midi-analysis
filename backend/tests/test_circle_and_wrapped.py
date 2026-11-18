import pytest

from app.analysis.chords import ChordMatch, ChordSegment
from app.analysis.circle_of_fifths import CirclePosition, circle_path, circle_position
from app.midi.parser import parse_midi
from app.video.wrapped import CARDS, MAX_CARDS, collect_facts, wrapped_cards
from tests.midi_factory import build_midi, chord_events

# --- circle of fifths --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("root", "quality", "ring", "index", "name"),
    [
        (0, "", "major", 0, "C"),
        (7, "7", "major", 1, "G"),
        (5, "maj7", "major", 11, "F"),
        (10, "", "major", 10, "B♭"),
        (9, "m", "minor", 0, "a"),  # A minor sits next to C major
        (2, "m7", "minor", 11, "d"),
        (11, "dim", "minor", 2, "b"),
        (6, "m", "minor", 3, "f♯"),
    ],
)
def test_circle_positions(root, quality, ring, index, name):
    position = circle_position(ChordMatch(root, quality, root))
    assert position == CirclePosition(ring, index)
    assert position.name == name


def test_circle_path_follows_the_chords():
    chords = [ChordSegment(i, i + 1, ChordMatch(r, q, r), ()) for i, (r, q) in enumerate([(0, ""), (9, "m"), (7, "")])]
    assert [(s.start, s.position.name) for s in circle_path(chords)] == [(0, "C"), (1, "a"), (2, "G")]


# --- Song Wrapped ------------------------------------------------------------------------------


def song():
    events = []
    for k in range(40):  # C - Am - F - G, 20 s
        chord = [[48, 60, 64, 67], [45, 57, 60, 64], [41, 57, 60, 65], [43, 55, 59, 62]][k % 4]
        events += chord_events(chord, k, 0.9)
    return parse_midi(build_midi(events))


def test_wrapped_cards_in_both_languages():
    facts = collect_facts(song())
    de = {c.id: c for c in wrapped_cards(facts, "de")}
    en = {c.id: c for c in wrapped_cards(facts, "en")}
    assert set(de) == set(en)
    assert de["notes"].value == "160" and en["notes"].title == "Notes played"
    assert de["favourite_chord"].value == "C (10×)"
    assert de["key"].value == "C-Dur" and en["key"].value == "C major"
    assert de["range"].value == "F2 – G4"
    assert "boss" in de  # 20 s: long enough for a boss
    assert len(de) <= MAX_CARDS


def test_cards_without_data_are_left_out():
    empty = collect_facts(parse_midi(build_midi(chord_events([60], 0, 1))))
    ids = [c.id for c in wrapped_cards(empty, "en")]
    assert "notes" in ids and "boss" not in ids and "main_motif" not in ids


def test_every_card_has_a_unique_id():
    ids = [card_id for card_id, _ in CARDS]
    assert len(ids) == len(set(ids))
