"""Renders a complete overlay video from parsed MIDI data."""

import os
from collections import deque
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import numpy as np

from app.analysis.achievements import find_achievements
from app.analysis.chords import ChordSegment, detect_chords
from app.analysis.harmony import analyze_harmony
from app.analysis.key import detect_keys
from app.analysis.keyboard_activity import KeyboardActivity
from app.analysis.note_rate import note_rate, summarize
from app.analysis.spectrum import compute_spectrum
from app.midi.models import MidiData
from app.video.achievement_renderer import AchievementRenderer
from app.video.chord_renderer import ChordRenderer
from app.video.encoder import VideoEncoder
from app.video.harmony_renderer import HarmonyRenderer
from app.video.heatmap_renderer import HeatmapRenderer
from app.video.key_renderer import KeyRenderer
from app.video.note_rate_renderer import NoteRateRenderer
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
    frames = _FRAME_SOURCES[options.kind](midi, options)

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


def _render_states(states: list, render_state: Callable[[object], bytes]):
    """Draws each run of identical consecutive states once (in parallel) and repeats it."""
    runs: list[tuple[object, int]] = []
    for state in states:
        if runs and runs[-1][0] == state:
            runs[-1] = (state, runs[-1][1] + 1)
        else:
            runs.append((state, 1))
    frames = _parallel_in_order(lambda i: render_state(runs[i][0]), len(runs))
    for (_, length), frame in zip(runs, frames):
        for _ in range(length):
            yield frame


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
    keys = detect_keys(midi)
    names = {id(c): c.chord.spelled(keys.prefer_flats_at(c.start)) for c in chords}
    renderer = ChordRenderer(options.width, options.height, options.color, options.language, list(names.values()))

    def state(index: int):
        time = index / options.fps
        chord = chord_at(chords, time)
        return renderer.state(names[id(chord)], time - chord.start) if chord else None

    states = [state(i) for i in range(_frame_count(midi, options.fps))]
    yield from _render_states(states, renderer.render_state)


def _key_frames(midi: MidiData, options: VideoOptions):
    renderer = KeyRenderer(options.width, options.height, options.color, options.language, detect_keys(midi))
    states = [renderer.state(i / options.fps) for i in range(_frame_count(midi, options.fps))]
    yield from _render_states(states, renderer.render_state)


def _note_rate_frames(midi: MidiData, options: VideoOptions):
    rate = note_rate(midi)
    summary = summarize(rate, midi.duration, options.fps)
    times = np.arange(_frame_count(midi, options.fps)) / options.fps
    values = rate.rate_at(times)
    totals = rate.total_at(times)
    best = np.maximum.accumulate(values)
    renderer = NoteRateRenderer(
        options.width,
        options.height,
        options.color,
        options.language,
        max_rate=int(values.max(initial=0)),
        max_total=int(totals.max(initial=0)),
        records=summary.records,
    )
    states = [
        renderer.state(float(time), int(values[i]), int(totals[i]), int(best[i])) for i, time in enumerate(times)
    ]
    yield from _render_states(states, renderer.render_state)


def _heatmap_frames(midi: MidiData, options: VideoOptions):
    activity = KeyboardActivity(midi)
    renderer = HeatmapRenderer(options.width, options.height, options.color)

    def render(index: int) -> bytes:
        time = index / options.fps
        counts = activity.press_counts(time)
        # Counts only grow, so the current maximum is also the running maximum.
        return renderer.render(counts, activity.held(time), int(counts.max()))

    yield from _parallel_in_order(render, _frame_count(midi, options.fps))


def _harmony_frames(midi: MidiData, options: VideoOptions):
    chords = detect_chords(midi)
    harmony = analyze_harmony(chords, detect_keys(midi))
    renderer = HarmonyRenderer(options.width, options.height, options.color, options.language, harmony)
    index_of = {id(c): i for i, c in enumerate(chords)}

    def state(index: int):
        time = index / options.fps
        chord = chord_at(chords, time)
        return renderer.state(index_of[id(chord)] if chord else None, time)

    states = [state(i) for i in range(_frame_count(midi, options.fps))]
    yield from _render_states(states, renderer.render_state)


def _achievement_frames(midi: MidiData, options: VideoOptions):
    renderer = AchievementRenderer(
        options.width, options.height, options.color, options.language, find_achievements(midi)
    )
    states = [renderer.state(i / options.fps) for i in range(_frame_count(midi, options.fps))]
    yield from _render_states(states, renderer.render_state)


def chord_at(chords: list[ChordSegment], time: float) -> ChordSegment | None:
    """Chord to display at `time` (chords sorted by start), holding through short gaps."""
    current = None
    for i, chord in enumerate(chords):
        if chord.start > time:
            break
        next_start = chords[i + 1].start if i + 1 < len(chords) else float("inf")
        if time < chord.end or (time < next_start and time - chord.end < CHORD_HOLD_SECONDS):
            current = chord
        else:
            current = None
    return current


_FRAME_SOURCES = {
    "spectrum": _spectrum_frames,
    "chords": _chord_frames,
    "key": _key_frames,
    "note_rate": _note_rate_frames,
    "heatmap": _heatmap_frames,
    "harmony": _harmony_frames,
    "achievements": _achievement_frames,
}
