// The three neon text overlays, styled like the exported videos
// (backend/app/video/neon_overlay.py and the *_renderer.py files).
import type { CSSProperties, ReactNode } from "react";
import type { KeySegment, Language } from "../../types/analysis";
import { displayAccidentals, keyName, text } from "../../utils/labels";
import type { NoteRateState } from "../../utils/stats";

const METER_SEGMENTS = 24;

function NeonPanel({
  color,
  label,
  labelAccent = false,
  flashKey,
  boosted = false,
  children,
}: {
  color: string;
  label: string;
  labelAccent?: boolean;
  flashKey?: string | number; // a new value restarts the flash animation
  boosted?: boolean; // stronger glow while a record / modulation is highlighted
  children: ReactNode;
}) {
  return (
    <div className={`neon-panel${boosted ? " neon-panel--boosted" : ""}`} style={{ "--neon": color } as CSSProperties}>
      <span className={`neon-label${labelAccent ? " neon-label--accent" : ""}`}>{label}</span>
      <div key={flashKey} className={flashKey !== undefined ? "neon-flash" : undefined}>
        {children}
      </div>
    </div>
  );
}

export function ChordField({
  name,
  start,
  color,
  language,
}: {
  name: string | null;
  start: number | null; // start of the current chord: each change flashes
  color: string;
  language: Language;
}) {
  return (
    <NeonPanel color={color} label={text("chord", language)} flashKey={start ?? undefined}>
      <span className="neon-value">{name ? displayAccidentals(name) : "–"}</span>
    </NeonPanel>
  );
}

export function KeyField({
  current,
  color,
  language,
}: {
  current: { segment: KeySegment; modulated: boolean } | null;
  color: string;
  language: Language;
}) {
  const modulated = current?.modulated ?? false;
  return (
    <NeonPanel
      color={color}
      label={modulated ? `${text("modulation", language)} →` : text("key", language)}
      labelAccent={modulated}
      boosted={modulated}
      flashKey={modulated ? current?.segment.start : undefined}
    >
      <span className="neon-value">{current ? keyName(current.segment.key, language) : "–"}</span>
    </NeonPanel>
  );
}

export function NoteRateField({
  state,
  peak,
  color,
  language,
}: {
  state: NoteRateState;
  peak: number; // highest rate of the piece = full meter
  color: string;
  language: Language;
}) {
  const lit = Math.round(Math.min(state.rate / Math.max(peak, 1), 1) * METER_SEGMENTS);
  const record = state.newRecord !== null;
  return (
    <NeonPanel
      color={color}
      label={text("notesPerSecond", language)}
      boosted={record}
      flashKey={record ? `record-${state.newRecord}` : undefined}
    >
      <span className="neon-value">{state.rate}</span>
      <div className="neon-meter" aria-hidden="true">
        {Array.from({ length: METER_SEGMENTS }, (_, i) => (
          <span key={i} className={i < lit ? "neon-meter__on" : undefined} />
        ))}
      </div>
      <span className={`neon-footer${record ? " neon-label--accent" : ""}`}>
        {record
          ? `${text("newRecord", language)}: ${state.newRecord}`
          : `${text("total", language)} ${state.total}  ·  ${text("record", language)} ${state.best}`}
      </span>
    </NeonPanel>
  );
}
