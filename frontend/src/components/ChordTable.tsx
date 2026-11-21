import type { Chord } from "../types/analysis";
import { formatTime } from "../utils/format";
import { displayAccidentals } from "../utils/labels";

export default function ChordTable({ chords }: { chords: Chord[] }) {
  if (chords.length === 0) {
    return (
      <p className="empty">
        No chords detected. Chords are determined from simultaneously sounding notes, so monophonic melodies or
        broken chords do not produce matches.
      </p>
    );
  }

  return (
    <div className="table-scroll">
      <table className="chord-table">
        <thead>
          <tr>
            <th>Start</th>
            <th>End</th>
            <th>Chord</th>
            <th>Degree</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {chords.map((chord) => (
            <tr key={`${chord.start}-${chord.name}`}>
              <td className="num">{formatTime(chord.start, 2)}</td>
              <td className="num">{formatTime(chord.end, 2)}</td>
              <td className="chord-name">{displayAccidentals(chord.name)}</td>
              <td className="chord-name">{chord.numeral ?? "–"}</td>
              <td className="notes">{chord.notes.map(displayAccidentals).join(" ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
