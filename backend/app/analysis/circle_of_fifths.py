"""Chords on the circle of fifths.

The circle has 12 positions in fifths order (C G D A E B F♯ D♭ A♭ E♭ B♭ F). Major chords
sit on the outer ring at their root; minor (and diminished) chords on the inner ring
next to their relative major (A minor beside C major). The path of the harmony through
the piece is the sequence of these positions.
"""

from dataclasses import dataclass
from typing import Literal

from app.analysis.chords import ChordMatch, ChordSegment
from app.analysis.harmony import chord_type

Ring = Literal["major", "minor"]

FIFTHS_ORDER = (0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5)  # position -> pitch class of the major key
MAJOR_NAMES = ("C", "G", "D", "A", "E", "B", "F♯", "D♭", "A♭", "E♭", "B♭", "F")
MINOR_NAMES = ("a", "e", "b", "f♯", "c♯", "g♯", "e♭", "b♭", "f", "c", "g", "d")  # relative minors
POSITIONS = len(FIFTHS_ORDER)


@dataclass(frozen=True, slots=True)
class CirclePosition:
    ring: Ring
    index: int  # 0 = top (C / a), clockwise

    @property
    def name(self) -> str:
        return (MAJOR_NAMES if self.ring == "major" else MINOR_NAMES)[self.index]


@dataclass(frozen=True, slots=True)
class CircleStep:
    start: float
    end: float
    position: CirclePosition


def circle_position(chord: ChordMatch) -> CirclePosition:
    if chord_type(chord.quality) in ("minor", "diminished"):
        return CirclePosition("minor", FIFTHS_ORDER.index((chord.root + 3) % 12))  # relative major's spot
    return CirclePosition("major", FIFTHS_ORDER.index(chord.root))


def circle_path(chords: list[ChordSegment]) -> list[CircleStep]:
    """One step per chord, in order."""
    return [CircleStep(c.start, c.end, circle_position(c.chord)) for c in chords]
