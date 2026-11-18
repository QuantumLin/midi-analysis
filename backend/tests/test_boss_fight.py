import numpy as np

from app.analysis.boss_fight import BOSS_SECONDS, FACTORS, BossFight, find_boss_fight
from app.midi.parser import parse_midi
from tests.midi_factory import build_midi, chord_events

# Times in beats; at 120 BPM one beat is 0.5 s.


def calm(start: float, beats: float):
    """One note per beat (2 notes/s)."""
    events = []
    for k in range(int(beats)):
        events += chord_events([60 + (k % 3) * 2], start + k, 0.9)
    return events


def storm(start: float, beats: float):
    """Eight notes per beat (16 notes/s)."""
    events = []
    for k in range(int(beats * 8)):
        events += chord_events([72 + (k % 5)], start + k / 8, 0.1)
    return events


def boss_of(events) -> BossFight | None:
    return find_boss_fight(parse_midi(build_midi(events)))


def test_the_fastest_passage_is_the_boss():
    boss = boss_of(calm(0, 40) + storm(40, 16) + calm(56, 40))  # storm at 20-28 s
    assert boss is not None
    assert boss.factor == "speed"
    assert abs(boss.start - 20) <= 1.5 and boss.end - boss.start == BOSS_SECONDS
    assert boss.difficulty > 3


def test_big_chords_make_a_chord_boss():
    events = calm(0, 30)
    for k in range(16):  # 8-note chords every beat at 15-23 s
        events += chord_events([36, 43, 48, 52, 55, 60, 64, 67], 30 + k, 0.9)
    events += calm(46, 30)
    boss = boss_of(events)
    assert boss.factor == "chords"
    assert 13 <= boss.start <= 17


def test_health_drops_with_every_hit():
    boss = BossFight(10.0, 18.0, "speed", 7.0, np.array([10.0, 11.0, 12.0, 13.0]))
    assert boss.health_at(9.0) == 1.0
    assert boss.health_at(10.5) == 0.75
    assert boss.health_at(13.0) == 0.0


def test_short_or_empty_pieces_have_no_boss():
    assert boss_of(storm(0, 8)) is None  # 4 s
    assert boss_of([]) is None


def test_factor_weights_add_up_to_one():
    assert abs(sum(f.weight for f in FACTORS) - 1.0) < 1e-9
