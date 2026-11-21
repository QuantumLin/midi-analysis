# Funktionen

MIDI-Datei (`.mid`, `.midi`) auswählen oder per Drag & Drop hochladen. Die Anwendung zeigt dann eine Overlay-Vorschau, den Video-Export und eine Akkordtabelle.

Wie die Werte berechnet werden, steht in [Analyse](analysis.md). Wie die Overlays als Video exportiert werden, steht in [Video-Export](video-export.md).

## Overlay-Vorschau

Play, Pause und eine Zeitleiste spielen alle Overlays synchron ab. Anfangs ist nur das Frequenzspektrum sichtbar; die Schalter unter dem Titel blenden weitere Features einzeln ein oder aus. Die Vorschau zeigt Farbe, Sprache und Raster so, wie die exportierten Videos aussehen werden.

| Overlay | Was es zeigt |
| --- | --- |
| Noten pro Sekunde | Live-Wert (Tastenanschläge in der letzten Sekunde), Gesamtzahl bisher und bisheriger Rekord. Bei einem neuen Rekord erscheint „Neuer Rekord: 29“. Ein LED-Pegel zeigt die Geschwindigkeit relativ zum Höchstwert des Stücks. |
| Tonart | Die aktuelle Tonart, z. B. „d-Moll“. Bei einem Tonartwechsel steht 3 s lang „Modulation →“ darüber. |
| Akkord | Der aktuelle Akkord, z. B. `C`, `Am7`, `G7`, `Cmaj7`, `Bm7b5` oder Umkehrungen wie `C/E`. |
| Stufe | Der aktuelle Akkord als Stufe in der Tonart, z. B. „vi“ oder „V⁷“. Darunter die letzten vier Stufen als Kette („I – V – vi – IV“) und die Bezugstonart („in C-Dur“). Bei einer bekannten Akkordfolge erscheint ihr Name, z. B. „Die Pop-Formel ×2“. |
| Achievements | Pop-ups wie in einem Videospiel („Erfolg freigeschaltet: 8-Finger-Akkord“) für besondere Momente. |
| Endgegner | Die schwerste Stelle des Stücks als „Boss“. 3 s vorher blinkt „Achtung: Boss naht!“, dann sinkt der HP-Balken mit jeder gespielten Note, am Ende steht „Besiegt!“. Der Name richtet sich nach dem, was die Stelle schwer macht: „Notensturm“ (Tempo), „Sprungriese“ (Sprünge), „Akkord-Koloss“ (große Akkorde). |
| Quintenzirkel | Alle 12 Dur-Tonarten außen, die parallelen Moll-Tonarten innen. Der aktuelle Akkord leuchtet auf und steht groß in der Mitte, eine Leuchtspur verbindet die letzten Akkorde. Jede bisher besuchte Tonart glüht umso stärker, je öfter sie vorkam: Am Ende zeigt der Kreis den harmonischen „Fingerabdruck“ des Stücks. |
| Tastatur-Bingo | Eine 3×3-Karte mit musikalischen Ereignissen (Oktave, Septakkord, Blitzlauf, Pause …). Ein Feld leuchtet auf, sobald sein Ereignis zum ersten Mal vorkommt. Eine volle Reihe, Spalte oder Diagonale wird durchgestrichen, darunter erscheint „Bingo!“. |
| Frequenzspektrum | Ein Analyzer wie in einer DAW (z. B. ReaEQ in Reaper) von 20 Hz bis 20 kHz, logarithmisch, in dB. |
| Tasten-Heatmap | Ein leuchtender Balken über alle 88 Tasten, von A0 links bis C8 rechts. Die Farbintensität zeigt, wie oft eine Lage bisher gespielt wurde: von dunkel über die Neonfarbe bis weißglühend. Gerade gedrückte Tasten leuchten als heller Punkt auf. Striche markieren die Cs (C1–C8). |

## Video-Export

Jedes Overlay lässt sich einzeln als **transparentes Video** exportieren und in DaVinci Resolve frei platzieren, z. B. neben einem Piano-Visualizer. Details: [Video-Export](video-export.md).

## Song Wrapped

Ein Abspann im Stil von „Spotify Wrapped“ mit den Zahlen des Stücks: gespielte Noten, schnellste Stelle, Lieblingsakkord, Tonart, Tonumfang, Endgegner und Anzahl der Achievements. Die Karten springen nacheinander ins Bild. Anders als die anderen Overlays ist es ein eigener Clip (ca. 13 s), der im Schnitt hinter das Stück gelegt wird. Die Vorschau ist standardmäßig ausgeblendet und lässt sich über den „Song Wrapped“-Schalter unter „Overlay Preview“ einblenden.

## Akkordtabelle

Jeder erkannte Akkord mit Start, Ende, Stufe und Noten.
