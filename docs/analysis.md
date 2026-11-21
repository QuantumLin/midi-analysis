# Analyse

Wie die Anwendung aus den MIDI-Noten ihre Werte berechnet. Der Code dazu liegt in `backend/app/analysis/`, ein Modul pro Analyse (siehe [Architektur](architecture.md)).

## Einlesen

- **Tempowechsel:** Sie werden bei der Umrechnung in Sekunden berücksichtigt.
- **Haltepedal (CC 64):** Es verlängert den *Klang* der Noten bis zum Loslassen des Pedals. Das wirkt auf das Spektrum.
- **Schlagzeug (MIDI-Kanal 10):** Es hat keine Tonhöhe und wird nur gezählt.

## Noten pro Sekunde

Jede angeschlagene Taste zählt, ein Vierklang also als vier Noten. Rekorde zählen erst nach den ersten 5 s. Schnell aufeinanderfolgende Rekorde in einem Lauf werden zu einem zusammengefasst.

## Akkorde

- **Gehaltene Tasten zuerst:** Für die Akkorderkennung zählt zuerst, welche Tasten gerade *gedrückt* sind. Sonst würde ein gehaltenes oder nie losgelassenes Pedal alle Harmonien zu einem Cluster verschmelzen. Nur wenn die gedrückten Tasten keinen Akkord ergeben, werden die per Pedal nachklingenden Töne verwendet, z. B. bei einem ins Pedal gespielten Arpeggio.
- **Toleranz:** Bis zu zwei Fremdtöne (Melodie, Durchgangstöne) und eine fehlende Quinte verhindern die Erkennung nicht. Eine exakte Übereinstimmung gewinnt immer, deshalb kann ein Melodieton den Namen ändern, z. B. `C` → `Cadd9`.
- **Kurze Abschnitte:** Abschnitte unter 80 ms werden ignoriert.
- **Gebrochene Akkorde:** Arpeggien ohne Pedal werden nicht erkannt.

## Tonart

- **Verfahren:** Krumhansl-Schmuckler. Ein 8-s-Fenster vergleicht, wie lange jede Tonstufe klingt, mit den Profilen aller 24 Dur- und Moll-Tonarten. Ein Wechsel wird erst gemeldet, wenn die neue Tonart einige Sekunden klar besser passt, kurze Ausweichungen zählen nicht als Modulation.
- **Gesamt-Tonart:** Das ist die Tonart, in der das Stück am längsten steht. Bei fast gleicher Dauer gewinnt die zuerst erklingende.
- **Schreibweise:** Notennamen und Akkorde werden passend zur Tonart geschrieben, z. B. `B♭` in d-Moll und `A♯` in H-Dur.

## Stufen und Akkordfolgen

- **Stufen:** Sie beziehen sich auf die Tonart in diesem Moment. Großbuchstaben stehen für Dur, Kleinbuchstaben für Moll, ° für vermindert, ø für halbvermindert, + für übermäßig. In Moll wird von natürlich Moll aus gezählt (i, ii°, III, iv, v, VI, VII). Akkorde ohne Terz (Powerchords, sus) bekommen die Schreibweise der leitereigenen Stufe.
- **Akkordfolgen:** Erkannt werden die Pop-Formel I–V–vi–IV, die Doo-Wop-Folge I–vi–IV–V, Pachelbels Kanon, die Royal Road IV–V–iii–vi, die Andalusische Kadenz i–VII–VI–V, die Jazz-Kadenz ii–V–I und Quintfälle ab vier Akkorden.
  - Verglichen werden Grundton-Abstände und Akkordtyp, daher funktioniert das in jeder Tonart.
  - Schleifen wie die Pop-Formel werden auch erkannt, wenn sie mit einem anderen Akkord beginnen (vi–IV–I–V), und jede Wiederholung wird mitgezählt.
  - Kurze Durchgangsakkorde und sus-/Powerchords werden dabei übersprungen.

## Achievements

Sie werden allein aus den Noten erkannt:

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

## Endgegner

