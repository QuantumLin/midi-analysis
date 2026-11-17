import { useEffect, useState } from "react";
import { analyzeMidi, fetchHealth } from "./api/client";
import AnalysisSummary from "./components/AnalysisSummary";
import ChordTable from "./components/ChordTable";
import FileUpload from "./components/FileUpload";
import OverlayPreview from "./components/preview/OverlayPreview";
import VideoExport from "./components/VideoExport";
import type { AnalysisResult, VideoSettings } from "./types/analysis";

type BackendState = "checking" | "online" | "offline";

const DEFAULT_VIDEO_SETTINGS: VideoSettings = {
  format: "prores",
  width: 1920,
  height: 1080,
  fps: 30,
  color: "#00e5ff",
  showGrid: true,
  language: "de",
};

export default function App() {
  const [backend, setBackend] = useState<BackendState>("checking");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [videoSettings, setVideoSettings] = useState<VideoSettings>(DEFAULT_VIDEO_SETTINGS);

  useEffect(() => {
    fetchHealth()
      .then((health) => setBackend(health.status === "ok" ? "online" : "offline"))
      .catch(() => setBackend("offline"));
  }, []);

  async function handleFile(selected: File) {
    setLoading(true);
    setError(null);
    try {
      setResult(await analyzeMidi(selected));
      setFile(selected); // kept for the video export, which re-uploads it
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analyse fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <header className="app__header">
        <h1>MIDI Analysis</h1>
        <span className={`status status--${backend}`}>Backend: {backend}</span>
      </header>

      <FileUpload disabled={loading || backend === "offline"} onFileSelected={handleFile} />
      {loading && <p className="message">Analysiere …</p>}
      {error && (
        <p className="message message--error" role="alert">
          {error}
        </p>
      )}

      {result && file && (
        <>
          <AnalysisSummary result={result} />
          <section className="card">
            <h2>Overlay-Vorschau</h2>
            <OverlayPreview result={result} settings={videoSettings} />
          </section>
          <section className="card">
            <h2>Video-Export</h2>
            <VideoExport file={file} settings={videoSettings} onSettingsChange={setVideoSettings} />
          </section>
          <section className="card">
            <h2>Akkorde</h2>
            <ChordTable chords={result.chords} />
          </section>
        </>
      )}
    </main>
  );
}
