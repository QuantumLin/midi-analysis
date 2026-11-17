# MIDI Analysis

Eine Desktop-Anwendung, die MIDI-Dateien einliest und daraus musikalische Metriken, Statistiken und Analysen erstellt (z. B. Notenanzahl, Tonart, Tempo, Oktavverteilung, Harmonik).

## Funktionen

MIDI-Datei (`.mid`, `.midi`) auswählen oder per Drag & Drop hochladen. Die Anwendung zeigt dann:

- **Overlay-Vorschau:** Play, Pause und eine Zeitleiste spielen alle Overlays synchron ab:
  - **Noten pro Sekunde:** Live-Wert (Tastenanschläge in der letzten Sekunde), Gesamtzahl bisher und bisheriger Rekord. Bei einem neuen Rekord erscheint „Neuer Rekord: 29 Noten/s“.
  - **Tonart:** Die aktuelle Tonart, z. B. „d-Moll“. Bei einem Tonartwechsel steht 3 s lang „Modulation →“ darüber.
  - **Akkord:** Der aktuelle Akkord, z. B. `C`, `Am7`, `G7`, `Cmaj7`, `Bm7b5` oder Umkehrungen wie `C/E`.
  - **Stufe:** Der aktuelle Akkord als Stufe in der Tonart, z. B. „vi“ oder „V⁷“, darunter die letzten vier Stufen als Kette („I – V – vi – IV“) und die Bezugstonart („in C-Dur“). Erkennt das Programm eine bekannte Akkordfolge, erscheint ihr Name, z. B. „Die Pop-Formel ×2“.
  - **Achievements:** Pop-ups wie in einem Videospiel („Erfolg freigeschaltet: 8-Finger-Akkord“) für besondere Momente.
  - **Abschnitt:** Der aktuelle Teil des Stücks („Teil B“) und ob er neu ist oder wiederkehrt („zum 2. Mal“).
  - **Motiv:** Erscheint, während ein wiederkehrendes Melodie-Motiv gespielt wird: „Motiv A, 5. Mal – kehrt zurück“. In der Vorschau ist das Feld sonst abgedunkelt, im Video ausgeblendet.
  - **Frequenzspektrum:** Ein Analyzer wie in einer DAW (z. B. ReaEQ in Reaper) von 20 Hz bis 20 kHz, logarithmisch, in dB.
  - **Tasten-Heatmap:** Ein leuchtender Balken über alle 88 Tasten, von A0 links bis C8 rechts. Die Farbintensität zeigt, wie oft eine Lage bisher gespielt wurde: von dunkel über die Neonfarbe bis weißglühend. Gerade gedrückte Tasten leuchten als heller Punkt auf. Striche markieren die Cs (C1–C8).
- **Video-Export:** Jedes Overlay lässt sich einzeln als **transparentes Video** exportieren und in DaVinci Resolve frei platzieren, z. B. neben einem Piano-Visualizer.
- **Akkordtabelle:** Jeder Akkord mit Start, Ende, Stufe und Noten.

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
| Neonfarbe | Vorlagen (Cyan, Magenta, Lime, Orange, Violett, Gelb) oder eine eigene Farbe für alle Overlays |
| Sprache | Deutsch oder Englisch für die Texte („d-Moll“ / „D minor“, „Noten/s“ / „notes/s“) |
| Raster | Spektrum mit Raster und Hz/dB-Beschriftung oder nur die Kurve |

- **Vorschau:** Sie zeigt Farbe, Sprache und Raster vorab so, wie die Videos aussehen werden.
- **„Alle erstellen“:** Rendert alle neun Videos nacheinander.
- **Neon-Look:** Die Schrift ist Orbitron. Die Textfelder sind dunkle Glas-Panels mit leuchtendem Rahmen, darin großer Neon-Text mit Glow und eine Beschriftung in Großbuchstaben. Jedes Panel behält im ganzen Video seine Größe, damit nichts springt.
- **Effekte:**
  - **Akkordwechsel:** Das Akkordfeld blitzt kurz auf.
  - **Noten/s:** Ein LED-Pegel zeigt die aktuelle Geschwindigkeit relativ zum Höchstwert des Stücks.
  - **Rekord, Modulation, Akkordfolge, wiederkehrender Teil:** Das Feld leuchtet 2–4 s lang stärker.
  - **Motiv:** Das Feld erscheint nur, während das Motiv erklingt (plus 1 s), und blitzt bei jedem neuen Auftreten auf.
  - **Achievements:** Das Pop-up springt mit einem kurzen Aufblitzen ins Bild, bleibt 3 s stehen und blendet aus. Dazwischen ist das Video leer.
