"""Messkern: der Preis einer Schlagzeile.

Für einen binären Markt (JA/NEIN) wird aus dem Orderbuch berechnet, wie viel
Kapital durch Käufe gebunden werden muss, um den Handelspreis um `delta`
Prozentpunkte zu verschieben.

Konventionen
------------
* Alle Preise sind Wahrscheinlichkeiten in [0, 1] aus Sicht der JA-Seite.
* `bids`: Kaufaufträge für JA, absteigend sortiert (bester zuerst).
* `asks`: Verkaufsaufträge für JA, aufsteigend sortiert (bester zuerst).
* `size` ist in Anteilen (ein Anteil zahlt bei Eintritt 1 Dollar aus).

Nach oben: alle JA-Asks zwischen Referenz und Ziel aufkaufen.
Kosten = Summe(preis * menge).
Nach unten: alle JA-Bids zwischen Referenz und Ziel bedienen, ohne Bestand
über den Kauf von NEIN zum Preis (1 - preis). Kosten = Summe((1 - preis) * menge).

Was die Zahl misst und was nicht
--------------------------------
Gemessen wird gebundenes Kapital für eine Verschiebung durch Handel, am
sichtbaren Buch zum Zeitpunkt der Abfrage. Drei Dinge misst sie nicht:

1. Kosmetische Verschiebung. Plattformen zeigen meist den Mittelkurs.
   Den kann man ohne einen einzigen Handel bewegen, indem man Aufträge in
   den Spread stellt. Ist der Spread so weit wie `delta` oder weiter, gibt
   es gegen solche Verschiebung praktisch keinen Widerstand. Diese Märkte
   werden als `status = "ohne_widerstand"` ausgewiesen statt mit einem
   Dollarbetrag.
2. Nachfüllen. Market Maker stellen nach, sobald jemand schiebt; die
   tatsächlichen Kosten können höher liegen.
3. Verlust. Wer verschiebt, hält danach Anteile, die Wert haben können.
   Einsatz ist nicht Schaden.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable, Optional

EPS = 1e-9
EDGE = 0.01  # Ziele werden auf [0.01, 0.99] gekappt
DECIDED = 0.97  # einseitiges Buch ab hier gilt als entschieden


@dataclass(frozen=True)
class Level:
    price: float  # 0..1
    size: float   # Anteile


@dataclass
class OrderBook:
    bids: list[Level] = field(default_factory=list)  # JA-Bids, absteigend
    asks: list[Level] = field(default_factory=list)  # JA-Asks, aufsteigend

    @classmethod
    def from_levels(cls, bids: Iterable[Level], asks: Iterable[Level]) -> "OrderBook":
        """Normalisiert: verwirft ungültige Stufen, aggregiert gleiche Preise,
        sortiert in die Konvention."""
        def clean(levels: Iterable[Level]) -> dict[float, float]:
            agg: dict[float, float] = {}
            for lv in levels:
                if lv.price is None or lv.size is None:
                    continue
                try:
                    p, s = round(float(lv.price), 6), float(lv.size)
                except (TypeError, ValueError):
                    continue
                if s <= 0 or not (0.0 < p < 1.0):
                    continue
                agg[p] = agg.get(p, 0.0) + s
            return agg

        b, a = clean(bids), clean(asks)
        return cls(
            bids=[Level(p, s) for p, s in sorted(b.items(), key=lambda x: -x[0])],
            asks=[Level(p, s) for p, s in sorted(a.items(), key=lambda x: x[0])],
        )

    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0].price if self.asks else None

    @property
    def spread(self) -> Optional[float]:
        if self.best_bid is None or self.best_ask is None:
            return None
        return round(self.best_ask - self.best_bid, 6)

    @property
    def crossed(self) -> bool:
        s = self.spread
        return s is not None and s <= 0

    def mid(self) -> Optional[float]:
        bb, ba = self.best_bid, self.best_ask
        if bb is not None and ba is not None:
            return (bb + ba) / 2
        return None


STATUS_TEXT = {
    "ok": "messbar",
    "ohne_widerstand": "Spread so weit, dass die angezeigte Zahl ohne Handel verschiebbar ist",
    "leer": "kein beidseitiges Orderbuch",
    "gekreuzt": "Orderbuch gekreuzt, Daten unplausibel",
    "entschieden": "Ausgang praktisch entschieden, Buch nur noch einseitig",
}


@dataclass
class MoveCost:
    reference: Optional[float]
    delta: float
    status: str                   # ok | ohne_widerstand | leer | gekreuzt
    cost_up: Optional[float]
    cost_down: Optional[float]
    up_exhausted: bool            # Buch reicht nicht bis zum Ziel: Betrag ist "mindestens"
    down_exhausted: bool
    up_capped: bool               # Ziel lag jenseits 0.99, gekappt
    down_capped: bool
    spread: Optional[float]
    depth_in_band: float          # sichtbares Kapital innerhalb ±delta

    @property
    def headline_price(self) -> Optional[float]:
        """Der billigere der beiden Wege. Nur bei status == ok."""
        if self.status != "ok":
            return None
        c = [x for x in (self.cost_up, self.cost_down) if x is not None]
        return min(c) if c else None

    @property
    def cheapest_direction(self) -> Optional[str]:
        if self.headline_price is None:
            return None
        if self.cost_down is None:
            return "up"
        if self.cost_up is None:
            return "down"
        return "up" if self.cost_up <= self.cost_down else "down"

    @property
    def lower_bound_only(self) -> bool:
        d = self.cheapest_direction
        return (d == "up" and self.up_exhausted) or (d == "down" and self.down_exhausted)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["headline_price"] = self.headline_price
        d["cheapest_direction"] = self.cheapest_direction
        d["lower_bound_only"] = self.lower_bound_only
        d["tier"] = tier(self.headline_price) if self.status == "ok" else STATUS_TIER[self.status]
        return d


def cost_to_move(book: OrderBook, delta: float = 0.10,
                 reference: Optional[float] = None) -> MoveCost:
    """Kapital, um den Handelspreis um `delta` zu verschieben.

    `reference` ist der angezeigte Preis; ohne Angabe der Mittelkurs. Liegt
    die Referenz außerhalb des Spreads, wird auf den nächsten Rand geklemmt,
    damit nicht Aufträge "zwischen" Referenz und Ziel übersehen werden.
    """
    if not 0 < delta < 1:
        raise ValueError("delta muss zwischen 0 und 1 liegen")

    spread = book.spread
    if not book.bids or not book.asks:
        # Einseitiges Buch am Rand: Ausgang praktisch entschieden, kein Messfehler.
        if (book.bids and not book.asks and book.best_bid >= DECIDED) or \
           (book.asks and not book.bids and book.best_ask <= 1 - DECIDED):
            return MoveCost(reference, delta, "entschieden", None, None, True, True, False, False, spread, 0.0)
        return MoveCost(reference, delta, "leer", None, None, True, True, False, False, spread, 0.0)
    if book.crossed:
        return MoveCost(reference, delta, "gekreuzt", None, None, True, True, False, False, spread, 0.0)

    ref = reference if reference is not None else book.mid()
    ref = min(max(ref, book.best_bid), book.best_ask)

    target_up = ref + delta
    up_capped = target_up > 1 - EDGE
    target_up = min(target_up, 1 - EDGE)
    target_down = ref - delta
    down_capped = target_down < EDGE
    target_down = max(target_down, EDGE)

    cost_up = sum(lv.price * lv.size for lv in book.asks if lv.price < target_up - EPS)
    up_exhausted = not any(lv.price >= target_up - EPS for lv in book.asks)
    cost_down = sum((1 - lv.price) * lv.size for lv in book.bids if lv.price > target_down + EPS)
    down_exhausted = not any(lv.price <= target_down + EPS for lv in book.bids)

    band = sum(lv.price * lv.size for lv in book.asks if lv.price <= ref + delta + EPS) + \
        sum((1 - lv.price) * lv.size for lv in book.bids if lv.price >= ref - delta - EPS)

    # Ohne Aufträge zwischen Referenz und Ziel kostet die Verschiebung durch
    # Handel nahezu nichts. Das ist kein "Preis von 0 $", sondern fehlender
    # Widerstand, und so wird es ausgewiesen.
    no_resistance = (spread is not None and spread >= delta - EPS) or cost_up <= EPS or cost_down <= EPS
    status = "ohne_widerstand" if no_resistance else "ok"

    return MoveCost(
        reference=round(ref, 6), delta=delta, status=status,
        cost_up=round(cost_up, 2), cost_down=round(cost_down, 2),
        up_exhausted=up_exhausted, down_exhausted=down_exhausted,
        up_capped=up_capped, down_capped=down_capped,
        spread=spread, depth_in_band=round(band, 2),
    )


TIERS = [
    (1_000, "Taschengeld"),
    (10_000, "Kleinwagen"),
    (100_000, "Eigentumswohnung"),
    (float("inf"), "teuer"),
]
TIER_ORDER = ["ohne Widerstand", "Taschengeld", "Kleinwagen", "Eigentumswohnung", "teuer"]
STATUS_TIER = {"ohne_widerstand": "ohne Widerstand", "leer": None, "gekreuzt": None, "entschieden": None}


def tier(dollars: Optional[float]) -> Optional[str]:
    if dollars is None:
        return None
    for limit, label in TIERS:
        if dollars < limit:
            return label
    return TIERS[-1][1]
