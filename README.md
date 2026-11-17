# MIDI Analysis

Eine Desktop-Anwendung, die MIDI-Dateien einliest und daraus musikalische Metriken, Statistiken und Analysen erstellt (z. B. Notenanzahl, Tonart, Tempo, Oktavverteilung, Harmonik).

## Funktionen

MIDI-Datei (`.mid`, `.midi`) auswählen oder per Drag & Drop hochladen. Die Anwendung zeigt dann:

- **Frequenzspektrum:** Ein Analyzer wie in einer DAW (z. B. ReaEQ in Reaper) über das gesamte Spektrum von 20 Hz bis 20 kHz, logarithmisch, in dB. Play, Pause und eine Zeitleiste spielen das Spektrum über die Dauer des Stücks ab.
- **Akkord-Textfeld:** Zeigt während der Wiedergabe den aktuellen Akkord, z. B. `C`, `Am7`, `G7`, `Cmaj7`, `Bm7b5` oder Umkehrungen wie `C/E`.
- **Video-Export:** Beides lässt sich als **transparentes Video** exportieren, um es in DaVinci Resolve über ein Video zu legen, z. B. neben einen Piano-Visualizer.
- **Velocity-Verlauf und Akkordwechsel:** Diagramm der mittleren Velocity über die Zeit mit Akkordspur. Werte erscheinen beim Überfahren mit der Maus oder per Pfeiltasten.
- **Akkordtabelle:** Jeder Akkord mit Start, Ende und Noten.

### Spektrum

MIDI enthält keinen Klang, deshalb wird das Spektrum aus den Noten berechnet:

- **Klangmodell:** Jede Note erzeugt ihren Grundton und bis zu 32 Obertöne. Der Anschlag ist sofort da, danach klingt die Note exponentiell aus, nach dem Loslassen folgt ein kurzes Release.
- **Tonhöhe und Lautstärke:** Tiefe Töne klingen länger nach, laute Noten klingen heller.
- **Anschlaggeräusch:** Jeder Anschlag erzeugt ein kurzes, breitbandiges Hammergeräusch.
- **Analyzer-Verhalten:** Der Pegel steigt sofort und fällt um höchstens 36 dB pro Sekunde, wie bei einem DAW-Analyzer.
- **Pegel:** Er ist relativ. Der lauteste Moment des Stücks liegt bei −3 dB.

### Video-Export

| Einstellung | Optionen |
| --- | --- |
| Format | **ProRes 4444 `.mov`** mit Alpha-Kanal (Standard für Resolve) oder **PNG-Sequenz** als `.zip` |
| Auflösung | 1280×720 bis 3840×2160 |
| Bildrate | 24, 25, 30, 50, 60 fps |
| Farbe | Kurve bzw. Akkordtext |
| Raster | Frequenz-Video mit Raster und Hz/dB-Beschriftung oder nur die Kurve |

- **Vorschau:** Der Player in der App zeigt Farbe und Raster vorab so, wie das Video aussehen wird.
- **Akkord-Video:** Es zeigt den Akkordnamen mittig in einem abgerundeten, halbtransparenten Kasten. Der Kasten hat für das ganze Video dieselbe Größe. Bei kurzen Pausen bleibt der letzte Akkord stehen, nach 2 s Stille verschwindet er.
- **Rendern:** Es läuft im Hintergrund mit Fortschrittsanzeige. Fertige Dateien werden nach 60 Minuten gelöscht.
- **Richtwerte:** Für ein 77-s-Stück in 1080p30 dauert das Rendern etwa 55 s. Das Frequenz-Video ist ca. 0,9 GB groß, das Akkord-Video ca. 0,12 GB.

**In DaVinci Resolve:**
1. Die `.mov`-Datei auf eine Spur über dem Hintergrund legen. Die Transparenz wird automatisch erkannt.
2. Bei einer PNG-Sequenz das ZIP entpacken und den Ordner importieren. Resolve erkennt die Bilder als Sequenz.

### Regeln der Auswertung

