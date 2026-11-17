import type { SpectrumData } from "../types/analysis";

export interface DecodedSpectrum {
  data: SpectrumData;
  levels: Uint8Array; // frame_count * bins
}

export function decodeSpectrum(data: SpectrumData): DecodedSpectrum {
  const binary = atob(data.levels);
  const levels = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) levels[i] = binary.charCodeAt(i);
  return { data, levels };
}

/**
 * Normalised level (0 = min_db, 1 = max_db) for every bin at `time`,
 * linearly interpolated between the two neighbouring preview frames.
 */
export function levelsAt(spectrum: DecodedSpectrum, time: number, out: Float32Array): Float32Array {
  const { fps, bins, frame_count: frames } = spectrum.data;
  const position = Math.min(Math.max(time * fps, 0), frames - 1);
  const a = Math.floor(position);
  const b = Math.min(a + 1, frames - 1);
  const t = position - a;
  const rowA = a * bins;
  const rowB = b * bins;
  for (let i = 0; i < bins; i++) {
    out[i] = (spectrum.levels[rowA + i] * (1 - t) + spectrum.levels[rowB + i] * t) / 255;
  }
  return out;
}
