import pytest

from kdw.metrics import Level, OrderBook, cost_to_move, tier


def book(bids, asks):
    return OrderBook.from_levels([Level(p, s) for p, s in bids], [Level(p, s) for p, s in asks])


def test_normalisation_sorts_aggregates_and_drops_garbage():
    b = book([(0.40, 10), (0.45, 5), (0.45, 5), (0.0, 3), (None, 4)], [(0.60, 2), (0.50, 1), (1.0, 9)])
    assert [l.price for l in b.bids] == [0.45, 0.40]
    assert b.bids[0].size == 10
    assert [l.price for l in b.asks] == [0.50, 0.60]
    assert b.mid() == pytest.approx(0.475)


def test_symmetric_book():
    b = book([(0.49, 100), (0.45, 100), (0.40, 100)], [(0.51, 100), (0.55, 100), (0.60, 100)])
    m = cost_to_move(b, 0.10)
    assert m.status == "ok"
    assert m.cost_up == pytest.approx(0.51 * 100 + 0.55 * 100)
    assert m.cost_down == pytest.approx(0.51 * 100 + 0.55 * 100)
    assert not m.up_exhausted and not m.down_exhausted
    assert m.headline_price == pytest.approx(106.0)


def test_cheapest_direction_and_exhaustion():
    b = book([(0.49, 10000)], [(0.51, 10)])
    m = cost_to_move(b, 0.10)
    assert m.cheapest_direction == "up"
    assert m.up_exhausted and m.lower_bound_only
    assert m.headline_price == pytest.approx(5.1)


def test_wide_spread_is_no_resistance_not_zero_dollars():
    # Befund des Prüfmodells: bid .30, ask .90, letzter Handel .79 ergab früher 0 $.
    b = book([(0.30, 1000)], [(0.90, 1000)])
    m = cost_to_move(b, 0.10, reference=0.79)
    assert m.status == "ohne_widerstand"
    assert m.headline_price is None
    assert m.to_dict()["tier"] == "ohne Widerstand"


def test_gap_beyond_target_is_no_resistance():
    b = book([(0.49, 100), (0.30, 100)], [(0.51, 100), (0.75, 100)])
    m = cost_to_move(b, 0.10)
    assert m.status == "ok"  # nach oben 0.51 im Weg, nach unten 0.49
    b2 = book([(0.49, 100)], [(0.52, 100)])
    b2.asks.clear()
    assert cost_to_move(b2, 0.10).status == "leer"


def test_cap_near_edge():
    b = book([(0.94, 10)], [(0.96, 10), (0.99, 10)])
    m = cost_to_move(b, 0.10)
    assert m.up_capped
    assert m.cost_up == pytest.approx(9.6)  # Ziel 0.99, die Stufe 0.99 bleibt stehen
    assert not m.up_exhausted


def test_empty_and_one_sided_book():
    assert cost_to_move(OrderBook(), 0.10).status == "leer"
    m = cost_to_move(book([], [(0.30, 50)]), 0.10)
    assert m.status == "leer" and m.headline_price is None


def test_crossed_book_rejected():
    b = OrderBook(bids=[Level(0.60, 10)], asks=[Level(0.55, 10)])
    assert cost_to_move(b, 0.10).status == "gekreuzt"


def test_reference_outside_spread_is_clamped():
    b = book([(0.48, 100), (0.40, 100)], [(0.52, 100), (0.58, 100), (0.70, 100)])
    m = cost_to_move(b, 0.10, reference=0.20)  # unplausible Anzeige
    assert m.reference == pytest.approx(0.48)
    assert m.cost_up == pytest.approx(0.52 * 100)  # Ziel 0.58, Stufe 0.58 bleibt


def test_tier_labels():
    assert tier(500) == "Taschengeld"
    assert tier(5_000) == "Kleinwagen"
    assert tier(500_000) == "teuer"
    assert tier(None) is None


def test_invalid_delta():
    with pytest.raises(ValueError):
        cost_to_move(OrderBook(), 1.5)


def test_one_sided_at_edge_is_decided_not_empty():
    m = cost_to_move(book([(0.99, 1000)], []), 0.10)
    assert m.status == "entschieden" and m.to_dict()["tier"] is None
    m = cost_to_move(book([], [(0.001, 1000)]), 0.10)
    assert m.status == "entschieden"
