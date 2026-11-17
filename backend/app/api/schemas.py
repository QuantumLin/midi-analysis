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
