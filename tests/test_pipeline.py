"""Parser und Gesamtlauf gegen Beispielantworten in der dokumentierten Form
(docs.polymarket.com, docs.kalshi.com, Stand 2026-10-18)."""

from datetime import date

import pytest

from kdw import analysis, store
from kdw.collect import normalize_kalshi, normalize_polymarket, parse_kalshi_book, parse_poly_book
from kdw.report import render

POLY_MARKET = {
    "question": "Will Flávio Bolsonaro win the 2026 Brazilian presidential election?",
    "slug": "brazil-bolsonaro", "conditionId": "0xabc", "endDate": "2026-10-25T23:00:00Z",
    "volumeNum": 184_200_000, "volume24hr": 2_100_000, "liquidityNum": 900_000,
    "outcomes": "[\"Yes\",\"No\"]", "outcomePrices": "[\"0.79\",\"0.21\"]",
    "clobTokenIds": "[\"111\",\"222\"]", "closed": False,
    "tags": [{"id": "2", "label": "Politics", "slug": "politics"}],
    "events": [{"slug": "brazil-presidential-election"}],
}
# absichtlich unsortiert, wie es live vorkommen soll
POLY_BOOK = {"market": "0xabc", "asset_id": "111", "last_trade_price": "0.79",
             "bids": [{"price": "0.70", "size": "1000"}, {"price": "0.78", "size": "5000"}],
             "asks": [{"price": "0.85", "size": "8000"}, {"price": "0.80", "size": "4000"}, {"price": "0.90", "size": "100"}]}

KALSHI_MARKET = {"ticker": "KXGERCHANCELLOR-26-MERZ", "event_ticker": "KXGERCHANCELLOR-26",
                 "yes_sub_title": "Merz out", "yes_bid_dollars": "0.1200", "yes_ask_dollars": "0.1600",
                 "volume_fp": "6000.00", "volume_24h_fp": "120.00", "close_time": "2026-12-31T23:59:00Z"}
# nur Bids, aufsteigend; bester Bid zuletzt
KALSHI_BOOK = {"orderbook_fp": {"yes_dollars": [["0.0800", "200.00"], ["0.1200", "300.00"]],
                                "no_dollars": [["0.7500", "50.00"], ["0.8400", "100.00"]]}}


def test_poly_book_sorted():
    b = parse_poly_book(POLY_BOOK)
    assert b.best_bid == 0.78 and b.best_ask == 0.80


def test_poly_normalize():
    r = normalize_polymarket(POLY_MARKET, POLY_BOOK, "2026-10-18T06:00:00Z")
    assert r["token_yes"] == "111"
    assert r["price"] == pytest.approx(0.79)
    # nach oben bis 0.89: Asks 0.80 x4000 und 0.85 x8000
    assert r["move"]["cost_up"] == pytest.approx(0.80 * 4000 + 0.85 * 8000)
    assert r["url"].endswith("brazil-presidential-election")


def test_poly_skips_non_binary():
    m = dict(POLY_MARKET, outcomes="[\"A\",\"B\",\"C\"]", clobTokenIds="[\"1\",\"2\",\"3\"]")
    assert normalize_polymarket(m, POLY_BOOK, "t") is None


def test_kalshi_book_inversion():
    b = parse_kalshi_book(KALSHI_BOOK)
    assert b.best_bid == pytest.approx(0.12)
    assert b.best_ask == pytest.approx(0.16)  # 1 - 0.84
    assert [l.price for l in b.asks] == pytest.approx([0.16, 0.25])


def test_kalshi_legacy_cents():
    b = parse_kalshi_book({"orderbook": {"yes": [[12, 300]], "no": [[84, 100]]}})
    assert b.best_bid == pytest.approx(0.12) and b.best_ask == pytest.approx(0.16)


def test_kalshi_missing_book_fails_loudly():
    with pytest.raises(ValueError):
        parse_kalshi_book({"something": {}})


def test_kalshi_normalize():
    meta = {"KXGERCHANCELLOR-26": {"title": "German Chancellor 2026", "category": "World", "series_ticker": "KXGERCHANCELLOR"}}
    r = normalize_kalshi(KALSHI_MARKET, KALSHI_BOOK, meta, "2026-10-18T06:00:00Z")
    assert r["price"] == pytest.approx(0.14)
    assert r["question"] == "German Chancellor 2026: Merz out"
    assert analysis.classify(r)[0] == "DACH"
    # nach oben bis 0.24: nur Ask 0.16 x100
    assert r["move"]["cost_up"] == pytest.approx(16.0)
    assert r["move"]["tier"] == "Taschengeld"
    # Kalshi zählt Kontrakte: Dollarvolumen ist Schätzung
    assert r["volume_unit"] == "usd_est" and r["volume_24h"] == pytest.approx(120 * 0.14)


