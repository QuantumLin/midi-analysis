import type { Chord } from "../types/analysis";

// Same rule as the exported chord video (backend/app/video/render.py, chord_at):
// the last chord stays visible through short gaps, and disappears after a longer silence.
export const CHORD_HOLD_SECONDS = 2.0;

/** Chord to display at `time` (chords sorted by start), or null. */
export function chordAt(chords: Chord[], time: number): Chord | null {
  let current: Chord | null = null;
  for (let i = 0; i < chords.length; i++) {
    const chord = chords[i];
    if (chord.start > time) break;
    const nextStart = i + 1 < chords.length ? chords[i + 1].start : Infinity;
    const holding = time < nextStart && time - chord.end < CHORD_HOLD_SECONDS;
    current = time < chord.end || holding ? chord : null;
  }
  return current;
}
