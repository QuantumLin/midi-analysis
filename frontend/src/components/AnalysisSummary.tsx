import type { AnalysisResult } from "../types/analysis";
import { formatTime } from "../utils/format";

export default function AnalysisSummary({ result }: { result: AnalysisResult }) {
  const stats = [
    { label: "Dauer", value: formatTime(result.duration_seconds) },
    { label: "Noten", value: result.note_count.toLocaleString("de-DE") },
    { label: "Akkordwechsel", value: result.chords.length.toLocaleString("de-DE") },
  ];
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
