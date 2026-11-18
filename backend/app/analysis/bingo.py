"""Keyboard bingo: a 3x3 card of musical events that fill up while the piece plays.

Each field has a detector that returns when its event first happens (or None). A
completed row, column or diagonal is a "BINGO".

To add an event, write a detector, register it in FIELDS and add its label to
app/video/labels.py BINGO_LABELS; CARD decides which nine events are on the card.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.analysis.chords import ChordSegment
from app.analysis.harmony import ProgressionHit
from app.analysis.key import KeyAnalysis
from app.analysis.motifs import Motif
from app.midi.models import MidiData, Note

GROUP_SECONDS = 0.04
FREE = "free"
SIZE = 3


@dataclass(frozen=True, slots=True)
class BingoContext:
    """Everything the detectors may look at."""

    midi: MidiData
    chords: list[ChordSegment]
    keys: KeyAnalysis
    progressions: list[ProgressionHit]
    motifs: list[Motif]

    @property
    def notes(self) -> list[Note]:
        return sorted(self.midi.notes, key=lambda n: (n.start, n.pitch))

    def strikes(self) -> list[tuple[float, list[Note]]]:
        """(start, notes) of notes struck together."""
        groups: list[tuple[float, list[Note]]] = []
        for note in self.notes:
            if groups and note.start - groups[-1][0] <= GROUP_SECONDS:
                groups[-1][1].append(note)
            else:
                groups.append((note.start, [note]))
        return groups


Detector = Callable[[BingoContext], float | None]


def _first_note(predicate: Callable[[Note], bool]) -> Detector:
    return lambda ctx: next((n.start for n in ctx.notes if predicate(n)), None)


def _octave(ctx: BingoContext) -> float | None:
    """Two notes an octave apart struck together."""
    for start, notes in ctx.strikes():
        pitches = {n.pitch for n in notes}
        if any(p + 12 in pitches for p in pitches):
            return start
    return None


def _big_chord(ctx: BingoContext) -> float | None:
    return next((start for start, notes in ctx.strikes() if len({n.pitch for n in notes}) >= 6), None)


def _seventh_chord(ctx: BingoContext) -> float | None:
    sevenths = {"7", "maj7", "m7", "dim7", "m7b5", "mMaj7", "7sus4"}
    return next((c.start for c in ctx.chords if c.chord.quality in sevenths), None)


def _modulation(ctx: BingoContext) -> float | None:
    return ctx.keys.segments[1].start if len(ctx.keys.segments) > 1 else None


def _progression(ctx: BingoContext) -> float | None:
    return ctx.progressions[0].time if ctx.progressions else None


def _motif_return(ctx: BingoContext) -> float | None:
    returns = [m.occurrences[1].start for m in ctx.motifs if len(m.occurrences) > 1]
    return min(returns, default=None)


def _fast_run(ctx: BingoContext, notes: int = 6, max_interval: float = 0.125) -> float | None:
    """`notes` single notes in a row, each at most `max_interval` after the previous one."""
    run = 0
    previous = None
    for start, group in ctx.strikes():
        single = len(group) == 1
        run = run + 1 if single and previous is not None and start - previous <= max_interval else (1 if single else 0)
        previous = start if single else None
        if run >= notes:
            return start
    return None


def _pause(ctx: BingoContext, seconds: float = 1.0) -> float | None:
    """A moment of complete silence (nothing sounding) of `seconds` within the piece."""
    sounding_until = None
    for note in ctx.notes:
        if sounding_until is not None and note.start - sounding_until >= seconds:
            return sounding_until + seconds
        sounding_until = max(sounding_until or 0.0, note.end)
    return None


FIELDS: dict[str, Detector] = {
    "octave": _octave,
    "seventh_chord": _seventh_chord,
    "deep_bass": _first_note(lambda n: n.pitch < 36),  # below C2
    "high_notes": _first_note(lambda n: n.pitch >= 84),  # C6 and above
    "fast_run": _fast_run,
    "progression": _progression,
    "pause": _pause,
    "motif_return": _motif_return,
    "fortissimo": _first_note(lambda n: n.velocity >= 110),
    "pianissimo": _first_note(lambda n: n.velocity <= 40),
    "modulation": _modulation,
    "big_chord": _big_chord,
}

# Row by row. Rarer events sit in the corners and the centre, common ones on the edges:
# every line contains at least two rare events, so a bingo doesn't come too early.
# (FREE may be used as a field that is ticked from the start.)
CARD: tuple[str, ...] = (
    "motif_return", "octave", "progression",
    "seventh_chord", "big_chord", "deep_bass",
    "high_notes", "pause", "fast_run",
)  # fmt: skip

LINES: tuple[tuple[int, ...], ...] = (
    *(tuple(range(r * SIZE, r * SIZE + SIZE)) for r in range(SIZE)),  # rows
    *(tuple(range(c, SIZE * SIZE, SIZE)) for c in range(SIZE)),  # columns
    (0, 4, 8),
    (2, 4, 6),
)


@dataclass(frozen=True, slots=True)
class BingoField:
    id: str
    time: float | None  # when it was ticked; None = never (free field: 0)


@dataclass(frozen=True, slots=True)
class BingoLine:
    cells: tuple[int, ...]
    time: float  # when its last field was ticked


@dataclass(frozen=True, slots=True)
class BingoCard:
    fields: list[BingoField]  # row by row
    lines: list[BingoLine]  # completed lines, in order of completion

    def ticked_at(self, time: float) -> tuple[bool, ...]:
        return tuple(f.time is not None and f.time <= time for f in self.fields)

    def lines_at(self, time: float) -> list[BingoLine]:
        return [line for line in self.lines if line.time <= time]


def play_bingo(context: BingoContext, card: tuple[str, ...] = CARD) -> BingoCard:
    fields = [BingoField(id, 0.0 if id == FREE else FIELDS[id](context)) for id in card]
    lines = []
    for cells in LINES:
        times = [fields[c].time for c in cells]
        if all(t is not None for t in times):
            lines.append(BingoLine(cells, max(times)))  # type: ignore[arg-type]
    return BingoCard(fields, sorted(lines, key=lambda line: line.time))
