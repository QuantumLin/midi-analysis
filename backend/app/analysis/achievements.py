"""Achievements: short pop-ups for remarkable moments, like in a video game.

Everything is detected from the notes alone:
- big_chord   many notes struck at once ("8-finger chord"); first one and every new record
- leap        a jump across the keyboard with both hands free (nothing held in between)
- run         a fast scale or arpeggio run in one direction; first one and every longer one
- trill       fast alternation of two neighbouring notes
- fortissimo  the first really hard strike, if the piece isn't loud throughout
- low / high  the first note in the very lowest / highest region of the keyboard
- range       5, 6, 7 octaves of the keyboard used so far
- milestone   500, 1000, 2000 ... notes played

Pop-ups never overlap: one that arrives while another is shown waits for it, and is
dropped if it would come too late to still match the music.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np

from app.midi.models import MidiData, Note

AchievementKind = Literal["big_chord", "leap", "run", "trill", "fortissimo", "low", "high", "range", "milestone"]

GROUP_SECONDS = 0.04  # notes starting this close together count as struck together
BIG_CHORD_MIN = 6
LEAP_MIN_SEMITONES = 24
LEAP_MAX_GAP_SECONDS = 0.35
LEAP_RECORD_STEP = 3
RUN_MIN_NOTES = 10
RUN_MAX_INTERVAL_SECONDS = 0.12
RUN_MAX_STEP = 4  # semitones between neighbouring run notes
RUN_RECORD_STEP = 4
TRILL_MIN_NOTES = 8
TRILL_MAX_INTERVAL_SECONDS = 0.15
TRILL_COOLDOWN_SECONDS = 20.0
FORTISSIMO_VELOCITY = 112
FORTISSIMO_MAX_SHARE = 0.1  # if more notes are this loud, the piece is just loud
WARMUP_SECONDS = 3.0
LOW_REGION_MAX = 28  # E1
HIGH_REGION_MIN = 96  # C7
RANGE_OCTAVES = (5, 6, 7)
MILESTONES = (500, 1000, 2000, 3000, 5000, 7500, 10000)

DISPLAY_SECONDS = 3.2
GAP_SECONDS = 0.3
MAX_DELAY_SECONDS = 4.0


@dataclass(frozen=True, slots=True)
class Achievement:
    time: float  # when the pop-up appears
    kind: AchievementKind
    value: int  # notes / semitones / octaves / velocity / pitch, depending on the kind
    seconds: float = 0.0  # duration of a run or trill
    low: int = 0  # range: lowest and highest pitch so far
    high: int = 0

    @property
    def end(self) -> float:
        return self.time + DISPLAY_SECONDS


@dataclass(frozen=True, slots=True)
class _Group:
    start: float
    pitches: tuple[int, ...]  # sorted
    velocity: int  # loudest note
    key_end: float  # latest key release


def find_achievements(midi: MidiData) -> list[Achievement]:
    notes = sorted(midi.notes, key=lambda n: (n.start, n.pitch))
    if not notes:
        return []
    groups = _groups(notes)
    found = [
        *_big_chords(groups),
        *_leaps(groups),
        *_runs(groups),
        *_trills(groups),
        *_fortissimo(notes),
        *_extremes(notes),
        *_ranges(notes),
        *_milestones(notes),
    ]
    return schedule(found)


def schedule(achievements: list[Achievement]) -> list[Achievement]:
    """Sorts by time and delays pop-ups so they don't overlap; drops those delayed too long."""
    shown: list[Achievement] = []
    free_from = float("-inf")
    for item in sorted(achievements, key=lambda a: a.time):
        start = max(item.time, free_from)
        if start - item.time > MAX_DELAY_SECONDS:
            continue
        shown.append(Achievement(start, item.kind, item.value, item.seconds, item.low, item.high))
        free_from = start + DISPLAY_SECONDS + GAP_SECONDS
    return shown


def _groups(notes: list[Note]) -> list[_Group]:
    groups: list[list[Note]] = []
    for note in notes:
        if groups and note.start - groups[-1][0].start <= GROUP_SECONDS:
            groups[-1].append(note)
        else:
            groups.append([note])
    return [
        _Group(g[0].start, tuple(sorted({n.pitch for n in g})), max(n.velocity for n in g), max(n.key_end for n in g))
        for g in groups
    ]


def _big_chords(groups: list[_Group]):
    best = BIG_CHORD_MIN - 1
    for group in groups:
        if len(group.pitches) > best:
            best = len(group.pitches)
            yield Achievement(group.start, "big_chord", best)


