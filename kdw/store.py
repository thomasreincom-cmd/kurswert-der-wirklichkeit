"""Archiv: ein gzip-JSONL pro Tag und Art. Versioniert im Git-Repo."""

from __future__ import annotations

import gzip
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, Iterator

DATA = Path(__file__).resolve().parent.parent / "data"


def path(kind: str, day: date, root: Path = DATA) -> Path:
    return root / kind / f"{day.isoformat()}.jsonl.gz"


def write(kind: str, day: date, records: Iterable[dict], root: Path = DATA) -> Path:
    p = path(kind, day, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    return p


def read(kind: str, day: date, root: Path = DATA) -> list[dict]:
    p = path(kind, day, root)
    if not p.exists():
        return []
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def read_all(kind: str, root: Path = DATA) -> Iterator[dict]:
    d = root / kind
    if not d.exists():
        return
    for p in sorted(d.glob("*.jsonl.gz")):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def latest_before(kind: str, day: date, max_back: int = 7, root: Path = DATA) -> tuple[date | None, list[dict]]:
    for i in range(1, max_back + 1):
        d = day - timedelta(days=i)
        recs = read(kind, d, root)
        if recs:
            return d, recs
    return None, []
