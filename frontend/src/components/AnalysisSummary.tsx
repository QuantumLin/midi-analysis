import type { AnalysisResult } from "../types/analysis";
import { formatTime } from "../utils/format";
import { keyName } from "../utils/labels";

export default function AnalysisSummary({ result }: { result: AnalysisResult }) {
  const stats = [
    { label: "Duration", value: formatTime(result.duration_seconds) },
    { label: "Notes", value: result.note_count.toLocaleString("en-US") },
    { label: "Chord changes", value: result.chords.length.toLocaleString("en-US") },
    { label: "Key", value: result.keys.overall ? keyName(result.keys.overall, "en") : "–" },
    { label: "Max. notes/s", value: String(result.note_rate.peak_value) },
  ];
  const modulations = result.keys.segments.length - 1;
  if (modulations > 0) {
    stats.push({ label: "Modulations", value: String(modulations) });
  }
  if (result.percussion_note_count > 0) {
    stats.push({ label: "Percussion (ignored)", value: result.percussion_note_count.toLocaleString("en-US") });
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
