// Motifs and sections: the same rules as the exported videos
// (backend/app/video/motif_renderer.py and section_renderer.py).
import type { Motif, MotifOccurrence, Section } from "../types/analysis";

export const MOTIF_HOLD_SECONDS = 1.0;
export const REPEAT_HIGHLIGHT_SECONDS = 3.0;

/** The latest motif appearance playing at `time` (plus a short hold), or null. */
export function motifAt(motifs: Motif[], time: number): { label: string; occurrence: MotifOccurrence } | null {
  let current: { label: string; occurrence: MotifOccurrence } | null = null;
  for (const motif of motifs) {
    for (const occurrence of motif.occurrences) {
      const playing = occurrence.start <= time && time < occurrence.end + MOTIF_HOLD_SECONDS;
      if (playing && (!current || occurrence.start > current.occurrence.start)) {
        current = { label: motif.label, occurrence };
      }
    }
  }
  return current;
}

export function sectionAt(sections: Section[], time: number): { section: Section; repeated: boolean } | null {
  const section = sections.find((s) => s.start <= time && time < s.end);
  if (!section) return null;
  return { section, repeated: section.number > 1 && time - section.start < REPEAT_HIGHLIGHT_SECONDS };
}
