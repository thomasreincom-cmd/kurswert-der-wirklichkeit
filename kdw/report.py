"""Tagesbericht als statische HTML-Seite im Convocare-Schema."""

from __future__ import annotations

import html
from datetime import date
from typing import Optional

from .analysis import is_sport
from .metrics import TIER_ORDER

CSS = """
:root{--bg:#0d0f12;--card:#151820;--raised:#1a1d24;--line:#2d3748;--text:#e2e8f0;
--muted:#94a3b8;--amber:#f59e0b;--teal:#2dd4bf;--red:#f87171}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:17px/1.5 system-ui,"Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:1040px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:42px;line-height:1.1;margin:0 0 8px;letter-spacing:-.01em}
h2{font-size:25px;margin:48px 0 6px}
h3{font-size:17px;margin:20px 0 8px;color:var(--muted);font-weight:600}
p.lead{color:var(--muted);max-width:720px;margin:0 0 8px}
p.note{color:var(--muted);font-size:15px;max-width:760px;margin:4px 0 16px}
.date{color:var(--amber);font-weight:600;font-size:15px;letter-spacing:.04em;text-transform:uppercase}
.banner{background:var(--red);color:var(--bg);padding:10px 16px;font-weight:700;border-radius:8px;margin-bottom:20px}
.grid{display:grid;gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.row{display:grid;grid-template-columns:1fr auto;gap:4px 16px;align-items:baseline}
.q{font-weight:600}
.q a,td a{color:var(--text);text-decoration:none;border-bottom:1px solid var(--line)}
.q a:hover,td a:hover{border-color:var(--teal)}
.meta{color:var(--muted);font-size:14px}
.right{text-align:right}
.prob{font-variant-numeric:tabular-nums;font-size:22px;font-weight:700;color:var(--teal);text-align:right}
.cost{font-variant-numeric:tabular-nums;font-weight:700;color:var(--amber)}
.tier{display:inline-block;font-size:12px;padding:1px 8px;border-radius:99px;border:1px solid var(--line);
color:var(--muted);margin-left:6px;white-space:nowrap}
.tier.t-ohne,.tier.t-Taschengeld,.tier.t-verwundbar{border-color:var(--red);color:var(--red)}
.tier.t-Kleinwagen{border-color:var(--amber);color:var(--amber)}
.bar{height:8px;background:var(--raised);border-radius:4px;overflow:hidden;margin-top:6px}
.bar>span{display:block;height:100%;background:var(--teal)}
.bar.amber>span{background:var(--amber)}
table{width:100%;border-collapse:collapse;font-size:15px;font-variant-numeric:tabular-nums}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:500}
td.num,th.num{text-align:right;white-space:nowrap}
.scroll{overflow-x:auto}
.empty{color:var(--muted);font-style:italic}
footer{margin-top:56px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:14px}
footer a{color:var(--teal)}
.term{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:help;
border-bottom:1px dotted var(--muted);text-align:inherit}
.term:hover,.term:focus-visible{border-bottom-color:var(--teal);color:var(--text);outline:none}
.tier.term{border-bottom:1px solid;cursor:help}
.pop{max-width:min(420px,calc(100vw - 32px));background:var(--raised);color:var(--text);
border:1px solid var(--teal);border-radius:10px;padding:14px 16px;font-size:15px;line-height:1.5;
box-shadow:0 12px 40px rgba(0,0,0,.6);margin:auto}
.pop::backdrop{background:rgba(13,15,18,.55)}
.pop strong{display:block;color:var(--teal);margin-bottom:4px}
.pop p{margin:0}
.pop .close{float:right;background:none;border:0;color:var(--muted);font-size:20px;cursor:pointer;line-height:1}
dl.glossary{display:grid;grid-template-columns:minmax(120px,max-content) 1fr;gap:8px 20px;font-size:15px}
dl.glossary dt{color:var(--teal);font-weight:600}
dl.glossary dd{margin:0;color:var(--muted)}
@media (max-width:560px){h1{font-size:32px}.prob{font-size:19px}dl.glossary{grid-template-columns:1fr}dl.glossary dd{margin-bottom:8px}}
"""

