"""Notes per second over time, with the peak and "new record" moments.

The rate at time t is the number of key presses in the second before t (a chord of
four notes counts four). A record is reported whenever the rate beats every value
seen so far, once the piece has been running for a few seconds; records in quick
succession (one fast run climbing 18, 19, 20 ...) are merged into one event.
"""

from dataclasses import dataclass

import numpy as np

from app.midi.models import MidiData

WINDOW_SECONDS = 1.0
RECORD_WARMUP_SECONDS = 5.0  # the opening always sets "records"; ignore it
RECORD_MERGE_SECONDS = 2.0


@dataclass(frozen=True, slots=True)
class NoteRateRecord:
    time: float  # when the record value was reached
    value: int


@dataclass(frozen=True, slots=True)
class NoteRate:
    onsets: np.ndarray  # sorted note start times

    def rate_at(self, times: np.ndarray) -> np.ndarray:
        """Key presses within (t - 1 s, t] for every t."""
        upper = np.searchsorted(self.onsets, times, side="right")
        lower = np.searchsorted(self.onsets, times - WINDOW_SECONDS, side="right")
        return upper - lower

    def total_at(self, times: np.ndarray) -> np.ndarray:
        """Key presses up to and including t."""
        return np.searchsorted(self.onsets, times, side="right")


@dataclass(frozen=True, slots=True)
class NoteRateSummary:
    fps: float
    values: np.ndarray  # rate per frame (frame i at time i / fps)
    peak_value: int
    peak_time: float
    records: list[NoteRateRecord]


def note_rate(midi: MidiData) -> NoteRate:
    return NoteRate(onsets=np.sort(np.array([n.start for n in midi.notes], dtype=np.float64)))


def summarize(rate: NoteRate, duration: float, fps: float) -> NoteRateSummary:
    times = np.arange(int(duration * fps) + 1) / fps
    values = rate.rate_at(times)
    peak_index = int(np.argmax(values)) if values.size else 0
    return NoteRateSummary(
        fps=fps,
        values=values,
        peak_value=int(values[peak_index]) if values.size else 0,
        peak_time=float(times[peak_index]) if values.size else 0.0,
        records=find_records(times, values),
    )


def find_records(times: np.ndarray, values: np.ndarray) -> list[NoteRateRecord]:
    records: list[NoteRateRecord] = []
    warmup = times < RECORD_WARMUP_SECONDS
    best = int(values[warmup].max()) if warmup.any() else 0
    for time, value in zip(times[~warmup], values[~warmup]):
        if value <= best:
            continue
        best = int(value)
        if records and time - records[-1].time < RECORD_MERGE_SECONDS:
            records[-1] = NoteRateRecord(float(time), best)
        else:
            records.append(NoteRateRecord(float(time), best))
    return records
