# MIDI Analytics

Eine Desktop-Anwendung, die MIDI-Dateien einliest und daraus musikalische Metriken, Statistiken und Analysen erstellt (z. B. Notenanzahl, Tonart, Tempo, Oktavverteilung, Harmonik).

> **Status:** Technisches Grundgerüst. Es sind noch keine MIDI-Funktionen implementiert. Die Oberfläche zeigt nur den Projektnamen und den Verbindungsstatus zum Backend.

## Tech-Stack

| Bereich  | Technologie                                     | Begründung                                                                                      |
| -------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Backend  | Python 3.14, FastAPI, Uvicorn, pydantic-settings | Python bietet die besten MIDI-/Musiktheorie-Bibliotheken (`mido`, `music21`, `pretty_midi`). FastAPI liefert typisierte APIs und automatische OpenAPI-Doku. |
| Frontend | React 19, TypeScript, Vite 8                    | Moderne, schlanke UI mit sehr schnellem Hot Reload. Lässt sich später unverändert in eine Desktop-Shell einbetten. |
| Docker   | Docker Compose                                  | Ein Befehl startet die gesamte Entwicklungsumgebung.                                            |

### Desktop-Anwendung und Docker

Docker stellt keine native Desktop-Oberfläche bereit. GUI-Fenster aus Containern (Electron oder Tauri) bräuchten X11- oder WSLg-Workarounds und sind dafür nicht sinnvoll. Deshalb gilt:

- **Jetzt (Entwicklung):** Docker betreibt Backend und Frontend-Dev-Server. Die UI wird im Browser unter `http://localhost:5173` genutzt.
- **Später (Desktop):** Eine **Tauri**-Shell auf dem Host lädt dasselbe Frontend und startet das Python-Backend als Sidecar-Prozess, z. B. als PyInstaller-Binary. Tauri ist deutlich schlanker als Electron. Frontend und Backend müssen dafür nicht umgebaut werden, weil sie nur über HTTP (`/api/...`) kommunizieren.

## Architektur

```
┌──────────────────────┐   HTTP /api/*   ┌──────────────────────┐
│ Frontend (React)     │ ──────────────▶ │ Backend (FastAPI)    │
│ Vite Dev Server :5173│   (Vite-Proxy)  │ Uvicorn :8000        │
│ – nur Darstellung    │                 │ – MIDI-Verarbeitung  │
└──────────────────────┘                 │ – Analysemodule      │
                                         └──────────────────────┘
```

- **Frontend:** Ist nur für die Darstellung zuständig. Alle Backend-Aufrufe laufen über `src/api/client.ts` mit relativen `/api`-Pfaden. Der Vite-Dev-Server leitet sie an das Backend weiter. Dadurch ist keine Backend-URL fest im Code hinterlegt und kein CORS nötig.
- **Backend:** Enthält die gesamte Fachlogik. Die Routen liegen in `app/api/routes/` (ein Modul pro Ressource), und `app/api/router.py` bündelt sie. Künftige Analysen kommen als eigene Module nach `app/analysis/`, z. B. `notes.py`, `tempo.py`, `harmony.py`.
- **Konfiguration:** Läuft über Umgebungsvariablen (`.env`). Das Backend liest sie typisiert über `app/config.py` ein.

## Projektstruktur

```
MidiAnalysis/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   └── health.py      # GET /api/health
│   │   │   └── router.py          # bündelt alle Routen
│   │   ├── analysis/              # künftige MIDI-Analysemodule
│   │   ├── config.py              # Settings aus Umgebungsvariablen
│   │   └── main.py                # FastAPI-Einstiegspunkt
│   ├── Dockerfile
│   ├── .dockerignore
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts          # HTTP-Client für das Backend
│   │   ├── App.tsx                # Startseite
│   │   ├── App.css
│   │   └── main.tsx               # React-Einstiegspunkt
│   ├── index.html
│   ├── vite.config.ts             # Dev-Server, Proxy, Polling
│   ├── tsconfig.json
│   ├── package.json
│   ├── package-lock.json
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .dockerignore
└── README.md
```

## Voraussetzungen

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (inkl. Docker Compose v2)
- Optional für lokale Entwicklung ohne Docker: Python ≥ 3.12 und Node.js ≥ 20.19

## Start mit Docker

```bash
# optional: Standardwerte überschreiben
cp .env.example .env

docker compose up --build
```

Danach erreichbar:

| Dienst            | URL                                  |
| ----------------- | ------------------------------------ |
| Frontend (UI)     | http://localhost:5173                |
| Backend Health    | http://localhost:8001/api/health     |
| API-Doku (Swagger)| http://localhost:8001/docs           |

Die Startseite zeigt **„Backend: online"**, sobald die Kommunikation zwischen Frontend und Backend funktioniert.

### Hot Reload

Die Quellordner sind per Volume in die Container eingebunden:

- Änderungen in `backend/app/` lösen einen Neustart von Uvicorn aus (`--reload`).
- Änderungen in `frontend/` werden über Vite HMR direkt im Browser übernommen.

Unter Windows und macOS lösen Bind-Mounts keine Dateisystem-Events im Container aus. Deshalb ist Polling aktiviert (`WATCHFILES_FORCE_POLLING`, `VITE_USE_POLLING`). Ein Image-Neubau ist nur nötig, wenn sich Abhängigkeiten ändern (`requirements.txt`, `package.json`).

## Konfiguration

| Variable              | Standard      | Beschreibung                           |
| --------------------- | ------------- | -------------------------------------- |
| `BACKEND_PORT`        | `8001`        | Host-Port des Backends (im Container: 8000) |
| `FRONTEND_PORT`       | `5173`        | Host-Port des Frontends                |
| `BACKEND_ENVIRONMENT` | `development` | Umgebungsname des Backends             |

Alle Variablen sind optional. Docker Compose funktioniert auch ohne `.env`.

## Docker-Befehle

```bash
docker compose up --build        # bauen und starten (Vordergrund)
docker compose up --build -d     # bauen und im Hintergrund starten
docker compose ps                # Status der Container
docker compose logs -f           # Logs aller Services verfolgen
docker compose logs -f backend   # Logs eines Service
docker compose restart backend   # einen Service neu starten
docker compose exec backend sh   # Shell im Backend-Container
docker compose down              # stoppen und Container entfernen
docker compose build --no-cache  # Images komplett neu bauen
```

Nach Änderungen an `package.json` muss das Frontend-Image neu gebaut werden. Dabei sollte das anonyme `node_modules`-Volume erneuert werden:

```bash
docker compose up --build -V frontend
```

## Lokale Entwicklung ohne Docker (optional)

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (zweites Terminal)
cd frontend
npm install
npm run dev                     # Proxy zeigt standardmäßig auf http://localhost:8000
```
