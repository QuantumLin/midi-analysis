"""Streams raw RGBA frames into ffmpeg and produces a file with alpha channel.

- "prores": QuickTime .mov with ProRes 4444 (yuva444p10le), imported by DaVinci
  Resolve, Premiere and Final Cut with transparency.
- "png": numbered PNG sequence (RGBA), delivered as a .zip archive.
"""

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from app.video.options import VideoFormat


class EncoderError(RuntimeError):
    pass


class VideoEncoder:
    def __init__(
        self,
        output_base: Path,
        format: VideoFormat,
        width: int,
        height: int,
        fps: int,
        frame_prefix: str | None = None,
    ):
        """output_base: target path without extension (.mov or .zip is added).
        frame_prefix: file name prefix of the PNGs (default: output_base.name)."""
        self.format = format
        self.frame_size = width * height * 4
        self._log = tempfile.TemporaryFile()
        source = [
            "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
        ]  # fmt: skip

        if format == "prores":
            self.output = output_base.with_suffix(".mov")
            # -q:v 11 and 8-bit alpha keep graphics crisp at ~40 % less size than the defaults.
            target = [
                "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                "-q:v", "11", "-alpha_bits", "8", "-vendor", "apl0", str(self.output),
            ]  # fmt: skip
        else:
            self.output = output_base.with_suffix(".zip")
            self._frames_dir = output_base.with_name(output_base.name + "_frames")
            self._frames_dir.mkdir(parents=True, exist_ok=True)
            target = [
                "-c:v", "png", "-pix_fmt", "rgba", "-start_number", "0",
                str(self._frames_dir / f"{frame_prefix or output_base.name}_%06d.png"),
            ]  # fmt: skip

        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *source, *target]
        try:
            self._process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=self._log)
        except FileNotFoundError as exc:
            raise EncoderError("ffmpeg is not installed.") from exc

    def write(self, frame: bytes) -> None:
        if len(frame) != self.frame_size:
            raise ValueError(f"Expected {self.frame_size} bytes per frame, got {len(frame)}.")
        try:
            self._process.stdin.write(frame)
        except BrokenPipeError as exc:
            raise EncoderError(self._error_text()) from exc

    def finish(self) -> Path:
        self._process.stdin.close()
        if self._process.wait() != 0:
            raise EncoderError(self._error_text())
        self._log.close()
        if self.format == "png":
            self._zip_frames()
        return self.output

    def abort(self) -> None:
        if self._process.poll() is None:
            self._process.kill()
            self._process.wait()
        self._log.close()
        if self.format == "png":
            shutil.rmtree(self._frames_dir, ignore_errors=True)
        self.output.unlink(missing_ok=True)

    def _zip_frames(self) -> None:
        # PNGs are already compressed; storing them is much faster than deflating again.
        with zipfile.ZipFile(self.output, "w", compression=zipfile.ZIP_STORED) as archive:
            for png in sorted(self._frames_dir.glob("*.png")):
                archive.write(png, arcname=png.name)
        shutil.rmtree(self._frames_dir, ignore_errors=True)

    def _error_text(self) -> str:
        self._log.seek(0)
        message = self._log.read().decode(errors="replace").strip()
        return f"ffmpeg failed: {message or 'unknown error'}"
