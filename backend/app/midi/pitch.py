"""Pitch helpers: note names and frequencies."""

PITCH_CLASS_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def pitch_to_frequency(pitch: float) -> float:
    """Equal temperament, A4 (MIDI 69) = 440 Hz. Accepts fractional pitches."""
    return 440.0 * 2 ** ((pitch - 69) / 12)


def pitch_class_name(pitch_class: int) -> str:
    return PITCH_CLASS_NAMES[pitch_class % 12]


def pitch_name(pitch: int) -> str:
    """MIDI 60 -> 'C4'."""
    return f"{pitch_class_name(pitch)}{pitch // 12 - 1}"
