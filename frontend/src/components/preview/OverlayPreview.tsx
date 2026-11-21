import { useMemo, useRef, useState, type CSSProperties, type KeyboardEvent, type ReactNode } from "react";
import { useElementWidth } from "../../hooks/useElementWidth";
import { usePlayback } from "../../hooks/usePlayback";
import type { AnalysisResult, VideoKind, VideoSettings } from "../../types/analysis";
import { chordAt } from "../../utils/chords";
import { fontFamily, glowFactor, overlayDesign, overlayStyle } from "../../utils/style";
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
  wrappedVisible: boolean;
  onWrappedVisibilityChange: (visible: boolean) => void;
}

type OverlayFeature = Exclude<VideoKind, "wrapped">;

const PREVIEW_FEATURES: { kind: VideoKind; label: string }[] = [
  { kind: "spectrum", label: "Frequency spectrum" },
  { kind: "note_rate", label: "Notes/s" },
  { kind: "key", label: "Key" },
  { kind: "chords", label: "Chord" },
  { kind: "harmony", label: "Degrees" },
  { kind: "boss", label: "Final boss" },
  { kind: "circle", label: "Circle of fifths" },
  { kind: "bingo", label: "Bingo" },
  { kind: "achievements", label: "Achievements" },
  { kind: "heatmap", label: "Key heatmap" },
  { kind: "wrapped", label: "Song Wrapped" },
];

function ScaledOverlay({ kind, settings, children }: { kind: VideoKind; settings: VideoSettings; children: ReactNode }) {
  const design = overlayDesign(settings, kind);
  return (
    <div
      className={`preview-overlay${design.showFrame ? "" : " preview-overlay--frameless"}`}
      style={{ "--overlay-scale": design.scale, ...overlayStyle(design) } as CSSProperties}
    >
      {children}
    </div>
  );
}

/**
 * Live preview of selected exportable overlays on a dark "editor" background,
 * driven by one playback clock. The exported videos are transparent.
 */
