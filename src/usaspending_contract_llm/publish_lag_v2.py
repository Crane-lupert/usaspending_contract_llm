"""Publish-lag v2 — per-transaction action_date based.

Day 3 measurement: for n=20 sample of recently-modified awards, fetch their
transactions, take the most recent transaction's action_date, compute lag
against the award's Last Modified Date.

This is the correct measurement for Phase 0 trigger #6 + Phase 1 trigger #2.
"""
from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from .manifest import append_jsonl, write_json
from .publish_lag import LagDistribution, measure_lag_from_transaction
from .usaspending_client import FetchSpec, UsaSpendingClient


async def measure_publish_lag_v2(*, n: int = 20, fy: int = 2024) -> dict:
    """Fetch n awards, then their transactions, then compute true publish lag.

    Cost: 1 search call + n transaction calls. With n=20, ~21 calls total.
    """
    spec = FetchSpec(fiscal_year=fy, limit_per_page=n)
    async with UsaSpendingClient(max_concurrent=3) as c:
        page = await c.search_spending_by_award(spec, page=1)
        rows: list[dict] = page.get("results", [])[:n]

        # Fetch transactions in parallel (asyncio.gather)
        tasks = [
            c.fetch_award_transactions(r["generated_internal_id"], limit=5)
            for r in rows
            if r.get("generated_internal_id")
        ]
        tx_responses: list[Any] = await asyncio.gather(*tasks, return_exceptions=True)

    dist = LagDistribution()
    measurements: list[dict] = []
    n_no_tx = 0
    n_tx_fetch_error = 0

    for award_row, tx_resp in zip(rows, tx_responses):
        if isinstance(tx_resp, Exception):
            n_tx_fetch_error += 1
            continue
        results = tx_resp.get("results", []) if isinstance(tx_resp, dict) else []
        if not results:
            n_no_tx += 1
            continue
        most_recent = results[0]  # already sorted desc by action_date
        m = measure_lag_from_transaction(
            award_row=award_row,
            most_recent_transaction=most_recent,
        )
        dist.add(m)
        row = m.to_row()
        row["modification_number"] = most_recent.get("modification_number")
        row["action_type"] = most_recent.get("action_type")
        measurements.append(row)
        append_jsonl("publish_lag", row)

    return {
        "n_sampled":             len(rows),
        "n_no_transactions":     n_no_tx,
        "n_tx_fetch_error":      n_tx_fetch_error,
        "n_with_lag":            dist.n_with_lag,
        "lt_24h_fraction":       round(dist.lt_24h_fraction(), 4),
        "lt_7d_fraction":        round(dist.lt_7d_fraction(), 4),
        "bin_counts":            dist.bin_counts,
        "bin_fractions":         dist.fractions(),
        "trigger_2a_threshold":  0.50,
        "trigger_2a_fired":      dist.lt_24h_fraction() >= 0.50,
        "measurements":          measurements,
    }


def main() -> int:
    out = asyncio.run(measure_publish_lag_v2(n=20))
    write_json("publish_lag", {"day3_v2_sample": {k: v for k, v in out.items() if k != "measurements"}})
    print(json.dumps({k: v for k, v in out.items() if k != "measurements"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
