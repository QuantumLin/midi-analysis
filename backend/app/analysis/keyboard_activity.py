"""Per-key activity on the 88-key piano, for the keyboard heatmap.

For any moment it answers: how often has each key been pressed so far, and which
keys are held down right now. Notes outside the piano range are clamped to A0/C8.
"""

import numpy as np

from app.midi.models import MidiData
from app.midi.pitch import HIGHEST_PIANO_KEY, LOWEST_PIANO_KEY

KEY_COUNT = HIGHEST_PIANO_KEY - LOWEST_PIANO_KEY + 1  # 88


class KeyboardActivity:
    def __init__(self, midi: MidiData):
        keys = np.clip([n.pitch for n in midi.notes], LOWEST_PIANO_KEY, HIGHEST_PIANO_KEY) - LOWEST_PIANO_KEY
        self.keys = np.asarray(keys, dtype=np.int64)
        self.starts = np.array([n.start for n in midi.notes], dtype=np.float64)
        self.key_ends = np.array([n.key_end for n in midi.notes], dtype=np.float64)
        order = np.argsort(self.starts, kind="stable")
        self.keys, self.starts, self.key_ends = self.keys[order], self.starts[order], self.key_ends[order]

    def press_counts(self, time: float) -> np.ndarray:
        """Presses per key (index 0 = A0) with start <= time."""
        pressed_so_far = np.searchsorted(self.starts, time, side="right")
        return np.bincount(self.keys[:pressed_so_far], minlength=KEY_COUNT)

    def held(self, time: float) -> np.ndarray:
        """Boolean per key: held down at `time`."""
        pressed_so_far = np.searchsorted(self.starts, time, side="right")
        active = self.key_ends[:pressed_so_far] > time
        held = np.zeros(KEY_COUNT, dtype=bool)
        held[self.keys[:pressed_so_far][active]] = True
        return held
