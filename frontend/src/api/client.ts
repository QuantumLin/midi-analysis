// Thin wrapper around the backend HTTP API. All requests go to relative /api paths;
// the dev server (or later the desktop shell) is responsible for routing them to the backend.

import type { AnalysisResult, VideoJob, VideoKind, VideoSettings } from "../types/analysis";

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json() as Promise<T>;
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // Not JSON - fall through to the generic message.
  }
  return `Request failed: ${response.status} ${response.statusText}`;
}

export const fetchHealth = () => request<HealthResponse>("/health");

export function analyzeMidi(file: File): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("file", file);
  return request<AnalysisResult>("/analysis", { method: "POST", body: form });
}

export function createVideoJob(file: File, kind: VideoKind, settings: VideoSettings): Promise<VideoJob> {
  const form = new FormData();
  form.append("file", file);
  form.append("kind", kind);
  form.append("format", settings.format);
  form.append("width", String(settings.width));
  form.append("height", String(settings.height));
  form.append("fps", String(settings.fps));
  form.append("color", settings.color);
  form.append("show_grid", String(settings.showGrid));
  form.append("show_frame", String(settings.showFrame));
  form.append("font", settings.font);
  form.append("glow", settings.glow);
  return request<VideoJob>("/videos", { method: "POST", body: form });
}

export const fetchVideoJob = (id: string) => request<VideoJob>(`/videos/${id}`);

export const videoDownloadUrl = (id: string) => `/api/videos/${id}/download`;
