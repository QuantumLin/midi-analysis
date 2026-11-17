"""Runs all analyses on an uploaded MIDI file and assembles the API response."""

import base64

from app.analysis.achievements import find_achievements
from app.analysis.chords import detect_chords
from app.analysis.harmony import analyze_harmony
from app.analysis.key import Key, KeyAnalysis, detect_keys
from app.analysis.motifs import find_motifs
from app.analysis.sections import find_sections
from app.analysis.note_rate import note_rate, summarize
from app.analysis.spectrum import MAX_DB, MAX_HZ, MIN_DB, MIN_HZ, compute_spectrum, quantize
from app.api.schemas import (
    AchievementOut,
    AnalysisResponse,
    ChordOut,
    KeyOut,
    KeySegmentOut,
    KeysOut,
    LocalizedOut,
    MotifOccurrenceOut,
    MotifOut,
    NoteRateOut,
    NoteRecordOut,
    NotesOut,
    ProgressionOut,
    SectionOut,
    SpectrumOut,
)
from app.midi.parser import parse_midi
from app.midi.pitch import pitch_class_name
from app.video.labels import achievement_texts, progression_text

# The in-app preview needs far less resolution than the exported videos.
PREVIEW_FPS = 20
PREVIEW_BINS = 256


def analyze_midi(data: bytes, file_name: str) -> AnalysisResponse:
    midi = parse_midi(data)
    spectrum = compute_spectrum(midi, PREVIEW_FPS, PREVIEW_BINS)
    chords = detect_chords(midi)
    keys = detect_keys(midi)
    harmony = analyze_harmony(chords, keys)
    rate = summarize(note_rate(midi), midi.duration, PREVIEW_FPS)
    levels = quantize(spectrum.levels_db)

    return AnalysisResponse(
        file_name=file_name,
        duration_seconds=round(midi.duration, 3),
        note_count=len(midi.notes),
        percussion_note_count=len(midi.percussion_notes),
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
        chords=[_chord_out(c, keys, numeral) for c, numeral in zip(chords, harmony.numerals)],
        keys=KeysOut(
            overall=_key_out(keys.overall) if keys.overall else None,
            segments=[
                KeySegmentOut(start=round(s.start, 3), end=round(s.end, 3), key=_key_out(s.key))
                for s in keys.segments
            ],
        ),
        note_rate=NoteRateOut(
            fps=rate.fps,
            values=rate.values.tolist(),
            peak_value=rate.peak_value,
            peak_time=round(rate.peak_time, 3),
            records=[NoteRecordOut(time=round(r.time, 3), value=r.value) for r in rate.records],
        ),
        progressions=[
            ProgressionOut(
                time=round(h.time, 3),
                end=round(h.end, 3),
                id=h.id,
                count=h.count,
                name=_localized(lambda language: progression_text(h.id, h.count, language)),
            )
            for h in harmony.progressions
        ],
        achievements=[
            AchievementOut(
                time=round(a.time, 3),
                end=round(a.end, 3),
                kind=a.kind,
                title=_localized(lambda language: achievement_texts(a, language)[0]),
                detail=_localized(lambda language: achievement_texts(a, language)[1]),
            )
            for a in find_achievements(midi)
        ],
        motifs=[
            MotifOut(
                label=m.label,
                length=m.length,
                occurrences=[
                    MotifOccurrenceOut(start=round(o.start, 3), end=round(o.end, 3), number=o.number)
                    for o in m.occurrences
                ],
            )
            for m in find_motifs(midi)
        ],
        sections=[
            SectionOut(start=round(s.start, 3), end=round(s.end, 3), label=s.label, number=s.number)
            for s in find_sections(midi)
        ],
        notes=NotesOut(
            start=[round(n.start, 3) for n in midi.notes],
            end=[round(n.key_end, 3) for n in midi.notes],
            pitch=[n.pitch for n in midi.notes],
        ),
    )


def _key_out(key: Key) -> KeyOut:
    return KeyOut(tonic=key.tonic_name, mode=key.mode)


def _localized(make) -> LocalizedOut:
    return LocalizedOut(de=make("de"), en=make("en"))


def _chord_out(segment, keys: KeyAnalysis, numeral: str) -> ChordOut:
    """Chord names are spelled to fit the key at that moment (Bb in d minor, A# in B major)."""
    flats = keys.prefer_flats_at(segment.start)
    chord = segment.chord
    return ChordOut(
        start=round(segment.start, 3),
        end=round(segment.end, 3),
        name=chord.spelled(flats),
        root=pitch_class_name(chord.root, flats),
        quality=chord.quality,
        bass=pitch_class_name(chord.bass, flats),
        notes=segment.spelled_note_names(flats),
        numeral=numeral or None,
    )
