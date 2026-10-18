"""Analyseschichten über den normalisierten Tagesschnappschüssen.

Ein Datensatz (ein Markt an einem Tag) enthält u. a. ts, venue, market_id,
question, url, category, tags, price (angezeigt), mid, volume_total und
volume_24h (USD; bei Kalshi geschätzt), move (MoveCost.to_dict()).
Auflösungen: {"venue", "market_id", "outcome": 1|0, "resolved_at"}.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Iterable, Optional

from .metrics import TIER_ORDER

# ---------------------------------------------------------------------------
# Leerstellen
# ---------------------------------------------------------------------------
# Heuristik über Schlüsselwörter mit Wortgrenzen. Grob; im Bericht als solche
# ausgewiesen. Erste passende Region bzw. erstes passendes Thema gewinnt.

REGIONS: list[tuple[str, list[str]]] = [
    ("DACH", ["austria", "austrian", "österreich", "vienna", "wien", "germany", "german",
              "bundestag", "merz", "afd", "switzerland", "swiss", "bundesliga", "fpö", "kickl"]),
    ("Russland/Ukraine", ["russia", "russian", "putin", "ukraine", "ukrainian", "zelensky",
                          "kremlin", "moscow", "kyiv"]),
    ("Europa", ["europe", "european", "eu", "ecb", "france", "french", "macron", "le pen",
                "uk", "britain", "british", "starmer", "england", "scotland", "italy", "italian",
                "meloni", "spain", "spanish", "poland", "polish", "netherlands", "dutch", "sweden",
                "norway", "denmark", "finland", "hungary", "orbán", "orban", "czech", "romania",
                "greece", "portugal", "ireland", "belgium", "eurovision", "premier league",
                "la liga", "serie a", "ligue 1", "champions league", "nato"]),
    ("Naher Osten", ["israel", "israeli", "netanyahu", "gaza", "hamas", "iran", "iranian",
                     "tehran", "saudi", "syria", "lebanon", "hezbollah", "yemen", "houthi",
                     "houthis", "iraq", "qatar", "uae", "hormuz", "turkey", "erdogan"]),
    ("Lateinamerika", ["brazil", "brazilian", "lula", "bolsonaro", "argentina", "milei",
                       "mexico", "mexican", "venezuela", "maduro", "machado", "colombia",
                       "chile", "peru", "liga mx", "flamengo", "palmeiras", "fluminense",
                       "ecuador", "cuba"]),
    ("Afrika", ["africa", "african", "nigeria", "kenya", "ethiopia", "egypt", "south africa",
                "sudan", "congo", "ghana", "morocco", "algeria", "senegal", "sahel", "mali",
                "somalia"]),
    ("Asien", ["china", "chinese", "xi jinping", "taiwan", "japan", "japanese", "korea",
               "korean", "india", "modi", "pakistan", "indonesia", "philippines", "vietnam",
               "thailand", "bangladesh", "hong kong", "singapore", "malaysia"]),
    ("Ozeanien", ["australia", "australian", "new zealand"]),
    ("Nordamerika", ["trump", "biden", "harris", "vance", "us", "u.s.", "usa", "united states",
                     "america", "american", "congress", "senate", "house", "fed", "federal reserve",
                     "fomc", "powell", "warsh", "supreme court", "midterm", "midterms", "governor",
                     "nfl", "nba", "mlb", "nhl", "ncaa", "super bowl", "world series", "canada",
                     "carney", "texas", "california", "new york", "cpi", "s&p", "nasdaq", "tesla",
                     "spacex", "musk", "democrats", "republicans"]),
]

TOPICS: list[tuple[str, list[str]]] = [
    ("Krieg/Konflikt", ["war", "ceasefire", "invade", "invasion", "airstrike", "missile",
                        "military", "troops", "nuclear weapon", "sanctions", "drone strike"]),
    ("Klima/Umwelt", ["climate", "global temperature", "hurricane", "emissions", "co2", "carbon",
                      "warming", "heatwave", "flood", "drought", "wildfire", "sea level",
                      "el niño", "la niña", "rainfall", "snowfall", "earthquake", "landfall"]),
    ("Gesundheit", ["pandemic", "covid", "virus", "measles", "bird flu", "h5n1", "vaccine",
                    "outbreak", "disease", "fda", "who declares"]),
    ("Krypto", ["bitcoin", "btc", "ethereum", "eth", "solana", "crypto", "hyperliquid",
                "doge", "dogecoin", "xrp", "stablecoin", "memecoin"]),
    ("KI/Tech", ["ai", "a.i.", "openai", "anthropic", "gemini", "gpt", "claude", "llm",
                 "nvidia", "apple", "google", "microsoft", "meta", "ipo", "chip", "chips"]),
    ("Sport", ["sports", "esports", "nfl", "nba", "mlb", "nhl", "ncaa", "soccer", "football", "premier league",
               "valorant", "counter-strike", "cs2", "league of legends", "dota", "o/u", "spread",
               "atp", "wta", "uefa", "fifa", "mls", "wnba", "pga", "lpga", "nascar", "game 1", "game 2",
               "game 3", "game 4", "game 5", "game 6", "game 7",
               "championship", "champion", "tennis", "golf", "f1", "formula 1", "ufc",
               "boxing", "olympics", "grand prix", "world series", "super bowl", "vs", "vs."]),
    ("Wirtschaft", ["fed", "interest rate", "rates", "inflation", "cpi", "gdp", "recession",
                    "unemployment", "tariff", "tariffs", "stock", "s&p", "nasdaq", "oil",
                    "gold", "market cap", "largest company", "earnings"]),
    ("Politik", ["election", "president", "presidential", "prime minister", "chancellor",
                 "senate", "house", "parliament", "vote", "referendum", "governor", "mayor",
                 "minister", "party", "nominee", "out by", "resign", "impeach", "coalition",
                 "midterm", "midterms"]),
    ("Kultur", ["oscar", "oscars", "grammy", "grammys", "emmy", "eurovision", "album", "movie",
                "box office", "billboard", "spotify", "netflix", "tweet", "tweets", "youtube",
                "tiktok", "nobel"]),
]


def _compile(table):
    return [(name, re.compile(r"(?<![\w])(?:" + "|".join(re.escape(k) for k in kws) + r")(?![\w])"))
            for name, kws in table]


_REG = _compile(REGIONS)
_TOP = _compile(TOPICS)


def _haystack(rec: dict) -> str:
    parts = [rec.get("question") or "", rec.get("category") or ""] + [str(t) for t in (rec.get("tags") or [])]
    return " ".join(parts).lower()


# Kalshi-Serienkürzel (z. B. KXNFLGAME, KXWTAMATCH) verraten den Sport
_KALSHI_SPORT = re.compile(r"^KX(NFL|NBA|WNBA|MLB|NHL|NCAA|CFB|CBB|WTA|ATP|EPL|UCL|UEL|MLS|UFC|F1|PGA|LPGA|"
                           r"NASCAR|LALIGA|SERIEA|BUNDESLIGA|LIGUE1|BOX|MMA|CS2|LOL|VALORANT|DOTA|SOCCER|TENNIS|"
                           r"GOLF|CRICKET|IPL|AFL|NRL|EUROLEAGUE|KBO|NPB)|(MATCH|GAME|SPREAD)$")


# Polymarket-Spieltagsmärkte: "Will Paris FC win on 2026-10-18?"
_MATCHDAY = re.compile(r"\bwin on \d{4}-\d{2}-\d{2}\b|\b(fc|sc|cf|afc)\b")


def classify(rec: dict) -> tuple[str, str]:
    h = _haystack(rec)
    region = next((n for n, rx in _REG if rx.search(h)), "unklar/global")
    if any(_KALSHI_SPORT.search(str(t).upper()) for t in (rec.get("tags") or [])):
        return region, "Sport"
    if _MATCHDAY.search(h):
        return region, "Sport"
    topic = next((n for n, rx in _TOP if rx.search(h)), "Sonstiges")
    return region, topic


_AI = re.compile(r"(?<![\w])(ai|a\.i\.|agi|asi|artificial intelligence|artificial general intelligence|"
                 r"superintelligence|openai|anthropic|claude|gemini|chatgpt|gpt-?\d*|grok|xai|deepmind|"
                 r"llm|llms|large language model|ai model|frontier model|mistral|deepseek|llama|"
                 r"sam altman|dario amodei|demis hassabis|ai safety|ai act|humanoid robot|"
                 r"robotaxi|turing test|arc-agi|imo gold|benchmark)(?![\w])", re.I)


def is_ai(rec: dict) -> bool:
    """Märkte zu künstlicher Intelligenz: Modelle, Firmen, AGI, Regulierung."""
    h = " ".join([rec.get("question") or ""] + [str(t) for t in (rec.get("tags") or [])])
    return bool(_AI.search(h))


def is_sport(rec: dict) -> bool:
    return classify(rec)[1] == "Sport"


def coverage(records: Iterable[dict]) -> dict:
    """Anzahl Märkte und (USD-)Volumen je Region und Thema."""
    def bucket():
        return {"n": 0, "volume_24h": 0.0, "volume_total": 0.0}
    by_region: dict[str, dict] = defaultdict(bucket)
    by_topic: dict[str, dict] = defaultdict(bucket)
    total = 0.0
    for r in records:
        reg, top = classify(r)
        v24, vt = float(r.get("volume_24h") or 0), float(r.get("volume_total") or 0)
        for b, k in ((by_region, reg), (by_topic, top)):
            b[k]["n"] += 1
            b[k]["volume_24h"] += v24
            b[k]["volume_total"] += vt
        total += vt

    def share(d):
        return {k: {**v, "share_volume": v["volume_total"] / total if total else 0.0}
                for k, v in sorted(d.items(), key=lambda kv: -kv[1]["volume_total"])}
    return {"regions": share(by_region), "topics": share(by_topic), "total_volume": total}


# ---------------------------------------------------------------------------
# Divergenz
# ---------------------------------------------------------------------------

def divergences(records: Iterable[dict], pairs: list[dict], references: list[dict],
                threshold: float = 0.05) -> list[dict]:
    idx = {(r["venue"], str(r["market_id"])): r for r in records}
    out = []
    for p in pairs:
        ra = idx.get((p["a"]["venue"], str(p["a"]["market_id"])))
        rb = idx.get((p["b"]["venue"], str(p["b"]["market_id"])))
        if not ra or not rb or ra.get("price") is None or rb.get("price") is None:
            continue
        pb = 1 - rb["price"] if p.get("invert_b") else rb["price"]
        gap = ra["price"] - pb
        out.append({"kind": "markt_vs_markt", "label": p["label"],
                    "a": {"venue": ra["venue"], "price": ra["price"], "tier": ra["move"].get("tier")},
                    "b": {"venue": rb["venue"], "price": pb, "tier": rb["move"].get("tier")},
                    "gap": round(gap, 4), "flag": abs(gap) >= threshold})
    for ref in references:
        r = idx.get((ref["market"]["venue"], str(ref["market"]["market_id"])))
        if not r or r.get("price") is None:
            continue
        gap = r["price"] - float(ref["value"])
        out.append({"kind": "markt_vs_referenz", "label": ref["label"],
                    "a": {"venue": r["venue"], "price": r["price"], "tier": r["move"].get("tier")},
                    "b": {"venue": ref.get("source", "Referenz"), "price": float(ref["value"]),
                          "date": ref.get("date")},
                    "gap": round(gap, 4), "flag": abs(gap) >= threshold})
    out.sort(key=lambda d: -abs(d["gap"]))
    return out


# ---------------------------------------------------------------------------
# Bewegungen
# ---------------------------------------------------------------------------

def _level(r: dict) -> Optional[float]:
    """Für Vergleiche über Tage der Mittelkurs, sonst der angezeigte Preis.
    So erzeugt der Wechsel der Anzeige-Regel keine Scheinbewegung."""
    return r.get("mid") if r.get("mid") is not None else r.get("price")


def anomalies(today: Iterable[dict], before: Iterable[dict], min_move: float = 0.08) -> list[dict]:
    """Märkte mit mindestens `min_move` Bewegung gegenüber dem Vergleichstag.
    `flag = "verwundbar"`, wenn der Markt am Vergleichstag ohne Widerstand
    oder unter 10.000 $ verschiebbar war. Das zeigt Verwundbarkeit, nicht
    Manipulation: echte Information bewegt dünne Märkte genauso.
    """
    prev = {(r["venue"], str(r["market_id"])): r for r in before}
    out = []
    for r in today:
        p = prev.get((r["venue"], str(r["market_id"])))
        if not p:
            continue
        a, b = _level(p), _level(r)
        if a is None or b is None or abs(b - a) < min_move:
            continue
        mv = p.get("move") or {}
        hp = mv.get("headline_price")
        weak = mv.get("tier") == "ohne Widerstand" or (hp is not None and hp < 10_000)
        out.append({"venue": r["venue"], "market_id": r["market_id"], "question": r.get("question"),
                    "url": r.get("url"), "from": a, "to": b, "change": round(b - a, 4),
                    "tier_before": mv.get("tier"), "headline_price_before": hp,
                    "flag": "verwundbar" if weak else "beobachten"})
    # verwundbare zuerst, dann nach Größe der Bewegung
    out.sort(key=lambda d: (d["flag"] != "verwundbar", -abs(d["change"])))
    return out


# ---------------------------------------------------------------------------
# Kalibrierung
# ---------------------------------------------------------------------------

def _parse_ts(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        if isinstance(s, (int, float)):
            return datetime.fromtimestamp(float(s), tz=timezone.utc)
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, OSError):
        return None


def brier(p: float, outcome: int) -> float:
    return (p - outcome) ** 2


def calibration_by_tier(snapshots: Iterable[dict], resolutions: Iterable[dict],
                        horizons: tuple[int, ...] = (1, 7)) -> dict:
    """Brier-Score je Schlagzeilen-Klasse, für feste Vorlaufzeiten.

    Für jede Vorlaufzeit h wird je Markt der letzte Schnappschuss genommen,
    der mindestens h Tage vor der Auflösung lag. Märkte ohne gültigen
    Auflösungszeitpunkt fallen heraus (kein Blick in die Zukunft).

    Weil Klasse und Preisniveau zusammenhängen (Außenseiter sind billig zu
    bewegen und auch der Brier-Score hängt vom Niveau ab), wird zusätzlich
    nur das Mittelfeld 0.15 bis 0.85 ausgewertet und je Klasse der mittlere
    Preis berichtet.
    """
    snaps = list(snapshots)
    res = {}
    for r in resolutions:
        t = _parse_ts(r.get("resolved_at"))
        if t is not None:
            res[(r["venue"], str(r["market_id"]))] = (t, int(r["outcome"]))

    result: dict = {"horizons": {}}
    for h in horizons:
        best: dict[tuple, tuple[datetime, dict]] = {}
        for s in snaps:
            key = (s["venue"], str(s["market_id"]))
            if key not in res or s.get("price") is None:
                continue
            ts = _parse_ts(s.get("ts"))
            if ts is None or ts > res[key][0] - timedelta(days=h):
                continue
            if key not in best or ts > best[key][0]:
                best[key] = (ts, s)
        groups: dict[str, dict[str, list]] = defaultdict(lambda: {"all": [], "mid": [], "p": []})
        curve: dict[int, list] = defaultdict(list)
        for key, (_, s) in best.items():
            p, o = float(s["price"]), res[key][1]
            t = (s.get("move") or {}).get("tier") or "unbekannt"
            g = groups[t]
            g["all"].append(brier(p, o))
            g["p"].append(p)
            if 0.15 <= p <= 0.85:
                g["mid"].append(brier(p, o))
            curve[min(int(p * 10), 9)].append((p, o))
        order = TIER_ORDER + ["unbekannt"]
        result["horizons"][str(h)] = {
            "by_tier": {t: {"n": len(groups[t]["all"]),
                            "brier": round(mean(groups[t]["all"]), 4),
                            "mean_price": round(mean(groups[t]["p"]), 3),
                            "n_mid": len(groups[t]["mid"]),
                            "brier_mid": round(mean(groups[t]["mid"]), 4) if groups[t]["mid"] else None}
                        for t in order if t in groups},
            "curve": [{"bin": f"{b/10:.1f}-{(b+1)/10:.1f}", "n": len(v),
                       "mean_forecast": round(mean(x for x, _ in v), 3),
                       "observed": round(mean(o for _, o in v), 3)} for b, v in sorted(curve.items())],
            "n_total": len(best),
        }
    result["n_resolved"] = len(res)
    return result
