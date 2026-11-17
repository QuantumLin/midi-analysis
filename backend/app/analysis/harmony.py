"""Harmonic analysis: scale degrees (roman numerals) and well-known chord progressions.

Every chord gets a roman numeral relative to the key at that moment: in C major,
C = I, Am = vi, G7 = V7, Bb = ♭VII; in a minor, Am = i, G = VII, E = V, Bdim = ii°.
Upper case = major chord, lower case = minor; ° diminished, ø half-diminished, + augmented.

Known progressions (the "pop formula" I–V–vi–IV, the Andalusian cadence, ii–V–I, ...)
are matched on the chord sequence by their root intervals and chord types, so they are
found independently of the key (I–V–vi–IV in C sounds the same as vi–IV–I–V). Loops
(e.g. the pop formula) are recognised starting on any of their chords; every completed
repetition is reported with a counter.
"""

import re
from dataclasses import dataclass
from typing import Literal

from app.analysis.chords import ChordMatch, ChordSegment
from app.analysis.key import Key, KeyAnalysis

# Roman numeral per semitone above the tonic. Minor keys count from natural minor,
# so the relative major's chords read III, VI, VII (the usual notation).
_MAJOR_DEGREES = ("I", "♭II", "II", "♭III", "III", "IV", "♯IV", "V", "♭VI", "VI", "♭VII", "VII")
_MINOR_DEGREES = ("I", "♭II", "II", "III", "♯III", "IV", "♯IV", "V", "VI", "♯VI", "VII", "♯VII")

# Diatonic triads: which degrees (semitones above the tonic) are minor / diminished.
_DIATONIC_LOWER = {"major": {2, 4, 9, 11}, "minor": {0, 2, 5, 7}}
_THIRDLESS_QUALITIES = {"5", "sus2", "sus4", "7sus4"}  # no third: case follows the key

_MINOR_QUALITIES = {"m", "m7", "m6", "madd9", "m9", "mMaj7"}
_DIMINISHED_QUALITIES = {"dim", "dim7", "m7b5"}
_OTHER_QUALITIES = {"sus4", "sus2", "7sus4", "5", "aug"}  # ambiguous: skipped when matching
# Quality suffix -> what follows the numeral.
_NUMERAL_SUFFIX = {
    "dim": "°",
    "dim7": "°7",
    "m7b5": "ø7",
    "aug": "+",
    "m7": "7",
    "m6": "6",
    "madd9": "add9",
    "m9": "9",
    "mMaj7": "maj7",
    "m": "",
    "5": "",  # a power chord just stands for its degree
}

ChordType = Literal["major", "minor", "diminished", "other"]

# Chords shorter than this are passing chords and don't take part in progressions.
MIN_PROGRESSION_CHORD_SECONDS = 0.15
CIRCLE_MIN_CHORDS = 4
PROGRESSION_HIGHLIGHT_SECONDS = 4.0


def chord_type(quality: str) -> ChordType:
    if quality in _MINOR_QUALITIES:
        return "minor"
    if quality in _DIMINISHED_QUALITIES:
        return "diminished"
    if quality in _OTHER_QUALITIES:
        return "other"
    return "major"  # major, dominant and major-seventh chords


def roman_numeral(chord: ChordMatch, key: Key) -> str:
    """'vi', 'V7', '♭VII', 'ii°', 'viiø7' ... (inversions are not marked).
    Chords without a third (power chords, sus) take the case of the key's own chord on that degree."""
    degrees = _MAJOR_DEGREES if key.mode == "major" else _MINOR_DEGREES
    degree = (chord.root - key.tonic) % 12
    numeral = degrees[degree]
    if chord.quality in _THIRDLESS_QUALITIES:
        lower = degree in _DIATONIC_LOWER[key.mode]
    else:
        lower = chord_type(chord.quality) in ("minor", "diminished")
    if lower:
        numeral = numeral.lower()
    return numeral + _NUMERAL_SUFFIX.get(chord.quality, chord.quality)


_NUMERAL = re.compile(r"^([♭♯]?[IViv]+)(.*)$")


def split_numeral(numeral: str) -> tuple[str, str]:
    """'♭VIImaj7' -> ('♭VII', 'maj7'): the degree and the chord suffix."""
    match = _NUMERAL.match(numeral)
    return (match.group(1), match.group(2)) if match else (numeral, "")


# --- progressions ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Progression:
    id: str
    steps: tuple[tuple[int, ChordType], ...]  # (semitones above the first chord's root, type)
    loop: bool  # may start on any of its chords (a repeating loop)
    repeats: bool = True  # immediate repetitions are counted


# Order = priority when several patterns match at the same chord (longer/more specific first).
PROGRESSIONS: tuple[Progression, ...] = (
    # I–V–vi–iii–IV–I (Pachelbel's Canon)
    Progression("canon", ((0, "major"), (7, "major"), (9, "minor"), (4, "minor"), (5, "major"), (0, "major")), False),
    # I–V–vi–IV ("Let It Be", "Someone Like You", ... and its rotations vi–IV–I–V etc.)
    Progression("pop", ((0, "major"), (7, "major"), (9, "minor"), (5, "major")), True),
    # I–vi–IV–V ("Stand by Me", 1950s doo-wop)
    Progression("fifties", ((0, "major"), (9, "minor"), (5, "major"), (7, "major")), True),
    # IV–V–iii–vi (J-pop / anime)
    Progression("royal_road", ((0, "major"), (2, "major"), (11, "minor"), (4, "minor")), False),
    # i–VII–VI–V ("Hit the Road Jack", flamenco)
    Progression("andalusian", ((0, "minor"), (10, "major"), (8, "major"), (7, "major")), False),
    # ii–V–I in major and ii°–V–i in minor (jazz standard cadence)
    Progression("two_five_one", ((0, "minor"), (5, "major"), (10, "major")), False, repeats=False),
    Progression("two_five_one", ((0, "diminished"), (5, "major"), (10, "minor")), False, repeats=False),
)


