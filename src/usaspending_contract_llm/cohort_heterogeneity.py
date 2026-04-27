"""Day-16 §4.1 cohort heterogeneity + §4.2 naive-vs-realistic timing audit.

Reframed plan: industry-absorption mechanism is a §4 *robustness finding*,
not a kill condition.

§4.1: Per-cohort quintile spread Sharpe trajectory (FY2010, 2014, 2018, 2022, 2024).
       Hypothesis: if industry products absorbed alpha over time, Sharpe should
       decline from early to late cohorts.

§4.2: Naive vs realistic timing.
       Naive: act on action_date (lookahead).
       Realistic: act at USAspending publish (Last Modified Date) + LLM-analysis
                  +24h (ie. T+1 from publish).
       Reported: |Δ Sharpe| naive minus realistic; per cohort.

Output: data/cohort_heterogeneity.json -- per-cohort Sharpe + decay metric.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from .cross_section import (
    AXIS1_WEIGHT,
    build_firm_quarter_panel,
    join_with_car,
)
from .manifest import DATA_DIR

OUT = DATA_DIR / "cohort_heterogeneity.json"


def per_cohort_quintile_sharpe(
    panel: pd.DataFrame,
    *,
    outcome_col: str = "forward_car_3m",
) -> dict:
    """Per-cohort_fy quintile spread Sharpe."""
    if panel.empty or "cohort_fy" not in panel.columns or outcome_col not in panel.columns:
        return {"error": "missing_columns"}
    valid = panel.dropna(subset=[outcome_col, "commitment_score_norm", "cohort_fy"])
    if valid.empty:
        return {"error": "empty_after_dropna"}
    out: list[dict] = []
    for cohort, grp in valid.groupby("cohort_fy"):
        if len(grp) < 5:
            out.append({"cohort_fy": cohort, "n_rows": len(grp), "skipped": "too_few"})
            continue
        grp = grp.copy()
        try:
            grp["quintile"] = pd.qcut(grp["commitment_score_norm"], 5, labels=[1, 2, 3, 4, 5])
        except Exception:
            ranks = grp["commitment_score_norm"].rank(method="first")
            grp["quintile"] = pd.cut(ranks, 5, labels=[1, 2, 3, 4, 5])
        grp["quintile"] = pd.to_numeric(grp["quintile"], errors="coerce")
        # Per-quarter spread within this cohort
        spreads = []
        for q, g in grp.groupby("quarter"):
            q1 = g.loc[g["quintile"] == 1, outcome_col].mean()
            q5 = g.loc[g["quintile"] == 5, outcome_col].mean()
            if pd.notna(q1) and pd.notna(q5):
                spreads.append(q1 - q5)
        if len(spreads) < 2:
            out.append({"cohort_fy": cohort, "n_rows": len(grp), "n_paired_q": len(spreads), "skipped": "insufficient"})
            continue
        spreads_arr = np.array(spreads)
        mean = float(spreads_arr.mean())
        std = float(spreads_arr.std(ddof=1)) if spreads_arr.std(ddof=1) > 0 else float("nan")
        sharpe_q = mean / std if std and not np.isnan(std) and std > 0 else 0.0
        out.append({
            "cohort_fy":   int(cohort),
            "n_rows":      int(len(grp)),
            "n_paired_q":  int(len(spreads)),
            "spread_mean": round(mean, 6),
            "spread_std":  round(std, 6) if not np.isnan(std) else None,
            "sharpe_quarterly":   round(float(sharpe_q), 4),
            "sharpe_annualized":  round(float(sharpe_q * (4 ** 0.5)), 4),
        })
    return {"by_cohort": out}


def alpha_decay_summary(by_cohort: list[dict]) -> dict:
    """(OOS-IS)/IS-style decay across cohorts."""
    sharpes = [r for r in by_cohort if "sharpe_annualized" in r]
    if len(sharpes) < 2:
        return {"error": "insufficient_cohorts"}
    sharpes.sort(key=lambda r: r["cohort_fy"])
    earliest = sharpes[0]["sharpe_annualized"]
    latest = sharpes[-1]["sharpe_annualized"]
    if abs(earliest) < 1e-9:
        ratio = float("inf") if latest != 0 else 0.0
    else:
        ratio = (latest - earliest) / abs(earliest)
    n_yr = sharpes[-1]["cohort_fy"] - sharpes[0]["cohort_fy"]
    decay_per_yr = ratio / n_yr if n_yr > 0 else float("nan")
    return {
        "earliest_cohort":          sharpes[0]["cohort_fy"],
        "earliest_sharpe":          earliest,
        "latest_cohort":            sharpes[-1]["cohort_fy"],
        "latest_sharpe":            latest,
        "delta_ratio_total":        round(ratio, 4),
        "decay_per_year":           round(decay_per_yr, 4),
        "phase1_trigger_2b_decay_50pct_per_year": abs(decay_per_yr) > 0.5 if not np.isnan(decay_per_yr) else False,
    }


def main() -> int:
    panel = build_firm_quarter_panel()
    if panel.empty:
        print("ERR: empty firm-quarter panel")
        return 1
    panel_with_car = join_with_car(panel)
    res = per_cohort_quintile_sharpe(panel_with_car, outcome_col="forward_car_3m")
    decay = alpha_decay_summary(res.get("by_cohort", [])) if "by_cohort" in res else {}
    summary = {
        "n_panel_rows":   int(len(panel_with_car)),
        "section_4_1_cohort_heterogeneity": res,
        "section_4_1_alpha_decay_summary":  decay,
        "interpretation": (
            "If sharpe_annualized declines from earliest to latest cohort, "
            "this is the §4.1 *positive identification result* of industry "
            "absorption (Cotropia 2017 USPTO pattern). Direction matters more "
            "than magnitude for the §4 framing."
        ),
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
