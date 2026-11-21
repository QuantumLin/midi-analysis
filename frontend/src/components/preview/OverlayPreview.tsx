import { useMemo, useRef, type CSSProperties, type KeyboardEvent, type ReactNode } from "react";
import { useElementWidth } from "../../hooks/useElementWidth";
import { usePlayback } from "../../hooks/usePlayback";
import type { AnalysisResult, VideoSettings } from "../../types/analysis";
import { chordAt } from "../../utils/chords";
import { fontFamily, glowFactor, overlayStyle } from "../../utils/style";
import { displayAccidentals } from "../../utils/labels";
import { bingoAt, bossAt, circleAt } from "../../utils/games";
import { achievementAt, chainBefore, progressionAt } from "../../utils/harmony";
import { formatTime } from "../../utils/format";
import { keySegmentAt, noteRateAt, runningMax } from "../../utils/stats";
import { BingoBoard, BossField, CircleOfFifths } from "./GameFields";
import HeatBar from "./HeatBar";
import {
  AchievementToast,
  ChordField,
  HarmonyField,
  KeyField,
  NoteRateField,
} from "./OverlayFields";
import SpectrumCanvas from "./SpectrumCanvas";

interface Props {
  result: AnalysisResult;
  settings: VideoSettings;
}

function ScaledOverlay({ scale, children }: { scale: number; children: ReactNode }) {
  return (
    <div className="preview-overlay" style={{ "--overlay-scale": scale } as CSSProperties}>
      {children}
    </div>
  );
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
  const chordIndex = chord ? result.chords.indexOf(chord) : -1;
  const chordKey = chord ? (keySegmentAt(result.keys.segments, chord.start)?.segment.key ?? result.keys.overall) : null;
  const achievement = achievementAt(result.achievements, time);

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === " " && event.target === event.currentTarget) {
      event.preventDefault();
      toggle();
    }
  }

  return (
    <div className="player" tabIndex={0} onKeyDown={onKeyDown} aria-label="Preview; press Space to play or pause">
      <div
        ref={screenRef}
        className={`player__screen${settings.showFrame ? "" : " player__screen--frameless"}`}
        style={overlayStyle(settings)}
      >
        <div className="player__fields">
          <ScaledOverlay scale={settings.overlayScales.note_rate}>
            <NoteRateField
              state={noteRateAt(result.note_rate, bestSoFar, result.notes, time)}
              peak={result.note_rate.peak_value}
              color={color}
              language={language}
            />
          </ScaledOverlay>
          <ScaledOverlay scale={settings.overlayScales.key}>
            <KeyField current={keySegmentAt(result.keys.segments, time)} color={color} language={language} />
          </ScaledOverlay>
          <ScaledOverlay scale={settings.overlayScales.chords}>
            <ChordField name={chord?.name ?? null} start={chord?.start ?? null} color={color} language={language} />
          </ScaledOverlay>
          <ScaledOverlay scale={settings.overlayScales.harmony}>
            <HarmonyField
              numeral={chord?.numeral ?? null}
              start={chord?.start ?? null}
              chain={chord ? chainBefore(result.chords, chordIndex) : []}
              musicalKey={chordKey}
              progression={chord ? progressionAt(result.progressions, time) : null}
              color={color}
              language={language}
            />
          </ScaledOverlay>
          <ScaledOverlay scale={settings.overlayScales.boss}>
            <BossField boss={result.boss} state={bossAt(result.boss, time)} color={color} language={language} />
          </ScaledOverlay>
        </div>
        <div className="player__fields">
          <ScaledOverlay scale={settings.overlayScales.circle}>
            <CircleOfFifths
              state={circleAt(result.chords, chord, time)}
              chordName={chord ? displayAccidentals(chord.name) : null}
              color={color}
              language={language}
            />
          </ScaledOverlay>
          <ScaledOverlay scale={settings.overlayScales.bingo}>
            <BingoBoard bingo={result.bingo} state={bingoAt(result.bingo, time)} color={color} language={language} />
          </ScaledOverlay>
        </div>
        <div className="player__stage">
          <ScaledOverlay scale={settings.overlayScales.spectrum}>
            <SpectrumCanvas
              spectrum={result.spectrum}
              time={time}
              width={width}
              height={Math.round(Math.min(Math.max(width * 0.36, 200), 360))}
              color={color}
              showGrid={settings.showGrid}
            />
          </ScaledOverlay>
          {achievement && (
            <div className="player__popup">
              <ScaledOverlay scale={settings.overlayScales.achievements}>
                <AchievementToast state={achievement} color={color} language={language} />
              </ScaledOverlay>
            </div>
          )}
        </div>
        <ScaledOverlay scale={settings.overlayScales.heatmap}>
          <HeatBar
            notes={result.notes}
            time={time}
            width={width}
            color={color}
            font={fontFamily(settings.font)}
            glow={glowFactor(settings.glow)}
          />
        </ScaledOverlay>
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
