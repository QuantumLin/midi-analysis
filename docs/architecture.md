# Architektur

## Tech-Stack

| Bereich | Technologie | Begründung |
| --- | --- | --- |
| Backend | Python 3.14, FastAPI, Uvicorn, pydantic-settings, mido | Python bietet die besten MIDI-/Musiktheorie-Bibliotheken. FastAPI liefert typisierte APIs und automatische OpenAPI-Doku. |
| Video | numpy, Pillow, ffmpeg, sechs Schriften | numpy berechnet Spektrum und Frames, Pillow rendert Text und Glow, ffmpeg erzeugt ProRes 4444 und PNG mit Alpha-Kanal. Die wählbaren Schriften (Orbitron, Montserrat, Bebas Neue, Playfair Display, Press Start 2P, Caveat; alle SIL Open Font License) werden mitgeliefert, damit App und Videos überall gleich aussehen. |
| Frontend | React 19, TypeScript, Vite 8 | Moderne, schlanke UI mit sehr schnellem Hot Reload. Lässt sich später unverändert in eine Desktop-Shell einbetten. |
| Docker | Docker Compose | Ein Befehl startet die gesamte Entwicklungsumgebung. |

## Aufbau

```
┌──────────────────────┐   HTTP /api/*   ┌──────────────────────┐
│ Frontend (React)     │ ──────────────▶ │ Backend (FastAPI)    │
│ Vite Dev Server :5173│   (Vite-Proxy)  │ Uvicorn :8000        │
│ – nur Darstellung    │                 │ – MIDI-Verarbeitung  │
└──────────────────────┘                 │ – Analysemodule      │
                                         │ – Video-Rendering    │
                                         └──────────────────────┘
```

- **Frontend:** Ist nur für die Darstellung zuständig. Alle Backend-Aufrufe laufen über `src/api/client.ts` mit relativen `/api`-Pfaden. Der Vite-Dev-Server leitet sie an das Backend weiter. Dadurch ist keine Backend-URL fest im Code hinterlegt und kein CORS nötig.
- **Backend:** Enthält die gesamte Fachlogik in klar getrennten Schichten:
  - `app/midi/` liest die MIDI-Bytes ein und erzeugt daraus eine Liste von Noten (Start, Ende, Tonhöhe, Velocity in Sekunden).
  - `app/analysis/` enthält je ein Modul pro Analyse. Jedes arbeitet nur auf dieser Notenliste, ohne HTTP- oder Dateibezug. Die Verfahren sind in [Analyse](analysis.md) beschrieben.
  - `app/services/analysis_service.py` führt alle Analysen aus und baut daraus die API-Antwort.
  - `app/video/` rendert die Overlay-Videos. Die Renderer zeichnen einzelne Frames, `encoder.py` übergibt sie an ffmpeg, `jobs.py` führt das Rendern als Hintergrundjob aus.
  - `app/api/` enthält die HTTP-Routen und die Antwortmodelle (`schemas.py`), also den Vertrag mit dem Frontend (siehe [API](api.md)).
