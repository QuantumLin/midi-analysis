import { useEffect, useState } from "react";
import { createVideoJob, fetchVideoJob, videoDownloadUrl } from "../api/client";
import type { VideoFormat, VideoJob, VideoKind, VideoSettings } from "../types/analysis";

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
const KIND_LABELS: Record<VideoKind, string> = { spectrum: "Frequenz-Video", chords: "Akkord-Video" };
const POLL_INTERVAL_MS = 1000;

export default function VideoExport({ file, settings, onSettingsChange }: Props) {
  const [jobs, setJobs] = useState<VideoJob[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Poll unfinished jobs until they are done or failed.
  const pendingIds = jobs.filter((j) => j.status === "queued" || j.status === "running").map((j) => j.id);
  const pendingKey = pendingIds.join(",");
  useEffect(() => {
    if (!pendingKey) return;
    const timer = setInterval(async () => {
      try {
        const updates = await Promise.all(pendingKey.split(",").map(fetchVideoJob));
        setJobs((current) => current.map((job) => updates.find((u) => u.id === job.id) ?? job));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Status konnte nicht abgefragt werden.");
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [pendingKey]);

  // A new file invalidates earlier jobs.
  useEffect(() => setJobs([]), [file]);

  async function start(kind: VideoKind) {
    setError(null);
    try {
      const job = await createVideoJob(file, kind, settings);
      setJobs((current) => [job, ...current]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export fehlgeschlagen.");
    }
  }

  const update = (patch: Partial<VideoSettings>) => onSettingsChange({ ...settings, ...patch });
  const resolution = `${settings.width}x${settings.height}`;

  return (
    <div className="export">
      <div className="export__settings">
        <label className="field">
          <span>Format</span>
          <select value={settings.format} onChange={(e) => update({ format: e.target.value as VideoFormat })}>
            <option value="prores">ProRes 4444 (.mov)</option>
            <option value="png">PNG-Sequenz (.zip)</option>
          </select>
        </label>
        <label className="field">
          <span>Auflösung</span>
          <select
            value={resolution}
            onChange={(e) => {
              const r = RESOLUTIONS.find((o) => `${o.width}x${o.height}` === e.target.value)!;
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
          <span>Bildrate</span>
          <select value={settings.fps} onChange={(e) => update({ fps: Number(e.target.value) })}>
            {FPS_OPTIONS.map((fps) => (
              <option key={fps} value={fps}>
                {fps} fps
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Farbe</span>
          <input type="color" value={settings.color} onChange={(e) => update({ color: e.target.value })} />
        </label>
        <label className="field field--checkbox">
          <input type="checkbox" checked={settings.showGrid} onChange={(e) => update({ showGrid: e.target.checked })} />
          <span>Raster &amp; Hz-Beschriftung (Frequenz-Video)</span>
        </label>
      </div>

      <p className="hint">
        Beide Videos haben einen transparenten Hintergrund. ProRes 4444 ist das gängige Format für DaVinci Resolve,
        aber groß (Frequenz-Video in 1080p30 ca. 0,7 GB pro Minute).
      </p>

      <div className="export__actions">
        <button type="button" className="button button--primary" onClick={() => start("spectrum")}>
          Frequenz-Video erstellen
        </button>
        <button type="button" className="button button--primary" onClick={() => start("chords")}>
          Akkord-Video erstellen
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
        <a className="button" href={videoDownloadUrl(job.id)} download={job.file_name ?? undefined}>
          Download {job.file_name} ({formatBytes(job.size_bytes ?? 0)})
        </a>
      ) : job.status === "failed" ? (
        <p className="message message--error">Fehlgeschlagen: {job.error}</p>
      ) : (
        <div className="job__progress">
          <progress max={100} value={percent} aria-label={`${KIND_LABELS[job.kind]} wird erstellt`} />
          <span>{job.status === "queued" ? "Wartet …" : `${percent} %`}</span>
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
