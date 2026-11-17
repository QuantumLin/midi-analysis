"""Form analysis: the piece split into sections, equal sections share a letter (A B A C ...).

Method (basic version, after Foote 2000):
1. Every FRAME_SECONDS the music is described by a feature vector: which pitch classes
   sound (harmony), how many notes start (density) and how high the music is (register),
   averaged over CONTEXT_SECONDS so single chords don't dominate.
2. A self-similarity matrix compares every moment with every other one. Section
   boundaries are where the music before and after a moment differ most ("novelty",
   a checkerboard kernel slid along the diagonal); peaks at least MIN_SECTION_SECONDS
   apart become boundaries.
3. Two sections are the same part when their course is similar moment by moment
   (mean similarity along the diagonal). Parts are lettered in order of first appearance.
"""

from dataclasses import dataclass

import numpy as np

from app.midi.models import MidiData

FRAME_SECONDS = 0.5
CONTEXT_SECONDS = 3.0
KERNEL_SECONDS = 5.0  # half width of the novelty kernel
MIN_SECTION_SECONDS = 6.0
NOVELTY_THRESHOLD = 0.25  # in standard deviations above the mean novelty
SAME_PART_SIMILARITY = 0.85
DENSITY_WEIGHT = 0.5
REGISTER_WEIGHT = 0.5


@dataclass(frozen=True, slots=True)
class Section:
    start: float
    end: float
    label: str  # "A", "B", ...
    number: int  # 1 = first time this part is heard


def find_sections(midi: MidiData) -> list[Section]:
    if not midi.notes or midi.duration <= 0:
        return []
    features = _features(midi)
    similarity = _self_similarity(features)
    boundaries = _boundaries(_novelty(similarity), len(features))
    return _label(boundaries, similarity, midi.duration)


def _features(midi: MidiData) -> np.ndarray:
    frames = max(1, int(np.ceil(midi.duration / FRAME_SECONDS)))
    chroma = np.zeros((frames, 12))
    onsets = np.zeros(frames)
    pitch_sum = np.zeros(frames)
    pitch_weight = np.zeros(frames)
    for note in midi.notes:
        first = int(note.start / FRAME_SECONDS)
        last = min(frames - 1, int(max(note.key_end - 1e-9, note.start) / FRAME_SECONDS))
        for f in range(first, last + 1):
            overlap = min(note.key_end, (f + 1) * FRAME_SECONDS) - max(note.start, f * FRAME_SECONDS)
            weight = max(overlap, 0.0) + 1e-3
            chroma[f, note.pitch % 12] += weight
            pitch_sum[f] += note.pitch * weight
            pitch_weight[f] += weight
        onsets[min(first, frames - 1)] += 1

    context = max(1, round(CONTEXT_SECONDS / FRAME_SECONDS))
    chroma = _moving_average(chroma, context)
    norms = np.linalg.norm(chroma, axis=1, keepdims=True)
    chroma = np.divide(chroma, norms, out=np.zeros_like(chroma), where=norms > 0)
    density = _moving_average(onsets[:, None], context)[:, 0]
    density = density / density.max() if density.max() > 0 else density
    register = _moving_average(pitch_sum[:, None], context)[:, 0] / np.maximum(
        _moving_average(pitch_weight[:, None], context)[:, 0], 1e-9
    )
    register = np.where(register > 0, (register - 21) / 87, 0.0)  # piano range -> 0..1
    return np.column_stack([chroma, DENSITY_WEIGHT * density, REGISTER_WEIGHT * register])


def _moving_average(values: np.ndarray, width: int) -> np.ndarray:
    kernel = np.ones(width) / width
    return np.column_stack([np.convolve(values[:, c], kernel, mode="same") for c in range(values.shape[1])])


def _self_similarity(features: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(features, axis=1, keepdims=True)
    unit = np.divide(features, norms, out=np.zeros_like(features), where=norms > 0)
    return unit @ unit.T


def _novelty(similarity: np.ndarray) -> np.ndarray:
    """Checkerboard kernel along the diagonal: high where past and future differ."""
    half = max(1, round(KERNEL_SECONDS / FRAME_SECONDS))
    size = len(similarity)
    taper = np.exp(-0.5 * (np.linspace(-1, 1, 2 * half) * 2) ** 2)
    sign = np.concatenate([-np.ones(half), np.ones(half)])
    kernel = np.outer(sign * taper, sign * taper)
    padded = np.pad(similarity, half, mode="edge")
    novelty = np.array([(padded[i : i + 2 * half, i : i + 2 * half] * kernel).sum() for i in range(size)])
    return np.maximum(novelty, 0)


def _boundaries(novelty: np.ndarray, frames: int) -> list[int]:
    """Frame indices where sections start (always including 0)."""
    min_gap = round(MIN_SECTION_SECONDS / FRAME_SECONDS)
    threshold = novelty.mean() + NOVELTY_THRESHOLD * novelty.std()
    candidates = [
        i
        for i in range(1, frames - 1)
        if novelty[i] >= threshold and novelty[i] == novelty[max(0, i - min_gap) : i + min_gap + 1].max()
    ]
    boundaries = [0]
    for i in sorted(candidates, key=lambda i: -novelty[i]):  # strongest first
        if all(abs(i - b) >= min_gap for b in boundaries) and frames - i >= min_gap:
            boundaries.append(i)
    return sorted(boundaries)


def _label(boundaries: list[int], similarity: np.ndarray, duration: float) -> list[Section]:
    frames = len(similarity)
    spans = [(b, boundaries[k + 1] if k + 1 < len(boundaries) else frames) for k, b in enumerate(boundaries)]
    letters: list[str] = []
    first_span: dict[str, tuple[int, int]] = {}
    sections: list[Section] = []
    counts: dict[str, int] = {}
    for start, end in spans:
        label = next(
            (letter for letter in letters if _diagonal_similarity(similarity, first_span[letter], (start, end))
             >= SAME_PART_SIMILARITY),
            None,
        )  # fmt: skip
        if label is None:
            label = chr(ord("A") + len(letters))
            letters.append(label)
            first_span[label] = (start, end)
        counts[label] = counts.get(label, 0) + 1
        sections.append(
            Section(start * FRAME_SECONDS, min(end * FRAME_SECONDS, duration), label, counts[label])
        )
    return sections


def _diagonal_similarity(similarity: np.ndarray, a: tuple[int, int], b: tuple[int, int]) -> float:
    """Mean similarity of the two sections compared moment by moment (aligned at their starts)."""
    length = min(a[1] - a[0], b[1] - b[0])
    if length <= 0:
        return 0.0
    return float(np.mean([similarity[a[0] + k, b[0] + k] for k in range(length)]))
