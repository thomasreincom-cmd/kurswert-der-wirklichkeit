# Kurswert der Wirklichkeit

*Was kostet es, eine Wahrscheinlichkeit zu verschieben? Ein Copoiema über Prognosemärkte, Manipulierbarkeit und erlernbare Resilienz*

Thomas Reiner, Dr. Markus W. J. Reiner und Claude Opus 5.5 (Anthropic). Studio Bifurkation · IC, Innsbruck. Session BIF-2026-10-18-001. Stand: 18. Oktober 2026.

## Abstract

Prognosemärkte wie Polymarket werden zunehmend zitiert, als wären ihre Quoten Umfragen. Das Copoiema *Kurswert der Wirklichkeit* stellt jeder Quote eine zweite Zahl zur Seite: das Kapital, das nötig wäre, um sie durch Handel um zehn Prozentpunkte zu verschieben. Am 18. Oktober 2026 lag dieser Wert für den meistgehandelten politischen Markt des Tages, die brasilianische Präsidentschaftswahl, bei rund 85.000 Dollar; 92 Prozent der übrigen messbaren Märkte waren billiger zu bewegen, der Median lag bei etwa 5.600 Dollar. 86 von 439 erfassten Märkten waren „ohne Widerstand“: Ihre angezeigte Zahl ließ sich durch einen einzigen Auftrag verändern, ohne dass ein Handel stattfand. Das Werk ist aus einer menschlichen Ausgangsidee, einer KI-gestützten Messung und einer unabhängigen maschinellen Gegenprüfung entstanden. Es läuft täglich, veröffentlicht nur abgeleitete Kennzahlen und vermittelt seine Befunde als interaktive Reise mit acht Prüffragen, die sich auf Feeds, KI-Antworten und politische Zahlen übertragen lassen.

**Schlagworte:** Prognosemärkte, Marktmanipulation, Medienkompetenz, Resilienz, Interlektische Copoiese, Mensch-KI-Ko-Autorschaft, hybride Bedrohungen

## 1 Ausgangsfrage

Am Anfang stand ein menschlicher Neugiervektor, formuliert von Thomas Reiner: ein Nachrichtenfeed, dessen Schlagzeilen aus Prognosemärkten stammen, dazu ein Prüfsystem, das die Trefferquote rückwirkend mit echten Schlagzeilen vergleicht, und ein Alarm, wenn Trolle den Markt offensichtlich manipulieren. Dahinter steht eine verbreitete Hoffnung. In den Echtzeitdaten digitaler Märkte, so die Annahme, könnte echte Information stecken, schneller als jede Redaktion.

Die erste Verdichtung hat diese Idee nicht verworfen, sondern geschärft. Ein Markt liefert keine Schlagzeile, sondern eine Wahrscheinlichkeit auf eine präzise Frage. Trefferquote ist dafür das falsche Maß; gemessen wird Kalibrierung. Und ein Insider mit echtem Wissen sieht im Moment des Handels genauso aus wie ein Troll.

Den Bruch brachte eine Rückfrage von zwei Wörtern: „Europabezug?“ Die Recherche zeigte, dass der Markt auf Brasiliens Präsidentschaftswahl über 184 Millionen Dollar Handelsvolumen trug, der Markt auf einen Rücktritt des deutschen Bundeskanzlers dagegen rund 6.000 Dollar (Stand Mai 2026). Beide erscheinen in Schlagzeilen als nüchterne Prozentzahl. Aus dieser Asymmetrie wurde das Werk: Die Märkte sind nicht länger Quelle, sondern Gegenstand der Prüfung.

## 2 Methode

**Der Preis einer Schlagzeile.** Ein binärer Marktanteil zahlt einen Dollar, wenn das Ereignis eintritt. Sein Preis wird als Wahrscheinlichkeit gelesen. Aus dem sichtbaren Orderbuch lässt sich berechnen, wie viel Kapital durch Käufe gebunden würde, um den Handelspreis um zehn Prozentpunkte zu verschieben: nach oben über den Kauf aller JA-Angebote bis zum Zielpreis, nach unten über den Kauf von NEIN zum Gegenpreis. Der billigere Weg ist der Schlagzeilenpreis. Grob klassiert wird in vier Stufen, benannt nach dem, was man sich für den Betrag ungefähr kaufen könnte: Taschengeld (unter 1.000 Dollar), Kleinwagen, Eigentumswohnung, teuer (ab 100.000 Dollar).

