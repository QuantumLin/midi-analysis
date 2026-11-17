import { useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import { useElementWidth } from "../hooks/useElementWidth";
import type { Chord, Timeline, TimelinePoint } from "../types/analysis";
import { formatTime } from "../utils/format";

interface Props {
  timeline: Timeline;
  chords: Chord[];
  duration: number;
}

// Vertical layout (px): velocity panel, chord lane, shared time axis.
const MARGIN = { left: 64, right: 16 };
const VELOCITY = { titleY: 14, top: 24, height: 140 };
const CHORDS = { titleY: 192, top: 202, height: 30 };
const AXIS_Y = 254;
const HEIGHT = 262;
const MAX_VELOCITY = 127;

export default function TimelineChart({ timeline, chords, duration }: Props) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const width = useElementWidth(wrapperRef);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const { points, step_seconds: step } = timeline;
  const plotWidth = Math.max(width - MARGIN.left - MARGIN.right, 1);
  const x = (t: number) => MARGIN.left + (Math.min(t, duration) / duration) * plotWidth;
  const pointX = (p: TimelinePoint) => x(p.time + step / 2);
  const velocityY = (v: number) => VELOCITY.top + VELOCITY.height * (1 - v / MAX_VELOCITY);

  const velocityPath = points
    .map((p, i) => `${i ? "L" : "M"}${pointX(p).toFixed(1)},${velocityY(p.velocity).toFixed(1)}`)
    .join("");
  const timeTicks = niceTimeTicks(duration, plotWidth);

  const hovered = hoverIndex === null ? null : points[hoverIndex];
  const hoveredTime = hovered ? hovered.time + step / 2 : null;
  const hoveredChord =
    hoveredTime === null ? null : (chords.find((c) => c.start <= hoveredTime && hoveredTime < c.end) ?? null);

  function indexAt(clientX: number): number {
    const rect = wrapperRef.current!.getBoundingClientRect();
    const t = ((clientX - rect.left - MARGIN.left) / plotWidth) * duration;
    return clamp(Math.round(t / step - 0.5), 0, points.length - 1);
  }

  function onKeyDown(event: KeyboardEvent) {
    const delta = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (delta) {
      event.preventDefault();
      const jump = event.shiftKey ? 10 : 1;
      setHoverIndex((i) => clamp((i ?? -delta) + delta * jump, 0, points.length - 1));
    } else if (event.key === "Escape") {
      setHoverIndex(null);
    }
  }

  if (points.length === 0) {
    return <p className="empty">Die Datei enthält keine Noten.</p>;
  }

  return (
    <div
      ref={wrapperRef}
      className="timeline"
      tabIndex={0}
      aria-label="Velocity-Verlauf und Akkorde. Pfeiltasten bewegen die Markierung."
      onKeyDown={onKeyDown}
      onBlur={() => setHoverIndex(null)}
    >
      {width > 0 && (
        <svg width={width} height={HEIGHT} role="img" aria-hidden="true">
          <text className="panel-title" x={MARGIN.left} y={VELOCITY.titleY}>
            Velocity (Ø klingende Noten)
          </text>
          {[0, 32, 64, 96, 127].map((v) => (
            <g key={v}>
              <line className="grid" x1={MARGIN.left} x2={width - MARGIN.right} y1={velocityY(v)} y2={velocityY(v)} />
              <text className="tick" x={MARGIN.left - 8} y={velocityY(v)} textAnchor="end" dominantBaseline="middle">
                {v}
              </text>
            </g>
          ))}
          <path className="series series--velocity" d={velocityPath} />

          <text className="panel-title" x={MARGIN.left} y={CHORDS.titleY}>
            Akkorde
          </text>
          {chords.map((chord) => {
            const left = x(chord.start) + 1;
            const blockWidth = Math.max(x(chord.end) - x(chord.start) - 2, 1);
            const fitsLabel = blockWidth > chord.name.length * 7 + 8;
            return (
              <g key={`${chord.start}-${chord.name}`}>
                <rect
                  className={`chord-block${chord === hoveredChord ? " chord-block--active" : ""}`}
                  x={left}
                  y={CHORDS.top}
                  width={blockWidth}
                  height={CHORDS.height}
                  rx={4}
                />
                {fitsLabel && (
                  <text
                    className="chord-label"
                    x={left + blockWidth / 2}
                    y={CHORDS.top + CHORDS.height / 2}
                    textAnchor="middle"
                    dominantBaseline="central"
                  >
                    {chord.name}
                  </text>
                )}
              </g>
            );
          })}

          {timeTicks.map((t) => (
            <text key={t} className="tick" x={x(t)} y={AXIS_Y} textAnchor="middle">
              {formatTime(t, 0)}
            </text>
          ))}

          {hovered && (
            <g pointerEvents="none">
              <line
                className="crosshair"
                x1={pointX(hovered)}
                x2={pointX(hovered)}
                y1={VELOCITY.top}
                y2={CHORDS.top + CHORDS.height}
              />
              <circle
                className="marker series-fill--velocity"
                cx={pointX(hovered)}
                cy={velocityY(hovered.velocity)}
                r={4}
              />
            </g>
          )}

          <rect
            x={MARGIN.left}
            y={VELOCITY.top}
            width={plotWidth}
            height={CHORDS.top + CHORDS.height - VELOCITY.top}
            fill="transparent"
            onPointerMove={(e: PointerEvent) => setHoverIndex(indexAt(e.clientX))}
            onPointerLeave={() => setHoverIndex(null)}
          />
        </svg>
      )}

      {hovered && (
        <div
          className="tooltip"
          style={{
            left: pointX(hovered),
            transform: pointX(hovered) > width - 220 ? "translateX(calc(-100% - 12px))" : "translateX(12px)",
          }}
        >
          <div className="tooltip__time">{formatTime(hovered.time + step / 2)}</div>
          <div className="tooltip__row">
            <span className="line-key series-fill--velocity" aria-hidden="true" />
            <strong>{hovered.velocity.toFixed(0)}</strong> <span>Velocity</span>
          </div>
          <div className="tooltip__row">
            <strong>{hovered.active_notes}</strong> <span>klingende Noten</span>
          </div>
          <div className="tooltip__row">
            <strong>{hoveredChord?.name ?? "–"}</strong> <span>Akkord</span>
          </div>
        </div>
      )}
    </div>
  );
}

function niceTimeTicks(duration: number, plotWidth: number): number[] {
  const maxTicks = Math.max(2, Math.floor(plotWidth / 80));
  const steps = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600];
  const stepSize = steps.find((s) => duration / s <= maxTicks) ?? 1200;
  const ticks = [];
  for (let t = 0; t <= duration; t += stepSize) ticks.push(t);
  return ticks;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}
