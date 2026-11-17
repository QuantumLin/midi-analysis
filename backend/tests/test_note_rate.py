import numpy as np

from app.analysis.keyboard_activity import KEY_COUNT, KeyboardActivity
from app.analysis.note_rate import find_records, note_rate, summarize
from app.midi.parser import parse_midi
from tests.midi_factory import build_midi, chord_events


def run(pitch: int, start_beat: float, count: int, step_beats: float) -> list:
    events = []
    for i in range(count):
        events += chord_events([pitch], start=start_beat + i * step_beats, length=step_beats * 0.9)
    return events


def test_rate_counts_presses_in_the_last_second():
    # 8 presses within the first second (16th notes at 120 BPM), then 4 per second.
    midi = parse_midi(build_midi(run(60, 0, 8, 0.25) + run(62, 2, 8, 0.5)))
    rate = note_rate(midi)
    assert rate.rate_at(np.array([0.99]))[0] == 8
    assert rate.rate_at(np.array([1.99]))[0] == 4
    assert rate.total_at(np.array([0.0, 0.99, 10.0])).tolist() == [1, 8, 16]


def test_chord_notes_count_individually():
    rate = note_rate(parse_midi(build_midi(chord_events([60, 64, 67, 72], 0, 1))))
    assert rate.rate_at(np.array([0.1]))[0] == 4


def test_summary_peak():
    midi = parse_midi(build_midi(run(60, 0, 4, 0.5) + run(64, 8, 12, 0.125)))  # fast run at 4 s
    summary = summarize(note_rate(midi), midi.duration, fps=20)
    assert summary.peak_value == 12
    assert 4.5 <= summary.peak_time <= 5.5
    assert len(summary.values) == int(midi.duration * 20) + 1


def test_records_ignore_warmup_and_merge_quick_succession():
    times = np.arange(0, 20, 0.5)
    values = np.zeros_like(times, dtype=int)
    values[times < 5] = 6  # warm-up best: 6
    values[(times >= 8) & (times < 9)] = [7, 9]  # climbs within 0.5 s -> one record (9)
    values[times == 15] = 12  # later, separate record
    records = find_records(times, values)
    assert [(r.time, r.value) for r in records] == [(8.5, 9), (15.0, 12)]


def test_keyboard_activity_counts_and_held_keys():
    midi = parse_midi(build_midi(chord_events([21, 60], 0, 2) + chord_events([60], 4, 2) + chord_events([120], 4, 1)))
    activity = KeyboardActivity(midi)

    counts = activity.press_counts(0.5)
    assert counts.shape == (KEY_COUNT,)
    assert counts[0] == 1 and counts[60 - 21] == 1 and counts.sum() == 2
    assert activity.press_counts(10).tolist()[60 - 21] == 2
    assert activity.press_counts(10)[-1] == 1  # out-of-range note clamped to C8

    held = activity.held(0.5)
    assert held[0] and held[60 - 21] and held.sum() == 2
    assert not activity.held(1.5).any()  # released after one second