def test_end_to_end(tmp_path):
    ts1, ts2 = "2026-10-17T06:00:00Z", "2026-10-18T06:00:00Z"
    k1 = normalize_kalshi(KALSHI_MARKET, KALSHI_BOOK, {}, ts1)
    k2 = dict(normalize_kalshi(KALSHI_MARKET, KALSHI_BOOK, {}, ts2), price=0.30, mid=0.30)
    p1 = normalize_polymarket(POLY_MARKET, POLY_BOOK, ts1)
    p2 = normalize_polymarket(POLY_MARKET, POLY_BOOK, ts2)
    store.write("snapshots", date(2026, 10, 17), [k1, p1], root=tmp_path)
    store.write("snapshots", date(2026, 10, 18), [k2, p2], root=tmp_path)
    today = store.read("snapshots", date(2026, 10, 18), root=tmp_path)
    _, yest = store.latest_before("snapshots", date(2026, 10, 18), root=tmp_path)
    ano = analysis.anomalies(today, yest)
    assert len(ano) == 1 and ano[0]["flag"] == "verwundbar"
    pairs = [{"label": "Test", "a": {"venue": "kalshi", "market_id": k2["market_id"]},
              "b": {"venue": "polymarket", "market_id": p2["market_id"]}, "invert_b": True}]
    div = analysis.divergences(today, pairs, [])
    assert div[0]["gap"] == pytest.approx(0.30 - 0.21, abs=1e-6)
    cov = analysis.coverage(today)
    assert "Lateinamerika" in cov["regions"]
    res = [{"venue": "polymarket", "market_id": "0xabc", "outcome": 1, "resolved_at": "2026-10-26T00:00:00Z"}]
    cal = analysis.calibration_by_tier(store.read_all("snapshots", root=tmp_path), res)
    assert cal["horizons"]["7"]["n_total"] == 1
    assert cal["horizons"]["7"]["by_tier"]  # Klasse vorhanden
    html = render(date(2026, 10, 18), today, ano, div, cov, cal, {"n_markets": 2})
    assert "Kurswert der Wirklichkeit" in html
    # Stilregel des Studios: kein Gedankenstrich als Einschub im Fließtext
    assert " — " not in html and " – " not in html


def test_keyword_false_positives_fixed():
    c = analysis.classify
    assert c({"question": "Will the senator from Ohio resign?"})[0] == "unklar/global"
    assert c({"question": "Who will win the Ukraine talks?"})[1] != "Gesundheit"
    assert c({"question": "Will the Miami Heat win?"})[1] != "Klima/Umwelt"
    assert c({"question": "Warriors vs. Lakers"})[1] == "Sport"
    assert c({"question": "Will Seth Rogen host?"})[1] != "Krypto"
    assert c({"question": "Will Merz remain chancellor?"}) == ("DACH", "Politik")


def test_calibration_requires_resolution_time():
    snap = {"venue": "x", "market_id": "1", "ts": "2026-10-01T00:00:00Z", "price": 0.6, "move": {"tier": "teuer"}}
    res = [{"venue": "x", "market_id": "1", "outcome": 1, "resolved_at": None}]
    assert analysis.calibration_by_tier([snap], res)["horizons"]["1"]["n_total"] == 0
    res = [{"venue": "x", "market_id": "1", "outcome": 1, "resolved_at": "2026-10-20"}]  # nur Datum
    assert analysis.calibration_by_tier([snap], res)["horizons"]["1"]["n_total"] == 1


def test_usd_format():
    from kdw.report import usd
    assert usd(1_234_567) == "1,2 Mio. $"
    assert usd(25_000) == "25 Tsd. $"
    assert usd(1_500) == "1.500 $"


def test_kalshi_series_marks_sport():
    assert analysis.is_sport({"question": "Shi vs Korneeva: Han Shi", "tags": ["KXWTAMATCH"]})
    assert analysis.is_sport({"question": "HOU Texans vs JAC Jaguars: Houston", "tags": ["KXNFLGAME"]})
    assert not analysis.is_sport({"question": "German Chancellor 2026: Merz out", "tags": ["KXGERCHANCELLOR"]})
    assert analysis.is_sport({"question": "Valorant: LOUD vs Team Vitality (BO5)", "tags": []})


def test_matchday_is_sport():
    assert analysis.is_sport({"question": "Will Paris FC win on 2026-10-18?"})


def test_ai_detection():
    assert analysis.is_ai({"question": "Will Anthropic have the best AI model at the end of October 2026?"})
    assert analysis.is_ai({"question": "OpenAI announces AGI before 2027?"})
    assert not analysis.is_ai({"question": "Will Paris FC win on 2026-10-18?"})
    assert not analysis.is_ai({"question": "Will the Fed raise rates in October?"})
