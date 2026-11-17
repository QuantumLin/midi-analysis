"""Renders a complete overlay video from parsed MIDI data."""

import os
from collections import deque
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from app.analysis.chords import ChordSegment, detect_chords
from app.analysis.spectrum import compute_spectrum
from app.midi.models import MidiData
from app.video.chord_renderer import ChordRenderer
from app.video.encoder import VideoEncoder
from app.video.options import VideoOptions
from app.video.spectrum_renderer import SpectrumRenderer

SPECTRUM_BINS = 1024  # interpolated to the pixel columns when drawing
RENDER_THREADS = 8
# The chord field keeps showing the last chord through short gaps (rests, staccato),
# so it doesn't flicker; after a longer silence it is hidden.
CHORD_HOLD_SECONDS = 2.0

ProgressCallback = Callable[[float], None]


def render_video(
    midi: MidiData,
    options: VideoOptions,
    output_base: Path,
    on_progress: ProgressCallback,
    frame_prefix: str | None = None,
) -> Path:
    if options.kind == "spectrum":
        frames = _spectrum_frames(midi, options)
    else:
        frames = _chord_frames(midi, options)

    frame_count = _frame_count(midi, options.fps)
    encoder = VideoEncoder(output_base, options.format, options.width, options.height, options.fps, frame_prefix)
    try:
        for index, frame in enumerate(frames):
            encoder.write(frame)
            if index % 10 == 0:
                on_progress(index / frame_count)
        path = encoder.finish()
    except BaseException:
        encoder.abort()
        raise
    on_progress(1.0)
    return path


def _frame_count(midi: MidiData, fps: int) -> int:
    return max(1, int(midi.duration * fps) + 1)


def _spectrum_frames(midi: MidiData, options: VideoOptions):
    spectrum = compute_spectrum(midi, options.fps, SPECTRUM_BINS)
    renderer = SpectrumRenderer(options.width, options.height, options.color, options.show_grid)
    last_row = spectrum.levels_db.shape[0] - 1

    def render(index: int) -> bytes:
        return renderer.render(spectrum.levels_db[min(index, last_row)], spectrum.frequencies)

    yield from _parallel_in_order(render, _frame_count(midi, options.fps))


def _parallel_in_order(render: Callable[[int], bytes], count: int):
    """Renders frames on several threads (numpy releases the GIL) and yields them in
    order, keeping only a few frames in memory at a time."""
    workers = min(RENDER_THREADS, os.cpu_count() or 1)
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="frame") as pool:
        pending: deque[Future[bytes]] = deque()
        for index in range(count):
            pending.append(pool.submit(render, index))
            if len(pending) >= workers * 2:
                yield pending.popleft().result()
        while pending:
            yield pending.popleft().result()


def _chord_frames(midi: MidiData, options: VideoOptions):
    chords = detect_chords(midi)
    renderer = ChordRenderer(options.width, options.height, options.color, [c.chord.name for c in chords])
    for index in range(_frame_count(midi, options.fps)):
        yield renderer.render(chord_at(chords, index / options.fps))


def chord_at(chords: list[ChordSegment], time: float) -> str | None:
    """Chord to display at `time` (chords sorted by start), holding through short gaps."""
    current = None
    for i, chord in enumerate(chords):
        if chord.start > time:
            break
        next_start = chords[i + 1].start if i + 1 < len(chords) else float("inf")
        if time < chord.end or (time < next_start and time - chord.end < CHORD_HOLD_SECONDS):
            current = chord.chord.name
        else:
            current = None
    return current
