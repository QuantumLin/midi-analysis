import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { useElementWidth } from "../hooks/useElementWidth";
import type { Chord, SpectrumData } from "../types/analysis";
import { chordAt } from "../utils/chords";
import { formatTime } from "../utils/format";
import { decodeSpectrum, levelsAt, type DecodedSpectrum } from "../utils/spectrum";

interface Props {
  spectrum: SpectrumData;
  chords: Chord[];
  duration: number;
  color: string; // export colour, previewed here
  showGrid: boolean;
}

const GRID_HZ = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000];
const GRID_DB_STEP = 12;

/**
 * Live preview of the exported overlays: the spectrum analyzer and the chord field,
 * on a dark "editor" background (the videos themselves are transparent).
 */
export default function SpectrumPlayer({ spectrum, chords, duration, color, showGrid }: Props) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const width = useElementWidth(wrapperRef);
  const height = Math.round(Math.min(Math.max(width * 0.42, 220), 420));

  const decoded = useMemo(() => decodeSpectrum(spectrum), [spectrum]);
  const buffer = useMemo(() => new Float32Array(spectrum.bins), [spectrum.bins]);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);

  // Playback clock.
  useEffect(() => {
    if (!playing) return;
    const startedAt = performance.now() - time * 1000;
    let frame = requestAnimationFrame(function tick(now) {
      const t = (now - startedAt) / 1000;
      if (t >= duration) {
        setTime(duration);
        setPlaying(false);
        return;
      }
      setTime(t);
      frame = requestAnimationFrame(tick);
    });
    return () => cancelAnimationFrame(frame);
    // `time` is deliberately not a dependency: it is read once when playback starts,
    // otherwise the clock would restart on every frame.
  }, [playing, duration]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || width === 0) return;
    drawSpectrum(canvas, width, height, decoded, levelsAt(decoded, time, buffer), color, showGrid);
  }, [decoded, buffer, time, width, height, color, showGrid]);

  const chord = chordAt(chords, time);

  function togglePlay() {
    if (!playing && time >= duration) setTime(0);
    setPlaying((p) => !p);
  }

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === " " && event.target === event.currentTarget) {
      event.preventDefault();
      togglePlay();
    }
  }

  return (
    <div className="player" tabIndex={0} onKeyDown={onKeyDown} aria-label="Vorschau, Leertaste startet und pausiert">
      <div ref={wrapperRef} className="player__screen">
        <canvas ref={canvasRef} style={{ width, height }} aria-label="Frequenzspektrum" role="img" />
        <div className="player__chord-area">
          {chord && (
            <div className="player__chord" style={{ color }}>
              {chord.name}
            </div>
          )}
        </div>
      </div>
      <div className="player__controls">
        <button type="button" className="button" onClick={togglePlay}>
          {playing ? "Pause" : "Play"}
        </button>
        <input
          type="range"
          className="player__seek"
          min={0}
          max={duration}
          step={0.01}
          value={time}
          aria-label="Position"
          onChange={(e) => {
            setPlaying(false);
            setTime(Number(e.target.value));
          }}
        />
        <span className="player__time">
          {formatTime(time)} / {formatTime(duration)}
        </span>
      </div>
    </div>
  );
}

function drawSpectrum(
  canvas: HTMLCanvasElement,
  width: number,
  height: number,
  spectrum: DecodedSpectrum,
  levels: Float32Array,
  color: string,
  showGrid: boolean,
) {
  const ratio = window.devicePixelRatio || 1;
  if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
  }
  const ctx = canvas.getContext("2d")!;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);

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
  gradient.addColorStop(0, withAlpha(color, 0.45));
  gradient.addColorStop(1, withAlpha(color, 0.08));
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

function withAlpha(hex: string, alpha: number): string {
  const n = parseInt(hex.slice(1), 16);
  return `rgb(${(n >> 16) & 255} ${(n >> 8) & 255} ${n & 255} / ${alpha})`;
}
