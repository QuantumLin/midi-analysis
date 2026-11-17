"""Velocity curve over the duration of a piece.

The piece is split into equally sized time bins. For every bin we report the
mean velocity of the notes sounding in it and how many notes sound.
(The frequency content over time is covered by `spectrum.py`.)
"""

import math
from dataclasses import dataclass

from app.midi.models import MidiData

MAX_POINTS = 1000
MIN_STEP_SECONDS = 0.05


@dataclass(frozen=True, slots=True)
class TimelinePoint:
    time: float  # bin start, seconds
    velocity: float  # mean velocity of sounding notes, 0 when silent
    active_notes: int


@dataclass(frozen=True, slots=True)
class Timeline:
    step_seconds: float
    points: list[TimelinePoint]


def compute_timeline(midi: MidiData, max_points: int = MAX_POINTS) -> Timeline:
    if midi.duration <= 0:
        return Timeline(step_seconds=MIN_STEP_SECONDS, points=[])

    step = max(MIN_STEP_SECONDS, midi.duration / max_points)
    bin_count = math.ceil(midi.duration / step)
    velocity_sum = [0.0] * bin_count
    counts = [0] * bin_count

    for note in midi.notes:
        first = min(int(note.start / step), bin_count - 1)
        last = min(math.ceil(note.end / step) - 1, bin_count - 1)
        for i in range(first, max(first, last) + 1):
            velocity_sum[i] += note.velocity
            counts[i] += 1

    points = [
        TimelinePoint(
            time=round(i * step, 4),
            velocity=round(velocity_sum[i] / counts[i], 2) if counts[i] else 0.0,
            active_notes=counts[i],
        )
        for i in range(bin_count)
    ]
    return Timeline(step_seconds=round(step, 4), points=points)
