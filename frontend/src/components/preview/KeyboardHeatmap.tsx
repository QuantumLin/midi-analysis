import { useEffect, useRef } from "react";
import type { Notes } from "../../types/analysis";
import { hexToRgb, prepareCanvas, rgba } from "../../utils/canvas";
import { keyboardAt, PIANO_KEYS, PIANO_LOWEST } from "../../utils/stats";

interface Props {
  notes: Notes;
  time: number;
  width: number;
  color: string;
}

// Same geometry and colours as backend/app/video/heatmap_renderer.py.
const WHITE_KEY_COUNT = 52;
const KEY_ASPECT = 5.6;
const BLACK_WIDTH = 0.6;
const BLACK_LENGTH = 0.62;
const HEAT_GAMMA = 0.5;
const BLACK_PITCH_CLASSES = new Set([1, 3, 6, 8, 10]);

export function heatmapHeight(width: number): number {
  return Math.round((width / WHITE_KEY_COUNT) * KEY_ASPECT);
}

export default function KeyboardHeatmap({ notes, time, width, color }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const height = heatmapHeight(width);

  useEffect(() => {
    if (!canvasRef.current || width === 0) return;
    const { counts, held } = keyboardAt(notes, time);
    draw(canvasRef.current, width, height, counts, held, hexToRgb(color));
  }, [notes, time, width, height, color]);

  return <canvas ref={canvasRef} style={{ width, height }} role="img" aria-label="Tasten-Heatmap" />;
}

function draw(
  canvas: HTMLCanvasElement,
  width: number,
  height: number,
  counts: Uint32Array,
  held: Uint8Array,
  color: [number, number, number],
) {
  const ctx = prepareCanvas(canvas, width, height);
  const maxCount = Math.max(...counts);
  const whiteWidth = width / WHITE_KEY_COUNT;

  const style = (key: number, black: boolean): string => {
    if (held[key]) return rgba(mix(color, [255, 255, 255], 0.55), 1);
    const count = counts[key];
    if (count === 0) return black ? rgba([16, 16, 16], 0.75) : rgba([255, 255, 255], 0.12);
    const heat = (count / maxCount) ** HEAT_GAMMA;
    return black ? rgba(mix([16, 16, 16], color, 0.35 + 0.65 * heat), 0.85) : rgba(color, 0.22 + 0.7 * heat);
  };

  const blackKeys: [number, number][] = [];
  let whiteIndex = 0;
  for (let key = 0; key < PIANO_KEYS; key++) {
    if (BLACK_PITCH_CLASSES.has((key + PIANO_LOWEST) % 12)) {
      blackKeys.push([key, whiteIndex * whiteWidth]);
      continue;
    }
    ctx.fillStyle = style(key, false);
    ctx.fillRect(whiteIndex * whiteWidth, 0, whiteWidth - 1, height);
    whiteIndex++;
  }
  const blackWidth = whiteWidth * BLACK_WIDTH;
  for (const [key, boundary] of blackKeys) {
    ctx.clearRect(boundary - blackWidth / 2 - 1, 0, blackWidth + 2, height * BLACK_LENGTH);
    ctx.fillStyle = style(key, true);
    ctx.fillRect(boundary - blackWidth / 2, 0, blackWidth, height * BLACK_LENGTH - 1);
  }
}

function mix(a: [number, number, number], b: [number, number, number], t: number): [number, number, number] {
  return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
}