**Ohne Widerstand.** Die unabhängige Prüfung des Codes durch ein zweites Modell hat einen methodischen Fehler der ersten Fassung aufgedeckt. Der Schlagzeilenpreis war dort als Untergrenze beschrieben. Das war falsch. Plattformen zeigen meist den Mittelkurs zwischen bestem Kauf- und bestem Verkaufsangebot, und dieser lässt sich ohne jeden Handel verschieben, indem man einen Auftrag in die Lücke stellt. Märkte mit einer Lücke von zehn Punkten oder mehr werden deshalb nicht mit einem Dollarbetrag, sondern als „ohne Widerstand“ ausgewiesen. Damit unterscheidet das Werk zwei Arten, eine Schlagzeile zu kaufen: durch Handel, messbar und kapitalintensiv, und durch Kosmetik, nahezu kostenlos.

**Prüfstand.** Nach Auflösung der Märkte wird der Brier-Score je Schlagzeilenklasse verglichen, gemessen ein und sieben Tage vor der Auflösung. Weil billige Märkte häufig Außenseiter mit extremen Preisen sind, wird das Mittelfeld zwischen 15 und 85 Prozent gesondert ausgewertet. Die These, die sich bewähren muss: Billig verschiebbare Quoten sind schlechter kalibriert. Ein Beweis wird daraus nicht, ein begründeter Verdacht oder seine Widerlegung schon.

**Technik.** Ein täglicher Lauf in GitHub Actions liest die öffentliche, dokumentierte Schnittstelle von Polymarket: die 400 meistgehandelten Märkte und zusätzlich alle KI-Märkte unter den 2.000 meistgehandelten. Orderbücher dienen nur der Berechnung und werden nicht archiviert. Code unter MIT-Lizenz, eigene Texte und Kennzahlen unter CC BY 4.0.

## 3 Befunde vom 18. Oktober 2026

Die meisten zitierfähigen Quoten sind billig zu verschieben. Von 439 erfassten Polymarket-Märkten verteilten sich die messbaren so:

| Klasse | Kapital für 10 Punkte | Märkte |
| --- | --- | --- |
| ohne Widerstand | Verschiebung ohne Handel möglich | 86 |
| Taschengeld | unter 1.000 $ | 50 |
| Kleinwagen | 1.000 bis 10.000 $ | 86 |
| Eigentumswohnung | 10.000 bis 100.000 $ | 103 |
| teuer | über 100.000 $ | 47 |
| praktisch entschieden | Preis bei 97 % oder darüber bzw. 3 % oder darunter | 43 |

24 weitere Märkte hatten kein beidseitiges Orderbuch.

**Aufmerksamkeit ist nicht Gewicht.** Der meistgehandelte politische Markt, Flávio Bolsonaros Sieg bei der brasilianischen Präsidentschaftswahl bei 81 Prozent, erforderte rund 85.000 Dollar für zehn Punkte. 92 Prozent der übrigen messbaren Märkte waren billiger. Im Direktvergleich stand die Kontrolle des US-Senats mit 1,4 Millionen Dollar einem Markt auf das Ausscheiden eines brasilianischen Höchstrichters mit 115 Dollar gegenüber. Beide Zahlen sehen im Zitat gleich aus.

**Sport verdrängt Welt.** Sportwetten machten 44 Prozent des Tagesvolumens auf Polymarket aus; im ersten Lauf mit Kalshi waren es 59 Prozent. Ein ungefilterter Feed aus Marktquoten wäre eine Sportseite.

**Weiße Flecken.** Nach Schlüsselwortzuordnung entfielen 25,8 Prozent des Volumens auf Nordamerika, 17,9 auf den Nahen Osten, 9,6 auf Europa, 5,7 auf Lateinamerika; Afrika und Klimafragen kamen praktisch nicht vor. Polymarket ist in Frankreich seit Juli 2026 gesperrt, Deutschland und Italien stehen auf der Liste der Länder, aus denen nicht gehandelt werden darf. Europäische Quoten spiegeln damit vor allem einen Blick von außen.

**KI als Wettgegenstand.** Unter den 2.000 meistgehandelten Märkten fanden sich 43 zu künstlicher Intelligenz. Sie drehten sich fast ausschließlich um Börsengänge, Firmenwerte und die Rangliste der besten Modelle. Keiner war teurer als rund 15.000 Dollar für zehn Punkte; 18 fielen in die Klasse Taschengeld. 19 der 43 betrafen Anthropic, den Hersteller des KI-Ko-Autors dieses Werks.

**Ein Widerspruch, noch ungeprüft.** Polymarket führte zwei Brasilien-Märkte, die sich zu widersprechen scheinen: Bolsonaro gewinnt die Wahl mit 81 Prozent, gewinnt die zweite Runde mit 9 Prozent. Vermutlich gelten unterschiedliche Auflösungsregeln. Vor einer Deutung sind die Regeltexte zu lesen.

## 4 Recht als Material

