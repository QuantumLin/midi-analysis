// Mirrors the backend response models in backend/app/api/schemas.py.

/** Spectrum preview: frame i is at time i / fps; bins are log-spaced from min_hz to max_hz. */
export interface SpectrumData {
  fps: number;
  bins: number;
  frame_count: number;
  min_hz: number;
  max_hz: number;
  min_db: number;
  max_db: number;
  levels: string; // base64 of uint8[frame_count][bins], 0 = min_db, 255 = max_db
}

export interface Chord {
  start: number;
  end: number;
  name: string;
  root: string;
  quality: string;
  bass: string;
  notes: string[];
  numeral: string | null; // scale degree in the key at that moment: "vi", "V7", "♭VII"
  circle: CirclePosition; // place on the circle of fifths
}

/** Major chords on the outer ring, minor chords inside next to their relative major; index 0 = top. */
export interface CirclePosition {
  ring: "major" | "minor";
  index: number;
  name: string; // "C", "F♯", "a", "b♭"
}

export interface MusicalKey {
  tonic: string; // ASCII accidentals: "D", "Bb", "F#"
  mode: "major" | "minor";
}

export interface KeySegment {
  start: number;
  end: number;
  key: MusicalKey;
}

export interface Keys {
  overall: MusicalKey | null;
  segments: KeySegment[]; // contiguous; every segment after the first is a modulation
}

/** Key presses in the last second; frame i is at time i / fps. */
export interface NoteRate {
  fps: number;
  values: number[];
  peak_value: number;
  peak_time: number;
  records: { time: number; value: number }[];
}

export interface Localized {
  de: string;
  en: string;
}

/** A known chord progression, complete at `time` and highlighted until `end`. */
export interface Progression {
  time: number;
  end: number;
  id: string;
  count: number; // 1 = first time through, 2 = first repetition ...
  name: Localized; // including the counter, e.g. "Die Pop-Formel ×2"
}

/** A pop-up shown from `time` to `end` (scheduled so pop-ups never overlap). */
export interface Achievement {
  time: number;
  end: number;
  kind: string;
  title: Localized;
  detail: Localized;
}

export interface MotifOccurrence {
  start: number;
  end: number; // end of the motif's last note
  number: number; // 1 = first appearance
}

/** A melodic fragment that recurs (also transposed): label "A", "B", "C". */
export interface Motif {
  label: string;
  length: number; // notes
  occurrences: MotifOccurrence[];
}

/** A section of the piece; sections with the same label are the same part (A B A ...). */
export interface Section {
  start: number;
  end: number;
  label: string;
  number: number; // 1 = first time this part is heard
}

/** The hardest passage as "final boss"; every note in it is a hit. */
export interface Boss {
  start: number;
  end: number;
  factor: string; // "speed", "leaps", "chords"
  name: Localized;
  difficulty: number; // 0-10
  hits: number[]; // note start times in the passage
}

export interface Bingo {
  fields: { id: string; label: Localized; time: number | null }[]; // 3x3, row by row
  lines: { cells: number[]; time: number }[]; // completed lines, in order
}

export interface WrappedCard {
  id: string;
  title: Localized;
  value: Localized;
}

/** All pitched notes as parallel arrays, sorted by start; `end` is the key release. */
export interface Notes {
  start: number[];
  end: number[];
  pitch: number[];
}

export interface AnalysisResult {
  file_name: string;
  duration_seconds: number;
  note_count: number;
  percussion_note_count: number;
  spectrum: SpectrumData;
  chords: Chord[];
  keys: Keys;
  note_rate: NoteRate;
  progressions: Progression[];
  achievements: Achievement[];
  motifs: Motif[];
  sections: Section[];
  boss: Boss | null; // null for pieces shorter than 10 s
  bingo: Bingo;
  wrapped: WrappedCard[];
  notes: Notes;
}

export type VideoKind = "spectrum" | "chords" | "key" | "note_rate" | "heatmap" | "harmony" | "achievements" | "motifs" | "sections" | "boss" | "circle" | "bingo" | "wrapped";
export type Language = "en";
export type VideoFormat = "prores" | "png";
export type FontId = "orbitron" | "montserrat" | "bebas" | "playfair" | "pixel" | "handwriting";
export type GlowLevel = "subtle" | "normal" | "strong";

export interface VideoSettings {
  format: VideoFormat;
  width: number;
  height: number;
  fps: number;
  color: string; // hex, e.g. "#ffffff"
  showGrid: boolean;
  language: Language; // texts in the overlays
  showFrame: boolean; // glass panel with glowing border around the text and game overlays
  font: FontId; // display font of the overlays
  glow: GlowLevel;
}

export interface VideoJob {
  id: string;
  kind: VideoKind;
  format: VideoFormat;
  status: "queued" | "running" | "done" | "failed";
  progress: number; // 0..1
  error: string | null;
  file_name: string | null;
  size_bytes: number | null;
}
