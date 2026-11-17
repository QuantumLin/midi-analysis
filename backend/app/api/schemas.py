"""Request/response models of the HTTP API (the contract with the frontend)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.video.options import VideoFormat, VideoKind


class TimelinePointOut(BaseModel):
    time: float
    velocity: float
    active_notes: int


class TimelineOut(BaseModel):
    step_seconds: float
    points: list[TimelinePointOut]


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


class AnalysisResponse(BaseModel):
    file_name: str
    duration_seconds: float
    note_count: int
    percussion_note_count: int
    timeline: TimelineOut
    spectrum: SpectrumOut
    chords: list[ChordOut]


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
