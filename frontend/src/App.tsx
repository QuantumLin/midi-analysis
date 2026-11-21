import { useEffect, useState } from "react";
import { analyzeMidi, fetchHealth } from "./api/client";
import AnalysisSummary from "./components/AnalysisSummary";
import ChordTable from "./components/ChordTable";
import FileUpload from "./components/FileUpload";
import Logo from "./components/Logo";
import { WrappedPreview } from "./components/preview/GameFields";
import OverlayPreview from "./components/preview/OverlayPreview";
import VideoExport from "./components/VideoExport";
import type { AnalysisResult, VideoSettings } from "./types/analysis";
import { overlayStyle } from "./utils/style";

type BackendState = "checking" | "online" | "offline";

const DEFAULT_VIDEO_SETTINGS: VideoSettings = {
  format: "prores",
  width: 1920,
  height: 1080,
  fps: 30,
  color: "#00e5ff",
  showGrid: true,
  language: "en",
  showFrame: true,
  font: "orbitron",
  glow: "normal",
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
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <header className="app__header">
        <Logo />
        <span className={`status status--${backend}`}>Backend: {backend}</span>
      </header>

      <FileUpload disabled={loading || backend === "offline"} onFileSelected={handleFile} />
      {loading && <p className="message">Analyzing …</p>}
      {error && (
        <p className="message message--error" role="alert">
          {error}
        </p>
      )}

      {result && file && (
        <>
          <AnalysisSummary result={result} />
          <section className="card">
            <h2>Overlay Preview</h2>
            <OverlayPreview result={result} settings={videoSettings} />
          </section>
          <section className="card">
            <h2>Song Wrapped</h2>
            <p className="hint">
              An ending with the numbers from the piece. The cards appear one after another in the video; it is a
              separate clip that can be placed behind the piece in the editor.
            </p>
            <div className="player__screen" style={overlayStyle(videoSettings)}>
              <WrappedPreview cards={result.wrapped} color={videoSettings.color} language={videoSettings.language} />
            </div>
          </section>
          <section className="card">
            <h2>Video Export</h2>
            <VideoExport file={file} settings={videoSettings} onSettingsChange={setVideoSettings} />
          </section>
          <section className="card">
            <h2>Chords</h2>
            <ChordTable chords={result.chords} />
          </section>
        </>
      )}
    </main>
  );
}