def _leaps(groups: list[_Group]):
    """A jump between two consecutive strikes with no key held in between: one gesture."""
    best = LEAP_MIN_SEMITONES - LEAP_RECORD_STEP
    for previous, group in zip(groups, groups[1:]):
        gap = group.start - previous.key_end
        if not 0 <= gap <= LEAP_MAX_GAP_SECONDS:
            continue  # still held (two hands at work) or a pause
        distance = round(abs(np.mean(group.pitches) - np.mean(previous.pitches)))
        if distance >= best + LEAP_RECORD_STEP:
            best = distance
            yield Achievement(group.start, "leap", distance)


def _single_note_sequences(groups: list[_Group], max_interval: float):
    """Maximal sequences of single notes, each following the previous one quickly."""
    sequence: list[_Group] = []
    for group in groups:
        if len(group.pitches) == 1 and sequence and group.start - sequence[-1].start <= max_interval:
            sequence.append(group)
            continue
        if len(sequence) > 1:
            yield sequence
        sequence = [group] if len(group.pitches) == 1 else []
    if len(sequence) > 1:
        yield sequence


def _runs(groups: list[_Group]):
    best = RUN_MIN_NOTES - RUN_RECORD_STEP
    for sequence in _single_note_sequences(groups, RUN_MAX_INTERVAL_SECONDS):
        for run in _directional_runs([g.pitches[0] for g in sequence]):
            start, stop = run
            length = stop - start
            if length >= best + RUN_RECORD_STEP:
                best = length
                seconds = sequence[stop - 1].start - sequence[start].start
                yield Achievement(sequence[stop - 1].start, "run", length, seconds=round(seconds, 2))


def _directional_runs(pitches: list[int]):
    """(start, stop) index ranges where the pitch keeps moving in one direction by small steps."""
    start, direction = 0, 0
    for i in range(1, len(pitches)):
        step = pitches[i] - pitches[i - 1]
        step_direction = (step > 0) - (step < 0)
        small = 0 < abs(step) <= RUN_MAX_STEP
        if small and direction in (0, step_direction):
            direction = step_direction
            continue
        if i - start >= RUN_MIN_NOTES:
            yield start, i
        # At a turning point the last note starts the next run.
        start, direction = (i - 1, step_direction) if small else (i, 0)
    if len(pitches) - start >= RUN_MIN_NOTES:
        yield start, len(pitches)


def _trills(groups: list[_Group]):
    last = float("-inf")
    for sequence in _single_note_sequences(groups, TRILL_MAX_INTERVAL_SECONDS):
        pitches = [g.pitches[0] for g in sequence]
        start = 0
        for i in range(1, len(pitches) + 1):
            neighbour = i < len(pitches) and 0 < abs(pitches[i] - pitches[i - 1]) <= 2
            if neighbour and (i - start < 2 or pitches[i] == pitches[i - 2]):
                continue  # still alternating between the same two notes
            if i - start >= TRILL_MIN_NOTES and sequence[start].start - last >= TRILL_COOLDOWN_SECONDS:
                last = sequence[start].start
                seconds = sequence[i - 1].start - sequence[start].start
                yield Achievement(sequence[i - 1].start, "trill", i - start, seconds=round(seconds, 2))
            start = i - 1 if neighbour else i


def _fortissimo(notes: list[Note]):
    loud = [n for n in notes if n.velocity >= FORTISSIMO_VELOCITY]
    if not loud or len(loud) > FORTISSIMO_MAX_SHARE * len(notes):
        return
    first = next((n for n in loud if n.start >= WARMUP_SECONDS), None)
    if first:
        yield Achievement(first.start, "fortissimo", first.velocity)


def _extremes(notes: list[Note]):
    low = next((n for n in notes if n.pitch <= LOW_REGION_MAX), None)
    high = next((n for n in notes if n.pitch >= HIGH_REGION_MIN), None)
    if low:
        yield Achievement(low.start, "low", low.pitch)
    if high:
        yield Achievement(high.start, "high", high.pitch)


def _ranges(notes: list[Note]):
    low = high = notes[0].pitch
    targets = list(RANGE_OCTAVES)
    for note in notes:
        low, high = min(low, note.pitch), max(high, note.pitch)
        reached = [octaves for octaves in targets if high - low >= octaves * 12]
        if reached:  # several thresholds at once: only the highest
            targets = [octaves for octaves in targets if octaves not in reached]
            yield Achievement(max(note.start, WARMUP_SECONDS), "range", reached[-1], low=low, high=high)


def _milestones(notes: list[Note]):
    for count in MILESTONES:
        if count <= len(notes):
            yield Achievement(notes[count - 1].start, "milestone", count)
