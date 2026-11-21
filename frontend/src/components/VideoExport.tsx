import { useEffect, useState } from "react";
import { createVideoJob, fetchVideoJob, videoDownloadUrl } from "../api/client";
import type { OverlayDesign, VideoFormat, VideoJob, VideoKind, VideoSettings } from "../types/analysis";
import { DEFAULT_OVERLAY_DESIGN, FONTS, GLOW_LEVELS, overlayDesign } from "../utils/style";

interface Props {
  file: File;
  settings: VideoSettings;
  onSettingsChange: (settings: VideoSettings) => void;
}

const RESOLUTIONS = [
  { label: "1280 × 720", width: 1280, height: 720 },
  { label: "1920 × 1080", width: 1920, height: 1080 },
  { label: "2560 × 1440", width: 2560, height: 1440 },
  { label: "3840 × 2160", width: 3840, height: 2160 },
];
const FPS_OPTIONS = [24, 25, 30, 50, 60];
const KIND_LABELS: Record<VideoKind, string> = {
  note_rate: "Notes/s",
  key: "Key",
  chords: "Chord",
  harmony: "Degrees",
  achievements: "Achievements",
  boss: "Final boss",
  circle: "Circle of fifths",
  bingo: "Bingo",
  wrapped: "Song Wrapped",
  spectrum: "Frequency spectrum",
  heatmap: "Key heatmap",
};
const KINDS = Object.keys(KIND_LABELS) as VideoKind[];
const POLL_INTERVAL_MS = 1000;
const NEON_PRESETS = [
  { name: "Cyan", value: "#00e5ff" },
  { name: "Magenta", value: "#ff2bd6" },
  { name: "Lime", value: "#39ff14" },
  { name: "Orange", value: "#ff8a00" },
  { name: "Purple", value: "#a855ff" },
  { name: "Yellow", value: "#ffe600" },
];

