"""Day-5 universe-filtered fetch driver.

Pulls a small sample of contracts *for each prime in the 39-firm universe*
via /search/spending_by_award/ + recipient_search_text. By construction
this gives us ticker-mappable rows (Stage D coverage by design).
"""
from __future__ import annotations

import asyncio
import csv
import json
import sys
from pathlib import Path
from typing import Any

from .manifest import DATA_DIR, append_jsonl, manifest_path
from .parse import parse_award_row
from .universe import lookup_ticker
from .usaspending_client import FetchSpec, UsaSpendingClient

UNIVERSE_CSV = DATA_DIR / "universe_defense_it_r1000_fy2024.csv"


def load_universe() -> list[tuple[str, str]]:
    """Return [(canonical_name, ticker)] for all rows in the universe CSV with a ticker."""
    out = []
    with UNIVERSE_CSV.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            t = r.get("ticker", "").strip()
            if t:
                out.append((r["canonical"], t))
    return out


async def fetch_for_prime(
    client: UsaSpendingClient,
    *,
    name: str,
    fy: int = 2024,
    limit: int = 5,
) -> list[dict]:
    """Page 1 of /search/spending_by_award/ for a single prime."""
    spec = FetchSpec(fiscal_year=fy, limit_per_page=limit)
    resp = await client.search_spending_by_award(spec, page=1, recipient_name=name)
    return resp.get("results", [])


async def fetch_universe_sample(*, fy: int = 2024, per_prime: int = 5, max_primes: int = 30) -> list[dict]:
    universe = load_universe()[:max_primes]
    print(f"Fetching {per_prime} contracts each for {len(universe)} primes (FY{fy})")
    async with UsaSpendingClient(max_concurrent=4) as c:
        tasks = [fetch_for_prime(c, name=name, fy=fy, limit=per_prime) for name, _ in universe]
        results: list[Any] = await asyncio.gather(*tasks, return_exceptions=True)
    rows: list[dict] = []
    for (name, ticker), res in zip(universe, results):
        if isinstance(res, Exception):
            continue
        for r in res:
            r["_universe_canonical"] = name
            r["_universe_ticker"] = ticker
            rows.append(r)
    return rows


def main() -> int:
    rows = asyncio.run(fetch_universe_sample(fy=2024, per_prime=5, max_primes=30))
    parsed_count = 0
    for r in rows:
        p = parse_award_row(r)
        if p is None:
            continue
        # Append to a separate manifest specific to the universe-filtered sample.
        append_jsonl_path = DATA_DIR / "manifest_parse_universe.jsonl"
        # Just write directly.
        line = json.dumps(p.to_row(), ensure_ascii=False, default=str) + "\n"
        with append_jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(line)
        parsed_count += 1
    print(json.dumps({"raw_fetched": len(rows), "parsed": parsed_count,
                      "universe_parsed_path": str(DATA_DIR / "manifest_parse_universe.jsonl")},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
