// Texts of the overlays, matching backend/app/video/labels.py so preview and video agree.
import type { Language, MusicalKey } from "../types/analysis";

const TEXTS = {
  chord: { en: "Chord" },
  key: { en: "Key" },
  modulation: { en: "Key change" },
  notesPerSecond: { en: "Notes per second" },
  total: { en: "Total" },
  record: { en: "Record" },
  newRecord: { en: "New record" },
  degree: { en: "Degree" },
  inKey: { en: "in" },
  achievement: { en: "Achievement unlocked" },
  motif: { en: "Motif" },
  firstAppearance: { en: "First appearance" },
  returns: { en: "Returns" },
  section: { en: "Section" },
  part: { en: "Part" },
  new: { en: "New" },
  finalBoss: { en: "Final boss" },
  bossWarning: { en: "Warning: boss ahead!" },
  defeated: { en: "Defeated!" },
  health: { en: "HP" },
  difficulty: { en: "Difficulty" },
  circleOfFifths: { en: "Circle of fifths" },
  bingoTitle: { en: "Keyboard bingo" },
  bingo: { en: "Bingo!" },
  songWrapped: { en: "Song Wrapped" },
} satisfies Record<string, Record<Language, string>>;

export function text(name: keyof typeof TEXTS, language: Language): string {
  return TEXTS[name][language];
}

/** "Bb" -> "B♭", "F#m7" -> "F♯m7"; only right after a note letter, so "m7b5" stays. */
export function displayAccidentals(name: string): string {
  return name.replace(/([A-G])([#b])/g, (_, letter: string, accidental: string) =>
    letter + (accidental === "#" ? "♯" : "♭"),
  );
}

/** Format a key name, such as "D minor" or "B♭ major". */
export function keyName(key: MusicalKey, language: Language): string {
  const tonic = displayAccidentals(key.tonic);
  return `${tonic} ${key.mode}`;
}

/** 1 -> "1st", 2 -> "2nd", 11 -> "11th", 23 -> "23rd". */
export function ordinalEn(n: number): string {
  const suffix = n % 100 >= 10 && n % 100 <= 20 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[n % 10] ?? "th");
  return `${n}${suffix}`;
}

/** "6. Mal" / "6th time". */
export function motifCount(n: number, language: Language): string {
  return `${ordinalEn(n)} time`;
}

/** "Neu" for a part heard for the first time, otherwise "zum 3. Mal" / "3rd time". */
export function sectionCount(n: number, language: Language): string {
  if (n === 1) return text("new", language);
  return `${ordinalEn(n)} time`;
}

/** "Bingo!" for the first completed line, then "2× Bingo!" ... */
export function bingoBanner(lines: number, language: Language): string {
  return lines <= 1 ? text("bingo", language) : `${lines}× ${text("bingo", language)}`;
}

/** Format a decimal value using a dot as the decimal separator. */
export function decimal(value: number, language: Language): string {
  const formatted = value.toFixed(1);
  return formatted;
}
