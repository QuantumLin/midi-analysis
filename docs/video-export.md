# Video-Export

Jedes Overlay wird als eigenes Video mit transparentem Hintergrund gerendert, damit es sich im Schnittprogramm frei platzieren lässt.

## Einstellungen

| Einstellung | Optionen |
| --- | --- |
| Format | **ProRes 4444 `.mov`** mit Alpha-Kanal (Standard für Resolve) oder **PNG-Sequenz** als `.zip` |
| Auflösung | 1280×720 bis 3840×2160 |
| Bildrate | 24, 25, 30, 50, 60 fps |
| Neonfarbe | Vorlagen (Cyan, Magenta, Lime, Orange, Violett, Gelb) oder eine eigene Farbe für alle Overlays |
| Raster | Spektrum mit Raster und Hz/dB-Beschriftung oder nur die Kurve |
| Rahmen | Glas-Panel mit leuchtendem Rahmen um die Text- und Spiel-Overlays, oder nur der leuchtende Inhalt (Song Wrapped, Spektrum und Heatmap sind nicht betroffen) |
| Schriftart | Orbitron (Neon-Tech, Standard), Montserrat (modern), Bebas Neue (fett, YouTube-Look), Playfair Display (elegant, klassisch), Press Start 2P (Retro-Pixel), Caveat (Handschrift) |
| Leuchten | Dezent, Normal oder Stark: wie weit der Glow um Text, Pegel und Rahmen strahlt |

- **Einzeln oder alle:** Jede Videoart hat einen eigenen Button. „Alle erstellen“ rendert alle 13 Videos nacheinander.
- **Rendern:** Es läuft im Hintergrund mit Fortschrittsanzeige. Fertige Dateien werden nach 60 Minuten gelöscht (einstellbar, siehe [Entwicklung](development.md#konfiguration)).

## Gestaltung

- **Neon-Look:** Die Schrift ist wählbar (Standard: Orbitron). Unterschiedlich große Schriften werden angeglichen, damit jedes Panel ähnlich groß bleibt. Die Textfelder sind dunkle Glas-Panels mit leuchtendem Rahmen, darin großer Neon-Text mit Glow und eine Beschriftung in Großbuchstaben. Jedes Panel behält im ganzen Video seine Größe, damit nichts springt.
- **Effekte:**
  - **Akkordwechsel:** Das Akkord- und das Stufenfeld blitzen kurz auf.
  - **Noten/s:** Ein LED-Pegel zeigt die aktuelle Geschwindigkeit relativ zum Höchstwert des Stücks.
  - **Rekord, Modulation, Akkordfolge, wiederkehrender Teil:** Das Feld leuchtet 2–4 s lang stärker.
  - **Motiv:** Das Feld erscheint nur, während das Motiv erklingt (plus 1 s), und blitzt bei jedem neuen Auftreten auf.
  - **Achievements:** Das Pop-up springt mit einem kurzen Aufblitzen ins Bild, bleibt 3 s stehen und blendet aus. Dazwischen ist das Video leer.
  - **Endgegner:** Erscheint 3 s vor der schweren Stelle mit blinkender Warnung und verschwindet 3 s nach „Besiegt!“. Sonst ist das Video leer.
  - **Quintenzirkel und Bingo:** Immer sichtbar. Ein neuer Akkord bzw. ein neu abgehaktes Feld blitzt auf, „Bingo!“ leuchtet 3 s lang.
- **Song Wrapped:** Das einzige Video, das nicht so lang ist wie das Stück: Titel, dann eine Karte pro Sekunde, 4 s Standbild, Ausblenden.
- **Akkord bei Pausen:** Bei kurzen Pausen bleibt der letzte Akkord stehen, nach 2 s Stille verschwindet er.
- **Platzierung:** Alle Overlays liegen mittig im Bild, der Heatmap-Balken ist 90 % so breit wie das Bild. In Resolve lassen sie sich frei verschieben und skalieren.

## Richtwerte

Für ein 77-s-Stück in 1080p30 als ProRes:

| Video | Renderzeit | Größe |
| --- | --- | --- |
| Spektrum | ca. 55 s | ca. 0,9 GB |
| Heatmap | ca. 50 s | ca. 0,4 GB |
| Noten/s, Tonart, Akkord, Stufe, Abschnitt | je ca. 50 s | je 0,25–0,4 GB |
| Achievements, Motive, Endgegner | je ca. 45 s | je ca. 0,15 GB |
| Quintenzirkel, Bingo | je ca. 50 s | je ca. 0,8 GB |
| Song Wrapped (ca. 13 s Clip) | ca. 10 s | ca. 0,2 GB |

## In DaVinci Resolve

1. Die `.mov`-Datei auf eine Spur über dem Hintergrund legen. Die Transparenz wird automatisch erkannt.
2. Bei einer PNG-Sequenz das ZIP entpacken und den Ordner importieren. Resolve erkennt die Bilder als Sequenz.
