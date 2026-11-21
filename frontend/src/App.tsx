import { useEffect, useState, type CSSProperties } from "react";
import { analyzeMidi, fetchHealth } from "./api/client";
import ChordTable from "./components/ChordTable";
import FileUpload from "./components/FileUpload";
import Logo from "./components/Logo";
import { WrappedPreview } from "./components/preview/GameFields";
import OverlayPreview from "./components/preview/OverlayPreview";
import VideoExport from "./components/VideoExport";
import type { AnalysisResult, VideoKind, VideoSettings } from "./types/analysis";
import { DEFAULT_OVERLAY_DESIGN, overlayDesign, overlayStyle } from "./utils/style";

type BackendState = "checking" | "online" | "offline";
type SidebarTab = "video" | "chords";

const DEFAULT_FEATURE_DESIGNS: Record<VideoKind, typeof DEFAULT_OVERLAY_DESIGN> = {
  spectrum: { ...DEFAULT_OVERLAY_DESIGN },
  chords: { ...DEFAULT_OVERLAY_DESIGN },
  key: { ...DEFAULT_OVERLAY_DESIGN },
  note_rate: { ...DEFAULT_OVERLAY_DESIGN },
  heatmap: { ...DEFAULT_OVERLAY_DESIGN },
  harmony: { ...DEFAULT_OVERLAY_DESIGN },
  achievements: { ...DEFAULT_OVERLAY_DESIGN },
  boss: { ...DEFAULT_OVERLAY_DESIGN },
  circle: { ...DEFAULT_OVERLAY_DESIGN },
  bingo: { ...DEFAULT_OVERLAY_DESIGN },
  wrapped: { ...DEFAULT_OVERLAY_DESIGN },
};

const DEFAULT_VIDEO_SETTINGS: VideoSettings = {
  format: "prores",
  width: 1920,
  height: 1080,
  fps: 30,
  language: "en",
  designMode: "global",
  globalDesign: { ...DEFAULT_OVERLAY_DESIGN },
  featureDesigns: DEFAULT_FEATURE_DESIGNS,
};

export default function App() {
  const [backend, setBackend] = useState<BackendState>("checking");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [videoSettings, setVideoSettings] = useState<VideoSettings>(DEFAULT_VIDEO_SETTINGS);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("video");
  const [wrappedVisible, setWrappedVisible] = useState(false);
  const wrappedDesign = overlayDesign(videoSettings, "wrapped");

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
      setSidebarTab("video");
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
          <div className="workspace">
            <aside className="sidebar card">
              <div className="sidebar__tabs" role="tablist" aria-label="Workspace tools">
                <button
                  id="tab-video"
                  type="button"
                  role="tab"
                  aria-selected={sidebarTab === "video"}
                  aria-controls="panel-video"
                  className={`sidebar__tab${sidebarTab === "video" ? " sidebar__tab--active" : ""}`}
                  onClick={() => setSidebarTab("video")}
                >
                  Video Export
                </button>
                <button
                  id="tab-chords"
                  type="button"
                  role="tab"
                  aria-selected={sidebarTab === "chords"}
                  aria-controls="panel-chords"
                  className={`sidebar__tab${sidebarTab === "chords" ? " sidebar__tab--active" : ""}`}
                  onClick={() => setSidebarTab("chords")}
                >
                  Chords
                </button>
              </div>
              <div id="panel-video" role="tabpanel" aria-labelledby="tab-video" hidden={sidebarTab !== "video"}>
                <VideoExport file={file} settings={videoSettings} onSettingsChange={setVideoSettings} />
              </div>
              <div id="panel-chords" role="tabpanel" aria-labelledby="tab-chords" hidden={sidebarTab !== "chords"}>
                <div className="chord-summary">
                  <span>Chord changes</span>
                  <strong>{result.chords.length.toLocaleString("en-US")}</strong>
                </div>
                <ChordTable chords={result.chords} />
              </div>
            </aside>
            <section className="preview card">
              <h2>Overlay Preview</h2>
              <OverlayPreview
                result={result}
                settings={videoSettings}
                wrappedVisible={wrappedVisible}
                onWrappedVisibilityChange={setWrappedVisible}
              />
            </section>
          </div>
          {wrappedVisible && (
            <section className="card">
              <h2>Song Wrapped</h2>
              <p className="hint">
                An ending with the numbers from the piece. The cards appear one after another in the video; it is a
                separate clip that can be placed behind the piece in the editor.
              </p>
              <div className="player__screen" style={overlayStyle(wrappedDesign)}>
                <div
                  className="preview-overlay preview-overlay--wrapped"
                  style={{ "--overlay-scale": wrappedDesign.scale } as CSSProperties}
                >
                  <WrappedPreview cards={result.wrapped} color={wrappedDesign.color} language={videoSettings.language} />
                </div>
              </div>
            </section>
          )}
        </>
      )}
    </main>
  );
}
