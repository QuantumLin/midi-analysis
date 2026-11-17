"""Chord recognition from simultaneously held notes.

The piece is cut wherever a key is pressed or released. For each slice, the held
pitch classes are scored against chord templates; the best match names the chord.
Consecutive slices with the same chord are merged.

Design decisions:
- Held keys are evaluated first: with the sustain pedal down every note keeps ringing,
  which would blur all harmonies into one cluster. Only if the held keys form no chord,
  the pedal-sustained notes are tried (this catches chords arpeggiated into the pedal).
- Matching tolerates a few extra tones (melody, passing notes) and a missing fifth,
  but an exact match always wins.
- Arpeggiated (broken) chords without pedal are not detected, because their notes never
  sound together.
"""

from collections import Counter
from dataclasses import dataclass

from app.midi.models import MidiData, Note
from app.midi.pitch import pitch_class_name, pitch_name

# Slices shorter than this are ignored (overlaps from legato playing, grace notes).
MIN_SEGMENT_SECONDS = 0.08
MAX_EXTRA_TONES = 2
PERFECT_FIFTH = 7

# Scoring weights (per pitch class; doubled notes count more, the bass a bit more).
EXTRA_TONE_PENALTY = 1.0
MISSING_FIFTH_PENALTY = 0.5
ROOT_IN_BASS_BONUS = 0.5
TEMPLATE_RANK_PENALTY = 0.01  # tie-breaker: earlier (simpler) templates win

# Chord quality suffix -> intervals above the root (as pitch classes).
CHORD_TEMPLATES: tuple[tuple[str, frozenset[int]], ...] = tuple(
    (name, frozenset(intervals))
    for name, intervals in (
        ("", (0, 4, 7)),
        ("m", (0, 3, 7)),
        ("7", (0, 4, 7, 10)),
        ("maj7", (0, 4, 7, 11)),
        ("m7", (0, 3, 7, 10)),
        ("dim", (0, 3, 6)),
        ("aug", (0, 4, 8)),
        ("sus4", (0, 5, 7)),
        ("sus2", (0, 2, 7)),
        ("dim7", (0, 3, 6, 9)),
        ("m7b5", (0, 3, 6, 10)),
        ("mMaj7", (0, 3, 7, 11)),
        ("6", (0, 4, 7, 9)),
        ("m6", (0, 3, 7, 9)),
        ("7sus4", (0, 5, 7, 10)),
        ("add9", (0, 2, 4, 7)),
        ("madd9", (0, 2, 3, 7)),
        ("9", (0, 2, 4, 7, 10)),
        ("maj9", (0, 2, 4, 7, 11)),
        ("m9", (0, 2, 3, 7, 10)),
        # Common voicings without the fifth.
        ("7", (0, 4, 10)),
        ("maj7", (0, 4, 11)),
        ("m7", (0, 3, 10)),
        ("5", (0, 7)),
    )
)


@dataclass(frozen=True, slots=True)
class ChordMatch:
    root: int  # pitch class 0-11
    quality: str  # template suffix, "" = major
    bass: int  # pitch class of the lowest note

    @property
    def name(self) -> str:
        return self.spelled(prefer_flats=False)

    def spelled(self, prefer_flats: bool) -> str:
        """Chord name with sharps ("A#") or flats ("Bb"), depending on the key."""
        name = pitch_class_name(self.root, prefer_flats) + self.quality
        if self.bass != self.root:
            name += "/" + pitch_class_name(self.bass, prefer_flats)
        return name


@dataclass(frozen=True, slots=True)
class ChordSegment:
    start: float
    end: float
    chord: ChordMatch
    pitches: tuple[int, ...]  # sorted MIDI pitches held at the segment start

    @property
    def note_names(self) -> list[str]:
        return self.spelled_note_names(prefer_flats=False)

    def spelled_note_names(self, prefer_flats: bool) -> list[str]:
        return [pitch_name(p, prefer_flats) for p in self.pitches]


def identify_chord(pitches: list[int] | tuple[int, ...]) -> ChordMatch | None:
    """Names the chord formed by the given MIDI pitches, or None if nothing fits."""
    if not pitches:
        return None
    weights = Counter(p % 12 for p in pitches)
    present = set(weights)
    if len(present) < 2:
        return None
    bass = min(pitches) % 12
    weights[bass] += 1

    best: tuple[float, ChordMatch] | None = None
    for rank, (quality, intervals) in enumerate(CHORD_TEMPLATES):
        for root in present:
            score = _score(root, intervals, present, weights)
            if score is None:
                continue
            score += (ROOT_IN_BASS_BONUS if root == bass else 0) - rank * TEMPLATE_RANK_PENALTY
            if best is None or score > best[0]:
                best = (score, ChordMatch(root, quality, bass))
    return best[1] if best else None


def _score(root: int, intervals: frozenset[int], present: set[int], weights: Counter) -> float | None:
    chord_tones = {(root + i) % 12 for i in intervals}
    matched = chord_tones & present
    missing = chord_tones - present
    extra = present - chord_tones

    if len(intervals) == 2:  # power chord: exact only, no tolerance
        return float(sum(weights[pc] for pc in matched)) if not missing and not extra else None
    # Only the perfect fifth may be missing; at least three chord tones must sound.
    if missing - {(root + PERFECT_FIFTH) % 12} or len(matched) < 3 or len(extra) > MAX_EXTRA_TONES:
        return None
    return (
        sum(weights[pc] for pc in matched)
        - EXTRA_TONE_PENALTY * sum(weights[pc] for pc in extra)
        - MISSING_FIFTH_PENALTY * len(missing)
    )


def detect_chords(midi: MidiData) -> list[ChordSegment]:
    segments: list[ChordSegment] = []
    # Start of the last chord recognised from held keys. Pedal-sustained notes struck
    # before it belong to an earlier harmony and must not blur the fallback.
    anchor = float("-inf")
    for start, end, sounding in _slices(midi.notes):
        if end - start < MIN_SEGMENT_SECONDS:
            continue
        held_notes = [n for n in sounding if n.key_end > start]
        held = tuple(sorted({n.pitch for n in held_notes}))
        pitches, chord = held, identify_chord(held)
        if chord is not None:
            anchor = min(n.start for n in held_notes)
        else:
            # Fallback: notes still ringing via the pedal (e.g. a chord arpeggiated into the pedal).
            ringing = tuple(sorted({n.pitch for n in sounding if n.start >= anchor}))
            if ringing != held:
                pitches, chord = ringing, identify_chord(ringing)
        if chord is None:
            continue
        previous = segments[-1] if segments else None
        # Merge with the previous segment if it is the same chord and (nearly) adjacent.
        if previous and previous.chord == chord and start - previous.end < MIN_SEGMENT_SECONDS:
            segments[-1] = ChordSegment(previous.start, end, chord, previous.pitches)
        else:
            segments.append(ChordSegment(start, end, chord, pitches))
    return segments


def _slices(notes: list[Note]):
    """Yields (start, end, sounding_notes) between consecutive note boundaries
    (note start, key release, end of sound)."""
    boundaries = sorted({t for n in notes for t in (n.start, n.key_end, n.end)})
    by_start = sorted(notes, key=lambda n: n.start)
    active: list[Note] = []
    next_note = 0
    for start, end in zip(boundaries, boundaries[1:]):
        active = [n for n in active if n.end > start]
        while next_note < len(by_start) and by_start[next_note].start <= start:
            if by_start[next_note].end > start:
                active.append(by_start[next_note])
            next_note += 1
        if active:
            yield start, end, active