# Begriffe, die im Bericht ein Erklärfenster öffnen. Reihenfolge = Reihenfolge im Glossar.
GLOSSARY: list[tuple[str, str, str]] = [
    ("prognosemarkt", "Prognosemarkt",
     "Eine Plattform, auf der Menschen mit Geld darauf wetten, ob etwas eintritt. Ein Anteil zahlt 1 $, wenn es eintritt, sonst nichts. Kostet er 62 Cent, liest man das als 62 % Wahrscheinlichkeit."),
    ("zehnpunkte", "Kapital für 10 Punkte",
     "So viel Geld müsste jemand einsetzen, um die angezeigte Wahrscheinlichkeit durch Käufe um zehn Prozentpunkte zu verschieben, etwa von 60 auf 70 %. Je kleiner der Betrag, desto leichter lässt sich die Zahl beeinflussen, die in Schlagzeilen zitiert wird."),
    ("richtung", "nach oben, nach unten",
     "Die Richtung, in die das Verschieben billiger wäre. Nach oben heißt: JA-Anteile kaufen, bis die Wahrscheinlichkeit zehn Punkte höher steht. Nach unten heißt: NEIN-Anteile kaufen."),
    ("ohne", "ohne Widerstand",
     "Zwischen dem besten Kaufangebot und dem besten Verkaufsangebot klafft eine Lücke von zehn Punkten oder mehr. Dann genügt ein einziger Auftrag in diese Lücke, und die angezeigte Zahl springt, ohne dass irgendetwas gehandelt wird. Solche Quoten sind praktisch beliebig formbar."),
    ("taschengeld", "Taschengeld",
     "Unter 1.000 $ reichen, um die Quote um zehn Punkte zu verschieben. Die Klassen sind nach dem benannt, was man sich für diesen Betrag ungefähr kaufen könnte."),
    ("kleinwagen", "Kleinwagen",
     "Zwischen 1.000 und 10.000 $ reichen, um die Quote um zehn Punkte zu verschieben."),
    ("wohnung", "Eigentumswohnung",
     "Zwischen 10.000 und 100.000 $ sind nötig, um die Quote um zehn Punkte zu verschieben."),
    ("teuer", "teuer",
     "Über 100.000 $ sind nötig. Solche Quoten lassen sich nur mit großem Einsatz verschieben und sind entsprechend belastbarer."),
    ("entschieden", "praktisch entschieden",
     "Der Preis steht bei 97 % oder mehr (oder bei 3 % oder weniger), und nur noch eine Seite bietet. Der Ausgang gilt als so gut wie sicher; gemessen wird hier nichts mehr."),
    ("verwundbar", "verwundbar",
     "Der Markt hat sich seit dem Vortag um mindestens acht Punkte bewegt und war am Vortag ohne Widerstand oder für weniger als 10.000 $ verschiebbar. Das ist ein Hinweis auf Verwundbarkeit, kein Beweis für Manipulation: Echte Nachrichten bewegen dünne Märkte genauso."),
    ("beobachten", "beobachten",
     "Der Markt hat sich stark bewegt, war am Vortag aber teuer zu verschieben. Die Bewegung ist wahrscheinlich echt."),
    ("volumen", "24h-Volumen",
     "Der Geldbetrag, der in den letzten 24 Stunden in diesem Markt gehandelt wurde. Ein Maß für Aufmerksamkeit, nicht für Belastbarkeit."),
    ("orderbuch", "Orderbuch",
     "Die Liste aller offenen Kauf- und Verkaufsangebote mit Preis und Menge. Aus ihr lässt sich ablesen, wie viel Geld im Weg liegt, wenn jemand die Quote verschieben will."),
    ("mittelkurs", "Mittelkurs",
     "Die Mitte zwischen bestem Kauf- und bestem Verkaufsangebot. Meist ist das die Zahl, die eine Plattform als Wahrscheinlichkeit anzeigt."),
    ("brier", "Brier-Score",
     "Ein Maß dafür, wie gut Wahrscheinlichkeiten im Nachhinein gestimmt haben. 0 ist perfekt, 0,25 entspricht dem Münzwurf. Kleiner ist besser."),
    ("mittelfeld", "Mittelfeld",
     "Nur Märkte mit einer Wahrscheinlichkeit zwischen 15 und 85 %. Außenseiter und Favoriten fallen heraus, weil sie den Vergleich verzerren würden."),
]
_GKEY = {label: key for key, label, _ in GLOSSARY}
TIER_KEY = {"ohne Widerstand": "ohne", "Taschengeld": "taschengeld", "Kleinwagen": "kleinwagen",
            "Eigentumswohnung": "wohnung", "teuer": "teuer", "verwundbar": "verwundbar",
            "beobachten": "beobachten"}


