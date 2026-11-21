import { useEffect, useMemo, useRef } from "react";
import type { SpectrumData, SpectrumStyle } from "../../types/analysis";
import { hexToRgb, prepareCanvas, rgba } from "../../utils/canvas";
import { decodeSpectrum, levelsAt, type DecodedSpectrum } from "../../utils/spectrum";

interface Props {
  spectrum: SpectrumData;
  time: number;
  width: number;
  height: number;
  color: string;
  showGrid: boolean;
  displayStyle: SpectrumStyle;
}

const GRID_HZ = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000];
const GRID_DB_STEP = 12;
const BAR_COUNT = 72;

/** Spectrum analyzer frame, drawn like the exported video (backend/app/video/spectrum_renderer.py). */
export default function SpectrumCanvas({ spectrum, time, width, height, color, showGrid, displayStyle }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const decoded = useMemo(() => decodeSpectrum(spectrum), [spectrum]);
  const buffer = useMemo(() => new Float32Array(spectrum.bins), [spectrum.bins]);

  useEffect(() => {
    if (!canvasRef.current || width === 0) return;
    draw(canvasRef.current, width, height, decoded, levelsAt(decoded, time, buffer), color, showGrid, displayStyle);
  }, [decoded, buffer, time, width, height, color, showGrid, displayStyle]);

  return <canvas ref={canvasRef} style={{ width, height }} role="img" aria-label="Frequency spectrum" />;
}

function draw(
  canvas: HTMLCanvasElement,
  width: number,
  height: number,
  spectrum: DecodedSpectrum,
  levels: Float32Array,
  color: string,
  showGrid: boolean,
  displayStyle: SpectrumStyle,
) {
  const ctx = prepareCanvas(canvas, width, height);
  const rgb = hexToRgb(color);
  const { min_hz, max_hz, min_db, max_db, bins } = spectrum.data;
  const plot = showGrid
    ? { left: 12, right: width - 52, top: 12, bottom: height - 26 }
    : { left: 0, right: width, top: height * 0.04, bottom: height };
  const logMin = Math.log(min_hz);
  const logSpan = Math.log(max_hz) - logMin;
  const xOf = (hz: number) => plot.left + ((Math.log(hz) - logMin) / logSpan) * (plot.right - plot.left);
  const yOf = (normalized: number) => plot.bottom - normalized * (plot.bottom - plot.top);

  if (showGrid) {
    ctx.strokeStyle = "rgb(255 255 255 / 0.16)";
    ctx.fillStyle = "rgb(255 255 255 / 0.7)";
    ctx.lineWidth = 1;
    ctx.font = "11px system-ui, sans-serif";
    ctx.textBaseline = "top";
    for (const hz of GRID_HZ) {
      const x = Math.round(xOf(hz)) + 0.5;
      line(ctx, x, plot.top, x, plot.bottom);
      ctx.textAlign = hz === GRID_HZ[0] ? "left" : hz === GRID_HZ[GRID_HZ.length - 1] ? "right" : "center";
      ctx.fillText(hz >= 1000 ? `${hz / 1000}k` : String(hz), x, plot.bottom + 6);
    }
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    for (let db = max_db; db >= min_db; db -= GRID_DB_STEP) {
      const y = Math.round(yOf((db - min_db) / (max_db - min_db))) + 0.5;
      line(ctx, plot.left, y, plot.right, y);
      ctx.fillText(`${db} dB`, plot.right + 6, y);
    }
  }

  if (displayStyle === "centered_bars") {
    const spacing = (plot.right - plot.left) / BAR_COUNT;
    const centerY = (plot.top + plot.bottom) / 2;
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = Math.max(1, spacing * 0.18);
    ctx.lineCap = "butt";
    for (let index = 0; index < BAR_COUNT; index++) {
      const position = ((index + 0.5) / BAR_COUNT) * (bins - 1);
      const bin = Math.min(Math.floor(position), bins - 2);
      const fraction = position - bin;
      const normalized = levels[bin] * (1 - fraction) + levels[bin + 1] * fraction;
      const halfLength = normalized * ((plot.bottom - plot.top) / 2);
      const x = plot.left + (index + 0.5) * spacing;
      ctx.moveTo(x, centerY - halfLength);
      ctx.lineTo(x, centerY + halfLength);
    }
    ctx.stroke();
    return;
  }

  // Curve: one point per CSS pixel column, sampled from the log-spaced bins.
  const curve = new Path2D();
  for (let x = plot.left; x <= plot.right; x++) {
    const position = ((x - plot.left) / (plot.right - plot.left)) * (bins - 1);
    const i = Math.min(Math.floor(position), bins - 2);
    const t = position - i;
    const y = yOf(levels[i] * (1 - t) + levels[i + 1] * t);
    if (x === plot.left) curve.moveTo(x, y);
    else curve.lineTo(x, y);
  }

  // Fill first, then the line on top (same as the exported video).
  const area = new Path2D(curve);
  area.lineTo(plot.right, plot.bottom);
  area.lineTo(plot.left, plot.bottom);
  area.closePath();
  const gradient = ctx.createLinearGradient(0, plot.top, 0, plot.bottom);
  gradient.addColorStop(0, rgba(rgb, 0.45));
  gradient.addColorStop(1, rgba(rgb, 0.08));
  ctx.fillStyle = gradient;
  ctx.fill(area);

  ctx.lineJoin = "round";
  ctx.lineWidth = 2;
  ctx.strokeStyle = color;
  ctx.stroke(curve);
}

function line(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number) {
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}
