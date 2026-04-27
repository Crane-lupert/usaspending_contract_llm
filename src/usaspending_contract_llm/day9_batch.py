"""Day-9 stratified LLM 3-axis batch — Phase 1 spend $23 commit.

Reads manifest_strategic_sample.jsonl, draws stratified subsample by
(prime_ticker x cohort_fy), runs 3-vendor ensemble in parallel, writes
to manifest_axis_classify.jsonl + on-disk dedup cache.

Cost guard: classify_one is idempotent on (model x contract_id) -- re-runs
hit the cache and incur $0. Spending only progresses on first-time pairs.
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from .ensemble import DEFAULT_VENDORS, classify_batch
from .manifest import DATA_DIR

STRATEGIC = DATA_DIR / "manifest_strategic_sample.jsonl"
SUMMARY_OUT = DATA_DIR / "day9_batch_summary.json"


def stratified_subsample(
    rows: list[dict],
    *,
    per_pair: int = 13,
    seed: int = 42,
) -> list[dict]:
    """Stratified sampler: equal draws per (ticker, cohort_fy)."""
    rng = random.Random(seed)
    by_pair: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for r in rows:
        key = (r.get("_prime_ticker") or "", r.get("_cohort_fy"))
        by_pair[key].append(r)
    sample: list[dict] = []
    for key, group in by_pair.items():
        if len(group) <= per_pair:
            sample.extend(group)
        else:
            sample.extend(rng.sample(group, per_pair))
    return sample


def main() -> int:
    with STRATEGIC.open("r", encoding="utf-8") as fh:
        rows = [json.loads(ln) for ln in fh if ln.strip()]
    print(f"strategic sample available: {len(rows)}")

    sample = stratified_subsample(rows, per_pair=13)
    print(f"stratified subsample: {len(sample)} contracts")
    print(f"per (ticker, cohort) cap: 13 -> max 30 primes x 5 cohorts x 13 = 1,950")
    print(f"3-vendor ensemble: {len(sample)} x 3 = {len(sample)*3} LLM calls")

    # Cost preflight: at $0.0038/call avg the projected spend is len(sample) * 3 * 0.0038
    projected = len(sample) * 3 * 0.0038
    cap = 25.0
    print(f"projected spend (validation-rate $0.0038/call): ${projected:.2f}")
    print(f"Phase 1 cap: ${cap}")
    if projected > cap:
        print(f"PROJECTED OVER CAP -- aborting.")
        return 1

    # Run batch (3-vendor ensemble, with on-disk cache for idempotency).
    batch = classify_batch(
        contracts=sample,
        vendors=DEFAULT_VENDORS,
        max_concurrent_contracts=4,
        use_cache=True,
    )

    # Tabulate
    n_full = 0
    n_any_axis1 = 0
    n_all_err = 0
    cost_total = 0.0
    by_vendor_ok: dict[str, int] = {m: 0 for m in DEFAULT_VENDORS}
    by_vendor_err: dict[str, int] = {m: 0 for m in DEFAULT_VENDORS}

    for cid, labels in batch.items():
        any_ok = False
        all_err = True
        for l in labels:
            cost_total += l.cost_usd
            if l.axis1 is not None:
                by_vendor_ok[l.model] += 1
                any_ok = True
                all_err = False
            else:
                by_vendor_err[l.model] += 1
        if any_ok:
            n_any_axis1 += 1
        if all([lbl.axis1 is not None for lbl in labels]):
            n_full += 1
        if all_err:
            n_all_err += 1

    summary = {
        "n_sample":                len(sample),
        "n_with_full_3vendor":     n_full,
        "n_with_at_least_1_vendor": n_any_axis1,
        "n_all_3_vendors_failed":  n_all_err,
        "by_vendor_ok":            by_vendor_ok,
        "by_vendor_err":           by_vendor_err,
        "total_cost_usd":          round(cost_total, 4),
        "phase1_cap":              cap,
        "remaining_cap":           round(cap - cost_total, 4),
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
