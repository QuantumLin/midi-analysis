"""Synthetic frequency spectrum of a MIDI performance over time.

MIDI contains no audio, so the spectrum is modelled from the notes: every note
produces its fundamental plus harmonics with a piano-like envelope (instant attack,
exponential decay, short release). Louder notes are brighter (more energy in the
upper harmonics), lower notes ring longer. The per-frame levels then pass through
analyzer ballistics (instant rise, constant dB fall) like a DAW spectrum analyzer.

The result is a level in dB for every (frame, frequency bin) on a logarithmic
frequency axis from 20 Hz to 20 kHz. A short broadband hammer noise at every attack
lets the upper spectrum react to note onsets like a real piano.
"""

import math
from dataclasses import dataclass

import numpy as np

from app.midi.models import MidiData
from app.midi.pitch import pitch_to_frequency

MIN_HZ = 20.0
MAX_HZ = 20_000.0
MIN_DB = -72.0  # bottom of the display range
MAX_DB = 0.0
HEADROOM_DB = 3.0  # loudest moment of the piece peaks at MAX_DB - HEADROOM_DB

MAX_HARMONICS = 32
RELEASE_SECONDS = 0.25  # fade-out after the sound ends
FALL_DB_PER_SECOND = 36.0  # analyzer ballistics
SILENCE_DB = 60.0  # envelopes below -60 dB are not computed
# Hammer noise: a short broadband burst at each attack, falling 6 dB/octave above the fundamental.
HAMMER_NOISE_LEVEL = 0.03  # amplitude relative to the fundamental
HAMMER_NOISE_DECAY = 0.06  # seconds

# Width (standard deviation) of each partial's peak: constant in Hz at the low end,
# proportional to frequency higher up (~1/28 octave), similar to a smoothed FFT.
MIN_PEAK_WIDTH_HZ = 8.0
RELATIVE_PEAK_WIDTH = 0.025


@dataclass(frozen=True, slots=True)
class Spectrum:
    fps: float
    frequencies: np.ndarray  # (bins,) Hz, log-spaced
    levels_db: np.ndarray  # (frames, bins), MIN_DB..MAX_DB; frame i is at time i / fps


def log_frequencies(bins: int) -> np.ndarray:
    return np.geomspace(MIN_HZ, MAX_HZ, bins)


def compute_spectrum(midi: MidiData, fps: float, bins: int) -> Spectrum:
    frequencies = log_frequencies(bins)
    frame_count = max(1, math.ceil(midi.duration * fps) + 1)
    power = np.zeros((frame_count, bins), dtype=np.float64)

    for note in midi.notes:
        _add_note(power, note.pitch, note.velocity, note.start, note.end, fps, frequencies)

    levels = _to_db(power)
    _apply_ballistics(levels, fps)
    return Spectrum(fps=fps, frequencies=frequencies, levels_db=levels.astype(np.float32))


def _add_note(
    power: np.ndarray, pitch: int, velocity: int, start: float, end: float, fps: float, frequencies: np.ndarray
) -> None:
    f0 = pitch_to_frequency(pitch)
    harmonics = np.arange(1, MAX_HARMONICS + 1)
    partials = f0 * harmonics
    keep = partials < MAX_HZ
    harmonics, partials = harmonics[keep], partials[keep]
    if partials.size == 0:
        return

    loudness = velocity / 127
    rolloff = 1.6 - 0.8 * loudness  # louder -> brighter
    amplitudes = loudness**1.5 / harmonics**rolloff
    decay = np.clip(6.0 * 2 ** (-(pitch - 48) / 18), 0.6, 10.0) / np.sqrt(harmonics)  # seconds

    # Frames in which the note is audible (stop once even the fundamental is inaudible).
    silent_after = SILENCE_DB / 20 * math.log(10)  # time constants until -60 dB
    last_time = min(end + RELEASE_SECONDS * silent_after, start + decay[0] * silent_after)
    first_frame = math.ceil(start * fps)
    last_frame = min(math.floor(last_time * fps), power.shape[0] - 1)
    if last_frame < first_frame:
        return
    times = np.arange(first_frame, last_frame + 1) / fps

    envelope = np.exp(-(times[:, None] - start) / decay[None, :])  # (frames, partials)
    released = times > end
    envelope[released] *= np.exp(-(times[released] - end) / RELEASE_SECONDS)[:, None]
    partial_amplitude = envelope * amplitudes[None, :]

    widths = np.maximum(MIN_PEAK_WIDTH_HZ, partials * RELATIVE_PEAK_WIDTH)
    shapes = np.exp(-0.5 * ((frequencies[None, :] - partials[:, None]) / widths[:, None]) ** 2)  # (partials, bins)

    power[first_frame : last_frame + 1] += (partial_amplitude**2) @ (shapes**2)
    _add_hammer_noise(power, f0, amplitudes[0], start, first_frame, fps, frequencies)


def _add_hammer_noise(
    power: np.ndarray, f0: float, amplitude: float, start: float, first_frame: int, fps: float, frequencies: np.ndarray
) -> None:
    duration = HAMMER_NOISE_DECAY * SILENCE_DB / 20 * math.log(10)
    last_frame = min(math.floor((start + duration) * fps), power.shape[0] - 1)
    if last_frame < first_frame:
        return
    times = np.arange(first_frame, last_frame + 1) / fps
    envelope = HAMMER_NOISE_LEVEL * amplitude * np.exp(-(times - start) / HAMMER_NOISE_DECAY)
    shape = np.where(frequencies >= f0, f0 / frequencies, (frequencies / f0) ** 4)
    power[first_frame : last_frame + 1] += (envelope**2)[:, None] * (shape**2)[None, :]


def _to_db(power: np.ndarray) -> np.ndarray:
    peak = power.max()
    if peak <= 0:
        return np.full(power.shape, MIN_DB)
    reference = peak * 10 ** (HEADROOM_DB / 10)
    with np.errstate(divide="ignore"):
        levels = 10 * np.log10(power / reference)
    return np.clip(levels, MIN_DB, MAX_DB)


def _apply_ballistics(levels: np.ndarray, fps: float) -> None:
    """In place: levels rise instantly but fall at most FALL_DB_PER_SECOND."""
    fall = FALL_DB_PER_SECOND / fps
    for i in range(1, levels.shape[0]):
        np.maximum(levels[i], levels[i - 1] - fall, out=levels[i])


def quantize(levels_db: np.ndarray) -> np.ndarray:
    """Maps MIN_DB..MAX_DB to 0..255 (uint8) for compact transfer."""
    scaled = (levels_db - MIN_DB) / (MAX_DB - MIN_DB) * 255
    return np.clip(np.rint(scaled), 0, 255).astype(np.uint8)
