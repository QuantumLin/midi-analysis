import mido

from app.analysis.bingo import CARD, FIELDS, FREE, LINES, BingoContext, play_bingo
from app.analysis.chords import detect_chords
from app.analysis.harmony import analyze_harmony
from app.analysis.key import detect_keys
from app.analysis.motifs import find_motifs
from app.midi.parser import parse_midi
from app.video.labels import BINGO_LABELS, bingo_banner
from tests.midi_factory import build_midi, chord_events

# Times in beats; at 120 BPM one beat is 0.5 s.


def context_of(events) -> BingoContext:
    midi = parse_midi(build_midi(events))
    chords = detect_chords(midi)
    keys = detect_keys(midi)
    return BingoContext(midi, chords, keys, analyze_harmony(chords, keys).progressions, find_motifs(midi))


def detect(field: str, events) -> float | None:
    return FIELDS[field](context_of(events))


def test_note_based_fields():
    assert detect("octave", chord_events([48, 52], 0, 1) + chord_events([48, 60], 4, 1)) == 2.0
    assert detect("deep_bass", chord_events([60], 0, 1) + chord_events([30], 2, 1)) == 1.0
    assert detect("high_notes", chord_events([90], 6, 1)) == 3.0
    assert detect("big_chord", chord_events([48, 52, 55, 60, 64, 67], 1, 1)) == 0.5
    loud = chord_events([60], 0, 1) + chord_events([64], 2, 1, velocity=120)
    assert detect("fortissimo", loud) == 1.0
    assert detect("pianissimo", loud) is None


def test_fast_run_and_pause():
    run = []
    for k in range(6):
        run += chord_events([60 + k], k * 0.2, 0.15)  # 0.1 s apart
    assert detect("fast_run", run) == 0.5
    assert detect("fast_run", chord_events([60], 0, 0.5) + chord_events([62], 1, 0.5)) is None
    gap = chord_events([60], 0, 1) + chord_events([62], 6, 1)  # silent from 0.5 s to 3 s
    assert detect("pause", gap) == 1.5


def test_chord_based_fields():
    events = chord_events([60, 64, 67], 0, 2) + chord_events([55, 59, 62, 65], 2, 2)  # C, G7
    assert detect("seventh_chord", events) == 1.0
    assert detect("progression", events) is None


def test_lines_complete_when_all_their_fields_are_ticked():
    events = chord_events([48, 60], 0, 1)  # octave at 0 s
    events += chord_events([30], 2, 1)  # deep bass at 1 s
    events += chord_events([55, 59, 62, 65], 4, 1)  # G7: seventh chord at 2 s
    card = play_bingo(context_of(events), card=("octave", "deep_bass", "seventh_chord", *[FREE] * 6))
    assert [f.time for f in card.fields[:3]] == [0.0, 1.0, 2.0]
    assert card.ticked_at(1.5)[:3] == (True, True, False)
    first = card.lines[0]
    assert first.time == 0.0 and first.cells in LINES  # a line of free fields is complete at once
    top_row = next(line for line in card.lines if line.cells == (0, 1, 2))
    assert top_row.time == 2.0
    assert card.lines_at(1.5) == [line for line in card.lines if line.time <= 1.5]


def test_every_field_on_the_card_exists_and_has_labels():
    assert len(CARD) == 9 and len(LINES) == 8
    for field in CARD:
        assert field == FREE or field in FIELDS
        assert set(BINGO_LABELS[field]) == {"de", "en"}


def test_empty_piece_ticks_nothing():
    card = play_bingo(context_of([(0, mido.MetaMessage("text", text="x"))]))
    assert all(f.time is None for f in card.fields) and card.lines == []


def test_banner_text():
    assert bingo_banner(1, "de") == "Bingo!"
    assert bingo_banner(3, "en") == "3× Bingo!"
