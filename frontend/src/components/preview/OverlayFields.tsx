// The neon text overlays and the achievement pop-up, styled like the exported videos
// (backend/app/video/neon_overlay.py and the *_renderer.py files).
import type { CSSProperties, ReactNode } from "react";
import type { KeySegment, Language, MusicalKey, Progression } from "../../types/analysis";
import { type AchievementState, splitNumeral } from "../../utils/harmony";
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

export function HarmonyField({
  numeral,
  start,
  chain,
  musicalKey,
  progression,
  color,
  language,
}: {
  numeral: string | null; // current chord as roman numeral, null = no chord
  start: number | null; // start of the current chord: each change flashes
  chain: string[]; // last degrees, the current one last
  musicalKey: MusicalKey | null; // what the numerals refer to
  progression: Progression | null; // known progression being highlighted
  color: string;
  language: Language;
}) {
  const [degree, suffix] = numeral ? splitNumeral(numeral) : ["–", ""];
  let footer = "\u00a0";
  if (progression) footer = progression.name[language];
  else if (musicalKey) footer = `${text("inKey", language)} ${keyName(musicalKey, language)}`;
  return (
    <NeonPanel color={color} label={text("degree", language)} boosted={progression !== null} flashKey={start ?? undefined}>
      <span className="neon-value neon-numeral">
        {degree}
        {suffix && <sup>{suffix}</sup>}
      </span>
      <div className="neon-chain">
        {chain.map((item, i) => (
          <span key={i}>
            {i > 0 && <span>–</span>}
            <span className={i === chain.length - 1 ? "neon-chain__current" : undefined}>{item}</span>
          </span>
        ))}
      </div>
      <span className={`neon-footer${progression ? " neon-label--accent" : ""}`}>{footer}</span>
    </NeonPanel>
  );
}

export function AchievementToast({
  state,
  color,
  language,
}: {
  state: AchievementState;
  color: string;
  language: Language;
}) {
  const { achievement, scale, opacity } = state;
  return (
    <div
      className="neon-panel neon-toast"
      style={{ "--neon": color, transform: `scale(${scale})`, opacity } as CSSProperties}
      role="status"
    >
      <span className="neon-label neon-label--accent">{text("achievement", language)}</span>
      <div key={achievement.time} className="neon-flash neon-toast__title">
        <svg viewBox="-1 -1 2 2" aria-hidden="true">
          <polygon points={STAR_POINTS} />
        </svg>
        <span>{achievement.title[language]}</span>
      </div>
      <span className="neon-footer">{achievement.detail[language]}</span>
    </div>
  );
}

// Five-pointed star, first tip up (as draw_star in backend/app/video/neon.py).
const STAR_POINTS = Array.from({ length: 10 }, (_, i) => {
  const r = i % 2 === 0 ? 1 : 0.45;
  const angle = (Math.PI * i) / 5 - Math.PI / 2;
  return `${(r * Math.cos(angle)).toFixed(3)},${(r * Math.sin(angle)).toFixed(3)}`;
}).join(" ");
