// Boss fight, circle of fifths and bingo at a moment: the same rules as the exported videos
// (backend/app/video/boss_renderer.py, circle_renderer.py, bingo_renderer.py).
import type { Bingo, Boss, Chord, CirclePosition } from "../types/analysis";
import { countUpTo } from "./stats";

export const BOSS_WARNING_SECONDS = 3.0;
export const BOSS_DEFEATED_SECONDS = 3.0;
export const BINGO_BANNER_SECONDS = 3.0;
export const CIRCLE_TRAIL_LENGTH = 6;

export type BossPhase = "warning" | "fight" | "defeated";

export function bossAt(boss: Boss | null, time: number): { phase: BossPhase; health: number } | null {
  if (!boss) return null;
  if (boss.start - BOSS_WARNING_SECONDS <= time && time < boss.start) return { phase: "warning", health: 100 };
  if (boss.start <= time && time < boss.end) {
    const hits = boss.hits.length;
    const health = hits === 0 ? 100 : Math.round((1 - countUpTo(boss.hits, time) / hits) * 100);
    return { phase: "fight", health };
  }
  if (boss.end <= time && time < boss.end + BOSS_DEFEATED_SECONDS) return { phase: "defeated", health: 0 };
  return null;
}

export const samePosition = (a: CirclePosition, b: CirclePosition) => a.ring === b.ring && a.index === b.index;

export interface CircleState {
  current: CirclePosition | null; // the chord shown now
  trail: CirclePosition[]; // last positions, oldest first
  visits: Map<string, number>; // "major-0" -> visits so far
  maxVisits: number; // most visits of any position in the whole piece
}

export const positionKey = (p: { ring: string; index: number }) => `${p.ring}-${p.index}`;

export function circleAt(chords: Chord[], current: Chord | null, time: number): CircleState {
  const visits = new Map<string, number>();
  const all = new Map<string, number>();
  const trail: CirclePosition[] = [];
  for (const chord of chords) {
    const key = positionKey(chord.circle);
    all.set(key, (all.get(key) ?? 0) + 1);
    if (chord.start > time) continue;
    visits.set(key, (visits.get(key) ?? 0) + 1);
    if (!trail.length || !samePosition(trail[trail.length - 1], chord.circle)) trail.push(chord.circle);
  }
  return {
    current: current?.circle ?? null,
    trail: trail.slice(-CIRCLE_TRAIL_LENGTH),
    visits,
    maxVisits: Math.max(1, ...all.values()),
  };
}

export interface BingoState {
  ticked: boolean[];
  lines: number[][]; // completed lines (cell indices)
  banner: number | null; // number of lines while "BINGO!" is shown
}

export function bingoAt(bingo: Bingo, time: number): BingoState {
  const lines = bingo.lines.filter((l) => l.time <= time);
  const last = lines[lines.length - 1];
  return {
    ticked: bingo.fields.map((f) => f.time !== null && f.time <= time),
    lines: lines.map((l) => l.cells),
    banner: last && time - last.time < BINGO_BANNER_SECONDS ? lines.length : null,
  };
}
