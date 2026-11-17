"""Parses MIDI bytes into timed notes (in seconds, tempo changes applied)."""

import io
from collections import defaultdict

import mido

from app.midi.models import PERCUSSION_CHANNEL, MidiData, Note

SUSTAIN_PEDAL_CC = 64


class MidiParseError(ValueError):
    """Raised when the input is not a readable MIDI file."""


def parse_midi(data: bytes) -> MidiData:
    try:
        midi_file = mido.MidiFile(file=io.BytesIO(data))
    except Exception as exc:  # mido raises a variety of errors for broken input
        raise MidiParseError(f"Not a valid MIDI file: {exc}") from exc

    if midi_file.type == 2:
        raise MidiParseError("MIDI type 2 (asynchronous tracks) is not supported.")

    return _collect_notes(midi_file)


def _collect_notes(midi_file: mido.MidiFile) -> MidiData:
    result = MidiData()
    now = 0.0
    # (channel, pitch) -> stack of (start, velocity); a stack handles re-struck notes.
    sounding: dict[tuple[int, int], list[tuple[float, int]]] = defaultdict(list)
    # Notes released while the sustain pedal is down keep sounding until pedal-up.
    pedal_down: dict[int, bool] = defaultdict(bool)
    # channel -> [(pitch, start, velocity, key_end)]
    sustained: dict[int, list[tuple[int, float, int, float]]] = defaultdict(list)

    def finish(
        channel: int, pitch: int, start: float, velocity: int, end: float, key_end: float | None = None
    ) -> None:
        if end <= start:
            return
        note = Note(
            pitch=pitch,
            velocity=velocity,
            start=start,
            end=end,
            channel=channel,
            key_end=end if key_end is None else key_end,
        )
        target = result.percussion_notes if channel == PERCUSSION_CHANNEL else result.notes
        target.append(note)

    try:
        messages = list(midi_file)  # merged tracks; msg.time is delta time in seconds
    except Exception as exc:
        raise MidiParseError(f"Could not read MIDI events: {exc}") from exc

    for msg in messages:
        now += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            key = (msg.channel, msg.note)
            # A re-strike of a sustained note ends the sustained copy.
            for i, (pitch, start, vel, key_end) in enumerate(sustained[msg.channel]):
                if pitch == msg.note:
                    finish(msg.channel, pitch, start, vel, now, key_end)
                    del sustained[msg.channel][i]
                    break
            sounding[key].append((now, msg.velocity))
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            key = (msg.channel, msg.note)
            if not sounding[key]:
                continue  # note-off without matching note-on
            start, velocity = sounding[key].pop(0)
            if pedal_down[msg.channel]:
                sustained[msg.channel].append((msg.note, start, velocity, now))
            else:
                finish(msg.channel, msg.note, start, velocity, now)
        elif msg.type == "control_change" and msg.control == SUSTAIN_PEDAL_CC:
            is_down = msg.value >= 64
            if pedal_down[msg.channel] and not is_down:
                for pitch, start, velocity, key_end in sustained.pop(msg.channel, []):
                    finish(msg.channel, pitch, start, velocity, now, key_end)
            pedal_down[msg.channel] = is_down

    # Close anything still open at the end of the file.
    for (channel, pitch), starts in sounding.items():
        for start, velocity in starts:
            finish(channel, pitch, start, velocity, now)
    for channel, notes in sustained.items():
        for pitch, start, velocity, key_end in notes:
            finish(channel, pitch, start, velocity, now, key_end)

    result.notes.sort(key=lambda n: (n.start, n.pitch))
    result.percussion_notes.sort(key=lambda n: (n.start, n.pitch))
    result.duration = now
    return result
