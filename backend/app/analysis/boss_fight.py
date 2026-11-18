"""Boss fight: the hardest passage of the piece becomes the "final boss".

A difficulty score (0-10) is computed for every moment from several factors (speed,
leaps, chord size). The window of BOSS_SECONDS with the highest mean score is the boss.
Every note struck inside it is a hit; the boss's health drops with each one until it is
defeated at the end of the passage. The factor that contributes most names the boss
("The Note Storm" for fast passages ...).

To add a factor, append a DifficultyFactor to FACTORS (and a boss name to
app/video/labels.py BOSS_NAMES).
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from app.midi.models import MidiData

FRAME_SECONDS = 0.5
WINDOW_SECONDS = 1.0  # each factor looks at the last second
SMOOTHING_SECONDS = 2.0
BOSS_SECONDS = 8.0
MIN_PIECE_SECONDS = 10.0  # shorter pieces have no boss
GROUP_SECONDS = 0.04  # notes starting this close together are one strike


@dataclass(frozen=True, slots=True)
class Strikes:
    """Notes grouped into strikes (struck together), as numpy arrays."""

    starts: np.ndarray  # start time of each strike
    sizes: np.ndarray  # notes per strike
    centers: np.ndarray  # mean pitch per strike

    @staticmethod
    def of(midi: MidiData) -> "Strikes":
        groups: list[tuple[float, list[int]]] = []  # (start, pitches)
        for note in sorted(midi.notes, key=lambda n: n.start):
            if groups and note.start - groups[-1][0] <= GROUP_SECONDS:
                groups[-1][1].append(note.pitch)
            else:
                groups.append((note.start, [note.pitch]))
        return Strikes(
            starts=np.array([start for start, _ in groups], dtype=float),
            sizes=np.array([len(pitches) for _, pitches in groups], dtype=float),
            centers=np.array([np.mean(pitches) for _, pitches in groups], dtype=float),
        )

    def in_window(self, time: float) -> slice:
        """Strikes within (time - WINDOW_SECONDS, time]."""
        low = np.searchsorted(self.starts, time - WINDOW_SECONDS, side="right")
        high = np.searchsorted(self.starts, time, side="right")
        return slice(low, high)


def _speed(strikes: Strikes, times: np.ndarray) -> np.ndarray:
    """Strikes per second (a chord counts once: speed is how fast the hands move)."""
    return np.array([len(strikes.starts[strikes.in_window(t)]) for t in times], dtype=float)


def _leaps(strikes: Strikes, times: np.ndarray) -> np.ndarray:
    """Mean jump (semitones) between consecutive strikes."""
    jumps = np.abs(np.diff(strikes.centers, prepend=strikes.centers[:1]))
    values = []
    for t in times:
        window = strikes.in_window(t)
        values.append(jumps[window].mean() if window.stop > window.start else 0.0)
    return np.array(values)


def _chord_size(strikes: Strikes, times: np.ndarray) -> np.ndarray:
    """Most notes struck at once."""
    return np.array([strikes.sizes[strikes.in_window(t)].max(initial=0) for t in times])


@dataclass(frozen=True, slots=True)
class DifficultyFactor:
    id: str
    weight: float  # weights add up to 1
    full_scale: float  # raw value that counts as maximally hard
    measure: Callable[[Strikes, np.ndarray], np.ndarray]


FACTORS: tuple[DifficultyFactor, ...] = (
    DifficultyFactor("speed", 0.5, 12.0, _speed),
    DifficultyFactor("leaps", 0.25, 12.0, _leaps),
    DifficultyFactor("chords", 0.25, 8.0, _chord_size),
)


@dataclass(frozen=True, slots=True)
class BossFight:
    start: float
    end: float
    factor: str  # id of the factor contributing most: names the boss
    difficulty: float  # mean score in the passage, 0-10
    hits: np.ndarray  # note start times inside the passage (sorted)

    def health_at(self, time: float) -> float:
        """1.0 = full health, 0.0 = defeated."""
        if len(self.hits) == 0:
            return 1.0 if time < self.end else 0.0
        return 1.0 - np.searchsorted(self.hits, time, side="right") / len(self.hits)


def difficulty_curve(midi: MidiData) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """(times, {factor id: weighted contribution 0-10 per time}), smoothed."""
    times = np.arange(0.0, midi.duration, FRAME_SECONDS)
    strikes = Strikes.of(midi)
    width = max(1, round(SMOOTHING_SECONDS / FRAME_SECONDS))
    kernel = np.ones(width) / width
    contributions = {}
    for factor in FACTORS:
        raw = factor.measure(strikes, times) if len(strikes.starts) else np.zeros(len(times))
        scaled = 10 * factor.weight * np.clip(raw / factor.full_scale, 0, 1)
        contributions[factor.id] = np.convolve(scaled, kernel, mode="same")
    return times, contributions


def find_boss_fight(midi: MidiData) -> BossFight | None:
    if not midi.notes or midi.duration < MIN_PIECE_SECONDS:
        return None
    times, contributions = difficulty_curve(midi)
    total = sum(contributions.values())
    window = round(BOSS_SECONDS / FRAME_SECONDS)
    if len(total) < window:
        return None
    means = np.convolve(total, np.ones(window) / window, mode="valid")  # mean of [i, i + window)
    first = int(np.argmax(means))
    start, end = float(times[first]), float(times[first] + BOSS_SECONDS)
    passage = slice(first, first + window)
    factor = max(contributions, key=lambda f: contributions[f][passage].mean())
    onsets = np.sort(np.array([n.start for n in midi.notes]))
    hits = onsets[(onsets >= start) & (onsets < end)]
    return BossFight(start, end, factor, round(float(means[first]), 1), hits)