- **Akkord bei Pausen:** Bei kurzen Pausen bleibt der letzte Akkord stehen, nach 2 s Stille verschwindet er.
- **Platzierung:** Alle Overlays liegen mittig im Bild, der Heatmap-Balken ist 90 % so breit wie das Bild. In Resolve lassen sie sich frei verschieben und skalieren.
- **Rendern:** Es läuft im Hintergrund mit Fortschrittsanzeige. Fertige Dateien werden nach 60 Minuten gelöscht.

**Richtwerte** für ein 77-s-Stück in 1080p30 als ProRes:

| Video | Renderzeit | Größe |
| --- | --- | --- |
| Spektrum | ca. 55 s | ca. 0,9 GB |
| Heatmap | ca. 50 s | ca. 0,4 GB |
| Noten/s, Tonart, Akkord, Stufe, Abschnitt | je ca. 50 s | je 0,25–0,4 GB |
| Achievements, Motive | je ca. 45 s | je ca. 0,15 GB |

**In DaVinci Resolve:**
1. Die `.mov`-Datei auf eine Spur über dem Hintergrund legen. Die Transparenz wird automatisch erkannt.
2. Bei einer PNG-Sequenz das ZIP entpacken und den Ordner importieren. Resolve erkennt die Bilder als Sequenz.

### Regeln der Auswertung

