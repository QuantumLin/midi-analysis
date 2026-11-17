"""Pitch helpers: note names and frequencies.

Names use ASCII accidentals ("C#", "Bb"); the UI and the videos render them as ♯/♭.
Whether a black key is spelled with a sharp or a flat depends on the key of the piece.
"""

SHARP_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
FLAT_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
LOWEST_PIANO_KEY = 21  # A0
HIGHEST_PIANO_KEY = 108  # C8


def pitch_to_frequency(pitch: float) -> float:
    """Equal temperament, A4 (MIDI 69) = 440 Hz. Accepts fractional pitches."""
    return 440.0 * 2 ** ((pitch - 69) / 12)


def pitch_class_name(pitch_class: int, prefer_flats: bool = False) -> str:
    return (FLAT_NAMES if prefer_flats else SHARP_NAMES)[pitch_class % 12]


def pitch_name(pitch: int, prefer_flats: bool = False) -> str:
    """MIDI 60 -> 'C4'."""
    return f"{pitch_class_name(pitch, prefer_flats)}{pitch // 12 - 1}"


def is_black_key(pitch: int) -> bool:
    return pitch % 12 in (1, 3, 6, 8, 10)
