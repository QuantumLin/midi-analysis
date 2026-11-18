// Boss fight, circle of fifths, bingo and Song Wrapped in the preview, styled like the
// exported videos (backend/app/video/boss_renderer.py, circle_renderer.py, bingo_renderer.py,
// wrapped_renderer.py).
import type { CSSProperties } from "react";
import type { Bingo, Boss, Language, WrappedCard } from "../../types/analysis";
import type { BingoState, BossPhase, CircleState } from "../../utils/games";
import { positionKey, samePosition } from "../../utils/games";
import { bingoBanner, decimal, text } from "../../utils/labels";

const HP_SEGMENTS = 30;
const MAJOR = ["C", "G", "D", "A", "E", "B", "F♯", "D♭", "A♭", "E♭", "B♭", "F"];
const MINOR = ["a", "e", "b", "f♯", "c♯", "g♯", "e♭", "b♭", "f", "c", "g", "d"];

const neonStyle = (color: string) => ({ "--neon": color }) as CSSProperties;

export function BossField({
  boss,
  state,
  color,
  language,
}: {
  boss: Boss | null;
  state: { phase: BossPhase; health: number } | null; // null = boss not on screen
  color: string;
  language: Language;
}) {
  if (!boss) return null;
  const phase = state?.phase ?? null;
  const health = state?.health ?? 100;
  const lit = Math.round((health / 100) * HP_SEGMENTS);
  const details = `${text("health", language)} ${health} %  ·  ${text("difficulty", language)} ${decimal(boss.difficulty, language)}/10`;
  return (
    // Hidden in the video outside the fight; dimmed here so the other fields don't jump.
    <div className={state ? undefined : "neon-idle"}>
      <div
        className={`neon-panel${phase && phase !== "fight" ? " neon-panel--boosted" : ""}`}
        style={neonStyle(color)}
      >
        <span className={`neon-label${phase && phase !== "fight" ? " neon-label--accent" : ""}`}>
          {text("finalBoss", language)}
        </span>
        <div key={phase ?? "idle"} className={phase ? "neon-flash" : undefined}>
          <span className="neon-value">{phase === "defeated" ? text("defeated", language) : boss.name[language]}</span>
          <div className="neon-meter neon-meter--hp" aria-label={`HP ${health} %`}>
            {Array.from({ length: HP_SEGMENTS }, (_, i) => (
              <span key={i} className={i < lit ? "neon-meter__on" : undefined} />
            ))}
          </div>
          <span className={`neon-footer${phase === "warning" ? " neon-label--accent neon-blink" : ""}`}>
            {phase === "warning" ? text("bossWarning", language) : details}
          </span>
        </div>
      </div>
    </div>
  );
}

export function CircleOfFifths({
  state,
  chordName,
  color,
  language,
}: {
  state: CircleState;
  chordName: string | null;
  color: string;
  language: Language;
}) {
  const size = 280;
  const c = size / 2;
  const radius = { major: 118, minor: 78 };
  const dot = { major: 16, minor: 13 };
  const point = (ring: "major" | "minor", index: number) => {
    const angle = (2 * Math.PI * index) / 12 - Math.PI / 2;
    return [c + radius[ring] * Math.cos(angle), c + radius[ring] * Math.sin(angle)] as const;
  };
  const rings = (["major", "minor"] as const).flatMap((ring) =>
    Array.from({ length: 12 }, (_, index) => ({ ring, index, name: (ring === "major" ? MAJOR : MINOR)[index] })),
  );
  return (
    <div className="neon-panel" style={neonStyle(color)}>
      <span className="neon-label">{text("circleOfFifths", language)}</span>
      <svg className="circle" viewBox={`0 0 ${size} ${size}`} width={size} height={size} role="img">
        <circle cx={c} cy={c} r={radius.major} className="circle__guide" />
        <circle cx={c} cy={c} r={radius.minor} className="circle__guide" />
        <polyline
          className="circle__trail"
          points={state.trail.map((p) => point(p.ring, p.index).join(",")).join(" ")}
        />
        {rings.map((p) => {
          const [x, y] = point(p.ring, p.index);
          const visits = state.visits.get(positionKey(p)) ?? 0;
          const current = state.current !== null && samePosition(state.current, p);
          return (
            <g key={positionKey(p)} className={current ? "circle__dot circle__dot--current" : "circle__dot"}>
              <circle
                cx={x}
                cy={y}
                r={dot[p.ring]}
                style={{ fillOpacity: current ? 1 : (visits / state.maxVisits) * 0.55 }}
              />
              <text x={x} y={y} dy="0.36em" fontSize={p.ring === "major" ? 12 : 10}>
                {p.name}
              </text>
            </g>
          );
        })}
        {chordName && (
          <text x={c} y={c} dy="0.36em" className="circle__center">
            {chordName}
          </text>
        )}
      </svg>
    </div>
  );
}

export function BingoBoard({
  bingo,
  state,
  color,
  language,
}: {
  bingo: Bingo;
  state: BingoState;
  color: string;
  language: Language;
}) {
  const inLine = new Set(state.lines.flat());
  return (
    <div className={`neon-panel${state.banner ? " neon-panel--boosted" : ""}`} style={neonStyle(color)}>
      <span className="neon-label">{text("bingoTitle", language)}</span>
      <div className="bingo">
        {bingo.fields.map((field, i) => (
          <div
            key={i}
            className={`bingo__cell${state.ticked[i] ? " bingo__cell--ticked" : ""}${inLine.has(i) ? " bingo__cell--line" : ""}`}
          >
            {field.label[language]}
          </div>
        ))}
      </div>
      {state.banner ? (
        <span key={state.banner} className="neon-value neon-flash bingo__banner">
          {bingoBanner(state.banner, language)}
        </span>
      ) : (
        <span className="neon-footer">
          {state.ticked.filter(Boolean).length} / {state.ticked.length}
        </span>
      )}
    </div>
  );
}

export function WrappedPreview({ cards, color, language }: { cards: WrappedCard[]; color: string; language: Language }) {
  return (
    <div className="wrapped" style={neonStyle(color)}>
      <span className="wrapped__title">{text("songWrapped", language)}</span>
      <div className="wrapped__cards">
        {cards.map((card) => (
          <div key={card.id} className="neon-panel wrapped__card" style={neonStyle(color)}>
            <span className="neon-label">{card.title[language]}</span>
            <span className="wrapped__value">{card.value[language]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
