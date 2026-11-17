"""Plain data structures shared by the parser and the analysis modules."""

from dataclasses import dataclass, field

PERCUSSION_CHANNEL = 9  # MIDI channel 10 (0-based index 9) is reserved for drums.


@dataclass(frozen=True, slots=True)
class Note:
    pitch: int  # MIDI note number 0-127
    velocity: int  # 1-127
    start: float  # seconds
    end: float  # seconds, end of the sound (includes sustain pedal)
    channel: int
    key_end: float  # seconds, when the key was released (ignores sustain pedal)

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass(slots=True)
class MidiData:
    notes: list[Note] = field(default_factory=list)  # pitched notes, sorted by start
    percussion_notes: list[Note] = field(default_factory=list)
    duration: float = 0.0  # seconds