Die Nutzungsprüfung war kein Anhang, sondern hat das Werk geformt. Die Kalshi Data Terms erlauben nur persönliche, nicht kommerzielle Ansicht und untersagen Veröffentlichung, abgeleitete Werke, Datenbanken sowie jede Nutzung für maschinelles Lernen oder KI ohne schriftliche Genehmigung. Kalshi wurde am Tag der Prüfung aus dem Werk entfernt, samt der bereits veröffentlichten Daten; das Repository wurde ohne alte Historie neu angelegt.

Die Polymarket-Bedingungen (Fassung vom 11. August 2026) untersagen Scraping und das Sammeln von Informationen für nicht autorisierte Zwecke, beschränken die Datennutzung aber ausdrücklich nur für Kapitalmarktakteure und Marktdatenhändler. Das Werk nutzt deshalb ausschließlich die dokumentierte Schnittstelle, einmal täglich, und veröffentlicht nur abgeleitete Kennzahlen und Fragetexte als Zitat. Die Rechtslage bleibt eine Grauzone und ist im Werk offen benannt. In der Konzeptionsphase wurde bewusst keine Plattform kontaktiert.

Nach österreichischem Recht treffen die Strafbestimmungen des Glücksspielrechts Veranstalter und Vermittler unkonzessionierter Angebote; Polymarket verfügt nach Kenntnisstand des Studios über keine Konzession in Österreich. Das Werk vermittelt nichts, setzt keine Partnerlinks, blendet Sportwetten aus den Listen aus und warnt ausdrücklich vor der Teilnahme. Offenlegung nach § 25 Mediengesetz, Datenschutzhinweis und Kennzeichnung nach Art. 50 der KI-Verordnung sind Teil jeder Seite.

Darin liegt ein eigener Befund. Eine der beiden großen Plattformen verbietet, ihre öffentlich angezeigten Wahrscheinlichkeiten für KI oder abgeleitete Werke zu verwenden. Ein Werk über die Verwundbarkeit öffentlicher Wahrscheinlichkeiten stößt damit auf die Frage, wem diese Wahrscheinlichkeiten gehören. Die Lücke, die Kalshi im Bericht hinterlässt, ist selbst eine Aussage.

## 5 Vermittlung: die Reise

Die Messung allein ist für Laien kaum lesbar. Auf Thomas Reiners Eingriff hin („jetzt muss es runtergebrochen werden, fast wie ein interaktives Wissensspiel“) wurde die Startseite zu einer Reise in sieben Stationen, gespeist aus den echten Daten des Tages. Im Prolog steht die meistgehandelte Quote groß im Bild; Besucher schätzen, was es kostet, sie zu verschieben, und sehen danach den tatsächlichen Wert. Ein Partikelfeld zeigt das Geld im Orderbuch als Lichtpunkte, dicht bei teuren, spärlich bei billigen Märkten.

Jede Station endet mit einem Werkzeug, einer Frage, die auf jede Zahl passt:

1. Die Preisfrage: Was würde es kosten, diese Zahl zu verschieben?
2. Die Herkunft: Wer hat die Zahl erzeugt, und womit?
3. Das Gewicht: Wie viel steht hinter dieser Zahl?
4. Die Lücke: Lässt sich die Zahl ändern, ohne dass etwas passiert?
5. Der Zweifel: Ist diese Bewegung ein Beweis oder ein Grund nachzufragen?
6. Der Blickwinkel: Wer schaut hier hin, und wer fehlt?
7. Die Befangenheit: Wer spricht hier, und hat die Quelle ein eigenes Interesse?
8. Der Nutzen: Wem nützt es, wenn ich diese Zahl glaube?

Die letzte Station überträgt die Werkzeuge auf einen Beitrag mit zwei Millionen Likes, auf eine KI-Antwort im Ton großer Sicherheit und auf eine Politikerin, die eine Marktquote zitiert. Das siebte Werkzeug entstand aus der eigenen Lage des Werks: Eine KI von Anthropic berichtet über Wetten auf Anthropic. Die Reise legt das offen. Besucher können über das öffentliche Repository ein neuntes Werkzeug vorschlagen; das Werk ist darauf angelegt, von Menschen für Menschen weiterzuwachsen.

## 6 Grenzen und Diskussion

Der Schlagzeilenpreis ist eine Momentaufnahme des sichtbaren Buchs. Market Maker füllen nach, sobald jemand schiebt, was die tatsächlichen Kosten erhöht. Wer verschiebt, hält danach Anteile, die Wert behalten können; gemessen wird Einsatz, nicht Verlust. Ob das Buch des JA-Anteils die gespiegelten NEIN-Aufträge vollständig enthält, ist offen. Die Zuordnung zu Regionen und Themen läuft über Schlüsselwörter und ist grob. Erfasst werden nur die meistgehandelten Märkte, was die Karte der Leerstellen verzerrt.