- **Schwierigkeit:** Alle 0,5 s wird aus mehreren Faktoren ein Wert von 0 bis 10 berechnet, jeweils über die letzte Sekunde und über 2 s geglättet:

  | Faktor | Gewicht | Maximal schwer bei | Boss-Name |
  | --- | --- | --- | --- |
  | Tempo | 50 % | 12 Anschlägen pro Sekunde (ein Akkord zählt einmal) | Notensturm |
  | Sprünge | 25 % | 12 Halbtönen mittlerem Sprung zwischen Anschlägen | Sprungriese |
  | Akkordgröße | 25 % | 8 gleichzeitig angeschlagenen Tönen | Akkord-Koloss |

- **Boss:** Das 8-s-Fenster mit dem höchsten mittleren Wert. Der Faktor mit dem größten Anteil darin gibt dem Boss seinen Namen. Jede Note in der Passage ist ein Treffer, die HP sinken entsprechend. Stücke unter 10 s haben keinen Boss.
- **Erweitern:** Einen weiteren Faktor in `FACTORS` (`backend/app/analysis/boss_fight.py`) eintragen und seinen Boss-Namen in `BOSS_NAMES` (`backend/app/video/labels.py`).

## Quintenzirkel

Dur-Akkorde (auch Dominant- und Major-Septakkorde) liegen außen auf ihrem Grundton, Moll- und verminderte Akkorde innen neben ihrer Paralleltonart (a-Moll neben C-Dur). Die Leuchtspur verbindet die letzten sechs verschiedenen Positionen. Der „Fingerabdruck“ zeigt in vier Helligkeitsstufen, wie oft eine Position bisher vorkam, relativ zur häufigsten Position des Stücks.

## Tastatur-Bingo

- **Felder:** Jedes Feld hat einen eigenen Detektor, der den Zeitpunkt des ersten Auftretens liefert:

  | Feld | Ereignis |
  | --- | --- |
  | Oktave | zwei Töne im Oktavabstand gleichzeitig angeschlagen |
  | Septakkord | erster Septakkord (7, maj7, m7, dim7, m7b5 …) |
  | Tiefer Bass / Höhenflug | erster Ton unter C2 bzw. ab C6 |
  | Blitzlauf | 6 Einzeltöne in Folge, je höchstens 0,125 s auseinander |
  | Akkordfolge | erste erkannte bekannte Akkordfolge |
  | Pause | 1 s völlige Stille mitten im Stück |
  | 6-Ton-Akkord | 6 verschiedene Töne gleichzeitig angeschlagen |
  | Fortissimo / Pianissimo / Modulation | stehen bereit, sind aber nicht auf der Standardkarte |

- **Karte:** Seltene Ereignisse liegen in den Ecken und in der Mitte, häufige an den Rändern. Jede Linie enthält so mindestens zwei seltene Ereignisse, und das erste Bingo kommt nicht schon in den ersten Sekunden.
- **Erweitern:** Einen Detektor in `FIELDS` (`backend/app/analysis/bingo.py`) eintragen, seine Beschriftung in `BINGO_LABELS` (`backend/app/video/labels.py`) und ihn in `CARD` platzieren. Ein Feld `free` ist von Anfang an abgehakt.

## Song Wrapped

Jede Karte ist eine kleine Funktion, die aus den Fakten des Stücks Titel und Wert in einer Sprache baut, oder nichts, wenn es dazu nichts zu sagen gibt (z. B. kein Boss bei sehr kurzen Stücken). Höchstens 7 Karten werden gezeigt. **Erweitern:** eine Funktion schreiben und in `CARDS` (`backend/app/video/wrapped.py`) eintragen; die Reihenfolge dort ist die Reihenfolge im Video.

## Spektrum

MIDI enthält keinen Klang, deshalb wird das Spektrum aus den Noten berechnet:

- **Klangmodell:** Jede Note erzeugt ihren Grundton und bis zu 32 Obertöne. Der Anschlag ist sofort da, danach klingt die Note exponentiell aus, nach dem Loslassen folgt ein kurzes Release.
- **Tonhöhe und Lautstärke:** Tiefe Töne klingen länger nach, laute Noten klingen heller.
- **Anschlaggeräusch:** Jeder Anschlag erzeugt ein kurzes, breitbandiges Hammergeräusch.
- **Analyzer-Verhalten:** Der Pegel steigt sofort und fällt um höchstens 36 dB pro Sekunde, wie bei einem DAW-Analyzer.
- **Pegel:** Er ist relativ. Der lauteste Moment des Stücks liegt bei −3 dB.
