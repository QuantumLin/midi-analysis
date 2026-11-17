// Degree overlay and achievement pop-ups: the same rules as the exported videos
// (backend/app/analysis/harmony.py, backend/app/video/harmony_renderer.py, achievement_renderer.py).
import type { Achievement, Chord, Progression } from "../types/analysis";

export const CHAIN_LENGTH = 4;
const NUMERAL = /^([♭♯]?[IViv]+)(.*)$/;

/** "♭VIImaj7" -> ["♭VII", "maj7"]: the degree and the chord suffix. */
export function splitNumeral(numeral: string): [string, string] {
  const match = NUMERAL.exec(numeral);
  return match ? [match[1], match[2]] : [numeral, ""];
}

/** The last degrees (without suffix) up to and including chord `index`, repeats collapsed. */
export function chainBefore(chords: Chord[], index: number, length = CHAIN_LENGTH): string[] {
  const chain: string[] = [];
  for (let i = index; i >= 0 && chain.length < length; i--) {
    const degree = chords[i].numeral ? splitNumeral(chords[i].numeral!)[0] : "";
    if (degree && chain[0] !== degree) chain.unshift(degree);
  }
  return chain;
}

export function progressionAt(progressions: Progression[], time: number): Progression | null {
  return progressions.find((p) => p.time <= time && time < p.end) ?? null;
}

// Pop-up animation (achievement_renderer.py): spring in, stay, fade out.
const APPEAR_SECONDS = 0.3;
const FADE_SECONDS = 0.4;
const START_SCALE = 0.6;

function easeOutBack(p: number): number {
  const c1 = 1.70158;
  return 1 + (c1 + 1) * (p - 1) ** 3 + c1 * (p - 1) ** 2;
}

export interface AchievementState {
  achievement: Achievement;
  scale: number;
  opacity: number;
}

export function achievementAt(achievements: Achievement[], time: number): AchievementState | null {
  const achievement = achievements.find((a) => a.time <= time && time < a.end);
  if (!achievement) return null;
  const since = time - achievement.time;
  const remaining = achievement.end - time;
  if (since < APPEAR_SECONDS) {
    const p = since / APPEAR_SECONDS;
    return { achievement, scale: START_SCALE + (1 - START_SCALE) * easeOutBack(p), opacity: Math.min(1, 0.25 + p) };
  }
  if (remaining < FADE_SECONDS) {
    const q = remaining / FADE_SECONDS;
    return { achievement, scale: 0.94 + 0.06 * q, opacity: q };
  }
  return { achievement, scale: 1, opacity: 1 };
}
