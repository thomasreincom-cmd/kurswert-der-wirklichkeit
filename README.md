# Kurswert der Wirklichkeit

Prognosemärkte werden inzwischen zitiert wie Umfragen. Eine Umfrage kommt mit Fehlermarge, eine Quote kommt nackt. Dieses Instrument setzt neben jede Quote, wie viel Kapital es binden würde, sie durch Handel um zehn Prozentpunkte zu verschieben.

Der Gedanke dahinter ist einfach. Eine Wahrscheinlichkeit, hinter der 184 Millionen Dollar Handelsvolumen stehen (Brasilien-Stichwahl auf Polymarket, Oktober 2026), ist etwas anderes als eine aus einem Markt mit 6.000 Dollar Gesamtvolumen (Merz' Abgang vor 2027, Polymarket, Stand Mai 2026). Beide erscheinen in Schlagzeilen als nüchterne Prozentzahl.

Ein nicht gewinnorientiertes Kunstwerk (Copoiema) des Studio Bifurkation · IC, Innsbruck, über Menschen, Maschinen und öffentliche Wahrscheinlichkeit. Entstanden in Session BIF-2026-10-18-001. Kein Wettangebot, keine Werbung, keine Anlageberatung.

Startseite (die Reise in sieben Stationen): https://thomasreincom-cmd.github.io/kurswert-der-wirklichkeit/
Tägliche Messung: https://thomasreincom-cmd.github.io/kurswert-der-wirklichkeit/heute.html

## Was täglich passiert

Eine GitHub Action fragt jeden Morgen die öffentliche, dokumentierte Lese-Schnittstelle von Polymarket ab: die 400 Märkte mit dem höchsten Tagesvolumen samt Orderbuch. Das Orderbuch wird nur zur Berechnung verwendet und nicht archiviert. Daraus entstehen vier Schichten:

**Der Preis einer Schlagzeile.** Aus dem sichtbaren Orderbuch: wie viel Kapital durch Käufe gebunden würde, um den Handelspreis um zehn Punkte zu verschieben, in die billigere Richtung. Grob klassiert als Taschengeld (unter 1.000 $), Kleinwagen, Eigentumswohnung, teuer (ab 100.000 $). Ist der Abstand zwischen bestem Kauf- und Verkaufsauftrag zehn Punkte oder mehr, heißt der Markt „ohne Widerstand“: Die angezeigte Zahl lässt sich dann schon durch bloßes Einstellen von Aufträgen bewegen.

**Bewegungen seit dem Vortag.** Märkte, deren Mittelkurs sich um mindestens acht Punkte bewegt hat. Verwundbare Märkte (am Vortag ohne Widerstand oder unter 10.000 $) stehen oben. Ein Hinweis, ausdrücklich kein Manipulationsnachweis.

**Divergenz.** Wo dieselbe Frage auf zwei Plattformen verschieden bepreist ist, oder wo ein Markt von einer Referenz (Umfrage, Futures) abweicht. Die Paare pflegen wir von Hand in `pairs.json` und `references.json`.

**Leerstellen.** Wie sich das Volumen auf Regionen und Themen verteilt. Die Stichproben vom Oktober 2026 lassen erwarten, dass Europa, Klima und Afrika kaum vorkommen; ob das hält, zeigen erst die täglichen Läufe.

Und rückwirkend der **Prüfstand**: Sobald Märkte aufgelöst sind, wird der Brier-Score nach Schlagzeilen-Klasse verglichen, gemessen ein und sieben Tage vor Auflösung. Die These, die sich daran bewähren muss: Billig verschiebbare Märkte sind schlechter kalibriert. Weil billige Märkte oft Außenseiter mit extremen Preisen sind, wird das Mittelfeld (15 bis 85 %) gesondert ausgewertet. Ein Beweis wird daraus nicht, ein begründeter Verdacht oder seine Widerlegung schon.

## Einrichten

Für eine eigene Kopie:

1. Leeres Repo auf GitHub anlegen, diesen Ordner hineinschieben.
2. Unter Settings → Pages als Quelle „GitHub Actions" wählen.
3. Unter Actions den Workflow „Tageslauf" einmal von Hand starten. Danach läuft er täglich um 05:13 UTC.

Der Bericht erscheint dann auf der Pages-Adresse des Repos, das Archiv wächst in `data/`.

Lokal (Python 3.12 oder neuer):

```
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python -m kdw.run --top 50
```

## Paare und Referenzen pflegen

`pairs.json`:

```json
[{"label": "Brasilien: zwei Polymarket-Märkte",
  "a": {"venue": "polymarket", "market_id": "<conditionId>"},
  "b": {"venue": "polymarket", "market_id": "<conditionId>"},
  "invert_b": false}]
```

`references.json`:

```json
[{"label": "Brasilien: Flávio Bolsonaro",
  "market": {"venue": "polymarket", "market_id": "<conditionId>"},
  "value": 0.50, "source": "Datafolha", "date": "2026-10-15"}]
```

Die IDs stehen nach dem ersten Lauf im Archiv und in `site/summary.json`.

## Grenzen, offen benannt

Der Schlagzeilenpreis ist eine Momentaufnahme des sichtbaren Buchs. Er ist keine Untergrenze für das Verschieben der *angezeigten* Zahl: Die meisten Plattformen zeigen den Mittelkurs, und der lässt sich durch Aufträge im Spread billiger bewegen als durch Handel. Gemessen wird nur die Verschiebung durch Handel. Market Maker füllen nach, sobald jemand schiebt, das macht es teurer. Wer verschiebt, hält danach Anteile, die Wert haben können: gemessen wird Einsatz, nicht Verlust.

Ob das Polymarket-Buch des JA-Tokens die gespiegelten NEIN-Aufträge vollständig enthält, ist nicht geklärt. Falls nicht, wird die Tiefe dort unterschätzt.

Die Regionen- und Themenzuordnung läuft über Schlüsselwörter mit Wortgrenzen. Sie ist grob und sollte an einer von Hand beschrifteten Stichprobe geprüft werden, bevor jemand Schlüsse daraus zieht.

Erfasst werden die 400 meistgehandelten Märkte. Nischenmärkte fehlen damit von vornherein, was die Leerstellen-Karte verzerrt.

## Rechtliches

Am 18.10.2026 wurden die Nutzungsbedingungen beider Plattformen geprüft. Ergebnis und Folgen:

**Kalshi ist ausgesetzt.** Die Kalshi Data Terms erlauben nur persönliche, nicht kommerzielle Ansicht und untersagen Veröffentlichung, abgeleitete Werke, Datenbanken und KI-Nutzung ohne schriftliche Genehmigung. Das API Developer Agreement beschränkt die Schnittstelle auf eigenes Handeln. Der Sammler ist abgeschaltet (`ENABLE_KALSHI = False` in `kdw/run.py`), Kalshi-Daten wurden aus dem aktuellen Archiv entfernt. Kalshi bleibt draußen, solange keine schriftliche Genehmigung vorliegt.

**Polymarket wird zurückhaltend genutzt.** Die Terms of Use (Fassung vom 11.08.2026) untersagen Scraping mit Crawlern und Bots sowie das Sammeln von Informationen „für nicht autorisierte Zwecke“, beschränken die Datennutzung aber ausdrücklich nur für Kapitalmarktakteure und Marktdatenhändler. Die Lese-Schnittstelle ist öffentlich dokumentiert, mit veröffentlichten Ratenlimits. Das Werk nutzt sie einmal täglich, nicht kommerziell, ohne Weiterverkauf, und veröffentlicht nur abgeleitete Kennzahlen und Fragetexte als Zitat, keine Orderbuch-Rohdaten. Das Studio nimmt in der Konzeptionsphase bewusst keinen Kontakt zu den Plattformen auf.

Weitere Absicherungen: Offenlegung nach § 25 Mediengesetz und Datenschutzhinweis auf der Berichtsseite (`impressum.html`), keine Cookies und keine externen Schriften, keine Partnerlinks, Quellenlinks mit `rel="nofollow"`, ausdrücklicher Hinweis auf fehlende österreichische Konzession, KI-Kennzeichnung nach Art. 50 KI-Verordnung.

Rechteinhaber, die eine Darstellung beanstanden, erreichen das Studio über convocare.at. Beanstandete Inhalte werden im Zweifel entfernt.

Diese Prüfung ist keine Rechtsberatung. Offene Punkte für eine anwaltliche Prüfung stehen im Prüfbericht.

## Autorschaft

Interlektische Copoiese. Thomas Reiner setzt den Neugiervektor und erdet. Claude Opus 5.5 (Anthropic) verdichtet und schreibt den Code; Claude Sonnet hat die API-Dokumentation recherchiert, ein weiteres Modell den Code unabhängig geprüft. KI-unterstützt, gekennzeichnet nach Art. 50 KI-Verordnung (EU) 2024/1689.

Lizenz: siehe `LICENSE`. Code MIT, eigene Texte und Kennzahlen CC BY 4.0. Daten und Fragetexte Dritter sind ausgenommen.
