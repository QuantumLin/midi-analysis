# Video-Export

Jedes Overlay wird als eigenes Video mit transparentem Hintergrund gerendert, damit es sich im Schnittprogramm frei platzieren lässt.

## Einstellungen

| Einstellung | Optionen |
| --- | --- |
| Format | **ProRes 4444 `.mov`** mit Alpha-Kanal (Standard für Resolve) oder **PNG-Sequenz** als `.zip` |
| Auflösung | 1280×720 bis 3840×2160 |
| Bildrate | 24, 25, 30, 50, 60 fps |
| Neonfarbe | Vorlagen (Cyan, Magenta, Lime, Orange, Violett, Gelb) oder eine eigene Farbe für alle Overlays |
| Sprache | Deutsch oder Englisch für die Texte („d-Moll“ / „D minor“) |
| Raster | Spektrum mit Raster und Hz/dB-Beschriftung oder nur die Kurve |

- **Einzeln oder alle:** Jede Videoart hat einen eigenen Button. „Alle erstellen“ rendert alle neun Videos nacheinander.
- **Rendern:** Es läuft im Hintergrund mit Fortschrittsanzeige. Fertige Dateien werden nach 60 Minuten gelöscht (einstellbar, siehe [Entwicklung](development.md#konfiguration)).

## Gestaltung

- **Neon-Look:** Die Schrift ist Orbitron. Die Textfelder sind dunkle Glas-Panels mit leuchtendem Rahmen, darin großer Neon-Text mit Glow und eine Beschriftung in Großbuchstaben. Jedes Panel behält im ganzen Video seine Größe, damit nichts springt.
- **Effekte:**
  - **Akkordwechsel:** Das Akkord- und das Stufenfeld blitzen kurz auf.
  - **Noten/s:** Ein LED-Pegel zeigt die aktuelle Geschwindigkeit relativ zum Höchstwert des Stücks.
  - **Rekord, Modulation, Akkordfolge, wiederkehrender Teil:** Das Feld leuchtet 2–4 s lang stärker.
  - **Motiv:** Das Feld erscheint nur, während das Motiv erklingt (plus 1 s), und blitzt bei jedem neuen Auftreten auf.
  - **Achievements:** Das Pop-up springt mit einem kurzen Aufblitzen ins Bild, bleibt 3 s stehen und blendet aus. Dazwischen ist das Video leer.
- **Akkord bei Pausen:** Bei kurzen Pausen bleibt der letzte Akkord stehen, nach 2 s Stille verschwindet er.
- **Platzierung:** Alle Overlays liegen mittig im Bild, der Heatmap-Balken ist 90 % so breit wie das Bild. In Resolve lassen sie sich frei verschieben und skalieren.

## Richtwerte

Für ein 77-s-Stück in 1080p30 als ProRes:

| Video | Renderzeit | Größe |
| --- | --- | --- |
| Spektrum | ca. 55 s | ca. 0,9 GB |
| Heatmap | ca. 50 s | ca. 0,4 GB |
| Noten/s, Tonart, Akkord, Stufe, Abschnitt | je ca. 50 s | je 0,25–0,4 GB |
| Achievements, Motive | je ca. 45 s | je ca. 0,15 GB |

## In DaVinci Resolve

1. Die `.mov`-Datei auf eine Spur über dem Hintergrund legen. Die Transparenz wird automatisch erkannt.
2. Bei einer PNG-Sequenz das ZIP entpacken und den Ordner importieren. Resolve erkennt die Bilder als Sequenz.
