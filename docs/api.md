# API

Das Backend stellt eine HTTP-API unter `/api` bereit. Das vollständige, automatisch erzeugte Schema steht unter http://localhost:8001/docs (Swagger), sobald die Container laufen.

## Endpunkte

| Methode | Pfad | Beschreibung |
| --- | --- | --- |
| `GET` | `/api/health` | Health-Check |
| `POST` | `/api/analysis` | MIDI-Datei analysieren (`multipart/form-data`, Feld `file`) |
| `POST` | `/api/videos` | Video-Export starten (`file`, `kind`, `format`, `width`, `height`, `fps`, `color`, `show_grid`, `show_frame`, `font`, `glow`) → Job |
| `GET` | `/api/videos/{id}` | Status eines Jobs (`status`, `progress`) |
| `GET` | `/api/videos/{id}/download` | Fertiges Video herunterladen |

Fehlerhafte oder zu große Dateien werden mit `400` bzw. `413` abgelehnt.

## Beispiele

```bash
curl -F "file=@song.mid" http://localhost:8001/api/analysis
curl -F "file=@song.mid" -F kind=spectrum -F format=prores http://localhost:8001/api/videos
```

## Analyse-Antwort

- **Kennzahlen:** `duration_seconds`, `note_count`, `percussion_note_count`
- **`spectrum`:** Vorschau mit 20 fps und 256 Bändern, als Base64-codierte Bytes
- **`chords`:** `start`, `end`, `name`, `root`, `quality`, `bass`, `notes`, `numeral` (Stufe, z. B. `vi`), `circle` (Platz im Quintenzirkel: `ring`, `index`, `name`)
- **`keys`:** `overall` und `segments` (`start`, `end`, `key` mit `tonic` und `mode`); jedes Segment nach dem ersten ist eine Modulation
- **`note_rate`:** `values` pro Frame (20 fps), `peak_value`, `peak_time`, `records`
- **`progressions`:** erkannte Akkordfolgen mit `time`, `end`, `id`, `count` und `name` (`de`/`en`)
- **`achievements`:** Pop-ups mit `time`, `end`, `kind`, `title` und `detail` (je `de`/`en`)
- **`motifs`:** `label`, `length` (Töne) und `occurrences` (`start`, `end`, `number`)
- **`sections`:** `start`, `end`, `label` (gleicher Buchstabe = gleicher Teil) und `number`
- **`boss`:** `start`, `end`, `factor`, `name` (`de`/`en`), `difficulty` (0–10), `hits` (Notenstarts in der Passage); `null` bei Stücken unter 10 s
- **`bingo`:** `fields` (3×3 zeilenweise, je `id`, `label` (`de`/`en`), `time` oder `null`) und `lines` (vollständige Linien mit `cells` und `time`)
- **`wrapped`:** Karten mit `id`, `title` und `value` (je `de`/`en`)
- **`notes`:** alle Noten als parallele Listen `start`, `end` (Loslassen der Taste), `pitch`

Die Typen sind im Frontend in `frontend/src/types/analysis.ts` gespiegelt.

## Video-Export

| Parameter | Werte |
| --- | --- |
| `kind` | `spectrum`, `chords`, `key`, `note_rate`, `heatmap`, `harmony`, `achievements`, `motifs`, `sections`, `boss`, `circle`, `bingo`, `wrapped` |
| `format` | `prores` (Standard) oder `png` |
| `width` × `height` | 320×180 bis 3840×2160, gerade Zahlen |
| `fps` | 24, 25, 30, 50, 60 |
| `color` | Hex-Farbe wie `#00e5ff` |
| `show_grid` | nur Spektrum: Raster und Beschriftung |
| `show_frame` | Glas-Panel mit Rahmen um Text- und Spiel-Overlays (Standard `true`) |
| `font` | `orbitron` (Standard), `montserrat`, `bebas`, `playfair`, `pixel`, `handwriting` |
| `glow` | `subtle`, `normal` (Standard), `strong` |
| `scale` | Overlay size from `0.25` to `1.0`; `1.0` is original size (API default) |

Was die einzelnen Videos zeigen, steht in [Video-Export](video-export.md).
