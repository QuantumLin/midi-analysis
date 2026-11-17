"""Builds small MIDI files in memory for tests."""

import io

import mido

TICKS_PER_BEAT = 480
TEMPO_120_BPM = 500_000  # microseconds per beat -> one beat = 0.5 s


def build_midi(
    events: list[tuple[float, mido.Message]],
    tempo: int = TEMPO_120_BPM,
) -> bytes:
    """events: (time in beats, message). Returns the bytes of a type-0 MIDI file."""
    midi = mido.MidiFile(type=0, ticks_per_beat=TICKS_PER_BEAT)
    track = mido.MidiTrack()
    midi.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))

    # At equal times, note-offs come before note-ons so re-struck notes stay separate.
    ordered = sorted(events, key=lambda e: (e[0], _is_note_on(e[1])))
    last_tick = 0
    for beat, msg in ordered:
        tick = round(beat * TICKS_PER_BEAT)
        track.append(msg.copy(time=tick - last_tick))
        last_tick = tick

    buffer = io.BytesIO()
    midi.save(file=buffer)
    return buffer.getvalue()


def chord_events(
    pitches: list[int], start: float, length: float, velocity: int = 80, channel: int = 0
) -> list[tuple[float, mido.Message]]:
    """Note-on/off events (times in beats) for notes played together."""
    events = []
    for p in pitches:
        events.append((start, mido.Message("note_on", note=p, velocity=velocity, channel=channel)))
        events.append((start + length, mido.Message("note_off", note=p, velocity=0, channel=channel)))
    return events


def _is_note_on(msg: mido.Message) -> bool:
    return msg.type == "note_on" and msg.velocity > 0
