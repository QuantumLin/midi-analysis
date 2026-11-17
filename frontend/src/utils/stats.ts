// Time lookups for the live overlays; the same rules as the exported videos
// (backend/app/video/*_renderer.py and render.py).
import type { KeySegment, NoteRate, Notes } from "../types/analysis";

export const RECORD_HIGHLIGHT_SECONDS = 2.0;
export const MODULATION_HIGHLIGHT_SECONDS = 3.0;
export const PIANO_LOWEST = 21; // A0
export const PIANO_KEYS = 88;

/** Number of sorted values <= x. */
export function countUpTo(sorted: number[], x: number): number {
  let lo = 0;
  let hi = sorted.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (sorted[mid] <= x) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

export interface NoteRateState {
  rate: number;
  total: number;
  best: number;
  newRecord: number | null; // record value while it is highlighted
}

export function noteRateAt(noteRate: NoteRate, bestSoFar: number[], notes: Notes, time: number): NoteRateState {
  const frame = Math.min(Math.round(time * noteRate.fps), noteRate.values.length - 1);
  const record = noteRate.records.find((r) => time - r.time >= 0 && time - r.time < RECORD_HIGHLIGHT_SECONDS);
  return {
    rate: frame >= 0 ? noteRate.values[frame] : 0,
    total: countUpTo(notes.start, time),
    best: frame >= 0 ? bestSoFar[frame] : 0,
    newRecord: record ? record.value : null,
  };
}

/** Running maximum of the rate per frame. */
export function runningMax(values: number[]): number[] {
  let best = 0;
  return values.map((v) => (best = Math.max(best, v)));
}

export function keySegmentAt(segments: KeySegment[], time: number): { segment: KeySegment; modulated: boolean } | null {
  const index = segments.findIndex((s) => s.start <= time && time < s.end);
  if (index < 0) return null;
  const segment = segments[index];
  return { segment, modulated: index > 0 && time - segment.start < MODULATION_HIGHLIGHT_SECONDS };
}

/** Presses per piano key so far and keys held right now (index 0 = A0). */
export function keyboardAt(notes: Notes, time: number): { counts: Uint32Array; held: Uint8Array } {
  const counts = new Uint32Array(PIANO_KEYS);
  const held = new Uint8Array(PIANO_KEYS);
  const pressed = countUpTo(notes.start, time);
  for (let i = 0; i < pressed; i++) {
    const key = Math.min(Math.max(notes.pitch[i] - PIANO_LOWEST, 0), PIANO_KEYS - 1);
    counts[key]++;
    if (notes.end[i] > time) held[key] = 1;
  }
  return { counts, held };
}
