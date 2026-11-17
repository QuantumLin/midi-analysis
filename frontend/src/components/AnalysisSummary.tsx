import type { AnalysisResult } from "../types/analysis";
import { formatTime } from "../utils/format";
import { keyName } from "../utils/labels";

export default function AnalysisSummary({ result }: { result: AnalysisResult }) {
  const stats = [
    { label: "Dauer", value: formatTime(result.duration_seconds) },
    { label: "Noten", value: result.note_count.toLocaleString("de-DE") },
    { label: "Akkordwechsel", value: result.chords.length.toLocaleString("de-DE") },
    { label: "Tonart", value: result.keys.overall ? keyName(result.keys.overall, "de") : "–" },
    { label: "Max. Noten/s", value: String(result.note_rate.peak_value) },
  ];
  const modulations = result.keys.segments.length - 1;
  if (modulations > 0) {
    stats.push({ label: "Modulationen", value: String(modulations) });
  }
  if (result.percussion_note_count > 0) {
    stats.push({ label: "Percussion (ignoriert)", value: result.percussion_note_count.toLocaleString("de-DE") });
  }

  return (
    <section className="summary">
      <h2 className="summary__file">{result.file_name}</h2>
      <dl className="summary__stats">
        {stats.map((s) => (
          <div key={s.label}>
            <dt>{s.label}</dt>
            <dd>{s.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