export default function OverlayPreview({ result, settings, wrappedVisible, onWrappedVisibilityChange }: Props) {
  const screenRef = useRef<HTMLDivElement>(null);
  const width = useElementWidth(screenRef);
  const { time, playing, toggle, seek } = usePlayback(result.duration_seconds);
  const bestSoFar = useMemo(() => runningMax(result.note_rate.values), [result.note_rate.values]);
  const [visibleFeatures, setVisibleFeatures] = useState<Set<OverlayFeature>>(() => new Set(["spectrum"]));

  const { language } = settings;
  const chord = chordAt(result.chords, time);
  const chordIndex = chord ? result.chords.indexOf(chord) : -1;
  const chordKey = chord ? (keySegmentAt(result.keys.segments, chord.start)?.segment.key ?? result.keys.overall) : null;
  const achievement = achievementAt(result.achievements, time);
  const showFeature = (feature: OverlayFeature) => visibleFeatures.has(feature);
  const showTopFields =
    showFeature("note_rate") ||
    showFeature("key") ||
    showFeature("chords") ||
    showFeature("harmony") ||
    showFeature("boss");
  const showGameFields = showFeature("circle") || showFeature("bingo");
  const showSpectrumStage = showFeature("spectrum") || (showFeature("achievements") && achievement !== null);
  const noteRateDesign = overlayDesign(settings, "note_rate");
  const keyDesign = overlayDesign(settings, "key");
  const chordDesign = overlayDesign(settings, "chords");
  const harmonyDesign = overlayDesign(settings, "harmony");
  const bossDesign = overlayDesign(settings, "boss");
  const circleDesign = overlayDesign(settings, "circle");
  const bingoDesign = overlayDesign(settings, "bingo");
  const spectrumDesign = overlayDesign(settings, "spectrum");
  const achievementDesign = overlayDesign(settings, "achievements");
  const heatmapDesign = overlayDesign(settings, "heatmap");

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === " " && event.target === event.currentTarget) {
      event.preventDefault();
      toggle();
    }
  }

  return (
    <div className="player" tabIndex={0} onKeyDown={onKeyDown} aria-label="Preview; press Space to play or pause">
      <div className="preview__feature-toggles" role="group" aria-label="Toggle preview features">
        {PREVIEW_FEATURES.map(({ kind, label }) => (
          <button
            key={kind}
            type="button"
            className="preview__feature-toggle"
            aria-pressed={kind === "wrapped" ? wrappedVisible : visibleFeatures.has(kind)}
            onClick={() => {
              if (kind === "wrapped") {
                onWrappedVisibilityChange(!wrappedVisible);
                return;
              }
              setVisibleFeatures((current) => {
                const next = new Set(current);
                if (next.has(kind)) next.delete(kind);
                else next.add(kind);
                return next;
              });
            }}
          >
            {label}
          </button>
        ))}
      </div>
      <div
        ref={screenRef}
        className="player__screen"
      >
        {showTopFields && (
          <div className="player__fields">
            {showFeature("note_rate") && (
              <ScaledOverlay kind="note_rate" settings={settings}>
                <NoteRateField
                  state={noteRateAt(result.note_rate, bestSoFar, result.notes, time)}
                  peak={result.note_rate.peak_value}
                  color={noteRateDesign.color}
                  language={language}
                />
              </ScaledOverlay>
            )}
            {showFeature("key") && (
              <ScaledOverlay kind="key" settings={settings}>
                <KeyField current={keySegmentAt(result.keys.segments, time)} color={keyDesign.color} language={language} />
              </ScaledOverlay>
            )}
            {showFeature("chords") && (
              <ScaledOverlay kind="chords" settings={settings}>
                <ChordField name={chord?.name ?? null} start={chord?.start ?? null} color={chordDesign.color} language={language} />
              </ScaledOverlay>
            )}
            {showFeature("harmony") && (
              <ScaledOverlay kind="harmony" settings={settings}>
                <HarmonyField
                  numeral={chord?.numeral ?? null}
                  start={chord?.start ?? null}
                  chain={chord ? chainBefore(result.chords, chordIndex) : []}
                  musicalKey={chordKey}
                  progression={chord ? progressionAt(result.progressions, time) : null}
                  color={harmonyDesign.color}
                  language={language}
                />
              </ScaledOverlay>
            )}
            {showFeature("boss") && (
              <ScaledOverlay kind="boss" settings={settings}>
                <BossField boss={result.boss} state={bossAt(result.boss, time)} color={bossDesign.color} language={language} />
              </ScaledOverlay>
            )}
          </div>
        )}
        {showGameFields && (
          <div className="player__fields">
            {showFeature("circle") && (
              <ScaledOverlay kind="circle" settings={settings}>
                <CircleOfFifths
                  state={circleAt(result.chords, chord, time)}
                  chordName={chord ? displayAccidentals(chord.name) : null}
                  color={circleDesign.color}
                  language={language}
                />
              </ScaledOverlay>
            )}
            {showFeature("bingo") && (
              <ScaledOverlay kind="bingo" settings={settings}>
                <BingoBoard bingo={result.bingo} state={bingoAt(result.bingo, time)} color={bingoDesign.color} language={language} />
              </ScaledOverlay>
            )}
          </div>
        )}
        {showSpectrumStage && (
          <div className="player__stage">
            {showFeature("spectrum") && (
              <ScaledOverlay kind="spectrum" settings={settings}>
                <SpectrumCanvas
                  spectrum={result.spectrum}
                  time={time}
                  width={width}
                  height={Math.round(Math.min(Math.max(width * 0.36, 200), 360))}
                  color={spectrumDesign.color}
                  showGrid={spectrumDesign.showGrid}
                  displayStyle={spectrumDesign.spectrumStyle}
                />
              </ScaledOverlay>
            )}
            {showFeature("achievements") && achievement && (
              <div className="player__popup">
                <ScaledOverlay kind="achievements" settings={settings}>
                  <AchievementToast state={achievement} color={achievementDesign.color} language={language} />
                </ScaledOverlay>
              </div>
            )}
          </div>
        )}
        {showFeature("heatmap") && (
          <ScaledOverlay kind="heatmap" settings={settings}>
            <HeatBar
              notes={result.notes}
              time={time}
              width={width}
              color={heatmapDesign.color}
              font={fontFamily(heatmapDesign.font)}
              glow={glowFactor(heatmapDesign.glow)}
            />
          </ScaledOverlay>
        )}
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
