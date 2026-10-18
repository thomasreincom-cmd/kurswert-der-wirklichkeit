"""Sammler für Polymarket und Kalshi (öffentliche, unauthentifizierte Lese-APIs).

API-Stand geprüft am 2026-10-18 gegen docs.polymarket.com und docs.kalshi.com.
Nicht live verifiziert (Werkstatt ohne Zugang); der erste Lauf in der
GitHub Action ist der Härtetest. Jede Übersprungene Einheit wird gezählt,
damit ein Formatwechsel nicht still einen leeren Bericht erzeugt.
"""

from __future__ import annotations

import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Optional

import requests

from .metrics import Level, OrderBook, cost_to_move

log = logging.getLogger("kdw.collect")

POLY_GAMMA = "https://gamma-api.polymarket.com"
POLY_CLOB = "https://clob.polymarket.com"
KALSHI = "https://external-api.kalshi.com/trade-api/v2"
KALSHI_FALLBACK = "https://api.elections.kalshi.com/trade-api/v2"

UA = "kurswert-der-wirklichkeit/0.2 (+https://convocare.at; Studio Bifurkation, nicht kommerziell)"
BOOK_BAND = 0.25  # archiviertes Buch: ±25 Punkte um die Referenz
# Orderbuch-Rohdaten werden nicht archiviert, weil das Archiv öffentlich ist
# und Rohdaten-Weitergabe den Plattformbedingungen widersprechen könnte.
STORE_BOOK = False

STATS: Counter = Counter()  # wird von run.py gelesen


class Http:
    def __init__(self, min_interval: float = 0.06, retries: int = 5, timeout: float = 20):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept": "application/json"})
        self.min_interval = min_interval
        self.retries = retries
        self.timeout = timeout
        self._last = 0.0

    def request(self, method: str, url: str, **kw) -> Optional[Any]:
        for attempt in range(self.retries):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                r = self.s.request(method, url, timeout=self.timeout, **kw)
            except requests.RequestException as e:
                log.warning("Netzfehler %s (%s), Versuch %d", url, e, attempt + 1)
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 404:
                return None
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** attempt, 30))
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Aufgegeben nach {self.retries} Versuchen: {url}")

    def get(self, url: str, **params) -> Optional[Any]:
        return self.request("GET", url, params=params)


def _f(x: Any) -> Optional[float]:
    try:
        return None if x is None or x == "" else float(x)
    except (TypeError, ValueError):
        return None


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _band(book: OrderBook, ref: Optional[float]) -> dict:
    if ref is None:
        return {"bids": [], "asks": []}
    return {
        "bids": [[l.price, round(l.size, 2)] for l in book.bids if l.price >= ref - BOOK_BAND],
        "asks": [[l.price, round(l.size, 2)] for l in book.asks if l.price <= ref + BOOK_BAND],
    }


# ---------------------------------------------------------------------------
# Polymarket
# ---------------------------------------------------------------------------

