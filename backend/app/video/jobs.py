"""Background jobs for video rendering.

Rendering takes from seconds to minutes, so it runs in a worker thread while the
client polls the job status. Jobs live in memory (this is a single-user desktop
app); finished files are deleted after `max_age_seconds`.
"""

import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from app.midi.parser import parse_midi
from app.video.options import VideoOptions
from app.video.render import render_video


@dataclass
class VideoJob:
    id: str
    options: VideoOptions
    name: str  # e.g. 'My_Song_spectrum', also the PNG frame prefix
    file_name: str  # download name
    status: str = "queued"  # queued | running | done | failed
    progress: float = 0.0
    error: str | None = None
    path: Path | None = None
    created: float = field(default_factory=time.monotonic)

    @property
    def size_bytes(self) -> int | None:
        return self.path.stat().st_size if self.path and self.path.exists() else None


class VideoJobManager:
    def __init__(self, output_dir: Path, max_age_seconds: float, workers: int = 1):
        self.output_dir = output_dir
        self.max_age_seconds = max_age_seconds
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="video")
        self._jobs: dict[str, VideoJob] = {}
        self._lock = threading.Lock()

    def submit(self, midi_bytes: bytes, source_name: str, options: VideoOptions) -> VideoJob:
        """Validates the MIDI synchronously (raises MidiParseError), then renders in the background."""
        midi = parse_midi(midi_bytes)
        self._remove_expired()
        job_id = uuid.uuid4().hex
        name = f"{_stem(source_name)}_{options.kind}"
        extension = ".mov" if options.format == "prores" else "_png.zip"
        job = VideoJob(id=job_id, options=options, name=name, file_name=name + extension)
        with self._lock:
            self._jobs[job_id] = job
        self._executor.submit(self._run, job, midi)
        return job

    def get(self, job_id: str) -> VideoJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _run(self, job: VideoJob, midi) -> None:
        job.status = "running"
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_base = self.output_dir / job.id
            job.path = render_video(
                midi, job.options, output_base, lambda p: setattr(job, "progress", p), frame_prefix=job.name
            )
            job.status = "done"
        except Exception as exc:  # reported to the client via the job status
            job.status = "failed"
            job.error = str(exc)

    def _remove_expired(self) -> None:
        now = time.monotonic()
        with self._lock:
            expired = [j for j in self._jobs.values() if j.status in ("done", "failed") and now - j.created > self.max_age_seconds]
            for job in expired:
                del self._jobs[job.id]
        for job in expired:
            if job.path:
                job.path.unlink(missing_ok=True)


def _stem(file_name: str) -> str:
    """'My Song (1).mid' -> 'My_Song_1' (safe for file systems and Content-Disposition)."""
    stem = Path(file_name).stem
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_.")
    return safe or "midi"