def term(text: str, key: str, cls: str = "term") -> str:
    """Ein Begriff, der beim Antippen sein Erklärfenster öffnet."""
    return f'<button type="button" class="{cls}" popovertarget="g-{key}">{text}</button>'


def popovers() -> str:
    return "".join(
        f'<div id="g-{key}" popover class="pop"><button type="button" class="close" popovertarget="g-{key}" '
        f'popovertargetaction="hide" aria-label="Schließen">×</button><strong>{e(label)}</strong><p>{e(text)}</p></div>'
        for key, label, text in GLOSSARY)


def glossary_section() -> str:
    items = "".join(f"<dt>{e(label)}</dt><dd>{e(text)}</dd>" for _, label, text in GLOSSARY)
    return f'<h2 id="begriffe">Begriffe</h2><p class="note">Jeder unterstrichene Begriff im Bericht öffnet beim Antippen diese Erklärung.</p><dl class="glossary">{items}</dl>'

VENUE = {"polymarket": "Polymarket", "kalshi": "Kalshi"}


def e(x) -> str:
    return html.escape("" if x is None else str(x))


def pct(p: Optional[float]) -> str:
    return "k. A." if p is None else f"{p*100:.0f} %"


def _de(n: float, decimals: int = 0) -> str:
    s = f"{n:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def usd(x: Optional[float], lower_bound: bool = False, est: bool = False) -> str:
    if x is None:
        return "k. A."
    pre = ("≥ " if lower_bound else "") + ("ca. " if est else "")
    if x >= 1_000_000:
        return f"{pre}{_de(x/1e6, 1)} Mio. $"
    if x >= 10_000:
        return f"{pre}{_de(x/1000)} Tsd. $"
    return f"{pre}{_de(x)} $"


def tier_badge(t: Optional[str]) -> str:
    if not t:
        return ""
    cls = "t-ohne" if t == "ohne Widerstand" else f"t-{t}"
    key = TIER_KEY.get(t)
    if key:
        return term(e(t), key, f"tier term {e(cls)}")
    return f'<span class="tier {e(cls)}">{e(t)}</span>'


def cost_text(mv: dict) -> str:
    if mv.get("status") == "ohne_widerstand":
        return ""
    if mv.get("headline_price") is None:
        return "nicht messbar"
    d = {"up": "nach oben", "down": "nach unten"}.get(mv.get("cheapest_direction"), "")
    d = term(d, "richtung") if d else d
    return f'{d}: <span class="cost">{usd(mv["headline_price"], mv.get("lower_bound_only"))}</span>'


def market_card(r: dict) -> str:
    mv = r.get("move") or {}
    est = r.get("volume_unit") == "usd_est"
    return f"""<div class="card"><div class="row">
<div class="q"><a href="{e(r.get('url'))}" rel="nofollow noopener noreferrer">{e(r.get('question'))}</a></div>
<div class="prob">{pct(r.get('price'))}</div>
<div class="meta">{VENUE.get(r['venue'], e(r['venue']))} · {term("24h-Volumen", "volumen")} {usd(r.get('volume_24h'), est=est)}</div>
<div class="meta right">{term("10 Punkte", "zehnpunkte")} {cost_text(mv)}{tier_badge(mv.get('tier'))}</div>
</div></div>"""


