"""Day-5 cohort-stratified publish-lag re-measurement.

The Day-3 publish-lag-v2 sample (n=20, sort=Last-Modified-desc) was biased
toward currently-flowing modifications and gave <24h fraction = 0.75.

Day 5 adds 3 cohort buckets (2014, 2018, 2024) to test whether:
  (a) the <24h fraction is contemporary-only (industry pickup window real for
      currently-flowing modifications, but historical records have huge lag
      because Last Modified is just an ETL refresh), or
  (b) the <24h fraction holds across cohorts (industry pickup-window thesis
      confirmed at scale).

Phase 1 trigger #2a binding evaluation (Day 16) needs cohort-stratified data.

Run:
    python -m usaspending_contract_llm.cohort_lag
"""
from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from pathlib import Path

from .manifest import DATA_DIR
from .publish_lag import LagDistribution, measure_lag_from_transaction
from .usaspending_client import FetchSpec, UsaSpendingClient

COHORTS = (
    ("2014", "2013-10-01", "2014-09-30"),
    ("2018", "2017-10-01", "2018-09-30"),
    ("2024", "2023-10-01", "2024-09-30"),
)


async def measure_cohort(
    *,
    label: str,
    start: str,
    end: str,
    n: int = 20,
) -> dict:
    spec = FetchSpec(fiscal_year=int(label), limit_per_page=n)
    async with UsaSpendingClient(max_concurrent=3) as c:
        page = await c.search_spending_by_award(
            spec, page=1, start_date=start, end_date=end,
        )
        rows: list[dict] = page.get("results", [])[:n]
        if not rows:
            return {"label": label, "n_sampled": 0, "n_with_lag": 0,
                    "lt_24h_fraction": 0.0, "bin_fractions": {}}
        tasks = [c.fetch_award_transactions(r["generated_internal_id"], limit=5) for r in rows]
        tx_responses: list[Any] = await asyncio.gather(*tasks, return_exceptions=True)
    dist = LagDistribution()
    for award_row, tx_resp in zip(rows, tx_responses):
        if isinstance(tx_resp, Exception):
            continue
        results = tx_resp.get("results", []) if isinstance(tx_resp, dict) else []
        if not results:
            continue
        m = measure_lag_from_transaction(
            award_row=award_row, most_recent_transaction=results[0],
        )
        dist.add(m)
    return {
        "label": label,
        "window": [start, end],
        "n_sampled": len(rows),
        "n_with_lag": dist.n_with_lag,
        "lt_24h_fraction": round(dist.lt_24h_fraction(), 4),
        "lt_7d_fraction":  round(dist.lt_7d_fraction(), 4),
        "bin_counts": dist.bin_counts,
        "bin_fractions": dist.fractions(),
    }


async def measure_all_cohorts(n_per_cohort: int = 20) -> dict:
    results = []
    for label, start, end in COHORTS:
        r = await measure_cohort(label=label, start=start, end=end, n=n_per_cohort)
        results.append(r)
    return {
        "n_per_cohort": n_per_cohort,
        "cohorts": results,
        "comment": "Phase 1 trigger #2a uses lt_24h_fraction across cohorts.",
    }


def main() -> int:
    out = asyncio.run(measure_all_cohorts(n_per_cohort=20))
    out_path: Path = DATA_DIR / "cohort_lag_v1.json"
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
