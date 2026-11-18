// Texts of the overlays, matching backend/app/video/labels.py so preview and video agree.
import type { Language, MusicalKey } from "../types/analysis";

const TEXTS = {
  chord: { de: "Akkord", en: "Chord" },
  key: { de: "Tonart", en: "Key" },
  modulation: { de: "Modulation", en: "Key change" },
  notesPerSecond: { de: "Noten pro Sekunde", en: "Notes per second" },
  total: { de: "Gesamt", en: "Total" },
  record: { de: "Rekord", en: "Record" },
  newRecord: { de: "Neuer Rekord", en: "New record" },
  degree: { de: "Stufe", en: "Degree" },
  inKey: { de: "in", en: "in" },
  achievement: { de: "Erfolg freigeschaltet", en: "Achievement unlocked" },
  motif: { de: "Motiv", en: "Motif" },
  firstAppearance: { de: "Erstes Auftreten", en: "First appearance" },
  returns: { de: "Kehrt zurück", en: "Returns" },
  section: { de: "Abschnitt", en: "Section" },
  part: { de: "Teil", en: "Part" },
  new: { de: "Neu", en: "New" },
  finalBoss: { de: "Endgegner", en: "Final boss" },
  bossWarning: { de: "Achtung: Boss naht!", en: "Warning: boss ahead!" },
  defeated: { de: "Besiegt!", en: "Defeated!" },
  health: { de: "HP", en: "HP" },
  difficulty: { de: "Schwierigkeit", en: "Difficulty" },
  circleOfFifths: { de: "Quintenzirkel", en: "Circle of fifths" },
  bingoTitle: { de: "Tastatur-Bingo", en: "Keyboard bingo" },
  bingo: { de: "Bingo!", en: "Bingo!" },
  songWrapped: { de: "Song Wrapped", en: "Song Wrapped" },
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

/** German "d-Moll" / "B♭-Dur", English "D minor" / "B♭ major". */
export function keyName(key: MusicalKey, language: Language): string {
  const tonic = displayAccidentals(key.tonic);
  if (language === "de") {
    return key.mode === "minor" ? `${tonic.toLowerCase()}-Moll` : `${tonic}-Dur`;
  }
  return `${tonic} ${key.mode}`;
}

/** 1 -> "1st", 2 -> "2nd", 11 -> "11th", 23 -> "23rd". */
export function ordinalEn(n: number): string {
  const suffix = n % 100 >= 10 && n % 100 <= 20 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[n % 10] ?? "th");
  return `${n}${suffix}`;
}

/** "6. Mal" / "6th time". */
export function motifCount(n: number, language: Language): string {
  return language === "de" ? `${n}. Mal` : `${ordinalEn(n)} time`;
}

/** "Neu" for a part heard for the first time, otherwise "zum 3. Mal" / "3rd time". */
export function sectionCount(n: number, language: Language): string {
  if (n === 1) return text("new", language);
  return language === "de" ? `zum ${n}. Mal` : `${ordinalEn(n)} time`;
}

/** "Bingo!" for the first completed line, then "2× Bingo!" ... */
export function bingoBanner(lines: number, language: Language): string {
  return lines <= 1 ? text("bingo", language) : `${lines}× ${text("bingo", language)}`;
}

/** 8.7 -> "8,7" in German. */
export function decimal(value: number, language: Language): string {
  const formatted = value.toFixed(1);
  return language === "de" ? formatted.replace(".", ",") : formatted;
}