@dataclass(frozen=True, slots=True)
class ProgressionHit:
    time: float  # when the progression is complete (start of its last chord)
    end: float  # highlighted until here
    id: str  # see PROGRESSIONS, plus "circle_of_fifths"
    count: int  # 1 = first time through, 2 = first repetition ...


@dataclass(frozen=True, slots=True)
class _Step:
    start: float
    root: int
    type: ChordType


def find_progressions(chords: list[ChordSegment]) -> list[ProgressionHit]:
    steps = _steps(chords)
    hits: list[ProgressionHit] = []
    i = 0
    while i < len(steps):
        found = _match_at(steps, i)
        if found is None:
            i += 1
            continue
        progression_id, length, period = found
        end = i + length  # index after the match
        count = 1
        hits.append(ProgressionHit(steps[end - 1].start, 0.0, progression_id, count))
        if progression_id == "circle_of_fifths":
            pass  # the chain itself was followed as far as it goes
        elif period:
            # Repetitions: the chord sequence keeps cycling with the same period.
            while end < len(steps) and _same(steps[end], steps[end - period]):
                end += 1
                if (end - i) % period == 0:
                    count += 1
                    hits.append(ProgressionHit(steps[end - 1].start, 0.0, progression_id, count))
        i = end
    return _with_highlight_ends(hits)


def _steps(chords: list[ChordSegment]) -> list[_Step]:
    """Chord sequence for matching: no passing chords, no ambiguous (sus, power) chords,
    and repeated chords (C, C7, C) collapsed into one."""
    steps: list[_Step] = []
    for segment in chords:
        kind = chord_type(segment.chord.quality)
        if kind == "other" or segment.end - segment.start < MIN_PROGRESSION_CHORD_SECONDS:
            continue
        step = _Step(segment.start, segment.chord.root, kind)
        if steps and _same(steps[-1], step):
            continue
        steps.append(step)
    return steps


def _same(a: _Step, b: _Step) -> bool:
    return a.root == b.root and a.type == b.type


def _match_at(steps: list[_Step], i: int) -> tuple[str, int, int] | None:
    """(progression id, chords matched, repetition period or 0) for a match starting at i."""
    for progression in PROGRESSIONS:
        rotations = range(len(progression.steps)) if progression.loop else range(1)
        for rotation in rotations:
            pattern = _rotated(progression.steps, rotation)
            if _matches(steps, i, pattern):
                return progression.id, len(pattern), len(pattern) if progression.repeats else 0
    chain = _fifths_chain_length(steps, i)
    if chain >= CIRCLE_MIN_CHORDS:
        return "circle_of_fifths", chain, 0
    return None


def _rotated(steps: tuple[tuple[int, ChordType], ...], rotation: int) -> list[tuple[int, ChordType]]:
    rotated = steps[rotation:] + steps[:rotation]
    base = rotated[0][0]
    return [((interval - base) % 12, kind) for interval, kind in rotated]


def _matches(steps: list[_Step], i: int, pattern: list[tuple[int, ChordType]]) -> bool:
    if i + len(pattern) > len(steps):
        return False
    root = steps[i].root
    return all(
        (steps[i + k].root - root) % 12 == interval and steps[i + k].type == kind
        for k, (interval, kind) in enumerate(pattern)
    )


def _fifths_chain_length(steps: list[_Step], i: int) -> int:
    """Chords from i on whose roots each fall a fifth (e.g. E–A–D–G–C)."""
    length = 1
    while i + length < len(steps) and (steps[i + length].root - steps[i + length - 1].root) % 12 == 5:
        length += 1
    return length


def _with_highlight_ends(hits: list[ProgressionHit]) -> list[ProgressionHit]:
    """Each hit stays highlighted for a few seconds, but never past the next hit."""
    result = []
    for k, hit in enumerate(hits):
        end = hit.time + PROGRESSION_HIGHLIGHT_SECONDS
        if k + 1 < len(hits):
            end = min(end, hits[k + 1].time)
        result.append(ProgressionHit(hit.time, end, hit.id, hit.count))
    return result


# --- per-moment view for the overlay -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class HarmonyAnalysis:
    chords: list[ChordSegment]
    numerals: list[str]  # per chord
    keys: list[Key | None]  # key per chord (at its start)
    progressions: list[ProgressionHit]

    def chain_before(self, index: int, length: int = 4) -> tuple[str, ...]:
        """The last `length` degrees (numerals without suffix) up to and including chord
        `index`, repeats collapsed: ('i', 'VI', 'III', 'VII')."""
        chain: list[str] = []
        for numeral in reversed(self.numerals[: index + 1]):
            numeral = split_numeral(numeral)[0]
            if not numeral or (chain and chain[0] == numeral):
                continue
            chain.insert(0, numeral)
            if len(chain) == length:
                break
        return tuple(chain)

    def progression_at(self, time: float) -> ProgressionHit | None:
        return next((h for h in self.progressions if h.time <= time < h.end), None)


def analyze_harmony(chords: list[ChordSegment], keys: KeyAnalysis) -> HarmonyAnalysis:
    chord_keys = [keys.key_at(c.start) for c in chords]
    numerals = [roman_numeral(c.chord, k) if k else "" for c, k in zip(chords, chord_keys)]
    return HarmonyAnalysis(chords, numerals, chord_keys, find_progressions(chords))
