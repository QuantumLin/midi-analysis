"""Key (tonality) detection over time, including modulations.

Method (Krumhansl-Schmuckler): the time each pitch class sounds within a window is
correlated with the Krumhansl-Kessler profiles of all 24 major/minor keys.
The window slides over the piece; a dynamic-programming pass (like Viterbi) then
picks the best key sequence with a penalty for every change, so short tonicisations
don't flicker but real modulations are reported.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np

from app.midi.models import MidiData, Note

Mode = Literal["major", "minor"]

# Krumhansl & Kessler (1982) probe-tone profiles, starting at the tonic.
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

WINDOW_SECONDS = 8.0  # centred on each sample
STEP_SECONDS = 0.5
SWITCH_PENALTY = 1.5  # in correlation units; ~3 s of clearly better fit are needed to switch
MAIN_KEY_TOLERANCE = 0.1  # keys with at least 90 % of the longest time tie for "main key"

# Spelling of each key's tonic (index = pitch class) and whether the key uses flats.
MAJOR_TONICS = ("C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
MINOR_TONICS = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B")
FLAT_MAJOR_KEYS = {1, 3, 5, 8, 10}  # Db Eb F Ab Bb
FLAT_MINOR_KEYS = {0, 2, 3, 5, 7, 10}  # c d eb f g bb


@dataclass(frozen=True, slots=True)
class Key:
    tonic: int  # pitch class 0-11
    mode: Mode

    @property
    def tonic_name(self) -> str:
        return (MAJOR_TONICS if self.mode == "major" else MINOR_TONICS)[self.tonic]

    @property
    def prefer_flats(self) -> bool:
        return self.tonic in (FLAT_MAJOR_KEYS if self.mode == "major" else FLAT_MINOR_KEYS)


@dataclass(frozen=True, slots=True)
class KeySegment:
    start: float
    end: float
    key: Key


@dataclass(frozen=True, slots=True)
class KeyAnalysis:
    overall: Key | None  # key of the whole piece
    segments: list[KeySegment]  # contiguous, covering the piece; empty without notes

    def key_at(self, time: float) -> Key | None:
        for segment in self.segments:
            if segment.start <= time < segment.end:
                return segment.key
        return self.segments[-1].key if self.segments and time >= self.segments[-1].end else self.overall

    def prefer_flats_at(self, time: float) -> bool:
        """Whether black keys are spelled as flats at `time` (e.g. Bb in d minor)."""
        key = self.key_at(time)
        return key.prefer_flats if key else False


ALL_KEYS: tuple[Key, ...] = tuple(Key(t, m) for m in ("major", "minor") for t in range(12))  # type: ignore[arg-type]
_PROFILES = np.array([np.roll(MAJOR_PROFILE if k.mode == "major" else MINOR_PROFILE, k.tonic) for k in ALL_KEYS])


def detect_keys(midi: MidiData) -> KeyAnalysis:
    if not midi.notes or midi.duration <= 0:
        return KeyAnalysis(overall=None, segments=[])

    notes = _NoteArrays(midi.notes)
    whole_piece_scores = key_correlations(notes.pitch_class_durations(0.0, midi.duration))

    times = np.arange(0.0, midi.duration, STEP_SECONDS)
    scores = np.array(
        [
            key_correlations(notes.pitch_class_durations(t - WINDOW_SECONDS / 2, t + WINDOW_SECONDS / 2))
            for t in times
        ]
    )
    path = _best_path(scores, start_bias=int(np.argmax(whole_piece_scores)))
    segments = _segments(path, times, midi.duration)
    return KeyAnalysis(overall=_main_key(segments), segments=segments)


def _main_key(segments: list["KeySegment"]) -> Key:
    """The key the piece spends the most time in. Keys within MAIN_KEY_TOLERANCE of that
    count as a tie, which the earliest one (the home key) wins.
    (Correlating the whole piece at once would blend e.g. C major + Eb major into c minor.)"""
    time_in_key: dict[Key, float] = {}
    for segment in segments:  # dicts keep insertion order = order of first appearance
        time_in_key[segment.key] = time_in_key.get(segment.key, 0.0) + segment.end - segment.start
    longest = max(time_in_key.values())
    return next(k for k, t in time_in_key.items() if t >= longest * (1 - MAIN_KEY_TOLERANCE))


def key_correlations(durations: np.ndarray) -> np.ndarray:
    """Pearson correlation of a pitch-class histogram with each of the 24 key profiles.
    A silent window correlates with nothing (all zeros)."""
    if durations.sum() <= 0 or np.allclose(durations, durations[0]):
        return np.zeros(len(ALL_KEYS))
    x = durations - durations.mean()
    profiles = _PROFILES - _PROFILES.mean(axis=1, keepdims=True)
    return profiles @ x / (np.linalg.norm(profiles, axis=1) * np.linalg.norm(x))


class _NoteArrays:
    """Notes as numpy arrays for fast windowed histograms (held-key durations, see chords.py)."""

    def __init__(self, notes: list[Note]):
        self.starts = np.array([n.start for n in notes])
        self.ends = np.array([n.key_end for n in notes])
        self.pitch_classes = np.array([n.pitch % 12 for n in notes])

    def pitch_class_durations(self, start: float, end: float) -> np.ndarray:
        overlap = np.clip(np.minimum(self.ends, end) - np.maximum(self.starts, start), 0, None)
        return np.bincount(self.pitch_classes, weights=overlap, minlength=12)


def _best_path(scores: np.ndarray, start_bias: int) -> list[int]:
    """Key index per sample maximising total correlation minus SWITCH_PENALTY per change."""
    count, keys = scores.shape
    total = scores[0].copy()
    total[start_bias] += 1e-6  # ties (e.g. silence at the start) resolve to the overall key
    back = np.zeros((count, keys), dtype=int)
    for i in range(1, count):
        best_previous = int(np.argmax(total))
        switch = total[best_previous] - SWITCH_PENALTY
        stay_better = total >= switch
        back[i] = np.where(stay_better, np.arange(keys), best_previous)
        total = np.maximum(total, switch) + scores[i]
    path = [int(np.argmax(total))]
    for i in range(count - 1, 0, -1):
        path.append(int(back[i, path[-1]]))
    return path[::-1]


def _segments(path: list[int], times: np.ndarray, duration: float) -> list[KeySegment]:
    segments: list[KeySegment] = []
    start_index = 0
    for i in range(1, len(path) + 1):
        if i == len(path) or path[i] != path[start_index]:
            # Boundaries sit halfway between samples; the first/last segment reach the edges.
            start = 0.0 if start_index == 0 else float(times[start_index] - STEP_SECONDS / 2)
            end = duration if i == len(path) else float(times[i] - STEP_SECONDS / 2)
            segments.append(KeySegment(start, end, ALL_KEYS[path[start_index]]))
            start_index = i
    return segments
