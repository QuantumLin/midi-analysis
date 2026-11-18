<p align="center"><img src="frontend/public/logo.svg" alt="" width="96" height="96"></p>

<h1 align="center">MIDI Analysis</h1>

Eine Anwendung, die MIDI-Dateien analysiert und die Ergebnisse als transparente Neon-Overlays für Piano-Visualizer-Videos exportiert, z. B. für den Schnitt in DaVinci Resolve.

## Funktionen

- **Live-Statistiken:** Noten pro Sekunde mit Rekorden, Tonart mit Modulationen, Akkorde und ihre Stufen
- **Musikalische Struktur:** bekannte Akkordfolgen („Die Pop-Formel ×2“), wiederkehrende Motive, Abschnitte (Teil A, B, …)
- **Achievements:** Pop-ups wie in einem Videospiel, z. B. „8-Finger-Akkord“ oder „Riesensprung“
- **Spiel-Elemente:** die schwerste Stelle als Endgegner mit HP-Balken, Tastatur-Bingo, ein leuchtender Quintenzirkel
- **Song Wrapped:** ein Abspann mit den Zahlen des Stücks
- **Visualisierungen:** Frequenzspektrum wie in einer DAW, Tasten-Heatmap über alle 88 Tasten
- **Video-Export:** Jedes Overlay als eigenes Video mit Alpha-Kanal (ProRes 4444 oder PNG-Sequenz), in eigener Neonfarbe, auf Deutsch oder Englisch
- **Vorschau:** Alle Overlays laufen synchron im Browser, so wie sie im Video aussehen werden

Ausführlich: [Funktionen](docs/features.md) · [Video-Export](docs/video-export.md)

## Schnellstart

Voraussetzung ist [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
docker compose up --build
```

Danach die Anwendung unter http://localhost:5173 öffnen und eine MIDI-Datei hineinziehen. Die API-Doku liegt unter http://localhost:8001/docs.

## Dokumentation

| Seite | Inhalt |
| --- | --- |
| [Funktionen](docs/features.md) | Alle Overlays, Vorschau, Akkordtabelle |
| [Video-Export](docs/video-export.md) | Einstellungen, Neon-Look, Renderzeiten, DaVinci Resolve |
| [Analyse](docs/analysis.md) | Wie Akkorde, Tonart, Stufen, Achievements, Motive, Abschnitte und Spektrum berechnet werden |
| [API](docs/api.md) | Endpunkte und Antwortfelder |
| [Architektur](docs/architecture.md) | Tech-Stack, Aufbau, Projektstruktur |
| [Entwicklung](docs/development.md) | Konfiguration, Tests, Hot Reload, Docker-Befehle, lokale Entwicklung |

## Tech-Stack

Python 3.14 mit FastAPI, numpy, Pillow und ffmpeg im Backend, React 19 mit TypeScript und Vite im Frontend, Docker Compose für die Entwicklungsumgebung. Details: [Architektur](docs/architecture.md).