def _jlist(x: Any) -> list:
    if isinstance(x, list):
        return x
    if isinstance(x, str) and x:
        try:
            v = json.loads(x)
            return v if isinstance(v, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _yes_index(outcomes: list) -> Optional[int]:
    """Index des JA-Ausgangs. Nicht-JA/NEIN-Märkte (z. B. "Over"/"Under",
    Teamnamen) werden mit Index 0 genommen, die Frage nennt den Ausgang mit."""
    if len(outcomes) != 2:
        return None
    low = [str(o).strip().lower() for o in outcomes]
    if "yes" in low:
        return low.index("yes")
    return 0


def polymarket_markets(http: Http, top_n: int) -> list[dict]:
    out: list[dict] = []
    offset, page = 0, 100
    while len(out) < top_n:
        batch = http.get(f"{POLY_GAMMA}/markets", closed="false", limit=page, offset=offset,
                         order="volume24hr", ascending="false")
        if not batch:
            break
        out.extend(batch)
        if len(batch) < page:
            break
        offset += page
    return out[:top_n]


def parse_poly_book(raw: dict) -> OrderBook:
    if raw is None or "bids" not in raw or "asks" not in raw:
        raise ValueError("Polymarket-Buch ohne bids/asks")
    return OrderBook.from_levels(
        [Level(_f(b.get("price")), _f(b.get("size"))) for b in raw["bids"]],
        [Level(_f(a.get("price")), _f(a.get("size"))) for a in raw["asks"]],
    )


def polymarket_books(http: Http, token_ids: list[str], batch: int = 200) -> dict[str, dict]:
    books: dict[str, dict] = {}
    for i in range(0, len(token_ids), batch):
        chunk = token_ids[i:i + batch]
        try:
            res = http.request("POST", f"{POLY_CLOB}/books", json=[{"token_id": t} for t in chunk])
            for b in res or []:
                books[str(b.get("asset_id"))] = b
        except Exception as e:  # noqa: BLE001
            log.warning("POST /books fehlgeschlagen (%s), hole einzeln", e)
            for t in chunk:
                b = http.get(f"{POLY_CLOB}/book", token_id=t)
                if b:
                    books[t] = b
    return books


def normalize_polymarket(m: dict, raw_book: Optional[dict], ts: str) -> Optional[dict]:
    outcomes = _jlist(m.get("outcomes"))
    tokens = _jlist(m.get("clobTokenIds"))
    prices = [_f(p) for p in _jlist(m.get("outcomePrices"))]
    yi = _yes_index(outcomes)
    if yi is None or len(tokens) != 2:
        return None  # nur binäre Märkte
    book = parse_poly_book(raw_book) if raw_book else OrderBook()
    mid = book.mid()
    # Anzeige-Regel Polymarket: Mittelkurs, solange Spread <= 0.10, sonst letzter Handel.
    if mid is not None and book.spread is not None and book.spread <= 0.10:
        shown = mid
    else:
        shown = _f((raw_book or {}).get("last_trade_price"))
        if shown is None and len(prices) == 2:
            shown = prices[yi]
    move = cost_to_move(book, 0.10, reference=shown)
    events = m.get("events") or []
    event_slug = events[0].get("slug") if events and isinstance(events[0], dict) else None
    question = m.get("question") or ""
    if str(outcomes[yi]).lower() not in ("yes", "ja"):
        question = f"{question} [{outcomes[yi]}]"
    return {
        "ts": ts, "venue": "polymarket",
        "market_id": str(m.get("conditionId") or m.get("id")),
        "token_yes": str(tokens[yi]),
        "event_id": event_slug,
        "question": question,
        "url": f"https://polymarket.com/event/{event_slug or m.get('slug') or ''}",
        "category": m.get("category"),
        "tags": [t.get("label") for t in (m.get("tags") or []) if isinstance(t, dict)],
        "end_date": m.get("endDate"),
        "price": shown,
        "mid": mid,
        "gamma_price": prices[yi] if len(prices) == 2 else None,
        "volume_total": _f(m.get("volumeNum")) or _f(m.get("volume")),   # USD
        "volume_24h": _f(m.get("volume24hr")),                           # USD
        "volume_unit": "usd",
        "liquidity": _f(m.get("liquidityNum")) or _f(m.get("liquidity")),
        "move": move.to_dict(),
        **({"book": _band(book, shown)} if STORE_BOOK else {}),
    }


def collect_polymarket(http: Http, top_n: int = 400, ai_scan: int = 2000) -> list[dict]:
    """Die top_n meistgehandelten Märkte, dazu alle KI-Märkte aus den
    ai_scan meistgehandelten (KI ist ein Schwerpunkt des Studios und fällt
    sonst fast ganz aus der Auswahl)."""
    from .analysis import is_ai
    ts = _now()
    scanned = polymarket_markets(http, max(top_n, ai_scan))
    markets = scanned[:top_n]
    seen = {m.get("conditionId") or m.get("id") for m in markets}
    extra = [m for m in scanned[top_n:]
             if is_ai({"question": m.get("question"), "tags": [t.get("label") for t in (m.get("tags") or []) if isinstance(t, dict)]})
             and (m.get("conditionId") or m.get("id")) not in seen]
    markets = markets + extra
    STATS["polymarket_listed"] += len(markets)
    STATS["polymarket_ai_extra"] += len(extra)
    want = []
    for m in markets:
        yi, toks = _yes_index(_jlist(m.get("outcomes"))), _jlist(m.get("clobTokenIds"))
        if yi is not None and len(toks) == 2:
            want.append(str(toks[yi]))
    books = polymarket_books(http, want)
    out = []
    for m in markets:
        try:
            yi, toks = _yes_index(_jlist(m.get("outcomes"))), _jlist(m.get("clobTokenIds"))
            if yi is None or len(toks) != 2:
                STATS["polymarket_not_binary"] += 1
                continue
            raw = books.get(str(toks[yi]))
            if raw is None:
                STATS["polymarket_no_book"] += 1
            rec = normalize_polymarket(m, raw, ts)
            if rec:
                out.append(rec)
        except Exception as e:  # noqa: BLE001
            STATS["polymarket_skipped"] += 1
            log.warning("Polymarket-Markt übersprungen %s: %s", m.get("slug"), e)
    return out


def polymarket_resolutions(http: Http, since_iso: str, pages: int = 20) -> list[dict]:
    out = []
    for i in range(pages):
        try:
            batch = http.get(f"{POLY_GAMMA}/markets", closed="true", limit=100, offset=i * 100,
                             end_date_min=since_iso, order="endDate", ascending="false")
        except requests.HTTPError as e:
            # Gamma begrenzt den Offset (422 ab etwa 2000); dann ist hier Schluss.
            log.info("Polymarket-Auflösungen: Ende bei Offset %d (%s)", i * 100, e)
            break
        if not batch:
            break
        for m in batch:
            outs = _jlist(m.get("outcomes"))
            prices = [_f(p) for p in _jlist(m.get("outcomePrices"))]
            yi = _yes_index(outs)
            if yi is None or len(prices) != 2 or None in prices:
                continue
            p = prices[yi]
            if p not in (0.0, 1.0):
                continue  # noch nicht endgültig
            out.append({"venue": "polymarket", "market_id": str(m.get("conditionId") or m.get("id")),
                        "outcome": int(p), "resolved_at": m.get("closedTime") or m.get("endDate")})
        if len(batch) < 100:
            break
    return out


# ---------------------------------------------------------------------------
# Kalshi
# ---------------------------------------------------------------------------

class KalshiAPI:
    def __init__(self, http: Http):
        self.http = http
        self.base = KALSHI
        self._switched = False

    def get(self, path: str, **params):
        try:
            return self.http.get(self.base + path, **params)
        except (requests.ConnectionError, RuntimeError):
            # Nur bei Erreichbarkeitsproblemen auf den Alias wechseln, nicht bei 4xx.
            if not self._switched:
                log.warning("Kalshi-Basis %s nicht erreichbar, wechsle auf Alias", self.base)
                self.base, self._switched = KALSHI_FALLBACK, True
                return self.http.get(self.base + path, **params)
            raise


def _kprice(m: dict, new: str, old: str) -> Optional[float]:
    v = _f(m.get(new))
    if v is not None:
        return v
    v = _f(m.get(old))
    if v is None:
        return None
    return v / 100 if v >= 1 else v  # Altformat in Cent


def _knum(m: dict, new: str, old: str) -> Optional[float]:
    v = _f(m.get(new))
    return v if v is not None else _f(m.get(old))


def parse_kalshi_book(raw: dict) -> OrderBook:
    """Kalshi liefert nur Bids für JA und NEIN, aufsteigend. JA-Ask = 1 - NEIN-Bid."""
    if raw is None:
        raise ValueError("leeres Kalshi-Buch")
    if "orderbook_fp" in raw:
        ob = raw["orderbook_fp"] or {}
        yes, no, scale = ob.get("yes_dollars") or [], ob.get("no_dollars") or [], 1.0
    elif "orderbook" in raw:
        ob = raw["orderbook"] or {}
        yes, no, scale = ob.get("yes") or [], ob.get("no") or [], 100.0
    else:
        raise ValueError("Kalshi-Buch ohne orderbook_fp/orderbook")

    def lv(pair, invert):
        p, q = _f(pair[0]), _f(pair[1])
        if p is None or q is None:
            return Level(None, None)
        p /= scale
        return Level(1 - p if invert else p, q)

    return OrderBook.from_levels([lv(x, False) for x in yes], [lv(x, True) for x in no])


def kalshi_markets(api: KalshiAPI, top_n: int, max_pages: int = 200) -> list[dict]:
    allm: list[dict] = []
    cursor = None
    for _ in range(max_pages):
        params = {"status": "open", "limit": 1000, "mve_filter": "exclude"}
        if cursor:
            params["cursor"] = cursor
        res = api.get("/markets", **params) or {}
        allm.extend(res.get("markets") or [])
        cursor = res.get("cursor")
        if not cursor:
            break
    else:
        STATS["kalshi_listing_truncated"] += 1
        log.warning("Kalshi-Liste nach %d Seiten abgeschnitten", max_pages)
    allm.sort(key=lambda m: -(_knum(m, "volume_24h_fp", "volume_24h") or 0))
    return allm[:top_n]


def kalshi_event_meta(api: KalshiAPI, event_tickers: set[str]) -> dict[str, dict]:
    """Nur die Events, die gebraucht werden, einzeln abgefragt."""
    meta: dict[str, dict] = {}
    for et in sorted(t for t in event_tickers if t):
        try:
            res = api.get(f"/events/{et}") or {}
            e = res.get("event") or res
            meta[et] = {"title": e.get("title"), "category": e.get("category"),
                        "series_ticker": e.get("series_ticker")}
        except Exception as ex:  # noqa: BLE001
            STATS["kalshi_event_meta_failed"] += 1
            log.warning("Kalshi-Event %s: %s", et, ex)
    return meta


def normalize_kalshi(m: dict, raw_book: Optional[dict], meta: dict, ts: str) -> dict:
    book = parse_kalshi_book(raw_book) if raw_book else OrderBook()
    yb = _kprice(m, "yes_bid_dollars", "yes_bid")
    ya = _kprice(m, "yes_ask_dollars", "yes_ask")
    mid = book.mid()
    if yb is not None and ya is not None and 0 < yb < ya < 1:
        shown = (yb + ya) / 2
    else:
        shown = mid if mid is not None else _kprice(m, "last_price_dollars", "last_price")
    move = cost_to_move(book, 0.10, reference=shown)
    ev = meta.get(m.get("event_ticker"), {})
    sub = m.get("yes_sub_title") or ""
    question = ev.get("title") or m.get("title") or m.get("ticker")
    if sub and sub.lower() not in str(question).lower():
        question = f"{question}: {sub}"
    series = ev.get("series_ticker") or (m.get("event_ticker") or "").split("-")[0]
    vol_c = _knum(m, "volume_fp", "volume")
    vol24_c = _knum(m, "volume_24h_fp", "volume_24h")
    # Kalshi zählt Kontrakte (Nennwert 1 $). Dollarvolumen geschätzt mit dem
    # aktuellen Preis; ausgewiesen als Schätzung.
    px = shown if shown is not None else 0.5
    return {
        "ts": ts, "venue": "kalshi",
        "market_id": m.get("ticker"),
        "event_id": m.get("event_ticker"),
        "question": question,
        "url": f"https://kalshi.com/markets/{series.lower()}" if series else "https://kalshi.com",
        "category": ev.get("category"),
        "tags": [series] if series else [],
        "end_date": m.get("close_time"),
        "price": shown,
        "mid": mid,
        "volume_contracts": vol_c,
        "volume_24h_contracts": vol24_c,
        "volume_total": vol_c * px if vol_c is not None else None,
        "volume_24h": vol24_c * px if vol24_c is not None else None,
        "volume_unit": "usd_est",
        "open_interest": _knum(m, "open_interest_fp", "open_interest"),
        "move": move.to_dict(),
        **({"book": _band(book, shown)} if STORE_BOOK else {}),
    }


def collect_kalshi(http: Http, top_n: int = 400) -> list[dict]:
    ts = _now()
    api = KalshiAPI(http)
    markets = kalshi_markets(api, top_n)
    STATS["kalshi_listed"] += len(markets)
    meta = kalshi_event_meta(api, {m.get("event_ticker") for m in markets})
    out = []
    for m in markets:
        try:
            raw = api.get(f"/markets/{m['ticker']}/orderbook", depth=0)
            if raw is None:
                STATS["kalshi_no_book"] += 1
            out.append(normalize_kalshi(m, raw, meta, ts))
        except Exception as e:  # noqa: BLE001
            STATS["kalshi_skipped"] += 1
            log.warning("Kalshi-Markt übersprungen %s: %s", m.get("ticker"), e)
    return out


def kalshi_resolutions(http: Http, tickers: list[str], batch: int = 100) -> list[dict]:
    """Auflösungen für bereits archivierte, noch offene Ticker. So gehen auch
    spät abgerechnete Märkte nicht verloren."""
    api = KalshiAPI(http)
    out = []
    for i in range(0, len(tickers), batch):
        res = api.get("/markets", tickers=",".join(tickers[i:i + batch]), limit=batch) or {}
        for m in res.get("markets") or []:
            r = str(m.get("result") or "").lower()
            if r in ("yes", "no"):
                out.append({"venue": "kalshi", "market_id": m.get("ticker"),
                            "outcome": 1 if r == "yes" else 0,
                            "resolved_at": m.get("settlement_ts") or m.get("close_time")})
    return out
