// Mirrors the backend response models in backend/app/api/schemas.py.

export interface TimelinePoint {
  time: number; // seconds
  velocity: number; // mean velocity of sounding notes, 0 when silent
  active_notes: number;
}

export interface Timeline {
  step_seconds: number;
  points: TimelinePoint[];
}

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
}

export interface AnalysisResult {
  file_name: string;
  duration_seconds: number;
  note_count: number;
  percussion_note_count: number;
  timeline: Timeline;
  spectrum: SpectrumData;
  chords: Chord[];
}

export type VideoKind = "spectrum" | "chords";
export type VideoFormat = "prores" | "png";

export interface VideoSettings {
  format: VideoFormat;
  width: number;
  height: number;
  fps: number;
  color: string; // hex, e.g. "#ffffff"
  showGrid: boolean;
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
