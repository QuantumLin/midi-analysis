"""Renders a complete overlay video from parsed MIDI data."""

import os
from collections import deque
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from app.analysis.achievements import find_achievements
from app.analysis.bingo import BingoContext, play_bingo
from app.analysis.boss_fight import find_boss_fight
from app.analysis.chords import ChordSegment, detect_chords
from app.analysis.circle_of_fifths import circle_path
from app.analysis.harmony import analyze_harmony
from app.analysis.key import detect_keys
from app.analysis.keyboard_activity import KeyboardActivity
from app.analysis.note_rate import note_rate, summarize
from app.analysis.spectrum import compute_spectrum
from app.midi.models import MidiData
from app.video.achievement_renderer import AchievementRenderer
from app.video.bingo_renderer import BingoRenderer
from app.video.boss_renderer import BossRenderer
from app.video.chord_renderer import ChordRenderer
from app.video.circle_renderer import CircleRenderer
from app.video.encoder import VideoEncoder
from app.video.harmony_renderer import HarmonyRenderer
from app.video.heatmap_renderer import HeatmapRenderer
from app.video.key_renderer import KeyRenderer
from app.video.neon_overlay import NeonOverlay
from app.video.note_rate_renderer import NoteRateRenderer
from app.video.options import VideoOptions
from app.video.spectrum_renderer import SpectrumRenderer
from app.video.style import Style, using
from app.video.wrapped import collect_facts, wrapped_cards
from app.video.wrapped_renderer import WrappedRenderer

SPECTRUM_BINS = 1024  # interpolated to the pixel columns when drawing
RENDER_THREADS = 8
# The chord field keeps showing the last chord through short gaps (rests, staccato),
# so it doesn't flicker; after a longer silence it is hidden.
CHORD_HOLD_SECONDS = 2.0

ProgressCallback = Callable[[float], None]


@dataclass(frozen=True, slots=True)
class FrameStream:
    """Frames of a video whose length differs from the piece's (e.g. the Wrapped end screen).
    Frame sources normally yield one frame per 1/fps of the piece."""

    count: int
    frames: Iterable[bytes]

    def __iter__(self) -> Iterator[bytes]:
        return iter(self.frames)


def render_video(
    midi: MidiData,
    options: VideoOptions,
    output_base: Path,
    on_progress: ProgressCallback,
    frame_prefix: str | None = None,
) -> Path:
    with using(Style(options.font, options.glow)):  # font and glow for everything drawn below
        frames = _FRAME_SOURCES[options.kind](midi, options)
        if options.scale < 1:
            frames = _scale_frames(frames, options.width, options.height, options.scale)
        frame_count = frames.count if isinstance(frames, FrameStream) else _frame_count(midi, options.fps)
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


def _scale_frame(frame: bytes, width: int, height: int, scale: float) -> bytes:
    scaled_width = max(1, round(width * scale))
    scaled_height = max(1, round(height * scale))
    image = Image.frombytes("RGBA", (width, height), frame).resize(
        (scaled_width, scaled_height), Image.Resampling.LANCZOS
    )
    canvas = Image.new("RGBA", (width, height))
    canvas.alpha_composite(image, ((width - scaled_width) // 2, (height - scaled_height) // 2))
    return canvas.tobytes()


def _scale_frames(
    frames: Iterable[bytes] | FrameStream, width: int, height: int, scale: float
) -> Iterable[bytes] | FrameStream:
    def resize(frame: bytes) -> bytes:
        return _scale_frame(frame, width, height, scale)

    if isinstance(frames, FrameStream):
        return FrameStream(frames.count, map(resize, frames.frames))
    return map(resize, frames)


def _apply_frame(renderer: NeonOverlay, options: VideoOptions) -> None:
    if not options.show_frame:
        renderer.hide_frame()


def _frame_count(midi: MidiData, fps: int) -> int:
    return max(1, int(midi.duration * fps) + 1)


def _spectrum_frames(midi: MidiData, options: VideoOptions):
    spectrum = compute_spectrum(midi, options.fps, SPECTRUM_BINS)
    renderer = SpectrumRenderer(
        options.width, options.height, options.color, options.show_grid, options.spectrum_style
    )
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
    _apply_frame(renderer, options)

    def state(index: int):
        time = index / options.fps
        chord = chord_at(chords, time)
        return renderer.state(names[id(chord)], time - chord.start) if chord else None

    states = [state(i) for i in range(_frame_count(midi, options.fps))]
    yield from _render_states(states, renderer.render_state)


def _key_frames(midi: MidiData, options: VideoOptions):
    renderer = KeyRenderer(options.width, options.height, options.color, options.language, detect_keys(midi))
    _apply_frame(renderer, options)
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
    _apply_frame(renderer, options)
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
    _apply_frame(renderer, options)
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
    _apply_frame(renderer, options)
    states = [renderer.state(i / options.fps) for i in range(_frame_count(midi, options.fps))]
    yield from _render_states(states, renderer.render_state)


def _boss_frames(midi: MidiData, options: VideoOptions):
    renderer = BossRenderer(options.width, options.height, options.color, options.language, find_boss_fight(midi))
    _apply_frame(renderer, options)
    states = [renderer.state(i / options.fps) for i in range(_frame_count(midi, options.fps))]
    yield from _render_states(states, renderer.render_state)


def _circle_frames(midi: MidiData, options: VideoOptions):
    chords = detect_chords(midi)
    keys = detect_keys(midi)
    names = [c.chord.spelled(keys.prefer_flats_at(c.start)) for c in chords]
    renderer = CircleRenderer(options.width, options.height, options.color, options.language, circle_path(chords),
                              names)  # fmt: skip
    _apply_frame(renderer, options)
    index_of = {id(c): i for i, c in enumerate(chords)}

    def state(index: int):
        time = index / options.fps
        chord = chord_at(chords, time)
        return renderer.state(index_of[id(chord)] if chord else None, time)

    states = [state(i) for i in range(_frame_count(midi, options.fps))]
    yield from _render_states(states, renderer.render_state)


def _bingo_frames(midi: MidiData, options: VideoOptions):
    chords = detect_chords(midi)
    keys = detect_keys(midi)
    harmony = analyze_harmony(chords, keys)
    card = play_bingo(BingoContext(midi, chords, keys, harmony.progressions))
    renderer = BingoRenderer(options.width, options.height, options.color, options.language, card)
    _apply_frame(renderer, options)
    states = [renderer.state(i / options.fps) for i in range(_frame_count(midi, options.fps))]
    yield from _render_states(states, renderer.render_state)


def _wrapped_frames(midi: MidiData, options: VideoOptions) -> FrameStream:
    cards = wrapped_cards(collect_facts(midi), options.language)
    renderer = WrappedRenderer(options.width, options.height, options.color, options.language, cards)
    count = renderer.frame_count(options.fps)
    states = [renderer.state(i / options.fps) for i in range(count)]
    return FrameStream(count, _render_states(states, renderer.render_state))


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
    "boss": _boss_frames,
    "circle": _circle_frames,
    "bingo": _bingo_frames,
    "wrapped": _wrapped_frames,
}
