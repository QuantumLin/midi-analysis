"""Texts shown in the videos, in German and English."""

from app.analysis.achievements import Achievement
from app.analysis.key import Key
from app.midi.pitch import pitch_name
from app.video.options import Language

_TEXTS: dict[str, dict[Language, str]] = {
    "chord": {"de": "Akkord", "en": "Chord"},
    "key": {"de": "Tonart", "en": "Key"},
    "modulation": {"de": "Modulation", "en": "Key change"},
    "notes_per_second": {"de": "Noten pro Sekunde", "en": "Notes per second"},
    "total": {"de": "Gesamt", "en": "Total"},
    "record": {"de": "Rekord", "en": "Record"},
    "new_record": {"de": "Neuer Rekord", "en": "New record"},
    "degree": {"de": "Stufe", "en": "Degree"},
    "in_key": {"de": "in", "en": "in"},
    "achievement": {"de": "Erfolg freigeschaltet", "en": "Achievement unlocked"},
    "motif": {"de": "Motiv", "en": "Motif"},
    "first_appearance": {"de": "Erstes Auftreten", "en": "First appearance"},
    "returns": {"de": "Kehrt zurück", "en": "Returns"},
    "section": {"de": "Abschnitt", "en": "Section"},
    "part": {"de": "Teil", "en": "Part"},
    "new": {"de": "Neu", "en": "New"},
    "final_boss": {"de": "Endgegner", "en": "Final boss"},
    "boss_warning": {"de": "Achtung: Boss naht!", "en": "Warning: boss ahead!"},
    "defeated": {"de": "Besiegt!", "en": "Defeated!"},
    "health": {"de": "HP", "en": "HP"},
    "difficulty": {"de": "Schwierigkeit", "en": "Difficulty"},
    "circle_of_fifths": {"de": "Quintenzirkel", "en": "Circle of fifths"},
    "bingo_title": {"de": "Tastatur-Bingo", "en": "Keyboard bingo"},
    "bingo": {"de": "Bingo!", "en": "Bingo!"},
    "song_wrapped": {"de": "Song Wrapped", "en": "Song Wrapped"},
}

# Boss names by the difficulty factor that dominates the passage (app/analysis/boss_fight.py).
BOSS_NAMES: dict[str, dict[Language, str]] = {
    "speed": {"de": "Notensturm", "en": "Note Storm"},
    "leaps": {"de": "Sprungriese", "en": "Leaping Giant"},
    "chords": {"de": "Akkord-Koloss", "en": "Chord Colossus"},
}

# Bingo fields (app/analysis/bingo.py).
BINGO_LABELS: dict[str, dict[Language, str]] = {
    "free": {"de": "Frei", "en": "Free"},
    "octave": {"de": "Oktave", "en": "Octave"},
    "seventh_chord": {"de": "Septakkord", "en": "7th chord"},
    "deep_bass": {"de": "Tiefer Bass", "en": "Deep bass"},
    "high_notes": {"de": "Höhenflug", "en": "Sky high"},
    "fast_run": {"de": "Blitzlauf", "en": "Fast run"},
    "progression": {"de": "Akkordfolge", "en": "Progression"},
    "pause": {"de": "Pause", "en": "Pause"},
    "motif_return": {"de": "Motiv zurück", "en": "Motif returns"},
    "fortissimo": {"de": "Fortissimo", "en": "Fortissimo"},
    "pianissimo": {"de": "Pianissimo", "en": "Pianissimo"},
    "modulation": {"de": "Modulation", "en": "Key change"},
    "big_chord": {"de": "6-Ton-Akkord", "en": "6-note chord"},
}

# Names of the known chord progressions (app/analysis/harmony.py).
PROGRESSION_NAMES: dict[str, dict[Language, str]] = {
    "pop": {"de": "Die Pop-Formel", "en": "The pop formula"},
    "fifties": {"de": "Doo-Wop-Folge", "en": "Doo-wop progression"},
    "canon": {"de": "Pachelbel-Kanon", "en": "Pachelbel's Canon"},
    "royal_road": {"de": "Royal Road (J-Pop)", "en": "Royal Road (J-pop)"},
    "andalusian": {"de": "Andalusische Kadenz", "en": "Andalusian cadence"},
    "two_five_one": {"de": "Jazz-Kadenz II–V–I", "en": "Jazz ii–V–I"},
    "circle_of_fifths": {"de": "Quintfall", "en": "Circle of fifths"},
}


def text(name: str, language: Language) -> str:
    return _TEXTS[name][language]


