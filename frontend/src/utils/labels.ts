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
