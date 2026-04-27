"""Day 3 smoke driver: fetch first 100 awards for the universe, parse 4-field,
measure publish-lag distribution. Idempotent + atomic-writes via manifests.

Run:
    python -m usaspending_contract_llm.day3_smoke
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from .manifest import DATA_DIR, append_jsonl, write_json
from .parse import parse_page, yield_pct
from .publish_lag import LagDistribution, measure_page
from .usaspending_client import FetchSpec, UsaSpendingClient


async def fetch_first_100() -> list[dict]:
    """Fetch one page of 100 from FY2024 defense/IT NAICS subset.

    Universe filter is implicit in the NAICS prefix list (set in FetchSpec).
    """
    spec = FetchSpec(fiscal_year=2024, limit_per_page=100)
    async with UsaSpendingClient(max_concurrent=2) as c:
        resp = await c.search_spending_by_award(spec, page=1)
    return resp.get("results", [])


def main() -> int:
    rows = asyncio.run(fetch_first_100())
    n_raw = len(rows)
    if n_raw == 0:
        print("FETCH FAIL: 0 raw rows from /search/spending_by_award/")
        return 1

    # Stamp every fetched row in manifest_usaspending_fetch (resumability).
    for r in rows:
        append_jsonl("fetch", {
            "generated_internal_id": r.get("generated_internal_id"),
            "Award ID": r.get("Award ID"),
            "Recipient Name": r.get("Recipient Name"),
            "Recipient UEI": r.get("Recipient UEI"),
            "Award Amount": r.get("Award Amount"),
            "fy": 2024,
        })

    # Parse 4-field
    parsed, skipped = parse_page(rows, log_to_manifest=True)
    yp = yield_pct(parsed, skipped)

    # Publish-lag measurement
    dist = measure_page(rows, log_to_manifest=True)

    # Recipient ticker mapping yield (Layer 1 only on this batch -- we don't
    # invoke layers 2-4 here to keep the smoke test fast and deterministic).
    from .recipient_map import map_recipient
    map_results = []
    for r in rows:
        mr = map_recipient(
            uei=r.get("Recipient UEI") or "",
            name=r.get("Recipient Name") or "",
            log_to_manifest=False,
        )
        map_results.append(mr)
    n_mapped = sum(1 for m in map_results if m.ticker)
    map_yield = round(100 * n_mapped / n_raw, 1) if n_raw else 0.0

    summary = {
        "n_raw_fetched": n_raw,
        "n_parsed": len(parsed),
        "n_skipped": skipped,
        "parse_yield_pct": yp,
        "publish_lag": {
            "n_with_lag": dist.n_with_lag,
            "lt_24h_fraction": round(dist.lt_24h_fraction(), 3),
            "lt_7d_fraction":  round(dist.lt_7d_fraction(), 3),
            "bin_counts": dist.bin_counts,
            "bin_fractions": dist.fractions(),
        },
        "mapping": {
            "n_mapped": n_mapped,
            "map_yield_pct": map_yield,
        },
        "phase0_trigger_check": {
            "trigger_2_n10_pipeline": "not yet measured (Day 5-7)",
            "trigger_6_publish_lag_distribution": "FIRST MEASUREMENT" if dist.n_with_lag > 0 else "MISSING",
        },
    }

    write_json("dryrun_n10", summary)  # ad-hoc reuse for Day 3 smoke summary
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
