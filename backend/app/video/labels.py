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