def _cards(rows: list[dict]) -> str:
    if not rows:
        return '<p class="empty">Keine Daten.</p>'
    return '<div class="grid">' + "".join(market_card(r) for r in rows) + "</div>"


def render(day: date, records: list[dict], anomalies: list[dict], divergences: list[dict],
           coverage: dict, calibration: dict, stats: dict) -> str:
    live = [r for r in records if (r.get("move") or {}).get("status") != "entschieden"]
    sport = [r for r in live if is_sport(r)]
    world = [r for r in live if not is_sport(r)]
    vol = lambda rs: sum(float(r.get("volume_24h") or 0) for r in rs)  # noqa: E731
    sport_share = vol(sport) / max(vol(live), 1)
    ranked = sorted((r for r in world if r.get("volume_24h")), key=lambda r: -(r["volume_24h"] or 0))
    top = ranked[:12]
    pool = ranked[:150]
    weak = [r for r in pool if (r.get("move") or {}).get("tier") in ("ohne Widerstand", "Taschengeld", "Kleinwagen")]
    tiers_count = {t: sum(1 for r in records if (r.get("move") or {}).get("tier") == t) for t in TIER_ORDER}

    out = [f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kurswert der Wirklichkeit</title>
<meta name="description" content="Was kostet es, eine Wahrscheinlichkeit zu verschieben? Täglicher Bericht über Prognosemärkte.">
<link rel="stylesheet" href="ci-convocare.css">
<style>{CSS}</style></head><body><main>"""]

    if stats.get("stale"):
        out.append(f'<div class="banner">Veraltet: Der heutige Abruf ist gescheitert. Angezeigt wird der Stand vom {e(stats.get("day"))}.</div>')
    elif stats.get("errors"):
        out.append('<div class="banner">Unvollständig: ' + e("; ".join(stats["errors"])) + "</div>")

    out.append(f"""<div class="date">{day.strftime('%d.%m.%Y')} · {stats.get('n_markets', 0)} Märkte</div>
<h1>Kurswert der Wirklichkeit</h1>
<p class="lead">{term("Prognosemärkte", "prognosemarkt")} werden zitiert wie Umfragen. Hier steht neben jeder Quote, wie viel Kapital es binden würde, sie durch Handel um zehn Prozentpunkte zu verschieben. Ob billig verschiebbare Quoten tatsächlich weniger taugen, prüft dieser Bericht laufend nach.</p>
<p class="note">Gemessen am sichtbaren {term("Orderbuch", "orderbuch")} zum Zeitpunkt der Abfrage. {term("„Ohne Widerstand“", "ohne")} heißt: Der Abstand zwischen bestem Kauf- und Verkaufsauftrag ist so groß, dass sich die angezeigte Zahl schon durch bloßes Einstellen von Aufträgen bewegen lässt, ganz ohne Handel. Market Maker füllen nach, wer verschiebt, hält danach Anteile mit möglichem Wert: gemessen wird Einsatz, nicht Verlust.</p>""")

    n_decided = len(records) - len(live)
    dist = " · ".join(f"{term(e(t), TIER_KEY[t])}: {n}" for t, n in tiers_count.items() if n) + \
        (f" · {term('praktisch entschieden', 'entschieden')}: {n_decided}" if n_decided else "")
    if dist:
        out.append(f'<p class="note">Verteilung heute: {dist}. Unterstrichene Begriffe antippen für eine Erklärung, alle auf einen Blick unter <a href="#begriffe" style="color:var(--teal)">Begriffe</a>.</p>')

    out.append("<h2>Die meistgehandelten Fragen des Tages</h2>")
    out.append(f'<p class="note">Sortiert nach 24-Stunden-Volumen, ohne Sport. Sportwetten machen heute {_de(sport_share*100)} % des Tagesvolumens aus ({len(sport)} von {len(live)} offenen Märkten) und würden diese Liste sonst füllen. Rechts unten das Kapital für zehn Punkte in die billigere Richtung.' + (' Kalshi zählt Kontrakte; das Dollarvolumen ist dort geschätzt.' if any(r['venue'] == 'kalshi' for r in records) else '') + '</p>')
    out.append(_cards(top))

    out.append("<h2>Viel Aufmerksamkeit, wenig Widerstand</h2>")
    out.append('<p class="note">Unter den 150 meistgehandelten Märkten ohne Sport jene, die ohne Widerstand oder mit weniger als 10.000 $ verschiebbar sind. Wer solche Quoten zitiert, zitiert eine dünne Zahl.</p>')
    out.append(_cards(weak[:12]))

    since = stats.get("compare_day")
    out.append(f"<h2>Bewegungen seit {e(date.fromisoformat(since).strftime('%d.%m.')) if since else 'dem Vortag'}</h2>")
    if anomalies:
        out.append('<p class="note">Märkte mit mindestens acht Punkten Bewegung im ' + term("Mittelkurs", "mittelkurs") + '. ' + term("„Verwundbar“", "verwundbar") + ' heißt: Am Vergleichstag war der Markt ohne Widerstand oder für weniger als 10.000 $ verschiebbar. Ein Hinweis, kein Manipulationsnachweis. Echte Nachrichten bewegen dünne Märkte genauso.</p>')
        rows = []
        for a in anomalies[:15]:
            rows.append(
                f"<tr><td><a href='{e(a.get('url'))}' rel='nofollow noopener noreferrer'>{e(a['question'])}</a><div class='meta'>{VENUE.get(a['venue'], '')}</div></td>"
                f"<td class='num'>{pct(a['from'])} → {pct(a['to'])}</td>"
                f"<td class='num'>{tier_badge(a.get('tier_before'))}</td>"
                f"<td>{tier_badge(a['flag'])}</td></tr>")
        out.append("<div class='scroll'><table><tr><th>Markt</th><th class='num'>Bewegung</th>"
                   "<th class='num'>Widerstand vorher</th><th></th></tr>" + "".join(rows) + "</table></div>")
    else:
        out.append('<p class="empty">Kein Vergleichstag im Archiv, oder keine Bewegung über acht Punkte.</p>')

    out.append("<h2>Wo die Quellen auseinanderlaufen</h2>")
    if divergences:
        rows = "".join(
            f"<tr><td>{e(d['label'])}</td><td>{e(VENUE.get(d['a']['venue'], d['a']['venue']))} {pct(d['a']['price'])}</td>"
            f"<td>{e(VENUE.get(d['b']['venue'], d['b']['venue']))} {pct(d['b']['price'])}</td>"
            f"<td class='num {'cost' if d['flag'] else ''}'>{d['gap']*100:+.0f} Pkt.</td></tr>" for d in divergences[:15])
        out.append("<div class='scroll'><table><tr><th>Frage</th><th>Quelle A</th><th>Quelle B</th>"
                   f"<th class='num'>Abstand</th></tr>{rows}</table></div>")
        out.append('<p class="note">Paare und Referenzwerte werden von Hand gepflegt. Abstand ab fünf Punkten hervorgehoben.</p>')
    else:
        out.append('<p class="empty">Noch keine gepflegten Paare mit aktuellen Daten.</p>')

    out.append("<h2>Worüber gewettet wird</h2>")
    out.append('<p class="note">Anteil am Volumen der erfassten Märkte, also der je 400 meistgehandelten pro Plattform. Nischenmärkte fehlen damit von vornherein. Die Zuordnung läuft über Schlüsselwörter und irrt im Einzelfall.</p>')
    for title, key, cls in (("Regionen", "regions", ""), ("Themen", "topics", "amber")):
        items = coverage.get(key, {})
        out.append(f"<h3>{title}</h3><div class='grid' style='gap:8px'>")
        for name, v in items.items():
            share = v.get("share_volume", 0)
            out.append(f"<div><div class='row'><span>{e(name)} <span class='meta'>· {v['n']} Märkte</span></span>"
                       f"<span class='meta'>{_de(share*100, 1)} %</span></div>"
                       f"<div class='bar {cls}'><span style='width:{max(share*100, 0.4):.1f}%'></span></div></div>")
        out.append("</div>")

    out.append("<h2>Prüfstand</h2>")
    hz = (calibration.get("horizons") or {}).get("7") or {}
    bt = hz.get("by_tier") or {}
    enough = [t for t, v in bt.items() if v["n"] >= 20]
    if len(enough) >= 2:
        out.append('<p class="note">' + term("Brier-Score", "brier") + ' je Klasse, gemessen am letzten Schnappschuss mindestens sieben Tage vor der Auflösung. Kleiner ist besser, 0,25 entspricht dem Münzwurf. Weil billige Märkte oft Außenseiter sind, steht daneben das ' + term("Mittelfeld", "mittelfeld") + ' (Preis 15 bis 85 %) gesondert.</p>')
        rows = "".join(
            f"<tr><td>{e(t)}</td><td class='num'>{v['n']}</td><td class='num'>{pct(v['mean_price'])}</td>"
            f"<td class='num'>{_de(v['brier'], 3)}</td><td class='num'>{v['n_mid']}</td>"
            f"<td class='num'>{_de(v['brier_mid'], 3) if v['brier_mid'] is not None else 'k. A.'}</td></tr>"
            for t, v in bt.items())
        out.append("<div class='scroll'><table><tr><th>Klasse</th><th class='num'>Märkte</th><th class='num'>Ø Preis</th>"
                   "<th class='num'>Brier</th><th class='num'>Mittelfeld</th><th class='num'>Brier Mittelfeld</th></tr>"
                   f"{rows}</table></div>")
    else:
        n = hz.get("n_total", 0)
        out.append(f'<p class="empty">Bisher {n} aufgelöste Märkte mit mindestens sieben Tagen Vorlauf im Archiv. Ausgewertet wird, sobald mindestens zwei Klassen je 20 Märkte haben.</p>')

    out.append(glossary_section())
    errs = stats.get("errors") or []
    out.append(f"""<footer>
<p><strong>Kurswert der Wirklichkeit</strong> ist ein nicht kommerzielles Kunstwerk (Copoiema) des Studio Bifurkation · IC, Innsbruck, über das Verhältnis von Mensch, Maschine und öffentlicher Wahrscheinlichkeit. <a href="impressum.html">Offenlegung, Datenschutz und Rechtliches</a> · <a href="https://convocare.at">convocare.at</a></p>
<p>Interlektische Copoiese: Thomas Reiner (Neugiervektor, Erdung, redaktionelle Verantwortung) mit Claude Opus 5.5 (Anthropic; Verdichtung, Code). Der Programmcode wurde mit KI erstellt; die Seite selbst wird täglich automatisch aus Marktdaten erzeugt. Kennzeichnung gemäß Art. 50 KI-Verordnung (EU) 2024/1689. Session BIF-2026-10-18-001.</p>
<p><strong>Keine Werbung, keine Empfehlung.</strong> Diese Seite bewirbt keine Wettangebote, erhält keine Vergütung und enthält keine Partnerlinks. Verweise auf Marktseiten dienen ausschließlich als Quellenangabe. Polymarket hat nach unserem Kenntnisstand keine Konzession in Österreich und ist in mehreren EU-Staaten gesperrt. Die gezeigten Quoten sind keine Prognosen des Studios und keine Anlage- oder Wettberatung. Markennamen gehören ihren Inhabern; es besteht keine Verbindung zu den Plattformen.</p>
<p>Datenquelle: öffentliche Lese-Schnittstelle von Polymarket. Veröffentlicht werden nur abgeleitete Kennzahlen, keine Orderbuch-Rohdaten.</p>
<p>Erzeugt {e(stats.get('generated'))} · {stats.get('n_markets', 0)} Märkte · Probleme {len(errs)}</p>
</footer></main>{popovers()}</body></html>""")
    return "\n".join(out)


def render_legal(generated: str) -> str:
    """Offenlegung nach § 25 MedienG, Datenschutz, Rechtliches."""
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Offenlegung · Kurswert der Wirklichkeit</title>
<meta name="robots" content="noindex">
<style>{CSS}</style></head><body><main>
<div class="date"><a href="index.html" style="color:var(--amber)">← Zum Bericht</a></div>
<h1>Offenlegung, Datenschutz, Rechtliches</h1>

<h2>Offenlegung gemäß § 25 Mediengesetz</h2>
<p>Medieninhaber und redaktionell verantwortlich: Thomas Reiner, Innsbruck, Österreich.<br>
Gegenstand: nicht kommerzielles Kunst- und Forschungsprojekt des Studio Bifurkation · IC (convocare.at).<br>
Grundlegende Richtung: künstlerische und wissenschaftliche Auseinandersetzung mit Prognosemärkten, ihrer Verwundbarkeit und ihrer Rolle in der öffentlichen Meinungsbildung. Das Werk ist eine Interlektische Copoiese, entstanden in Ko-Autorschaft von Mensch und KI.</p>

<h2>Was dieses Werk ist</h2>
<p>Ein Copoiema: ein Kunstwerk, das täglich eine Messung über Prognosemärkte veröffentlicht. Es untersucht, wie belastbar Wahrscheinlichkeiten sind, die als Nachricht zitiert werden. Es ist weder ein Wettangebot noch Werbung dafür, weder Anlageberatung noch eine Aufforderung zur Teilnahme. Das Studio verfolgt keinen Gewinnzweck, erhält keine Vergütung von Plattformen und setzt keine Partnerlinks.</p>
<p>Die Teilnahme an Prognosemärkten ist mit dem Risiko des Totalverlusts verbunden. Polymarket verfügt nach unserem Kenntnisstand über keine Konzession nach österreichischem Glücksspiel- oder Wettrecht und ist in mehreren EU-Staaten gesperrt. Wir raten von der Teilnahme ab.</p>

<h2>Daten und Rechte Dritter</h2>
<p>Die Marktdaten stammen aus der öffentlichen, dokumentierten Lese-Schnittstelle von Polymarket. Veröffentlicht werden abgeleitete Kennzahlen (Preis, Volumen, Kapitalbedarf für eine Verschiebung um zehn Punkte) und die Fragetexte der Märkte als Zitat. Rohdaten der Orderbücher werden nicht veröffentlicht. Rechte an den Daten verbleiben bei ihren Inhabern; diese Seite räumt daran keine Lizenz ein. Kalshi wurde nach Prüfung der Nutzungsbedingungen am 18.10.2026 aus dem Werk entfernt.</p>
<p>Rechteinhaber, die eine Darstellung beanstanden, erreichen uns über <a href="https://convocare.at">convocare.at</a>. Wir prüfen jede Beanstandung umgehend und entfernen Inhalte im Zweifel.</p>

<h2>Datenschutz</h2>
<p>Diese Seite setzt keine Cookies, verwendet keine Analysewerkzeuge, lädt keine externen Schriften und erhebt selbst keine personenbezogenen Daten. Gehostet wird sie bei GitHub Pages (GitHub, Inc., USA). GitHub verarbeitet beim Aufruf technisch notwendige Verbindungsdaten wie die IP-Adresse; Einzelheiten in der <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement">Datenschutzerklärung von GitHub</a>.</p>
<p>Marktfragen nennen mitunter Personen des öffentlichen Lebens. Das Werk gibt diese Fragen als Zitat wieder und trifft keine eigenen Aussagen über die genannten Personen.</p>

<h2>Künstliche Intelligenz</h2>
<p>Konzept, Methode und Programmcode entstanden in Ko-Autorschaft von Thomas Reiner und Claude Opus 5.5 (Anthropic). Ein weiteres KI-Modell hat Code und Methodik unabhängig geprüft. Die tägliche Seite wird ohne KI aus Daten erzeugt; die redaktionelle Verantwortung liegt beim Medieninhaber. Kennzeichnung gemäß Art. 50 KI-Verordnung (EU) 2024/1689.</p>

<h2>Lizenzen</h2>
<p>Programmcode: MIT-Lizenz. Texte und eigene Kennzahlen: CC BY 4.0. Daten und Fragetexte Dritter sind von diesen Lizenzen ausgenommen.</p>
<p class="note">Stand {e(generated)}</p>
</main></body></html>"""
