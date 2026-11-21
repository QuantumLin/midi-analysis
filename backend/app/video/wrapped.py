"""Song Wrapped: the piece in numbers, as cards for an end screen ("Spotify Wrapped" style).

collect_facts() runs the analyses once; each card builder turns the facts into a
(title, value) pair in one language, or None if it has nothing to say for this piece.

To add a card, write a builder and append it to CARDS (the order is the order on screen).
"""

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from app.analysis.achievements import Achievement, find_achievements
from app.analysis.boss_fight import BossFight, find_boss_fight
from app.analysis.chords import ChordSegment, detect_chords
from app.analysis.key import KeyAnalysis, detect_keys
from app.analysis.note_rate import NoteRateSummary, note_rate, summarize
from app.midi.models import MidiData
from app.midi.pitch import pitch_name
from app.video.labels import BOSS_NAMES, Language, display_accidentals, key_name

MAX_CARDS = 7
FACTS_FPS = 20  # resolution of the note-rate curve


@dataclass(frozen=True, slots=True)
class SongFacts:
    midi: MidiData
    chords: list[ChordSegment]
    chord_names: list[str]  # spelled for the key, per chord
    keys: KeyAnalysis
    rate: NoteRateSummary
    boss: BossFight | None
    achievements: list[Achievement]


def collect_facts(midi: MidiData) -> SongFacts:
    chords = detect_chords(midi)
    keys = detect_keys(midi)
    return SongFacts(
        midi=midi,
        chords=chords,
        chord_names=[c.chord.spelled(keys.prefer_flats_at(c.start)) for c in chords],
        keys=keys,
        rate=summarize(note_rate(midi), midi.duration, FACTS_FPS),
        boss=find_boss_fight(midi),
        achievements=find_achievements(midi),
    )


@dataclass(frozen=True, slots=True)
class WrappedCard:
    id: str
    title: str
    value: str


def _number(value: int, language: Language) -> str:
    return f"{value:,}".replace(",", "." if language == "de" else ",")


def _clock(seconds: float) -> str:
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def _de_en(language: Language, de: str, en: str) -> str:
    return de if language == "de" else en


# --- cards --------------------------------------------------------------------------------

Card = tuple[str, str] | None


def _notes(f: SongFacts, lang: Language) -> Card:
    if not f.midi.notes:
        return None
    return _de_en(lang, "Gespielte Noten", "Notes played"), _number(len(f.midi.notes), lang)


def _fastest(f: SongFacts, lang: Language) -> Card:
    if f.rate.peak_value == 0:
        return None
    at = _clock(f.rate.peak_time)
    return _de_en(lang, "Schnellste Stelle", "Fastest moment"), _de_en(
        lang, f"{f.rate.peak_value} Noten/s bei {at}", f"{f.rate.peak_value} notes/s at {at}"
    )


def _favourite_chord(f: SongFacts, lang: Language) -> Card:
    if not f.chord_names:
        return None
    name, count = Counter(f.chord_names).most_common(1)[0]
    return _de_en(lang, "Lieblingsakkord", "Favourite chord"), f"{display_accidentals(name)} ({count}×)"


def _key(f: SongFacts, lang: Language) -> Card:
    if f.keys.overall is None:
        return None
    changes = len(f.keys.segments) - 1
    value = key_name(f.keys.overall, lang)
    if changes:
        value += _de_en(lang, f" · {changes} Modulation" + ("en" if changes > 1 else ""),
                        f" · {changes} key change" + ("s" if changes > 1 else ""))  # fmt: skip
    return _de_en(lang, "Tonart", "Key"), value


def _range(f: SongFacts, lang: Language) -> Card:
    if not f.midi.notes:
        return None
    low = min(n.pitch for n in f.midi.notes)
    high = max(n.pitch for n in f.midi.notes)
    span = f"{display_accidentals(pitch_name(low))} – {display_accidentals(pitch_name(high))}"
    return _de_en(lang, "Tonumfang", "Range"), span


def _boss(f: SongFacts, lang: Language) -> Card:
    if f.boss is None:
        return None
    difficulty = f"{f.boss.difficulty:.1f}".replace(".", "," if lang == "de" else ".")
    return _de_en(lang, "Endgegner", "Final boss"), f"{BOSS_NAMES[f.boss.factor][lang]} · {difficulty}/10"


def _achievements(f: SongFacts, lang: Language) -> Card:
    if not f.achievements:
        return None
    return _de_en(lang, "Achievements", "Achievements"), str(len(f.achievements))


CARDS: tuple[tuple[str, Callable[[SongFacts, Language], Card]], ...] = (
    ("notes", _notes),
    ("fastest", _fastest),
    ("favourite_chord", _favourite_chord),
    ("key", _key),
    ("range", _range),
    ("boss", _boss),
    ("achievements", _achievements),
)


def wrapped_cards(facts: SongFacts, language: Language) -> list[WrappedCard]:
    cards = []
    for card_id, build in CARDS:
        built = build(facts, language)
        if built is not None:
            cards.append(WrappedCard(card_id, *built))
    return cards[:MAX_CARDS]
