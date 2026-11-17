"""Texts shown in the videos, in German and English."""

from app.analysis.key import Key
from app.video.options import Language

_TEXTS: dict[str, dict[Language, str]] = {
    "key": {"de": "Tonart", "en": "Key"},
    "modulation": {"de": "Modulation", "en": "Key change"},
    "notes_per_second": {"de": "Noten/s", "en": "notes/s"},
    "total": {"de": "Gesamt", "en": "Total"},
    "record": {"de": "Rekord", "en": "Record"},
    "new_record": {"de": "Neuer Rekord", "en": "New record"},
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
