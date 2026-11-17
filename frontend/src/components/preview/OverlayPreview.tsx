import { useMemo, useRef, type KeyboardEvent } from "react";
import { useElementWidth } from "../../hooks/useElementWidth";
import { usePlayback } from "../../hooks/usePlayback";
import type { AnalysisResult, VideoSettings } from "../../types/analysis";
import { chordAt } from "../../utils/chords";
import { formatTime } from "../../utils/format";
import { keySegmentAt, noteRateAt, runningMax } from "../../utils/stats";
import HeatBar from "./HeatBar";
import { ChordField, KeyField, NoteRateField } from "./OverlayFields";
import SpectrumCanvas from "./SpectrumCanvas";

interface Props {
  result: AnalysisResult;
  settings: VideoSettings;
}

/**
 * Live preview of all exportable overlays on a dark "editor" background,
 * driven by one playback clock. The exported videos are transparent.
 */
export default function OverlayPreview({ result, settings }: Props) {
  const screenRef = useRef<HTMLDivElement>(null);
  const width = useElementWidth(screenRef);
  const { time, playing, toggle, seek } = usePlayback(result.duration_seconds);
  const bestSoFar = useMemo(() => runningMax(result.note_rate.values), [result.note_rate.values]);

  const { color, language } = settings;
  const chord = chordAt(result.chords, time);

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === " " && event.target === event.currentTarget) {
      event.preventDefault();
      toggle();
    }
  }

  return (
    <div className="player" tabIndex={0} onKeyDown={onKeyDown} aria-label="Vorschau, Leertaste startet und pausiert">
      <div ref={screenRef} className="player__screen">
        <div className="player__fields">
          <NoteRateField
            state={noteRateAt(result.note_rate, bestSoFar, result.notes, time)}
            peak={result.note_rate.peak_value}
            color={color}
            language={language}
          />
          <KeyField current={keySegmentAt(result.keys.segments, time)} color={color} language={language} />
          <ChordField name={chord?.name ?? null} start={chord?.start ?? null} color={color} language={language} />
        </div>
        <SpectrumCanvas
          spectrum={result.spectrum}
          time={time}
          width={width}
          height={Math.round(Math.min(Math.max(width * 0.36, 200), 360))}
          color={color}
          showGrid={settings.showGrid}
        />
        <HeatBar notes={result.notes} time={time} width={width} color={color} />
      </div>
      <div className="player__controls">
        <button type="button" className="button" onClick={toggle}>
          {playing ? "Pause" : "Play"}
        </button>
        <input
          type="range"
          className="player__seek"
          min={0}
          max={result.duration_seconds}
          step={0.01}
          value={time}
          aria-label="Position"
          onChange={(e) => seek(Number(e.target.value))}
        />
        <span className="player__time">
          {formatTime(time)} / {formatTime(result.duration_seconds)}
        </span>
      </div>
    </div>
  );
}
