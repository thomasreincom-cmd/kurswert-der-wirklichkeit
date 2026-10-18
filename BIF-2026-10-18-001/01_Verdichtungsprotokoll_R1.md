# Verdichtungsprotokoll R1 · BIF-2026-10-18-001

KI: Claude Opus 5.5. Unterstützend: Claude Sonnet (API-Recherche, eigener Kontext), Claude Opus als unabhängiger Prüfer (eigener Kontext, hat den Code nicht geschrieben).

## V1 · Erste Verdichtung der Idee

Ein Markt liefert keine Schlagzeilen, sondern Wahrscheinlichkeiten auf präzise Fragen. Die Nachricht steckt in der Bewegung, nicht im Stand. Trefferquote ist das falsche Maß für das Prüfsystem; gemessen wird Kalibrierung (Brier-Score). Der Abgleich mit echten Schlagzeilen wird umgedeutet zur Frage der Vorlaufzeit: wie lange vor der Presse bewegt sich der Markt?

Zur Alarmfunktion: Ein Insider mit echtem Wissen sieht im Moment aus wie ein Troll. Der Alarm darf „auffällig“ sagen, nie „manipuliert“.

Erste Reflexivitätsthese: Sobald der Feed Leser hat, wird er selbst zum Manipulationsziel. Wer einen dünnen Markt bewegt, kauft sich eine Schlagzeile.

## V2 · Die Welt nach Quoten (auf Thomas' Erdung „einfacher gefragt“)

Websuche, Stand 15. bis 17.10.2026, über Aggregatoren. Sieben Schlagzeilen aus Polymarket und Kalshi: US-Midterms, Brasilien-Stichwahl, Netanyahu, Fed, Tesla-SpaceX, Bitcoin, Ukraine. Befund: Schlagseite zu US-Politik, Krypto, Sport; unter den größten Bewegern eine Wette auf Musks Tweet-Anzahl. Brasilien als erster prüfbarer Fall (Markt 79 % gegen Umfragen im Fehlerbereich).

## V3 · Europabezug (auf Thomas' Frage)

Frankreich 2027 (Le Pen 43 %), Merz-Abgang (14 %, Stand Mai, 6.000 $ Volumen), Starmer (67 %, Stand Mai). Polymarket in Frankreich seit Juli 2026 gesperrt. Kernbefund: 184 Mio. $ Volumen für Brasilien gegen 6.000 $ für den deutschen Kanzler. Ein europäischer Markt-Feed wäre dort am verwundbarsten, wo er am interessantesten wäre.

## V4 · Umkehrung (auf Thomas' Auftrag „etwas, das es kaum gibt“)

Die Märkte werden vom Werkzeug zum Gegenstand. Drei Schichten: Preis einer Schlagzeile (Kapital für zehn Punkte Verschiebung aus dem Orderbuch), Divergenz statt Stand, Karte der Leerstellen. Das Prüfsystem bleibt und wird schärfer: Sind billig verschiebbare Märkte schlechter kalibriert?

## V5 · Bau

Messkern `cost_to_move` mit offen gelegten Grenzen (Momentaufnahme, Untergrenze, Einsatz statt Verlust). Sammler für Polymarket (Gamma, CLOB) und Kalshi gegen die am selben Tag recherchierte Dokumentation. Analyse: Auffälligkeiten, Divergenz, Abdeckung, Kalibrierung nach Klasse. Tagesbericht im Convocare-Schema. GitHub Action als Sammler, weil die Cloud-Werkstatt die Markt-APIs nicht erreicht.

Stand: 17 Tests grün, Live-Test ausstehend.

## V6 · Unabhängige Prüfung und Korrektur

Ein zweites Modell (Claude Opus, eigener Kontext, ohne Kenntnis des Bauprozesses) hat Code und Methodik geprüft. Fünf kritische Befunde, alle eingearbeitet:

1. Märkte mit weitem Spread bekamen 0 $ als Schlagzeilenpreis. Jetzt: Status „ohne Widerstand“ statt Dollarbetrag.
2. Die Messung galt fälschlich als Untergrenze. Angezeigt wird meist der Mittelkurs, und der lässt sich ohne Handel durch Aufträge im Spread bewegen. Die Behauptung ist gestrichen, die Grenze offen benannt.
3. Kalshi-Volumen war in Kontrakten, nicht in Dollar. Jetzt geschätzt und als „ca.“ markiert.
4. Ein gescheiterter Abruf hätte alten Stand unter heutigem Datum gezeigt. Jetzt Warnbanner und roter Lauf.
5. Übersprungene Märkte blieben unsichtbar. Jetzt gezählt, ab 20 % rot.

Dazu: Schlüsselwörter mit Wortgrenzen (vorher wurde „senator“ als NATO und „Who will“ als Gesundheit gelesen), Kalibrierung mit festen Vorlaufzeiten und gesondertem Mittelfeld, Auflösungen für archivierte Ticker statt Zeitfenster, überzogene Formulierungen in Bericht und README zurückgenommen.

Stand: 22 Tests grün, gemockter Gesamtlauf erfolgreich, Live-Test ausstehend.

## V7 · Live

Auf Thomas' Auftrag („kommst du rein und kannst selbständig weiterarbeiten“): Repo thomasreincom-cmd/kurswert-der-wirklichkeit angelegt (öffentlich, mit Zustimmung), Pages eingeschaltet, Tageslauf zweimal gestartet. Beide Läufe grün, je 800 Märkte.

Der erste Lauf zeigte zwei Dinge, die keine Dokumentation verraten hätte. Sportwetten machen 59 % des Tagesvolumens aus und hätten die Schlagzeilenliste gefüllt; sie sind jetzt dort ausgeblendet und als Anteil ausgewiesen. Und die meisten „leeren“ Bücher waren praktisch entschiedene Märkte (Preis 99 % oder 0,1 %, nur noch eine Seite); sie heißen jetzt „entschieden“ statt Messfehler. Danach sank der Anteil unmessbarer Märkte von 17 auf 3 %.

Erste Beobachtung, noch ungeprüft: Polymarket führt zwei Brasilien-Märkte, die sich zu widersprechen scheinen (Bolsonaro gewinnt die Wahl 81 %, gewinnt die zweite Runde 9 %). Möglicherweise unterschiedliche Auflösungsregeln; vor jeder Aussage die Regeltexte lesen.
