import pytest

from app.analysis.timeline import compute_timeline
from app.midi.models import MidiData
from app.midi.parser import parse_midi
from tests.midi_factory import build_midi, chord_events


def test_velocity_per_bin():
    # 0-1 s: one note at velocity 100; 1-2 s: silence; 2-3 s: two notes at 40 and 60.
    events = chord_events([69], start=0, length=2, velocity=100)
    events += chord_events([57], start=4, length=2, velocity=40)
    events += chord_events([81], start=4, length=2, velocity=60)
    timeline = compute_timeline(parse_midi(build_midi(events)), max_points=3)

    assert timeline.step_seconds == pytest.approx(1.0)
    first, silent, last = timeline.points
    assert (first.velocity, first.active_notes) == (100, 1)
    assert (silent.velocity, silent.active_notes) == (0, 0)
    assert (last.velocity, last.active_notes) == (50, 2)


def test_point_count_is_capped():
    events = chord_events([60], start=0, length=2000)  # 1000 s
    timeline = compute_timeline(parse_midi(build_midi(events)), max_points=500)
    assert len(timeline.points) == 500


def test_empty_file_gives_empty_timeline():
    assert compute_timeline(MidiData()).points == []
