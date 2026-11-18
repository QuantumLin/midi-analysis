"""Request/response models of the HTTP API (the contract with the frontend)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.video.options import VideoFormat, VideoKind


class SpectrumOut(BaseModel):
    """Preview of the spectrum: frame i is at time i / fps; bins are log-spaced min_hz..max_hz."""

    fps: float
    bins: int
    frame_count: int
    min_hz: float
    max_hz: float
    min_db: float
    max_db: float
    levels: str = Field(description="Base64 of uint8[frame_count][bins], 0 = min_db, 255 = max_db")


class ChordOut(BaseModel):
    start: float
    end: float
    name: str
    root: str
    quality: str
    bass: str
    notes: list[str]
    numeral: str | None  # scale degree in the key at that moment: "vi", "V7", "♭VII"
    circle: "CirclePositionOut"  # place on the circle of fifths


class KeyOut(BaseModel):
    tonic: str  # spelled, ASCII accidentals: "D", "Bb", "F#"
    mode: Literal["major", "minor"]


class KeySegmentOut(BaseModel):
    start: float
    end: float
    key: KeyOut


class KeysOut(BaseModel):
    overall: KeyOut | None
    segments: list[KeySegmentOut]  # contiguous; a new segment after the first is a modulation


class NoteRecordOut(BaseModel):
    time: float
    value: int


class NoteRateOut(BaseModel):
    """Key presses in the last second; frame i is at time i / fps."""

    fps: float
    values: list[int]
    peak_value: int
    peak_time: float
    records: list[NoteRecordOut]


class LocalizedOut(BaseModel):
    de: str
    en: str


class ProgressionOut(BaseModel):
    """A known chord progression, complete at `time` and highlighted until `end`."""

    time: float
    end: float
    id: str
    count: int  # 1 = first time through, 2 = first repetition ...
    name: LocalizedOut  # including the counter, e.g. "Die Pop-Formel ×2"


class AchievementOut(BaseModel):
    """A pop-up shown from `time` to `end` (already scheduled so pop-ups never overlap)."""

    time: float
    end: float
    kind: str
    title: LocalizedOut
    detail: LocalizedOut


class MotifOccurrenceOut(BaseModel):
    start: float
    end: float  # end of the motif's last note
    number: int  # 1 = first appearance


class MotifOut(BaseModel):
    """A melodic fragment that recurs (also transposed): label "A", "B", "C"."""

    label: str
    length: int  # notes
    occurrences: list[MotifOccurrenceOut]


class SectionOut(BaseModel):
    """A section of the piece; sections with the same label are the same part (A B A ...)."""

    start: float
    end: float
    label: str
    number: int  # 1 = first time this part is heard


class CirclePositionOut(BaseModel):
    """Major chords on the outer ring at their root, minor chords on the inner ring next to
    their relative major; index 0 = top (C / a), clockwise in fifths."""

    ring: Literal["major", "minor"]
    index: int
    name: str  # "C", "F♯", "a", "b♭"


class BossOut(BaseModel):
    """The hardest passage as "final boss"; every note in it is a hit."""

    start: float
    end: float
    factor: str  # what makes it hard: "speed", "leaps", "chords"
    name: LocalizedOut  # "Notensturm" / "Note Storm"
    difficulty: float  # 0-10
    hits: list[float]  # note start times in the passage


class BingoFieldOut(BaseModel):
    id: str
    label: LocalizedOut
    time: float | None  # when it was ticked; None = never


class BingoLineOut(BaseModel):
    cells: list[int]  # indices into fields (row by row)
    time: float


class BingoOut(BaseModel):
    fields: list[BingoFieldOut]  # 3x3, row by row
    lines: list[BingoLineOut]  # completed lines, in order


class WrappedCardOut(BaseModel):
    id: str
    title: LocalizedOut
    value: LocalizedOut


class NotesOut(BaseModel):
    """All pitched notes as parallel arrays (compact), sorted by start; `end` is the key release."""

    start: list[float]
    end: list[float]
    pitch: list[int]


class AnalysisResponse(BaseModel):
    file_name: str
    duration_seconds: float
    note_count: int
    percussion_note_count: int
    spectrum: SpectrumOut
    chords: list[ChordOut]
    keys: KeysOut
    note_rate: NoteRateOut
    progressions: list[ProgressionOut]
    achievements: list[AchievementOut]
    motifs: list[MotifOut]
    sections: list[SectionOut]
    boss: BossOut | None  # None for pieces shorter than 10 s
    bingo: BingoOut
    wrapped: list[WrappedCardOut]
    notes: NotesOut


JobStatus = Literal["queued", "running", "done", "failed"]


class VideoJobOut(BaseModel):
    id: str
    kind: VideoKind
    format: VideoFormat
    status: JobStatus
    progress: float  # 0..1
    error: str | None = None
    file_name: str | None = None  # set when done
    size_bytes: int | None = None


ChordOut.model_rebuild()
