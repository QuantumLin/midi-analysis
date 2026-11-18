"""Runs all analyses on an uploaded MIDI file and assembles the API response."""

import base64

from app.analysis.achievements import find_achievements
from app.analysis.bingo import BingoContext, play_bingo
from app.analysis.boss_fight import find_boss_fight
from app.analysis.chords import detect_chords
from app.analysis.circle_of_fifths import circle_position
from app.analysis.harmony import analyze_harmony
from app.analysis.key import Key, KeyAnalysis, detect_keys
from app.analysis.motifs import find_motifs
from app.analysis.sections import find_sections
from app.analysis.note_rate import note_rate, summarize
from app.analysis.spectrum import MAX_DB, MAX_HZ, MIN_DB, MIN_HZ, compute_spectrum, quantize
from app.api.schemas import (
    AchievementOut,
    AnalysisResponse,
    BingoFieldOut,
    BingoLineOut,
    BingoOut,
    BossOut,
    ChordOut,
    CirclePositionOut,
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
    WrappedCardOut,
)
from app.midi.parser import parse_midi
from app.midi.pitch import pitch_class_name
from app.video.labels import BINGO_LABELS, BOSS_NAMES, achievement_texts, progression_text
from app.video.wrapped import SongFacts, wrapped_cards

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
    motifs = find_motifs(midi)
    achievements = find_achievements(midi)
    boss = find_boss_fight(midi)
    bingo = play_bingo(BingoContext(midi, chords, keys, harmony.progressions, motifs))
    chord_names = [c.chord.spelled(keys.prefer_flats_at(c.start)) for c in chords]
    facts = SongFacts(midi, chords, chord_names, keys, rate, boss, motifs, achievements)
    cards = {language: wrapped_cards(facts, language) for language in ("de", "en")}

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
            for a in achievements
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
            for m in motifs
        ],
        sections=[
            SectionOut(start=round(s.start, 3), end=round(s.end, 3), label=s.label, number=s.number)
            for s in find_sections(midi)
        ],
        boss=BossOut(
            start=round(boss.start, 3),
            end=round(boss.end, 3),
            factor=boss.factor,
            name=_localized(lambda language: BOSS_NAMES[boss.factor][language]),
            difficulty=boss.difficulty,
            hits=[round(float(t), 3) for t in boss.hits],
        )
        if boss
        else None,
        bingo=BingoOut(
            fields=[
                BingoFieldOut(
                    id=f.id,
                    label=_localized(lambda language: BINGO_LABELS[f.id][language]),
                    time=None if f.time is None else round(f.time, 3),
                )
                for f in bingo.fields
            ],
            lines=[BingoLineOut(cells=list(line.cells), time=round(line.time, 3)) for line in bingo.lines],
        ),
        wrapped=[
            WrappedCardOut(
                id=de.id,
                title=LocalizedOut(de=de.title, en=en.title),
                value=LocalizedOut(de=de.value, en=en.value),
            )
            for de, en in zip(cards["de"], cards["en"])
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
        circle=_circle_out(chord),
    )


def _circle_out(chord) -> CirclePositionOut:
    position = circle_position(chord)
    return CirclePositionOut(ring=position.ring, index=position.index, name=position.name)
