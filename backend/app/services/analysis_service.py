"""Runs all analyses on an uploaded MIDI file and assembles the API response."""

import base64

from app.analysis.chords import detect_chords
from app.analysis.spectrum import MAX_DB, MAX_HZ, MIN_DB, MIN_HZ, compute_spectrum, quantize
from app.analysis.timeline import compute_timeline
from app.api.schemas import AnalysisResponse, ChordOut, SpectrumOut, TimelineOut, TimelinePointOut
from app.midi.parser import parse_midi
from app.midi.pitch import pitch_class_name

# The in-app preview needs far less resolution than the exported video.
PREVIEW_FPS = 20
PREVIEW_BINS = 256


def analyze_midi(data: bytes, file_name: str) -> AnalysisResponse:
    midi = parse_midi(data)
    timeline = compute_timeline(midi)
    spectrum = compute_spectrum(midi, PREVIEW_FPS, PREVIEW_BINS)
    chords = detect_chords(midi)
    levels = quantize(spectrum.levels_db)

    return AnalysisResponse(
        file_name=file_name,
        duration_seconds=round(midi.duration, 3),
        note_count=len(midi.notes),
        percussion_note_count=len(midi.percussion_notes),
        timeline=TimelineOut(
            step_seconds=timeline.step_seconds,
            points=[
                TimelinePointOut(time=p.time, velocity=p.velocity, active_notes=p.active_notes)
                for p in timeline.points
            ],
        ),
        spectrum=SpectrumOut(
            fps=PREVIEW_FPS,
            bins=PREVIEW_BINS,
            frame_count=levels.shape[0],
            min_hz=MIN_HZ,
            max_hz=MAX_HZ,
            min_db=MIN_DB,
            max_db=MAX_DB,
            levels=base64.b64encode(levels.tobytes()).decode("ascii"),
        ),
        chords=[
            ChordOut(
                start=round(c.start, 3),
                end=round(c.end, 3),
                name=c.chord.name,
                root=pitch_class_name(c.chord.root),
                quality=c.chord.quality,
                bass=pitch_class_name(c.chord.bass),
                notes=c.note_names,
            )
            for c in chords
        ],
    )