- **Tempowechsel:** Sie werden bei der Umrechnung in Sekunden berücksichtigt.
- **Haltepedal (CC 64):** Es verlängert den *Klang* der Noten bis zum Loslassen des Pedals. Das wirkt auf das Spektrum.
- **Akkorde aus gehaltenen Tasten:** Für die Akkorderkennung zählt zuerst, welche Tasten gerade *gedrückt* sind. Sonst würde ein gehaltenes oder nie losgelassenes Pedal alle Harmonien zu einem Cluster verschmelzen. Nur wenn die gedrückten Tasten keinen Akkord ergeben, werden die per Pedal nachklingenden Töne verwendet, z. B. bei einem ins Pedal gespielten Arpeggio.
- **Toleranz:** Bis zu zwei Fremdtöne (Melodie, Durchgangstöne) und eine fehlende Quinte verhindern die Erkennung nicht. Eine exakte Übereinstimmung gewinnt immer, deshalb kann ein Melodieton den Namen ändern, z. B. `C` → `Cadd9`.
- **Schlagzeug (MIDI-Kanal 10):** Es hat keine Tonhöhe und wird nur gezählt.
- **Kurze Abschnitte:** Abschnitte unter 80 ms werden ignoriert.
- **Gebrochene Akkorde:** Arpeggien ohne Pedal werden nicht erkannt.
- **Tonart:** Sie wird nach Krumhansl-Schmuckler bestimmt. Ein 8-s-Fenster vergleicht, wie lange jede Tonstufe klingt, mit den Profilen aller 24 Dur- und Moll-Tonarten. Ein Wechsel wird erst gemeldet, wenn die neue Tonart einige Sekunden klar besser passt, kurze Ausweichungen zählen nicht als Modulation.
- **Gesamt-Tonart:** Das ist die Tonart, in der das Stück am längsten steht. Bei fast gleicher Dauer gewinnt die zuerst erklingende.
- **Schreibweise:** Notennamen und Akkorde werden passend zur Tonart geschrieben, z. B. `B♭` in d-Moll und `A♯` in H-Dur.
- **Stufen:** Sie beziehen sich auf die Tonart in diesem Moment. Großbuchstaben stehen für Dur, Kleinbuchstaben für Moll, ° für vermindert, ø für halbvermindert, + für übermäßig. In Moll wird von natürlich Moll aus gezählt (i, ii°, III, iv, v, VI, VII). Akkorde ohne Terz (Powerchords, sus) bekommen die Schreibweise der leitereigenen Stufe.
- **Akkordfolgen:** Erkannt werden die Pop-Formel I–V–vi–IV, die Doo-Wop-Folge I–vi–IV–V, Pachelbels Kanon, die Royal Road IV–V–iii–vi, die Andalusische Kadenz i–VII–VI–V, die Jazz-Kadenz ii–V–I und Quintfälle ab vier Akkorden. Verglichen werden Grundton-Abstände und Akkordtyp, daher funktioniert das in jeder Tonart. Schleifen wie die Pop-Formel werden auch erkannt, wenn sie mit einem anderen Akkord beginnen (vi–IV–I–V), und jede Wiederholung wird mitgezählt. Kurze Durchgangsakkorde und sus-/Powerchords werden dabei übersprungen.
- **Achievements:** Sie werden allein aus den Noten erkannt:

  | Achievement | Auslöser |
  | --- | --- |
  | n-Finger-Akkord | mindestens 6 gleichzeitig angeschlagene Töne; der erste und jeder neue Rekord |
  | Riesensprung | ein Sprung über mindestens 2 Oktaven, ohne dass dazwischen eine Taste gehalten wird |
  | Blitzlauf | mindestens 10 schnelle Einzeltöne (≤ 0,12 s Abstand) in eine Richtung; der erste und jeder deutlich längere |
  | Triller | mindestens 8 schnelle Wechsel zwischen zwei benachbarten Tönen |
  | Fortissimo! | der erste sehr harte Anschlag (Velocity ≥ 112), nur wenn das Stück nicht durchgehend so laut ist |
  | Ganz unten / Ganz oben | der erste Ton bis E1 bzw. ab C7 |
  | n Oktaven | 5, 6 oder 7 Oktaven Tonumfang bisher |
  | n Noten | 500, 1.000, 2.000 … gespielte Noten |

  Pop-ups überlappen sich nie. Kommt eines, während ein anderes zu sehen ist, wartet es bis zu 4 s und entfällt sonst.
- **Motive (Grundversion):** Als Melodie gilt der höchste Ton jedes Anschlags ab G3, tiefere Töne zählen als Begleitung. Ein Motiv ist eine Folge von mindestens 6 Tönen mit gleichen Intervallen und gleichem Rhythmus (Tondauern im Verhältnis, auf Faktor 2 gerundet), die mindestens dreimal vorkommt. Dadurch wird es auch transponiert und in anderem Tempo erkannt. Es wird so weit verlängert, wie alle Wiederholungen übereinstimmen (bis 16 Töne). Bis zu drei Motive (A, B, C) teilen sich keine Töne. Tonleitern, Triller und Tonwiederholungen zählen nicht als Motiv. Abgewandelte Wiederholungen (andere Verzierung, anderer Rhythmus) werden noch nicht erkannt.
- **Abschnitte (Grundversion):** Alle 0,5 s wird der Klang beschrieben: welche Tonstufen klingen, wie dicht und wie hoch gespielt wird, gemittelt über 3 s. Grenzen liegen dort, wo sich diese Beschreibung vorher und nachher am stärksten unterscheidet (Neuheitskurve nach Foote), mindestens 6 s auseinander. Teile mit ähnlichem Verlauf bekommen denselben Buchstaben. Ob ein Teil Strophe oder Refrain ist, wird noch nicht bestimmt.
- **Noten pro Sekunde:** Jede angeschlagene Taste zählt, ein Vierklang also als vier Noten. Rekorde zählen erst nach den ersten 5 s. Schnell aufeinanderfolgende Rekorde in einem Lauf werden zu einem zusammengefasst.

## Tech-Stack