- **Tempowechsel:** Sie werden bei der Umrechnung in Sekunden berücksichtigt.
- **Haltepedal (CC 64):** Es verlängert den *Klang* der Noten bis zum Loslassen des Pedals. Das wirkt auf Spektrum und Velocity.
- **Akkorde aus gehaltenen Tasten:** Für die Akkorderkennung zählt zuerst, welche Tasten gerade *gedrückt* sind. Sonst würde ein gehaltenes oder nie losgelassenes Pedal alle Harmonien zu einem Cluster verschmelzen. Nur wenn die gedrückten Tasten keinen Akkord ergeben, werden die per Pedal nachklingenden Töne verwendet, z. B. bei einem ins Pedal gespielten Arpeggio.
- **Toleranz:** Bis zu zwei Fremdtöne (Melodie, Durchgangstöne) und eine fehlende Quinte verhindern die Erkennung nicht. Eine exakte Übereinstimmung gewinnt immer, deshalb kann ein Melodieton den Namen ändern, z. B. `C` → `Cadd9`.
- **Schlagzeug (MIDI-Kanal 10):** Es hat keine Tonhöhe und wird nur gezählt.
- **Kurze Abschnitte:** Abschnitte unter 80 ms werden ignoriert.
- **Gebrochene Akkorde:** Arpeggien ohne Pedal werden nicht erkannt.
- **Notennamen:** Es werden Kreuz-Vorzeichen verwendet (`A#` statt `B♭`).

## Tech-Stack

| Bereich  | Technologie                                     | Begründung                                                                                      |
| -------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Backend  | Python 3.14, FastAPI, Uvicorn, pydantic-settings, mido | Python bietet die besten MIDI-/Musiktheorie-Bibliotheken. FastAPI liefert typisierte APIs und automatische OpenAPI-Doku. |
| Video    | numpy, Pillow, ffmpeg                           | numpy berechnet Spektrum und Frames mit Kantenglättung, Pillow rendert Text, ffmpeg erzeugt ProRes 4444 und PNG mit Alpha-Kanal. |
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
- **Backend:** Enthält die gesamte Fachlogik in klar getrennten Schichten:
  - `app/midi/` liest die MIDI-Bytes ein und erzeugt daraus eine Liste von Noten (Start, Ende, Tonhöhe, Velocity in Sekunden).
  - `app/analysis/` enthält je ein Modul pro Analyse. Jedes arbeitet nur auf dieser Notenliste, ohne HTTP- oder Dateibezug.
  - `app/services/analysis_service.py` führt alle Analysen aus und baut daraus die API-Antwort.
  - `app/video/` rendert die Overlay-Videos. Die Renderer zeichnen einzelne Frames, `encoder.py` übergibt sie an ffmpeg, `jobs.py` führt das Rendern als Hintergrundjob aus.
  - `app/api/` enthält die HTTP-Routen und die Antwortmodelle (`schemas.py`), also den Vertrag mit dem Frontend.

  **Neue Analyse hinzufügen:**
  1. Modul in `app/analysis/` anlegen.
  2. Feld in `schemas.py` ergänzen.
  3. Analyse im Service aufrufen.
  4. Typ in `frontend/src/types/analysis.ts` spiegeln.
- **Konfiguration:** Läuft über Umgebungsvariablen (`.env`). Das Backend liest sie typisiert über `app/config.py` ein.

## Projektstruktur

