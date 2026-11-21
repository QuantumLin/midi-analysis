<p align="center"><img src="frontend/public/logo.svg" alt="" width="96" height="96"></p>

<h1 align="center">MIDI Analysis</h1>

An application that analyzes MIDI files and exports the results as transparent neon overlays for piano visualizer videos, for example for editing in DaVinci Resolve.

## Features

- **Live statistics:** Notes per second with records, musical key with modulations, chords, and chord degrees
- **Musical structure:** Recognized chord progressions (for example, the pop formula ×2), recurring motifs, and sections (Part A, B, ...)
- **Achievements:** Video game-style pop-ups such as "8-finger chord" or "Giant leap"
- **Game elements:** The hardest section as a final boss with an HP bar, keyboard bingo, and a glowing circle of fifths
- **Song Wrapped:** A summary featuring key statistics about the piece
- **Visualizations:** DAW-style frequency spectrum and a key heatmap across all 88 piano keys
- **Video export:** Each overlay as a separate video with an alpha channel (ProRes 4444 or PNG sequence) in a selectable neon color
- **Preview:** All overlays play in sync in the browser, matching their appearance in the exported video

Details: [Features](docs/features.md) · [Video export](docs/video-export.md)

## Quick Start

[Docker Desktop](https://www.docker.com/products/docker-desktop/) is required.

```bash
docker compose up --build
```

Open http://localhost:5173 and drop in a MIDI file. The API documentation is available at http://localhost:8001/docs.

## Documentation

| Page | Description |
| --- | --- |
| [Features](docs/features.md) | All overlays, preview, and chord table |
| [Video export](docs/video-export.md) | Settings, neon look, render times, and DaVinci Resolve |
| [Analysis](docs/analysis.md) | How chords, keys, degrees, achievements, motifs, sections, and spectrum are calculated |
| [API](docs/api.md) | Endpoints and response fields |
| [Architecture](docs/architecture.md) | Technology stack, structure, and project layout |
| [Development](docs/development.md) | Configuration, tests, hot reload, Docker commands, and local development |

## Technology Stack

Python 3.14 with FastAPI, NumPy, Pillow, and FFmpeg in the backend; React 19 with TypeScript and Vite in the frontend; Docker Compose for the development environment. See [Architecture](docs/architecture.md).

## License

The source code is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE). Viewing, learning, and using it for private and other non-commercial purposes is permitted. Commercial use, such as selling it or incorporating it into paid products, requires explicit permission. Included fonts are distributed under the SIL Open Font License; each license is stored alongside its font in `assets/fonts/`.
