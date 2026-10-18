"""Tageslauf: sammeln, archivieren, auswerten, Bericht schreiben.

    python -m kdw.run                 # voller Lauf
    python -m kdw.run --report-only   # nur Bericht aus vorhandenem Archiv
    python -m kdw.run --top 200       # weniger Märkte je Plattform

Rückgabe 1 (Action wird rot), wenn heute keine Daten kamen oder mehr als
20 % der Märkte ohne Buch blieben oder übersprungen wurden.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import analysis, store
from .report import render, render_legal

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
MAX_BAD_SHARE = 0.20
ENABLE_KALSHI = False


def load_json(name: str) -> list:
    p = ROOT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def unresolved_kalshi_tickers(day: date, lookback: int = 60) -> list[str]:
    """Archivierte Kalshi-Ticker mit Schlusszeit in der Vergangenheit, die
    noch keine Auflösung haben."""
    resolved = {r["market_id"] for r in store.read_all("resolutions") if r.get("venue") == "kalshi"}
    now = datetime.now(timezone.utc)
    seen: set[str] = set()
    for i in range(lookback):
        for r in store.read("snapshots", day - timedelta(days=i)):
            if r.get("venue") != "kalshi" or r["market_id"] in resolved:
                continue
            end = analysis._parse_ts(r.get("end_date"))
            if end is not None and end < now:
                seen.add(r["market_id"])
    return sorted(seen)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=400)
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--day", type=str, default=None)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("kdw")
    day = date.fromisoformat(args.day) if args.day else datetime.now(timezone.utc).date()
    errors: list[str] = []
    counters: dict = {}

    if not args.report_only:
        from .collect import (STATS, Http, collect_kalshi, collect_polymarket,
                              kalshi_resolutions, polymarket_resolutions)
        http = Http()
        records = []
        # Kalshi ist seit 18.10.2026 ausgesetzt: Data Terms und Developer Agreement
        # untersagen Veröffentlichung und abgeleitete Werke ohne schriftliche
        # Genehmigung. Erst nach Genehmigung wieder aufnehmen (ENABLE_KALSHI).
        sources = [("Polymarket", collect_polymarket)]
        if ENABLE_KALSHI:
            sources.append(("Kalshi", collect_kalshi))
        for name, fn in sources:
            try:
                got = fn(http, args.top)
                log.info("%s: %d Märkte", name, len(got))
                records.extend(got)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{name}: {e}")
                log.error("%s fehlgeschlagen: %s", name, e)
        if records:
            store.write("snapshots", day, records)

        res = []
        try:
            since = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
            res.extend(polymarket_resolutions(http, since))
        except Exception as e:  # noqa: BLE001
            errors.append(f"Auflösungen Polymarket: {e}")
        try:
            if ENABLE_KALSHI:
                res.extend(kalshi_resolutions(http, unresolved_kalshi_tickers(day)))
        except Exception as e:  # noqa: BLE001
            errors.append(f"Auflösungen Kalshi: {e}")
        if res:
            store.write("resolutions", day, res)
        counters = dict(STATS)

    records = store.read("snapshots", day)
    stale_from = None
    if not records:
        stale_from, records = store.latest_before("snapshots", day, max_back=7)
        if stale_from:
            errors.append(f"Keine Daten für {day}, Bericht zeigt Stand {stale_from}")
    compare_day, before = store.latest_before("snapshots", stale_from or day)

    # Qualitätsprüfung: Märkte ohne messbares Buch oder übersprungen
    listed = counters.get("polymarket_listed", 0) + counters.get("kalshi_listed", 0)
    # Märkte ohne Buch tauchen als status "leer" in records auf; Übersprungene fehlen dort.
    bad = sum(counters.get(k, 0) for k in ("polymarket_skipped", "kalshi_skipped"))
    bad += sum(1 for r in records if (r.get("move") or {}).get("status") in ("leer", "gekreuzt"))
    measured = len(records)
    bad_share = bad / max(listed or measured, 1)
    if listed and bad_share > MAX_BAD_SHARE:
        errors.append(f"{bad_share:.0%} der Märkte ohne messbares Buch oder übersprungen")

    cov = analysis.coverage(records)
    div = analysis.divergences(records, load_json("pairs.json"), load_json("references.json"))
    ano = analysis.anomalies(records, before)
    cal = analysis.calibration_by_tier(store.read_all("snapshots"), store.read_all("resolutions"))

    stats = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "day": (stale_from or day).isoformat(),
        "stale": stale_from is not None,
        "compare_day": compare_day.isoformat() if compare_day else None,
        "n_markets": len(records),
        "n_polymarket": sum(r["venue"] == "polymarket" for r in records),
        "n_kalshi": sum(r["venue"] == "kalshi" for r in records),
        "bad_share": round(bad_share, 3),
        "errors": errors,
        "counters": counters,
    }
    SITE.mkdir(exist_ok=True)
    # Startseite = die Reise (statisch, liest summary.json); Tagesmessung = heute.html
    (SITE / "heute.html").write_text(render(stale_from or day, records, ano, div, cov, cal, stats),
                                     encoding="utf-8")
    static = Path(__file__).parent / "static"
    (SITE / "index.html").write_text((static / "reise.html").read_text(encoding="utf-8"), encoding="utf-8")
    (SITE / "ci.css").write_text((static / "ci.css").read_text(encoding="utf-8"), encoding="utf-8")
    import shutil
    shutil.copytree(static / "fonts", SITE / "fonts", dirs_exist_ok=True)
    (SITE / "impressum.html").write_text(render_legal(stats["generated"]), encoding="utf-8")
    (SITE / "summary.json").write_text(json.dumps({
        "stats": stats, "coverage": cov, "divergences": div, "anomalies": ano[:50],
        "calibration": cal,
        "markets": [{k: r.get(k) for k in ("venue", "market_id", "question", "price", "url", "volume_24h")}
                    | {"tier": r["move"].get("tier"), "headline_price": r["move"].get("headline_price"),
                       "status": r["move"].get("status"), "sport": analysis.is_sport(r),
                       "ai": analysis.is_ai(r)}
                    for r in records],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("Bericht: %s (%d Märkte, Fehler: %s)", SITE / "heute.html", len(records), errors or "keine")
    failed = (not records) or stale_from is not None or (listed and bad_share > MAX_BAD_SHARE) \
        or any(e.startswith(("Polymarket:", "Kalshi:")) for e in errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
