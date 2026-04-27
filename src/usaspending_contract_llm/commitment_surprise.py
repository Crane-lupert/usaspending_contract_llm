"""§3.5 Commitment SURPRISE form (CLAUDE.md sub-trigger #1b, pre-registered).

The §3 main effect tested commitment_score_norm *level*. Per CLAUDE.md /
ccm_baseline_spec.md §5b (F1 frozen lesson F1-3 retroactive), the *surprise*
form is a separate pre-registered test:

  surprise[i,q] = commitment_score_norm[i,q] - rolling_mean_4q[i, q-4:q-1]

If this within-firm change predicts cross-section variation when the level
does not, that is the F1-style "sell-the-news" pattern — level is priced
in, change is the actual alpha source.

Verdict matrix (CLAUDE.md):
  #1 PASS + #1b PASS = standard mechanism alpha
  #1 PASS + #1b FAIL = level-artifact, sell-the-news risk
  #1 FAIL + #1b PASS = paper headline candidate (expectation-prior is real alpha)
  #1 FAIL + #1b FAIL = two-layer null (frozen-as-is)

Output: data/commitment_surprise.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .ccm_baseline import TICKER_STATE_HQ, fit_two_step_regression, load_firm_quarter_outcome
from .cross_section import build_firm_quarter_panel, compute_spread_return, join_with_car
from .manifest import DATA_DIR

OUT = DATA_DIR / "commitment_surprise.json"


def add_surprise_column(panel: pd.DataFrame, *, lookback: int = 4) -> pd.DataFrame:
    """For each ticker, surprise = score[q] - rolling_mean(score[q-lookback : q-1]).

    quarter is "YYYYQn" string -> we use Period sort index.
    """
    if panel.empty:
        return panel
    panel = panel.copy()
    panel["quarter_period"] = pd.PeriodIndex(panel["quarter"], freq="Q")
    panel = panel.sort_values(["ticker", "quarter_period"]).reset_index(drop=True)
    rolling = (
        panel.groupby("ticker")["commitment_score_norm"]
        .transform(lambda s: s.shift(1).rolling(lookback, min_periods=1).mean())
    )
    panel["commitment_surprise"] = panel["commitment_score_norm"] - rolling
    return panel.drop(columns=["quarter_period"])


def quintile_spread_on_surprise(panel: pd.DataFrame) -> dict:
    """Per-quarter quintile sort by commitment_surprise (not level)."""
    if panel.empty or "commitment_surprise" not in panel.columns:
        return {"error": "missing_surprise_col"}
    valid = panel.dropna(subset=["commitment_surprise", "forward_car_3m"])
    if len(valid) < 30:
        return {"error": "insufficient_data", "n": int(len(valid))}
    spread_rows = []
    for q, grp in valid.groupby("quarter"):
        if len(grp) < 5:
            continue
        try:
            grp = grp.assign(quintile=pd.qcut(grp["commitment_surprise"], 5, labels=[1, 2, 3, 4, 5], duplicates="drop"))
        except Exception:
            continue
        grp["quintile"] = pd.to_numeric(grp["quintile"], errors="coerce")
        q1_mean = grp.loc[grp["quintile"] == 1, "forward_car_3m"].mean()
        q5_mean = grp.loc[grp["quintile"] == 5, "forward_car_3m"].mean()
        if pd.notna(q1_mean) and pd.notna(q5_mean):
            spread_rows.append({
                "quarter":  q,
                "q1_mean":  round(float(q1_mean), 6),
                "q5_mean":  round(float(q5_mean), 6),
                "spread":   round(float(q1_mean - q5_mean), 6),
                "n_q1":     int((grp["quintile"] == 1).sum()),
                "n_q5":     int((grp["quintile"] == 5).sum()),
            })
    if not spread_rows:
        return {"error": "no_paired_quintiles"}
    spreads = np.array([r["spread"] for r in spread_rows])
    sharpe_q = (spreads.mean() / spreads.std(ddof=1)) if spreads.std(ddof=1) > 0 else 0.0
    return {
        "n_quarters":         len(spread_rows),
        "spread_mean":        round(float(spreads.mean()), 6),
        "spread_std":         round(float(spreads.std(ddof=1)), 6),
        "sharpe_quarterly":   round(float(sharpe_q), 4),
        "sharpe_annualized":  round(float(sharpe_q * (4 ** 0.5)), 4),
        "t_stat":             round(float(sharpe_q * (len(spreads) ** 0.5)), 4),
        "rows":               spread_rows,
    }


def state_fed_spend_aggregate(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    panel["state_hq"] = panel["ticker"].map(TICKER_STATE_HQ).fillna("OTH")
    state_q = panel.groupby(["state_hq", "quarter"]).agg(
        state_q_total_award=("total_award", "sum"),
    ).reset_index()
    state_q["state_fed_spend_log"] = np.log1p(state_q["state_q_total_award"])
    return state_q


def fit_surprise_two_step(panel: pd.DataFrame, *, outcome_col: str = "forward_car_3m") -> dict:
    """2-step regression where commitment is replaced by commitment_surprise."""
    df = panel.dropna(subset=[outcome_col, "state_fed_spend_log", "commitment_surprise"]).copy()
    df = df[df["state_hq"] != "OTH"]
    if len(df) < 30:
        return {"error": "insufficient_data", "n_obs": int(len(df))}

    def demean(d, col):
        return d[col] - d.groupby("ticker")[col].transform("mean") - d.groupby("quarter")[col].transform("mean") + d[col].mean()

    y = demean(df, outcome_col).values
    x_state = demean(df, "state_fed_spend_log").values
    x_surp = demean(df, "commitment_surprise").values

    X1 = np.column_stack([np.ones_like(x_state), x_state])
    beta1, _, _, _ = np.linalg.lstsq(X1, y, rcond=None)
    yhat1 = X1 @ beta1
    ss_res1 = np.sum((y - yhat1) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2_1 = 1 - ss_res1 / ss_tot if ss_tot > 0 else 0.0

    X2 = np.column_stack([np.ones_like(x_state), x_state, x_surp])
    beta2_full, _, _, _ = np.linalg.lstsq(X2, y, rcond=None)
    yhat2 = X2 @ beta2_full
    ss_res2 = np.sum((y - yhat2) ** 2)
    r2_2 = 1 - ss_res2 / ss_tot if ss_tot > 0 else 0.0

    n, k = X2.shape
    if n > k:
        residual_var = ss_res2 / (n - k)
        try:
            xtx_inv = np.linalg.inv(X2.T @ X2)
            se = np.sqrt(residual_var * xtx_inv[2, 2])
            t_stat = float(beta2_full[2] / se) if se > 0 else float("nan")
        except np.linalg.LinAlgError:
            t_stat = float("nan")
    else:
        t_stat = float("nan")

    return {
        "n_obs":              int(n),
        "outcome_col":        outcome_col,
        "r2_step1":           round(float(r2_1), 6),
        "r2_step2_surprise":  round(float(r2_2), 6),
        "incremental_r2_surprise": round(float(r2_2 - r2_1), 6),
        "beta_state":         round(float(beta2_full[1]), 6),
        "beta_surprise":      round(float(beta2_full[2]), 6),
        "surprise_t_stat":    round(t_stat, 4),
    }


def main() -> int:
    panel = build_firm_quarter_panel()
    if panel.empty:
        print("ERR: empty panel")
        return 1
    panel = add_surprise_column(panel, lookback=4)
    panel_with_car = join_with_car(panel)
    state_q = state_fed_spend_aggregate(panel)
    panel_with_car = panel_with_car.copy()
    panel_with_car["state_hq"] = panel_with_car["ticker"].map(TICKER_STATE_HQ).fillna("OTH")
    panel_with_car = panel_with_car.merge(
        state_q[["state_hq", "quarter", "state_fed_spend_log"]],
        on=["state_hq", "quarter"], how="left",
    )

    n_with_surprise = int(panel_with_car["commitment_surprise"].notna().sum())
    summary = {
        "n_panel_rows":            int(len(panel_with_car)),
        "n_with_commitment_surprise": n_with_surprise,
        "quintile_spread_on_surprise": quintile_spread_on_surprise(panel_with_car),
        "two_step_regression_on_surprise": fit_surprise_two_step(panel_with_car, outcome_col="forward_car_3m"),
        "level_vs_surprise_verdict": {
            "rule": "Level + Surprise verdict matrix per CLAUDE.md trigger #1 + #1b",
            "level_pass":            None,  # filled by Day 14 mid-checkpoint
            "surprise_pass_inc_R2":  None,  # incremental_r2_surprise >= 0.03
            "interpretation":        "If level FAIL + surprise PASS -> F1 sub-trigger #1b PASS, paper headline candidate.",
        },
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
