"""Motif recognition: melodic fragments that keep coming back ("motif A, 8th time").

Method (basic version):
1. Melody: the highest note of every strike (notes starting together), ignoring the bass
   register, so the left hand doesn't interrupt the line.
2. Each melody fragment of MOTIF_NOTES notes is described by its intervals (semitones
   between neighbouring notes) and its rhythm (each note's length relative to the
   previous one, rounded to factors of 2). Fragments with the same description are the
   same motif, even when transposed or played at another tempo.
3. The fragment with the most non-overlapping repetitions (at least MIN_OCCURRENCES)
   becomes motif A, extended note by note as long as all its repetitions still agree.
   Further motifs (B, C) must not reuse the notes of earlier ones.
"""

import math
from collections import defaultdict
from dataclasses import dataclass

from app.midi.models import MidiData

GROUP_SECONDS = 0.04  # notes starting this close together are one strike
MELODY_MIN_PITCH = 55  # G3: lower notes are treated as accompaniment
MAX_GAP_SECONDS = 1.5  # a motif doesn't run across a longer pause
MOTIF_NOTES = 6  # minimum length
MAX_MOTIF_NOTES = 16
MIN_OCCURRENCES = 3
MAX_MOTIFS = 3
MAX_SHARED_NOTES = 0.5  # a new motif may share at most this share of notes with earlier ones
LABELS = "ABC"


@dataclass(frozen=True, slots=True)
class MotifOccurrence:
    start: float
    end: float  # end of the last note
    number: int  # 1 = first appearance


@dataclass(frozen=True, slots=True)
class Motif:
    label: str  # "A", "B", "C"
    length: int  # notes
    occurrences: list[MotifOccurrence]


@dataclass(frozen=True, slots=True)
class _Melody:
    starts: list[float]
    ends: list[float]
    pitches: list[int]
    intervals: list[int]  # pitches[k + 1] - pitches[k]
    rhythm: list[int | None]  # length ratio of note k + 1 to note k (log2, rounded); None = pause


def find_motifs(midi: MidiData) -> list[Motif]:
    melody = _melody(midi)
    used: set[int] = set()  # melody note indices taken by earlier motifs
    motifs: list[Motif] = []
    for label in LABELS[:MAX_MOTIFS]:
        found = _best_motif(melody, used)
        if found is None:
            break
        starts, length = found
        for start in starts:
            used.update(range(start, start + length))
        occurrences = [
            MotifOccurrence(melody.starts[s], melody.ends[s + length - 1], number)
            for number, s in enumerate(starts, start=1)
        ]
        motifs.append(Motif(label, length, occurrences))
    return motifs


def _melody(midi: MidiData) -> _Melody:
    """Skyline melody: the top note of every strike above the bass register."""
    top: list[tuple[float, float, int]] = []
    for note in sorted(midi.notes, key=lambda n: n.start):
        if note.pitch < MELODY_MIN_PITCH:
            continue
        if top and note.start - top[-1][0] <= GROUP_SECONDS:
            if note.pitch > top[-1][2]:
                top[-1] = (top[-1][0], note.key_end, note.pitch)
            continue
        top.append((note.start, note.key_end, note.pitch))
    starts = [t[0] for t in top]
    pitches = [t[2] for t in top]
    ends = [min(t[1], starts[k + 1]) if k + 1 < len(top) else t[1] for k, t in enumerate(top)]
    intervals = [b - a for a, b in zip(pitches, pitches[1:])]
    # Inter-onset intervals; rhythm k compares the step k+1 -> k+2 with k -> k+1.
    iois = [b - a for a, b in zip(starts, starts[1:])]
    rhythm: list[int | None] = []
    for a, b in zip(iois, iois[1:]):
        if a > MAX_GAP_SECONDS or b > MAX_GAP_SECONDS or a <= 0 or b <= 0:
            rhythm.append(None)
        else:
            rhythm.append(round(math.log2(b / a)))
    return _Melody(starts, ends, pitches, intervals, rhythm)


def _key(melody: _Melody, start: int, length: int):
    """Description of the fragment of `length` notes from `start`; None if it spans a pause."""
    if start + length > len(melody.pitches):
        return None
    if any(melody.starts[k + 1] - melody.starts[k] > MAX_GAP_SECONDS for k in range(start, start + length - 1)):
        return None
    rhythm = tuple(melody.rhythm[start : start + length - 2])
    if None in rhythm:
        return None
    return tuple(melody.intervals[start : start + length - 1]), rhythm


def _interesting(intervals: tuple[int, ...]) -> bool:
    """Excludes repeated notes, trills and plain scales: a motif needs a shape."""
    return len(set(intervals)) >= 3 and sum(1 for i in intervals if i == 0) <= len(intervals) // 2


def _non_overlapping(starts: list[int], length: int) -> list[int]:
    chosen: list[int] = []
    for s in starts:
        if not chosen or s >= chosen[-1] + length:
            chosen.append(s)
    return chosen


def _best_motif(melody: _Melody, used: set[int]) -> tuple[list[int], int] | None:
    candidates: dict[tuple, list[int]] = defaultdict(list)
    for start in range(len(melody.pitches)):
        key = _key(melody, start, MOTIF_NOTES)
        if key is not None and _interesting(key[0]):
            candidates[key].append(start)

    best: tuple[int, list[int]] | None = None
    for starts in candidates.values():
        starts = _non_overlapping(starts, MOTIF_NOTES)
        starts = [s for s in starts if _shared(s, MOTIF_NOTES, used) <= MAX_SHARED_NOTES]
        if len(starts) >= MIN_OCCURRENCES and (best is None or len(starts) > len(best[1])):
            best = (len(starts), starts)
    if best is None:
        return None
    starts = best[1]
    return starts, _extend(melody, starts, MOTIF_NOTES)


def _shared(start: int, length: int, used: set[int]) -> float:
    return sum(1 for k in range(start, start + length) if k in used) / length


def _extend(melody: _Melody, starts: list[int], length: int) -> int:
    """Grows the motif while every repetition continues the same way (and they don't overlap)."""
    while length < MAX_MOTIF_NOTES:
        longer = length + 1
        keys = {_key(melody, s, longer) for s in starts}
        gaps_ok = all(b - a >= longer for a, b in zip(starts, starts[1:]))
        if len(keys) != 1 or None in keys or not gaps_ok:
            break
        length = longer
    return length