- **Konfiguration:** Läuft über Umgebungsvariablen (`.env`). Das Backend liest sie typisiert über `app/config.py` ein (siehe [Entwicklung](development.md#konfiguration)).
- **Vorschau und Video gleich:** Die Texte der Overlays erzeugt das Backend (`app/video/labels.py`). Das Frontend spiegelt Regeln und Aussehen der Overlays in `components/preview/` und `utils/`, damit die Vorschau den exportierten Videos entspricht.

### Neue Analyse hinzufügen

1. Modul in `backend/app/analysis/` anlegen.
2. Feld in `backend/app/api/schemas.py` ergänzen.
3. Analyse in `backend/app/services/analysis_service.py` aufrufen.
4. Typ in `frontend/src/types/analysis.ts` spiegeln.
5. Für ein Video: Renderer in `backend/app/video/` (Basis `neon_overlay.py`) anlegen und in `render.py` (`_FRAME_SOURCES`) sowie `options.py` als neue Art eintragen. Ein Video, das nicht so lang ist wie das Stück, gibt einen `FrameStream` mit eigener Bildanzahl zurück (siehe Song Wrapped).

**Erweiterungspunkte ohne neues Modul:** Schriften und Leuchtstufen (`FONTS`, `GLOW_FACTORS` in `style.py`, gespiegelt in `frontend/src/utils/style.ts`), Boss-Faktoren (`FACTORS`), Bingo-Felder (`FIELDS`, `CARD`), Wrapped-Karten (`CARDS`), Akkordfolgen (`PROGRESSIONS`) und Achievements sind Listen, die sich um einen Eintrag erweitern lassen (siehe [Analyse](analysis.md)).

## Desktop-Anwendung und Docker

Docker stellt keine native Desktop-Oberfläche bereit. GUI-Fenster aus Containern (Electron oder Tauri) bräuchten X11- oder WSLg-Workarounds und sind dafür nicht sinnvoll. Deshalb gilt:

- **Jetzt (Entwicklung):** Docker betreibt Backend und Frontend-Dev-Server. Die UI wird im Browser unter `http://localhost:5173` genutzt.
- **Später (Desktop):** Eine **Tauri**-Shell auf dem Host lädt dasselbe Frontend und startet das Python-Backend als Sidecar-Prozess, z. B. als PyInstaller-Binary. Tauri ist deutlich schlanker als Electron. Frontend und Backend müssen dafür nicht umgebaut werden, weil sie nur über HTTP (`/api/...`) kommunizieren.

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
│   │   │   ├── achievements.py    # Achievements (Pop-ups)
│   │   │   ├── bingo.py           # Tastatur-Bingo
│   │   │   ├── boss_fight.py      # Schwierigkeit und Endgegner
│   │   │   ├── chords.py          # Akkorderkennung
│   │   │   ├── circle_of_fifths.py # Akkorde im Quintenzirkel
│   │   │   ├── harmony.py         # Stufen und bekannte Akkordfolgen
│   │   │   ├── key.py             # Tonart und Modulationen
│   │   │   ├── keyboard_activity.py # Anschläge pro Taste (Heatmap)
│   │   │   ├── motifs.py          # wiederkehrende Melodie-Motive
│   │   │   ├── note_rate.py       # Noten pro Sekunde, Rekorde
│   │   │   ├── sections.py        # Abschnitte (A B A …)
│   │   │   └── spectrum.py        # synthetisches Frequenzspektrum
│   │   ├── midi/
│   │   │   ├── models.py          # Note, MidiData
│   │   │   ├── parser.py          # MIDI-Bytes -> Noten in Sekunden
│   │   │   └── pitch.py           # Notennamen, Frequenzen
│   │   ├── services/
│   │   │   └── analysis_service.py # führt alle Analysen aus
│   │   ├── video/
│   │   │   ├── achievement_renderer.py # Achievement-Pop-ups
│   │   │   ├── assets/fonts/      # die sechs Schriften, je mit Lizenz (OFL)
│   │   │   ├── bingo_renderer.py  # Bingo-Karte
│   │   │   ├── boss_renderer.py   # Endgegner mit HP-Balken
│   │   │   ├── chord_renderer.py  # Akkord-Overlay
│   │   │   ├── circle_renderer.py # Quintenzirkel
│   │   │   ├── encoder.py         # ffmpeg: ProRes 4444 / PNG-Sequenz
│   │   │   ├── fonts.py           # gewählte Schrift + Ersatzschrift für ♯ ♭ →
│   │   │   ├── harmony_renderer.py # Stufen-Overlay
│   │   │   ├── heatmap_renderer.py # Heat-Balken (numpy)
│   │   │   ├── jobs.py            # Hintergrundjobs
│   │   │   ├── key_renderer.py    # Tonart-Overlay
│   │   │   ├── labels.py          # Texte Deutsch/Englisch, ♯/♭
│   │   │   ├── motif_renderer.py  # Motiv-Overlay
│   │   │   ├── neon.py            # Neon-Toolkit: Glow, Glas-Panel, Text
│   │   │   ├── neon_overlay.py    # gemeinsame Basis der Text-Overlays
│   │   │   ├── note_rate_renderer.py # Noten/s-Overlay mit LED-Pegel
│   │   │   ├── options.py         # Export-Einstellungen
│   │   │   ├── render.py          # rendert ein komplettes Video
│   │   │   ├── section_renderer.py # Abschnitt-Overlay
│   │   │   ├── spectrum_renderer.py # Spektrum-Frame (numpy)
│   │   │   ├── style.py           # wählbares Design: Schriften, Leuchtstärke
│   │   │   ├── wrapped.py         # Song-Wrapped-Karten
│   │   │   └── wrapped_renderer.py # Song-Wrapped-Abspann
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
│   │   │   ├── Logo.tsx           # Logo (Icon + Schriftzug)
│   │   │   ├── preview/           # Overlay-Vorschau
│   │   │   │   ├── OverlayPreview.tsx # Wiedergabe aller Overlays
│   │   │   │   ├── OverlayFields.tsx  # Text-Overlays und Achievement-Pop-up
│   │   │   │   ├── GameFields.tsx     # Endgegner, Quintenzirkel, Bingo, Song Wrapped
│   │   │   │   ├── SpectrumCanvas.tsx
│   │   │   │   └── HeatBar.tsx        # Heat-Balken
│   │   │   └── VideoExport.tsx    # Export-Einstellungen und Jobs
│   │   ├── assets/fonts/          # dieselben sechs Schriften für die Vorschau
│   │   ├── hooks/                 # usePlayback, useElementWidth
│   │   ├── types/analysis.ts      # Typen der API-Antwort
│   │   ├── utils/                 # labels, stats, harmony, form, games, spectrum, chords, canvas, format
│   │   ├── App.tsx                # Seitenaufbau und Zustand
│   │   ├── App.css
│   │   └── main.tsx               # React-Einstiegspunkt
│   ├── public/logo.svg        # Logo-Icon, auch Favicon
│   ├── index.html
│   ├── vite.config.ts             # Dev-Server, Proxy, Polling
│   ├── tsconfig.json
│   ├── package.json
│   ├── package-lock.json
│   ├── Dockerfile
│   └── .dockerignore
├── docs/                          # Dokumentation (siehe docs/README.md)
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .gitattributes
├── .dockerignore
└── README.md
```
