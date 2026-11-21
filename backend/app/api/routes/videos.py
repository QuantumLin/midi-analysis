"""Overlay video export: start a render job, poll its status, download the result."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from app.api.schemas import VideoJobOut
from app.api.uploads import read_midi_upload
from app.config import get_settings
from app.midi.parser import MidiParseError
from app.video.jobs import VideoJob, VideoJobManager
from app.video.options import VideoFormat, VideoKind, VideoOptions
from app.video.style import FontId, GlowLevel

router = APIRouter(prefix="/videos", tags=["videos"])


@lru_cache
def get_job_manager() -> VideoJobManager:
    settings = get_settings()
    return VideoJobManager(Path(settings.video_dir), max_age_seconds=settings.video_max_age_minutes * 60)


JobManager = Annotated[VideoJobManager, Depends(get_job_manager)]


@router.post("", response_model=VideoJobOut, status_code=status.HTTP_202_ACCEPTED)
async def create_video(
    jobs: JobManager,
    file: UploadFile,
    kind: Annotated[VideoKind, Form()],
    format: Annotated[VideoFormat, Form()] = "prores",
    width: Annotated[int, Form()] = 1920,
    height: Annotated[int, Form()] = 1080,
    fps: Annotated[int, Form()] = 30,
    color: Annotated[str, Form()] = "#ffffff",
    show_grid: Annotated[bool, Form()] = True,
    show_frame: Annotated[bool, Form()] = True,
    font: Annotated[FontId, Form()] = "orbitron",
    glow: Annotated[GlowLevel, Form()] = "normal",
) -> VideoJobOut:
    data, file_name = await read_midi_upload(file)
    try:
        options = VideoOptions.create(kind, format, width, height, fps, color, show_grid, "en", show_frame, font, glow)
        job = await run_in_threadpool(jobs.submit, data, file_name, options)
    except (ValueError, MidiParseError) as exc:  # MidiParseError is a ValueError, listed for clarity
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _to_out(job)


@router.get("/{job_id}", response_model=VideoJobOut)
def get_video(job_id: str, jobs: JobManager) -> VideoJobOut:
    return _to_out(_find(jobs, job_id))


@router.get("/{job_id}/download")
def download_video(job_id: str, jobs: JobManager) -> FileResponse:
    job = _find(jobs, job_id)
    if job.status != "done" or job.path is None or not job.path.exists():
        raise HTTPException(status.HTTP_409_CONFLICT, "The video is not ready.")
    media_type = "video/quicktime" if job.options.format == "prores" else "application/zip"
    return FileResponse(job.path, media_type=media_type, filename=job.file_name)


def _find(jobs: VideoJobManager, job_id: str) -> VideoJob:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown or expired video job.")
    return job


def _to_out(job: VideoJob) -> VideoJobOut:
    done = job.status == "done"
    return VideoJobOut(
        id=job.id,
        kind=job.options.kind,
        format=job.options.format,
        status=job.status,  # type: ignore[arg-type]
        progress=round(job.progress, 3),
        error=job.error,
        file_name=job.file_name if done else None,
        size_bytes=job.size_bytes if done else None,
    )