export default function VideoExport({
  file,
  settings,
  onSettingsChange,
}: Props) {
  const [jobs, setJobs] = useState<VideoJob[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [designKind, setDesignKind] = useState<VideoKind>("chords");

  // Poll unfinished jobs until they are done or failed.
  const pendingIds = jobs
    .filter((j) => j.status === "queued" || j.status === "running")
    .map((j) => j.id);
  const pendingKey = pendingIds.join(",");
  useEffect(() => {
    if (!pendingKey) return;
    const timer = setInterval(async () => {
      try {
        const updates = await Promise.all(
          pendingKey.split(",").map(fetchVideoJob),
        );
        setJobs((current) =>
          current.map((job) => updates.find((u) => u.id === job.id) ?? job),
        );
      } catch (e) {
        setError(
          e instanceof Error
            ? e.message
            : "Status could not be retrieved.",
        );
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [pendingKey]);

  // A new file invalidates earlier jobs.
  useEffect(() => setJobs([]), [file]);

  async function start(kinds: VideoKind[]) {
    setError(null);
    try {
      // Sequentially, so the jobs queue up in the listed order.
      for (const kind of kinds) {
        const job = await createVideoJob(file, kind, settings);
        setJobs((current) => [...current, job]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed.");
    }
  }

  const update = (patch: Partial<VideoSettings>) =>
    onSettingsChange({ ...settings, ...patch });
  const updateDesign = (patch: Partial<OverlayDesign>) => {
    if (settings.designMode === "global") {
      update({ globalDesign: { ...settings.globalDesign, ...patch } });
    } else {
      update({
        featureDesigns: {
          ...settings.featureDesigns,
          [designKind]: { ...settings.featureDesigns[designKind], ...patch },
        },
      });
    }
  };
  const resolution = `${settings.width}x${settings.height}`;
  const design = overlayDesign(settings, designKind);
  const scaleValue = design.scale;
  const overlayScalePercent = Math.round(scaleValue * 100);

  return (
    <div className="export">
      <fieldset className="export__group">
        <legend>Video</legend>
        <div className="export__settings">
          <label className="field">
            <span>Format</span>
            <select
              value={settings.format}
              onChange={(e) =>
                update({ format: e.target.value as VideoFormat })
              }
            >
              <option value="prores">ProRes 4444 (.mov)</option>
              <option value="png">PNG sequence (.zip)</option>
            </select>
          </label>
          <label className="field">
            <span>Resolution</span>
            <select
              value={resolution}
              onChange={(e) => {
                const r = RESOLUTIONS.find(
                  (o) => `${o.width}x${o.height}` === e.target.value,
                )!;
                update({ width: r.width, height: r.height });
              }}
            >
              {RESOLUTIONS.map((r) => (
                <option key={r.label} value={`${r.width}x${r.height}`}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Frame rate</span>
            <select
              value={settings.fps}
              onChange={(e) => update({ fps: Number(e.target.value) })}
            >
              {FPS_OPTIONS.map((fps) => (
                <option key={fps} value={fps}>
                  {fps} fps
                </option>
              ))}
            </select>
          </label>
        </div>
      </fieldset>
      <fieldset className="export__group">
        <legend>Design</legend>
        <div className="design-mode">
          <span id="design-mode-label">Apply design settings</span>
          <button
            type="button"
            role="switch"
            aria-checked={settings.designMode === "individual"}
            aria-labelledby="design-mode-label"
            className="design-mode__toggle"
            onClick={() =>
              update({ designMode: settings.designMode === "global" ? "individual" : "global" })
            }
          >
            <span className="design-mode__toggle-track" aria-hidden="true">
              <span />
            </span>
            {settings.designMode === "global" ? "Global" : "Individual"}
          </button>
        </div>
        {settings.designMode === "individual" && (
          <div className="feature-design__tabs" role="tablist" aria-label="Feature design">
            {KINDS.map((kind) => (
              <button
                key={kind}
                id={`feature-design-tab-${kind}`}
                type="button"
                role="tab"
                aria-selected={designKind === kind}
                aria-controls="feature-design-panel"
                className={`feature-design__tab${designKind === kind ? " feature-design__tab--active" : ""}`}
                onClick={() => setDesignKind(kind)}
              >
                {KIND_LABELS[kind]}
              </button>
            ))}
          </div>
        )}
        <div
          id="feature-design-panel"
          className="export__settings"
          role={settings.designMode === "individual" ? "tabpanel" : undefined}
          aria-labelledby={settings.designMode === "individual" ? `feature-design-tab-${designKind}` : undefined}
        >
          <div className="field">
            <span>Neon color</span>
            <div className="swatches">
              {NEON_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  type="button"
                  className={`swatch${design.color.toLowerCase() === preset.value ? " swatch--active" : ""}`}
                  style={{ background: preset.value, color: preset.value }}
                  aria-label={preset.name}
                  title={preset.name}
                  onClick={() => updateDesign({ color: preset.value })}
                />
              ))}
              <input
                type="color"
                value={design.color}
                aria-label="Custom color"
                title="Custom color"
                onChange={(e) => updateDesign({ color: e.target.value })}
              />
            </div>
          </div>
          <div className="field">
            <span>Font</span>
            <div className="choices" role="radiogroup" aria-label="Font">
              {FONTS.map((font) => (
                <button
                  key={font.id}
                  type="button"
                  role="radio"
                  aria-checked={design.font === font.id}
                  className={`choice${design.font === font.id ? " choice--active" : ""}`}
                  style={{ fontFamily: font.family, fontSize: `calc(0.8125rem * ${font.scale})` }}
                  title={font.hint}
                  onClick={() => updateDesign({ font: font.id })}
                >
                  {font.label}
                </button>
              ))}
            </div>
          </div>
          <div className="field">
            <span>Glow</span>
            <div className="choices" role="radiogroup" aria-label="Glow">
              {GLOW_LEVELS.map((level) => (
                <button
                  key={level.id}
                  type="button"
                  role="radio"
                  aria-checked={design.glow === level.id}
                  className={`choice${design.glow === level.id ? " choice--active" : ""}`}
                  onClick={() => updateDesign({ glow: level.id })}
                >
                  {level.label}
                </button>
              ))}
            </div>
          </div>
          <label className="field field--checkbox">
            <input
              type="checkbox"
              checked={design.showFrame}
              onChange={(e) => updateDesign({ showFrame: e.target.checked })}
            />
            <span>Frame around text and game overlays</span>
          </label>
          <label className="field field--checkbox">
            <input
              type="checkbox"
              checked={design.showGrid}
              onChange={(e) => updateDesign({ showGrid: e.target.checked })}
            />
            <span>Grid &amp; Hz labels (spectrum)</span>
          </label>
          {(settings.designMode === "global" || designKind === "spectrum") && (
            <div className="field">
              <span>Spectrum display</span>
              <div className="choices" role="radiogroup" aria-label="Spectrum display">
                <button
                  type="button"
                  role="radio"
                  aria-checked={design.spectrumStyle === "curve"}
                  className={`choice${design.spectrumStyle === "curve" ? " choice--active" : ""}`}
                  onClick={() => updateDesign({ spectrumStyle: "curve" })}
                >
                  Curve
                </button>
                <button
                  type="button"
                  role="radio"
                  aria-checked={design.spectrumStyle === "centered_bars"}
                  className={`choice${design.spectrumStyle === "centered_bars" ? " choice--active" : ""}`}
                  onClick={() => updateDesign({ spectrumStyle: "centered_bars" })}
                >
                  Centered bars
                </button>
              </div>
            </div>
          )}
          <div className="field field--scale">
            <label htmlFor="overlay-size">
              {settings.designMode === "global" ? "All overlays" : KIND_LABELS[designKind]} size: {overlayScalePercent}%
            </label>
            <div className="field--scale__controls">
              <input
                id="overlay-size"
                type="range"
                min={25}
                max={100}
                step={5}
                value={overlayScalePercent}
                aria-label={`Size of ${settings.designMode === "global" ? "all overlays" : KIND_LABELS[designKind]}`}
                onChange={(e) => updateDesign({ scale: Number(e.target.value) / 100 })}
              />
              <button
                type="button"
                className="button button--reset"
                disabled={scaleValue === DEFAULT_OVERLAY_DESIGN.scale}
                onClick={() => updateDesign({ scale: DEFAULT_OVERLAY_DESIGN.scale })}
              >
                Reset to default
              </button>
            </div>
          </div>
        </div>
      </fieldset>

      <p className="hint">
        Each overlay is a separate video with a transparent background, so it can
        be placed freely in DaVinci Resolve. ProRes 4444 is the recommended format,
        but it is large (about 0.7 GB per minute for 1080p30 spectrum).
      </p>

      <div className="export__actions">
        {KINDS.map((kind) => (
          <button
            key={kind}
            type="button"
            className="button"
            onClick={() => start([kind])}
          >
            {KIND_LABELS[kind]}
          </button>
        ))}
        <button
          type="button"
          className="button button--primary"
          onClick={() => start(KINDS)}
        >
          Create all
        </button>
      </div>

      {error && (
        <p className="message message--error" role="alert">
          {error}
        </p>
      )}

      {jobs.length > 0 && (
        <ul className="jobs">
          {jobs.map((job) => (
            <JobRow key={job.id} job={job} />
          ))}
        </ul>
      )}
    </div>
  );
}

function JobRow({ job }: { job: VideoJob }) {
  const percent = Math.round(job.progress * 100);
  const format = job.format === "prores" ? "ProRes" : "PNG";
  return (
    <li className="job">
      <div className="job__header">
        <strong>{KIND_LABELS[job.kind]}</strong>
        <span className="job__meta">{format}</span>
      </div>
      {job.status === "done" ? (
        <a
          className="button"
          href={videoDownloadUrl(job.id)}
          download={job.file_name ?? undefined}
        >
          Download {job.file_name} ({formatBytes(job.size_bytes ?? 0)})
        </a>
      ) : job.status === "failed" ? (
        <p className="message message--error">Failed: {job.error}</p>
      ) : (
        <div className="job__progress">
          <progress
            max={100}
            value={percent}
            aria-label={`Creating ${KIND_LABELS[job.kind]}`}
          />
          <span>{job.status === "queued" ? "Waiting …" : `${percent} %`}</span>
        </div>
      )}
    </li>
  );
}

function formatBytes(bytes: number): string {
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(2)} GB`;
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(0)} MB`;
  return `${Math.max(1, Math.round(bytes / 1e3))} kB`;
}