Eine starke Bewegung in einem billigen Markt ist kein Nachweis von Manipulation. Echte Nachrichten bewegen dünne Märkte genauso. Das Werk nennt solche Märkte „verwundbar“, nicht „manipuliert“, und hält diese Unterscheidung für den Kern seiner Redlichkeit. Ob billig verschiebbare Quoten tatsächlich schlechter kalibriert sind, ist zum Zeitpunkt dieses Textes ungeprüft; die ersten Auflösungen folgen mit den Wahlen in Brasilien und Israel Ende Oktober 2026.

Die Leistung des Werks liegt deshalb weniger in einer Wahrheitsfindung als in einer Verschiebung der Aufmerksamkeit. Wer eine Quote zitiert, zitiert eine Zahl mit Gewicht oder ohne. Nach unserem Kenntnisstand stellt kein Medium, das Marktquoten als Nachricht verwendet, diese Frage öffentlich. Aggregatoren wie SimpleFunctions weisen Spread und Markttiefe aus, aber als Handelssignal für Trader, nicht als Glaubwürdigkeitsmaß für Leser.

## 7 Ausblick

Quoten wandern in den Journalismus, und bald handeln KI-Agenten auf denselben Märkten. Die Quote wird zur epistemischen Infrastruktur, ohne dass jemand sie öffentlich prüft. Wir halten es für nötig, Methoden zu entwickeln, mit denen Menschen erkennen, ob Feeds, Maschinen, hybride Kriegsführung oder die Machtinteressen Einzelner sie lenken. *Kurswert der Wirklichkeit* ist ein Versuch in diese Richtung: klein, offen gelegt, nicht gewinnorientiert. Die nächsten Schritte sind die Auswertung des Prüfstands nach den ersten Auflösungen, von Hand gepflegte Referenzwerte aus veröffentlichten Umfragen und die Frage, ob dieselbe Frage mit Spielgeld anders bepreist wird als mit Geld.

## Autorschaft und Transparenz

Dieses Werk ist eine Interlektische Copoiese. Thomas Reiner setzte den Neugiervektor und erdete das Werk stilistisch und epistemisch, gemeinsam mit Dr. Markus W. J. Reiner. Claude Opus 5.5 (Anthropic) verdichtete, recherchierte, schrieb den Code und den Entwurf dieses Artikels. Claude Sonnet recherchierte die Schnittstellendokumentation, ein weiteres Claude-Modell prüfte Code und Methodik unabhängig und fand fünf kritische Fehler. Der KI-Ko-Autor stammt von Anthropic; Märkte über Anthropic werden im Werk ohne Auswahl und ohne Wertung gezeigt. Dokumentation: Vektor-Notat, Verdichtungsprotokoll, Eingriffsmarken und Emergenz-Log im Ordner BIF-2026-10-18-001 des Repositorys. Kein Bestandteil dieses Textes ist Anlage-, Wett- oder Rechtsberatung.

## Quellen

- Werk: [thomasreincom-cmd.github.io/kurswert-der-wirklichkeit](https://thomasreincom-cmd.github.io/kurswert-der-wirklichkeit/), Code: [github.com/thomasreincom-cmd/kurswert-der-wirklichkeit](https://github.com/thomasreincom-cmd/kurswert-der-wirklichkeit)
- [Polymarket Terms of Use, gültig ab 11.08.2026](https://docs.google.com/document/d/1N4aYlRcqaWCeKMID7vUSWJ1UPMvw_v6SP4cOFN8ZxR4/mobilebasic) und [Geoblock-Liste](https://docs.polymarket.com/api-reference/geoblock)
- [Kalshi Data Terms of Service](https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf)
- [Peschel: Polymarket, Kalshi und Co. aus österreichischer Sicht, 17.05.2026](https://casinoklage.at/blog/polymarket-kalshi-prognosemaerkte-oesterreich/)
- [Unternehmensserviceportal: Offenlegungspflicht nach § 25 Mediengesetz](https://www.usp.gv.at/themen/brancheninformationen/information-und-kommunikation/offenlegungspflicht-gemaess-para-25-mediengesetz.html)
- [cryptoactu.com zur Sperre von Polymarket in Frankreich](https://cryptoactu.com/lisnard-polymarket-cote-explose/)
- [SimpleFunctions: Merz-Markt, Volumen Mai 2026](https://simplefunctions.dev/answer/friedrich-merz-out-as-chancellor-of-germany)
- [rg.org, Polymarket Daily vom 16.10.2026](https://rg.org/news/prediction-markets/polymarket-daily-brazil-runoff-lula-bolsonaro-fed-hike-world-series-october-16-2026)
- Alle Marktzahlen: eigene Messung vom 18.10.2026, Archiv im Repository.
