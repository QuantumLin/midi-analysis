// The three text overlays, styled like the exported videos (backend/app/video/*_renderer.py).
import type { Language } from "../../types/analysis";
import { displayAccidentals, keyName, text } from "../../utils/labels";
import type { NoteRateState } from "../../utils/stats";
import type { KeySegment } from "../../types/analysis";

export function ChordField({ name, color }: { name: string | null; color: string }) {
  return (
    <div className="overlay-box" aria-label="Akkord">
      <span className="overlay-box__label">&nbsp;</span>
      <span className="overlay-box__value" style={{ color }}>
        {name ? displayAccidentals(name) : "–"}
      </span>
    </div>
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
  return (
    <div className="overlay-box" aria-label="Tonart">
      {current?.modulated ? (
        <span className="overlay-box__label overlay-box__label--accent" style={{ color }}>
          {text("modulation", language)} →
        </span>
      ) : (
        <span className="overlay-box__label">{text("key", language)}</span>
      )}
      <span className="overlay-box__value" style={{ color }}>
        {current ? keyName(current.segment.key, language) : "–"}
      </span>
    </div>
  );
}

export function NoteRateField({ state, color, language }: { state: NoteRateState; color: string; language: Language }) {
  const unit = text("notesPerSecond", language);
  return (
    <div className="overlay-box" aria-label="Noten pro Sekunde">
      <span className="overlay-box__value">
        <span style={{ color }}>{state.rate}</span> <span className="overlay-box__unit">{unit}</span>
      </span>
      {state.newRecord !== null ? (
        <span className="overlay-box__label overlay-box__label--accent" style={{ color }}>
          {text("newRecord", language)}: {state.newRecord} {unit}
        </span>
      ) : (
        <span className="overlay-box__label">
          {text("total", language)} {state.total} · {text("record", language)} {state.best}
        </span>
      )}
    </div>
  );
}