| Bereich  | Technologie                                     | Begründung                                                                                      |
| -------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Backend  | Python 3.14, FastAPI, Uvicorn, pydantic-settings, mido | Python bietet die besten MIDI-/Musiktheorie-Bibliotheken. FastAPI liefert typisierte APIs und automatische OpenAPI-Doku. |
| Video    | numpy, Pillow, ffmpeg, Schrift Orbitron         | numpy berechnet Spektrum und Frames, Pillow rendert Text und Glow, ffmpeg erzeugt ProRes 4444 und PNG mit Alpha-Kanal. Orbitron (SIL Open Font License) wird mitgeliefert, damit App und Videos überall gleich aussehen. |
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
│   │   │   ├── achievements.py    # Achievements (Pop-ups)
│   │   │   ├── chords.py          # Akkorderkennung
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
│   │   │   ├── assets/            # Orbitron.ttf + Lizenz (OFL)
│   │   │   ├── chord_renderer.py  # Akkord-Overlay
│   │   │   ├── encoder.py         # ffmpeg: ProRes 4444 / PNG-Sequenz
│   │   │   ├── fonts.py           # Orbitron + Ersatzschrift für ♯ ♭ →
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
│   │   │   ├── preview/           # Overlay-Vorschau
│   │   │   │   ├── OverlayPreview.tsx # Wiedergabe aller Overlays
│   │   │   │   ├── OverlayFields.tsx  # Text-Overlays und Achievement-Pop-up
│   │   │   │   ├── SpectrumCanvas.tsx
│   │   │   │   └── HeatBar.tsx        # Heat-Balken
│   │   │   └── VideoExport.tsx    # Export-Einstellungen und Jobs
│   │   ├── assets/fonts/          # Orbitron.ttf + Lizenz (OFL)
│   │   ├── hooks/                 # usePlayback, useElementWidth
│   │   ├── types/analysis.ts      # Typen der API-Antwort
│   │   ├── utils/                 # labels, stats, harmony, form, spectrum, chords, canvas, format
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
| `POST`  | `/api/videos`   | Video-Export starten (`file`, `kind`, `format`, `width`, `height`, `fps`, `color`, `show_grid`, `language`) → Job |
| `GET`   | `/api/videos/{id}` | Status eines Jobs (`status`, `progress`)                          |
| `GET`   | `/api/videos/{id}/download` | Fertiges Video herunterladen                             |

Beispiel:

```bash
curl -F "file=@song.mid" http://localhost:8001/api/analysis
curl -F "file=@song.mid" -F kind=spectrum -F format=prores http://localhost:8001/api/videos
```

Die Analyse-Antwort enthält:
- **Kennzahlen:** `duration_seconds`, `note_count`, `percussion_note_count`
- **`spectrum`:** Vorschau mit 20 fps und 256 Bändern, als Base64-codierte Bytes
- **`chords`:** `start`, `end`, `name`, `root`, `quality`, `bass`, `notes`, `numeral` (Stufe, z. B. `vi`)
- **`keys`:** `overall` und `segments` (`start`, `end`, `key` mit `tonic` und `mode`); jedes Segment nach dem ersten ist eine Modulation
- **`note_rate`:** `values` pro Frame (20 fps), `peak_value`, `peak_time`, `records`
- **`progressions`:** erkannte Akkordfolgen mit `time`, `end`, `id`, `count` und `name` (`de`/`en`)
- **`achievements`:** Pop-ups mit `time`, `end`, `kind`, `title` und `detail` (je `de`/`en`)
- **`motifs`:** `label`, `length` (Töne) und `occurrences` (`start`, `end`, `number`)
- **`sections`:** `start`, `end`, `label` (gleicher Buchstabe = gleicher Teil) und `number`
- **`notes`:** alle Noten als parallele Listen `start`, `end` (Loslassen der Taste), `pitch`

Für `kind` sind `spectrum`, `chords`, `key`, `note_rate`, `heatmap`, `harmony`, `achievements`, `motifs` und `sections` möglich, für `language` `de` oder `en`.

Fehlerhafte oder zu große Dateien werden mit `400` bzw. `413` abgelehnt. Das vollständige Schema steht unter `/docs`.

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
