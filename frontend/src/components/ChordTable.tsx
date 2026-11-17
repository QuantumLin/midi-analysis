import type { Chord } from "../types/analysis";
import { formatTime } from "../utils/format";
import { displayAccidentals } from "../utils/labels";

export default function ChordTable({ chords }: { chords: Chord[] }) {
  if (chords.length === 0) {
    return (
      <p className="empty">
        Keine Akkorde erkannt. Akkorde werden aus gleichzeitig klingenden Noten bestimmt – einstimmige Melodien oder
        gebrochene Akkorde ergeben daher keine Treffer.
      </p>
    );
  }

  return (
    <div className="table-scroll">
      <table className="chord-table">
        <thead>
          <tr>
            <th>Start</th>
            <th>Ende</th>
            <th>Akkord</th>
            <th>Noten</th>
          </tr>
        </thead>
        <tbody>
          {chords.map((chord) => (
            <tr key={`${chord.start}-${chord.name}`}>
              <td className="num">{formatTime(chord.start, 2)}</td>
              <td className="num">{formatTime(chord.end, 2)}</td>
              <td className="chord-name">{displayAccidentals(chord.name)}</td>
              <td className="notes">{chord.notes.map(displayAccidentals).join(" ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
