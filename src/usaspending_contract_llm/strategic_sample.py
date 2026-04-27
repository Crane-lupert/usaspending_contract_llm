"""Day-8 strategic sample expansion (Phase 1 entry).

Fetch contracts for the 39-firm universe across stratified cohorts:
  IS 2010-2020 / OOS 2021-2026  -> sampled via fiscal-year cohort buckets.
We use 5 cohort years (2010, 2014, 2018, 2022, 2024) as anchors and pull
~25-40 contracts per (prime x cohort) pair via recipient_search_text.

Output: data/manifest_strategic_sample.jsonl, one row per contract.

Scope discipline (Phase 1 budget = $25 cap for LLM batch in Day 9-10):
  - This module only does the FETCH (free API).
  - Day 9 LLM-classify a *subsample* of these (cost-budgeted).
  - Phase plan §4.5.1 effective-n: cross-section quintile-month observations
    are the binding power dimension, not raw event count.

Idempotency:
  - Each (prime, fy, page) triple gets one append; re-runs are append-only.
  - The Day-9 LLM batch dedups by request_id (sha256(model + prompt + cid)).
"""
from __future__ import annotations

import asyncio
import csv
import json
import sys
from pathlib import Path
from typing import Any

from .manifest import DATA_DIR
from .parse import parse_award_row
from .universe import lookup_ticker
from .usaspending_client import FetchSpec, UsaSpendingClient

UNIVERSE_CSV = DATA_DIR / "universe_defense_it_r1000_fy2024.csv"
STRATEGIC_MANIFEST = DATA_DIR / "manifest_strategic_sample.jsonl"

# Cohort buckets — anchor years across IS (2010-2020) + OOS (2021-2026).
# Each FY = 12-month window starting Oct-1 of the prior calendar year.
COHORT_FYS = (2010, 2014, 2018, 2022, 2024)


def load_universe_with_ticker() -> list[tuple[str, str]]:
    out = []
    with UNIVERSE_CSV.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            t = (r.get("ticker") or "").strip()
            if t:
                out.append((r["canonical"], t))
    # Dedup by ticker (universe.csv may have multiple rows per ticker for sub-divisions).
    seen: dict[str, str] = {}
    for name, t in out:
        if t not in seen:
            seen[t] = name
    return [(name, t) for t, name in seen.items()]


async def fetch_prime_cohort(
    client: UsaSpendingClient,
    *,
    prime_name: str,
    fy: int,
    pages: int = 2,
    limit: int = 30,
) -> list[dict]:
    """Up to (pages * limit) contracts for one (prime, FY) pair."""
    rows: list[dict] = []
    for page in range(1, pages + 1):
        spec = FetchSpec(fiscal_year=fy, limit_per_page=limit)
        resp = await client.search_spending_by_award(
            spec, page=page, recipient_name=prime_name,
        )
        results = resp.get("results", [])
        if not results:
            break
        for r in results:
            r["_prime_canonical"] = prime_name
            r["_cohort_fy"] = fy
        rows.extend(results)
        meta = resp.get("page_metadata", {})
        if not meta.get("hasNext"):
            break
    return rows


async def fetch_all(
    *,
    cohorts: tuple[int, ...] = COHORT_FYS,
    primes_limit: int = 30,
    pages_per_pair: int = 2,
    limit_per_page: int = 30,
    max_concurrent: int = 6,
) -> dict:
    universe = load_universe_with_ticker()[:primes_limit]
    print(f"primes: {len(universe)}, cohorts: {cohorts}")
    print(f"max records = {len(universe)} x {len(cohorts)} x {pages_per_pair} x {limit_per_page} = "
          f"{len(universe) * len(cohorts) * pages_per_pair * limit_per_page}")

    all_rows: list[dict] = []
    async with UsaSpendingClient(max_concurrent=max_concurrent) as c:
        # Build all (prime, fy) tasks
        tasks = []
        labels = []
        for name, ticker in universe:
            for fy in cohorts:
                tasks.append(fetch_prime_cohort(
                    c, prime_name=name, fy=fy,
                    pages=pages_per_pair, limit=limit_per_page,
                ))
                labels.append((name, ticker, fy))
        results: list[Any] = await asyncio.gather(*tasks, return_exceptions=True)

    n_err = 0
    by_pair_count: dict[str, int] = {}
    for (name, ticker, fy), res in zip(labels, results):
        key = f"{ticker}::{fy}"
        if isinstance(res, Exception):
            n_err += 1
            by_pair_count[key] = -1
            continue
        for r in res:
            r["_prime_ticker"] = ticker
        all_rows.extend(res)
        by_pair_count[key] = len(res)

    return {
        "rows": all_rows,
        "n_pairs": len(labels),
        "n_pair_errors": n_err,
        "by_pair_count": by_pair_count,
    }


def write_strategic_manifest(rows: list[dict]) -> int:
    """Append-only write of parsed rows to manifest_strategic_sample.jsonl."""
    n_written = 0
    with STRATEGIC_MANIFEST.open("a", encoding="utf-8") as fh:
        for r in rows:
            p = parse_award_row(r)
            if p is None:
                continue
            row = p.to_row()
            row["_prime_ticker"] = r.get("_prime_ticker") or ""
            row["_prime_canonical"] = r.get("_prime_canonical") or ""
            row["_cohort_fy"] = r.get("_cohort_fy")
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            n_written += 1
    return n_written


def main() -> int:
    # Reset the manifest at the start of each run -- this is idempotent
    # by external-system-state but for re-runs with different cohort sets
    # we want clean state.
    STRATEGIC_MANIFEST.write_text("", encoding="utf-8")

    out = asyncio.run(fetch_all(
        cohorts=COHORT_FYS,
        primes_limit=30,
        pages_per_pair=2,
        limit_per_page=30,
        max_concurrent=6,
    ))
    rows = out["rows"]
    n_written = write_strategic_manifest(rows)

    # Per-cohort and per-ticker counts for inspection
    per_cohort: dict[int, int] = {}
    per_ticker: dict[str, int] = {}
    for r in rows:
        per_cohort[r["_cohort_fy"]] = per_cohort.get(r["_cohort_fy"], 0) + 1
        per_ticker[r["_prime_ticker"]] = per_ticker.get(r["_prime_ticker"], 0) + 1

    summary = {
        "n_pair_attempted": out["n_pairs"],
        "n_pair_errors":    out["n_pair_errors"],
        "n_raw_rows":       len(rows),
        "n_parsed_written": n_written,
        "manifest_path":    str(STRATEGIC_MANIFEST),
        "per_cohort":       per_cohort,
        "per_ticker_top10": dict(sorted(per_ticker.items(), key=lambda kv: -kv[1])[:10]),
    }
    (DATA_DIR / "strategic_sample_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
