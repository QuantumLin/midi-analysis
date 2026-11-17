// Thin wrapper around the backend HTTP API. All requests go to relative /api paths;
// the dev server (or later the desktop shell) is responsible for routing them to the backend.

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`/api${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export const fetchHealth = () => getJson<HealthResponse>("/health");