def display_accidentals(name: str) -> str:
    """'Bb' -> 'B♭', 'F#m7' -> 'F♯m7' (only right after a note letter, so 'm7b5' stays)."""
    out = []
    for i, char in enumerate(name):
        if char in "#b" and i > 0 and name[i - 1] in "ABCDEFG":
            out.append("♯" if char == "#" else "♭")
        else:
            out.append(char)
    return "".join(out)


def key_name(key: Key, language: Language) -> str:
    """German: 'd-Moll', 'B♭-Dur'; English: 'D minor', 'B♭ major'."""
    tonic = display_accidentals(key.tonic_name)
    if language == "de":
        return f"{tonic.lower() if key.mode == 'minor' else tonic}-{'Moll' if key.mode == 'minor' else 'Dur'}"
    return f"{tonic} {key.mode}"


def progression_text(progression_id: str, count: int, language: Language) -> str:
    """'Die Pop-Formel', 'Die Pop-Formel ×3'."""
    name = PROGRESSION_NAMES[progression_id][language]
    return f"{name} ×{count}" if count > 1 else name


def key_context(key: Key, language: Language) -> str:
    """'in d-Moll' / 'in D minor': what the numerals refer to."""
    return f"{text('in_key', language)} {key_name(key, language)}"


def _seconds(value: float, language: Language) -> str:
    formatted = f"{value:.1f}"
    return formatted.replace(".", ",") if language == "de" else formatted


def achievement_texts(item: Achievement, language: Language) -> tuple[str, str]:
    """(title, detail) of a pop-up."""
    de = language == "de"
    v = item.value
    match item.kind:
        case "big_chord":
            if v > 10:
                return ("Klangwand" if de else "Wall of sound"), (f"{v} Töne auf einmal" if de else f"{v} notes at once")
            return (f"{v}-Finger-Akkord" if de else f"{v}-finger chord"), (
                f"{v} Töne auf einmal" if de else f"{v} notes at once"
            )
        case "leap":
            return ("Riesensprung" if de else "Giant leap"), (f"{v} Tasten weit" if de else f"{v} keys wide")
        case "run":
            seconds = _seconds(item.seconds, language)
            return ("Blitzlauf" if de else "Lightning run"), (
                f"{v} Noten in {seconds} s" if de else f"{v} notes in {seconds} s"
            )
        case "trill":
            seconds = _seconds(item.seconds, language)
            return ("Triller" if de else "Trill"), (f"{v} Anschläge in {seconds} s" if de else f"{v} strikes in {seconds} s")
        case "fortissimo":
            return "Fortissimo!", (f"Anschlagstärke {v} von 127" if de else f"Velocity {v} of 127")
        case "low":
            name = display_accidentals(pitch_name(v))
            return ("Ganz unten" if de else "Rock bottom"), (f"Tiefe Taste {name}" if de else f"Deep key {name}")
        case "high":
            name = display_accidentals(pitch_name(v))
            return ("Ganz oben" if de else "Sky high"), (f"Hohe Taste {name}" if de else f"High key {name}")
        case "range":
            span = f"{display_accidentals(pitch_name(item.low))} – {display_accidentals(pitch_name(item.high))}"
            return (f"{v} Oktaven" if de else f"{v} octaves"), (f"Tonumfang {span}" if de else f"Range {span}")
        case "milestone":
            number = f"{v:,}".replace(",", "." if de else ",")
            return (f"{number} Noten" if de else f"{number} notes"), ("gespielt" if de else "played")
    raise ValueError(item.kind)


def ordinal_en(n: int) -> str:
    """1 -> '1st', 2 -> '2nd', 11 -> '11th', 23 -> '23rd'."""
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def motif_count(number: int, language: Language) -> str:
    """'6. Mal' / '6th time'."""
    return f"{number}. Mal" if language == "de" else f"{ordinal_en(number)} time"


def section_name(label: str, language: Language) -> str:
    """'Teil B' / 'Part B'."""
    return f"{text('part', language)} {label}"


def section_count(number: int, language: Language) -> str:
    """'Neu' for a part heard for the first time, otherwise 'zum 3. Mal' / '3rd time'."""
    if number == 1:
        return text("new", language)
    return f"zum {number}. Mal" if language == "de" else f"{ordinal_en(number)} time"


def bingo_banner(lines: int, language: Language) -> str:
    """'Bingo!' for the first completed line, then '2× Bingo!' ..."""
    banner = text("bingo", language)
    return banner if lines <= 1 else f"{lines}× {banner}"


def decimal(value: float, language: Language) -> str:
    """8.7 -> '8,7' in German."""
    formatted = f"{value:.1f}"
    return formatted.replace(".", ",") if language == "de" else formatted
