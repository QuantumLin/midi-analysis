# Funktionen

MIDI-Datei (`.mid`, `.midi`) auswählen oder per Drag & Drop hochladen. Die Anwendung zeigt dann eine Overlay-Vorschau, den Video-Export und eine Akkordtabelle.

Wie die Werte berechnet werden, steht in [Analyse](analysis.md). Wie die Overlays als Video exportiert werden, steht in [Video-Export](video-export.md).

## Overlay-Vorschau

Play, Pause und eine Zeitleiste spielen alle Overlays synchron ab. Die Vorschau zeigt Farbe, Sprache und Raster so, wie die exportierten Videos aussehen werden.

| Overlay | Was es zeigt |
| --- | --- |
| Noten pro Sekunde | Live-Wert (Tastenanschläge in der letzten Sekunde), Gesamtzahl bisher und bisheriger Rekord. Bei einem neuen Rekord erscheint „Neuer Rekord: 29“. Ein LED-Pegel zeigt die Geschwindigkeit relativ zum Höchstwert des Stücks. |
| Tonart | Die aktuelle Tonart, z. B. „d-Moll“. Bei einem Tonartwechsel steht 3 s lang „Modulation →“ darüber. |
| Akkord | Der aktuelle Akkord, z. B. `C`, `Am7`, `G7`, `Cmaj7`, `Bm7b5` oder Umkehrungen wie `C/E`. |
| Stufe | Der aktuelle Akkord als Stufe in der Tonart, z. B. „vi“ oder „V⁷“. Darunter die letzten vier Stufen als Kette („I – V – vi – IV“) und die Bezugstonart („in C-Dur“). Bei einer bekannten Akkordfolge erscheint ihr Name, z. B. „Die Pop-Formel ×2“. |
| Abschnitt | Der aktuelle Teil des Stücks („Teil B“) und ob er neu ist oder wiederkehrt („zum 2. Mal“). |
| Motiv | Erscheint, während ein wiederkehrendes Melodie-Motiv gespielt wird: „Motiv A, 5. Mal – kehrt zurück“. In der Vorschau ist das Feld sonst abgedunkelt, im Video ausgeblendet. |
| Achievements | Pop-ups wie in einem Videospiel („Erfolg freigeschaltet: 8-Finger-Akkord“) für besondere Momente. |
| Frequenzspektrum | Ein Analyzer wie in einer DAW (z. B. ReaEQ in Reaper) von 20 Hz bis 20 kHz, logarithmisch, in dB. |
| Tasten-Heatmap | Ein leuchtender Balken über alle 88 Tasten, von A0 links bis C8 rechts. Die Farbintensität zeigt, wie oft eine Lage bisher gespielt wurde: von dunkel über die Neonfarbe bis weißglühend. Gerade gedrückte Tasten leuchten als heller Punkt auf. Striche markieren die Cs (C1–C8). |

## Video-Export

Jedes Overlay lässt sich einzeln als **transparentes Video** exportieren und in DaVinci Resolve frei platzieren, z. B. neben einem Piano-Visualizer. Details: [Video-Export](video-export.md).

## Akkordtabelle

Jeder erkannte Akkord mit Start, Ende, Stufe und Noten.
