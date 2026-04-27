"""Day-16 §4.2 naive-vs-realistic timing audit.

Naive backtest: hold from action_date (lookahead-aware).
Realistic backtest: hold from (USAspending publish + 24h LLM analysis lag) — i.e.
                    the earliest a public participant could trade on the signal.

Per Phase 0 cohort-stratified publish-lag finding (cohort_lag_v1.json):
  - 2014: 35% of awards publish < 24h after action_date  -> 65% of alpha unaffected
  - 2018: 65% publish < 24h                              -> 35% of alpha unaffected
  - 2024: 75% publish < 24h                              -> 25% of alpha unaffected

Realistic-Sharpe = naive-Sharpe × (1 - lt_24h_fraction) is a first-order proxy
that assumes industry pickup completely zeros the alpha for <24h-publish cases.
True realistic-vs-naive needs per-award publish_date + price-at-publish.

Output: data/timing_audit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .manifest import DATA_DIR

CROSS_SECTION = DATA_DIR / "cross_section_quintile.json"
COHORT_LAG = DATA_DIR / "cohort_lag_v1.json"
OUT = DATA_DIR / "timing_audit.json"


def first_order_decay_proxy() -> dict:
    """Decay each cohort's Sharpe by (1 - lt_24h_fraction)."""
    if not COHORT_LAG.exists():
        return {"error": "cohort_lag_missing"}
    if not CROSS_SECTION.exists():
        return {"error": "cross_section_missing"}

    lag_data = json.loads(COHORT_LAG.read_text(encoding="utf-8"))
    cohort_lag_map: dict[int, float] = {}
    for c in lag_data.get("cohorts", []):
        try:
            cohort_lag_map[int(c["label"])] = float(c["lt_24h_fraction"])
        except Exception:
            continue

    cs_data = json.loads(CROSS_SECTION.read_text(encoding="utf-8"))
    s = cs_data.get("spread_summary", {})
    naive_sharpe = s.get("sharpe_annualized", 0.0)
    naive_t = s.get("t_stat", 0.0)
    n_q = s.get("n_quarters", 0)

    # Average lt_24h across measured cohorts as the pooled industry-absorption rate.
    if cohort_lag_map:
        pooled_lt24 = float(np.mean(list(cohort_lag_map.values())))
        max_lt24 = max(cohort_lag_map.values())
    else:
        pooled_lt24 = 0.0
        max_lt24 = 0.0

    realistic_sharpe_pooled = naive_sharpe * (1 - pooled_lt24)
    realistic_sharpe_2024 = naive_sharpe * (1 - cohort_lag_map.get(2024, 0.0))
    realistic_t_pooled = naive_t * (1 - pooled_lt24)

    return {
        "naive_sharpe_annualized":         round(naive_sharpe, 4),
        "naive_t_stat":                    round(naive_t, 4),
        "n_quarters":                      n_q,
        "cohort_lt_24h":                   cohort_lag_map,
        "pooled_lt_24h_fraction":          round(pooled_lt24, 4),
        "realistic_sharpe_pooled":         round(realistic_sharpe_pooled, 4),
        "realistic_sharpe_2024_only":      round(realistic_sharpe_2024, 4),
        "realistic_t_pooled":              round(realistic_t_pooled, 4),
        "delta_sharpe_naive_minus_pooled": round(naive_sharpe - realistic_sharpe_pooled, 4),
        "interpretation": (
            "First-order industry-absorption haircut: realistic-Sharpe = "
            "naive-Sharpe x (1 - lt_24h_fraction). Cohort-pooled lt_24h "
            f"= {pooled_lt24:.2%}. Naive-vs-realistic gap = "
            f"{naive_sharpe - realistic_sharpe_pooled:.4f}. "
            "Note: this is a proxy. True per-award realistic backtest needs "
            "the publish_date stamp on each award + price tick at publish."
        ),
    }


def main() -> int:
    out = first_order_decay_proxy()
    OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
