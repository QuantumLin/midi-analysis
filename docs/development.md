# Entwicklung

## Voraussetzungen

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (inkl. Docker Compose v2)
- Optional für lokale Entwicklung ohne Docker: Python ≥ 3.12 und Node.js ≥ 20.19

## Start mit Docker

```bash
# optional: Standardwerte überschreiben
cp .env.example .env

docker compose up --build
```

| Dienst | URL |
| --- | --- |
| Frontend (UI) | http://localhost:5173 |
| Backend Health | http://localhost:8001/api/health |
| API-Doku (Swagger) | http://localhost:8001/docs |

Die Startseite zeigt **„Backend: online“**, sobald die Kommunikation zwischen Frontend und Backend funktioniert.

## Konfiguration

| Variable | Standard | Beschreibung |
| --- | --- | --- |
| `BACKEND_PORT` | `8001` | Host-Port des Backends (im Container: 8000) |
| `FRONTEND_PORT` | `5173` | Host-Port des Frontends |
| `BACKEND_ENVIRONMENT` | `development` | Umgebungsname des Backends |
| `BACKEND_MAX_UPLOAD_MB` | `10` | Maximale Größe einer MIDI-Datei in MB |
| `BACKEND_VIDEO_DIR` | System-Temp | Ablage der gerenderten Videos |
| `BACKEND_VIDEO_MAX_AGE_MINUTES` | `60` | Danach werden fertige Videos gelöscht |

Alle Variablen sind optional. Docker Compose funktioniert auch ohne `.env`.

## Tests

```bash
docker compose exec backend python -m pytest            # Backend-Tests
docker compose exec frontend npm run build              # TypeScript-Prüfung + Build
```

Die Backend-Tests erzeugen ihre MIDI-Dateien selbst (`tests/midi_factory.py`). Deshalb liegen keine Binärdateien im Repository.

## Hot Reload

Die Quellordner sind per Volume in die Container eingebunden:

- Änderungen in `backend/app/` lösen einen Neustart von Uvicorn aus (`--reload`).
- Änderungen in `frontend/` werden über Vite HMR direkt im Browser übernommen.

Unter Windows und macOS lösen Bind-Mounts keine Dateisystem-Events im Container aus. Deshalb ist Polling aktiviert (`WATCHFILES_FORCE_POLLING`, `VITE_USE_POLLING`). Ein Image-Neubau ist nur nötig, wenn sich Abhängigkeiten ändern (`requirements.txt`, `package.json`).

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

Nach Änderungen an `requirements*.txt` muss das Backend-Image neu gebaut werden (`docker compose up --build -d backend`). Nach Änderungen an `package.json` muss das Frontend-Image neu gebaut werden. Dabei sollte das anonyme `node_modules`-Volume erneuert werden:

```bash
docker compose up --build -V frontend
```

## Lokale Entwicklung ohne Docker (optional)

Auch bei der Entwicklung mit Docker lohnt sich einmal `npm install` im Ordner `frontend/`. Sonst findet der Editor (z. B. VS Code) die TypeScript-Typen nicht, weil die Pakete nur im Container liegen. Mit Docker kommt sich das nicht in die Quere, der Container nutzt seine eigenen Pakete.

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows; macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest
uvicorn app.main:app --reload --port 8000

# Frontend (zweites Terminal)
cd frontend
npm install
npm run dev                     # Proxy zeigt standardmäßig auf http://localhost:8000
```
