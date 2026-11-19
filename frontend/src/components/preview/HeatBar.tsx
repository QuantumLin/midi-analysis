import { useEffect, useRef } from "react";
import type { Notes } from "../../types/analysis";
import { hexToRgb, prepareCanvas } from "../../utils/canvas";
import { keyboardAt, PIANO_KEYS, PIANO_LOWEST } from "../../utils/stats";

interface Props {
  notes: Notes;
  time: number;
  width: number;
  color: string;
  font: string; // CSS font family of the C labels
  glow: number; // glow strength factor (1 = normal)
}

// Same look as backend/app/video/heatmap_renderer.py.
const HEAT_GAMMA = 0.55;
const HELD_BOOST = 0.3;
const SMOOTHING_SIGMA = 0.6;
const SMOOTHING_RADIUS = 2;
const PANEL_FILL: [number, number, number] = [8, 10, 22];
const KERNEL = (() => {
  const k = [];
  for (let i = -SMOOTHING_RADIUS; i <= SMOOTHING_RADIUS; i++) k.push(Math.exp(-0.5 * (i / SMOOTHING_SIGMA) ** 2));
  const sum = k.reduce((a, b) => a + b, 0);
  return k.map((v) => v / sum);
})();

export function heatBarHeight(width: number): number {
  return Math.round(Math.max(width * 0.085, 72));
}

/** The 88 keys (A0 left, C8 right) as one glowing bar with a smooth intensity distribution. */
export default function HeatBar({ notes, time, width, color, font, glow }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const height = heatBarHeight(width);

  useEffect(() => {
    if (!canvasRef.current || width === 0) return;
    const { counts, held } = keyboardAt(notes, time);
    draw(canvasRef.current, width, height, keyHeat(counts, held), hexToRgb(color), font, glow);
  }, [notes, time, width, height, color, font, glow]);

  return <canvas ref={canvasRef} style={{ width, height }} role="img" aria-label="Tasten-Heatmap" />;
}

function keyHeat(counts: Uint32Array, held: Uint8Array): number[] {
  const max = Math.max(...counts);
  const raw = Array.from(counts, (c) => (max > 0 ? (c / max) ** HEAT_GAMMA : 0));
  const smooth = raw.map((_, key) =>
    KERNEL.reduce((sum, w, i) => {
      const k = Math.min(Math.max(key + i - SMOOTHING_RADIUS, 0), PIANO_KEYS - 1);
      return sum + raw[k] * w;
    }, 0),
  );
  const peak = Math.max(...smooth);
  return smooth.map((h, key) => {
    const normalized = peak > 0 ? h / peak : 0;
    return held[key] ? Math.max(normalized, 1) + HELD_BOOST : normalized;
  });
}

/** heat 0 -> dark glass, 0.6 -> accent, >= 1.2 -> white-hot. */
function ramp(heat: number, color: [number, number, number]): string {
  const core = color.map((c) => c + (255 - c) * 0.55) as [number, number, number];
  const [from, to, t] = heat <= 0.6 ? [PANEL_FILL, color, heat / 0.6] : [color, core, Math.min((heat - 0.6) / 0.6, 1)];
  const rgb = from.map((c, i) => Math.round(c + (to[i] - c) * t));
  const alpha = heat <= 0 ? 0.55 : Math.min(0.6 + heat * 0.5, 1);
  return `rgb(${rgb[0]} ${rgb[1]} ${rgb[2]} / ${alpha})`;
}

function draw(
  canvas: HTMLCanvasElement,
  width: number,
  height: number,
  heat: number[],
  color: [number, number, number],
  font: string,
  glow: number,
) {
  const ctx = prepareCanvas(canvas, width, height);
  const barHeight = height * 0.26;
  const margin = height * 0.3; // room for the glow
  const left = margin;
  const barWidth = width - 2 * margin;
  const top = margin;

  const gradient = ctx.createLinearGradient(left, 0, left + barWidth, 0);
  heat.forEach((h, key) => gradient.addColorStop((key + 0.5) / PIANO_KEYS, ramp(h, color)));
  const bar = new Path2D();
  bar.roundRect(left, top, barWidth, barHeight, barHeight / 2);

  // Glow: the same bar, softly blurred.
  ctx.save();
  ctx.filter = `blur(${barHeight * 0.11}px)`;
  ctx.fillStyle = gradient;
  for (let rest = glow; rest > 0; rest -= 1) {
    ctx.globalAlpha = Math.min(rest, 1); // > 1: an extra, partial layer
    ctx.fill(bar);
  }
  ctx.restore();
  ctx.fillStyle = gradient;
  ctx.fill(bar);

  // A mark and label for every C.
  const core = `rgb(${color.map((c) => Math.round(c + (255 - c) * 0.55)).join(" ")} / 0.55)`;
  ctx.fillStyle = core;
  ctx.strokeStyle = core;
  ctx.font = `600 ${Math.max(10, Math.round(height * 0.12))}px ${font}, system-ui, sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  for (let key = 0; key < PIANO_KEYS; key++) {
    const pitch = PIANO_LOWEST + key;
    if (pitch % 12 !== 0) continue;
    const x = left + ((key + 0.5) / PIANO_KEYS) * barWidth;
    const tick = top + barHeight + height * 0.06;
    ctx.beginPath();
    ctx.moveTo(x, tick);
    ctx.lineTo(x, tick + height * 0.07);
    ctx.stroke();
    ctx.fillText(`C${Math.floor(pitch / 12) - 1}`, x, tick + height * 0.1);
  }
}