```
MidiAnalysis/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── analysis.py    # POST /api/analysis
│   │   │   │   ├── health.py      # GET /api/health
│   │   │   │   └── videos.py      # Video-Export (Jobs, Download)
│   │   │   ├── router.py          # bündelt alle Routen
│   │   │   ├── schemas.py         # Antwortmodelle (API-Vertrag)
│   │   │   └── uploads.py         # Prüfung hochgeladener MIDI-Dateien
│   │   ├── analysis/
│   │   │   ├── chords.py          # Akkorderkennung
│   │   │   ├── spectrum.py        # synthetisches Frequenzspektrum
│   │   │   └── timeline.py        # Velocity-Verlauf
│   │   ├── midi/
│   │   │   ├── models.py          # Note, MidiData
│   │   │   ├── parser.py          # MIDI-Bytes -> Noten in Sekunden
│   │   │   └── pitch.py           # Notennamen, Frequenzen
│   │   ├── services/
│   │   │   └── analysis_service.py # führt alle Analysen aus
│   │   ├── video/
│   │   │   ├── chord_renderer.py  # Akkord-Textfeld (Pillow)
│   │   │   ├── encoder.py         # ffmpeg: ProRes 4444 / PNG-Sequenz
│   │   │   ├── fonts.py           # Schriftsuche
│   │   │   ├── jobs.py            # Hintergrundjobs
│   │   │   ├── options.py         # Export-Einstellungen
│   │   │   ├── render.py          # rendert ein komplettes Video
│   │   │   └── spectrum_renderer.py # Spektrum-Frame (numpy)
│   │   ├── config.py              # Settings aus Umgebungsvariablen
│   │   └── main.py                # FastAPI-Einstiegspunkt
│   ├── tests/                     # pytest (erzeugt Test-MIDIs selbst)
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── requirements-dev.txt       # + pytest, httpx2
├── frontend/
│   ├── src/
│   │   ├── api/client.ts          # HTTP-Client für das Backend
│   │   ├── components/
│   │   │   ├── AnalysisSummary.tsx # Kennzahlen
│   │   │   ├── ChordTable.tsx     # Akkordtabelle
│   │   │   ├── FileUpload.tsx     # Dateiauswahl / Drag & Drop
│   │   │   ├── SpectrumPlayer.tsx # Spektrum-Player + Akkordfeld
│   │   │   ├── TimelineChart.tsx  # Velocity und Akkordspur
│   │   │   └── VideoExport.tsx    # Export-Einstellungen und Jobs
│   │   ├── hooks/useElementWidth.ts
│   │   ├── types/analysis.ts      # Typen der API-Antwort
│   │   ├── utils/                 # chords, format, spectrum
│   │   ├── App.tsx                # Seitenaufbau und Zustand
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

## API

| Methode | Pfad            | Beschreibung                                                         |
| ------- | --------------- | -------------------------------------------------------------------- |
| `GET`   | `/api/health`   | Health-Check                                                         |
| `POST`  | `/api/analysis` | MIDI-Datei analysieren (`multipart/form-data`, Feld `file`)          |
| `POST`  | `/api/videos`   | Video-Export starten (`file`, `kind`, `format`, `width`, `height`, `fps`, `color`, `show_grid`) → Job |
| `GET`   | `/api/videos/{id}` | Status eines Jobs (`status`, `progress`)                          |
| `GET`   | `/api/videos/{id}/download` | Fertiges Video herunterladen                             |

Beispiel:

```bash
curl -F "file=@song.mid" http://localhost:8001/api/analysis
curl -F "file=@song.mid" -F kind=spectrum -F format=prores http://localhost:8001/api/videos
```

Die Analyse-Antwort enthält:
- **Kennzahlen:** `duration_seconds`, `note_count`, `percussion_note_count`
- **`timeline`:** `points` mit `time`, `velocity`, `active_notes`
- **`spectrum`:** Vorschau mit 20 fps und 256 Bändern, als Base64-codierte Bytes
- **`chords`:** `start`, `end`, `name`, `root`, `quality`, `bass`, `notes` Fehlerhafte oder zu große Dateien werden mit `400` bzw. `413` abgelehnt. Das vollständige Schema steht unter `/docs`.

## Tests

```bash
docker compose exec backend python -m pytest            # Backend-Tests
docker compose exec frontend npm run build              # TypeScript-Prüfung + Build
```

Die Backend-Tests erzeugen ihre MIDI-Dateien selbst (`tests/midi_factory.py`). Deshalb liegen keine Binärdateien im Repository.

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
| `BACKEND_MAX_UPLOAD_MB` | `10`        | Maximale Größe einer MIDI-Datei in MB  |
| `BACKEND_VIDEO_DIR`   | System-Temp   | Ablage der gerenderten Videos          |
| `BACKEND_VIDEO_MAX_AGE_MINUTES` | `60` | Danach werden fertige Videos gelöscht |

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

Nach Änderungen an `requirements*.txt` muss das Backend-Image neu gebaut werden (`docker compose up --build -d backend`). Nach Änderungen an `package.json` muss das Frontend-Image neu gebaut werden. Dabei sollte das anonyme `node_modules`-Volume erneuert werden:

```bash
docker compose up --build -V frontend
```

## Lokale Entwicklung ohne Docker (optional)

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
