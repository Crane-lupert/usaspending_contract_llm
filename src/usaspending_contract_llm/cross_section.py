"""Day-11 cross-section quintile portfolio construction.

Given:
  manifest_axis_classify.jsonl  -- LLM 3-axis labels per contract
  manifest_strategic_sample.jsonl -- contract metadata (ticker + cohort_fy + amount)
  yfinance_car.json              -- 8-K event-window CAR + 3m forward CAR per (ticker, quarter)

Build firm-quarter panel:
  forward_revenue_commitment_score[firm, quarter] =
    sum over contracts in quarter of:
      axis1_weight * award_amount     (FFP=0.0, IDIQ_CEILING=1.0, OPTION_PERIOD=0.7, COST_PLUS=1.5)
                                     -- higher = more *uncertain* commitment, sells-the-news risk
  agg per firm-quarter -> sort cross-section into quintiles
  spread = bottom-quintile-long minus top-quintile-short, monthly rebalance proxy via quarterly EPS announce.

Output:
  data/cross_section_quintile.json   -- quintile assignment + spread returns
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from .manifest import DATA_DIR

AXIS_CLASSIFY = DATA_DIR / "manifest_axis_classify.jsonl"
STRATEGIC = DATA_DIR / "manifest_strategic_sample.jsonl"
CAR_JSON = DATA_DIR / "yfinance_car.json"
OUT = DATA_DIR / "cross_section_quintile.json"

# Axis-1 commitment-uncertainty weights.
# Lower = more committed (FFP fixed price = least uncertain),
# higher = more conditional (cost-plus = most uncertain on $).
# Quintile sort: low weight = "low-commitment-uncertainty" = LONG.
AXIS1_WEIGHT = {
    "FFP":           0.0,
    "OPTION_PERIOD": 0.7,
    "IDIQ_CEILING":  1.0,
    "COST_PLUS":     1.5,
    None:            None,
}


def load_axis_labels() -> dict[str, dict]:
    """Map contract_id -> {axis1: voted_label, n_vendors}."""
    rows: list[dict] = []
    with AXIS_CLASSIFY.open("r", encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    by_cid: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        cid = r.get("contract_id")
        a1 = r.get("axis1")
        if cid and a1:
            by_cid[cid].append(a1)
    out: dict[str, dict] = {}
    for cid, labels in by_cid.items():
        # mode = most common
        from collections import Counter
        mode_label, mode_n = Counter(labels).most_common(1)[0]
        out[cid] = {"axis1_voted": mode_label, "n_vendors_agree": mode_n,
                    "n_vendors_total": len(labels)}
    return out


def load_strategic_meta() -> dict[str, dict]:
    """contract_id -> {ticker, cohort_fy, base_obligation_date, award_amount}."""
    out: dict[str, dict] = {}
    with STRATEGIC.open("r", encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            cid = r.get("generated_internal_id")
            if cid:
                out[cid] = {
                    "ticker":               r.get("_prime_ticker"),
                    "cohort_fy":            r.get("_cohort_fy"),
                    "base_obligation_date": r.get("base_obligation_date"),
                    "start_date":           r.get("start_date"),
                    "award_amount":         float(r.get("award_amount") or 0.0),
                }
    return out


def build_firm_quarter_panel() -> pd.DataFrame:
    labels = load_axis_labels()
    meta = load_strategic_meta()

    rows: list[dict] = []
    for cid, m in meta.items():
        lbl = labels.get(cid)
        if lbl is None:
            continue
        a1 = lbl["axis1_voted"]
        weight = AXIS1_WEIGHT.get(a1)
        if weight is None or m["ticker"] is None:
            continue
        # Quarter from start_date (FY anchor) -- prefer start_date over base_obligation
        date_str = m["start_date"] or m["base_obligation_date"]
        if not date_str:
            continue
        try:
            ts = pd.Timestamp(date_str)
        except Exception:
            continue
        quarter = ts.to_period("Q")
        rows.append({
            "contract_id":   cid,
            "ticker":        m["ticker"],
            "quarter":       str(quarter),
            "cohort_fy":     m["cohort_fy"],
            "axis1":         a1,
            "weight":        weight,
            "award_amount":  m["award_amount"],
            "weighted_amt":  weight * m["award_amount"],
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    panel = df.groupby(["ticker", "quarter"]).agg(
        n_contracts=("contract_id", "count"),
        total_award=("award_amount", "sum"),
        commitment_score_raw=("weighted_amt", "sum"),
        cohort_fy=("cohort_fy", "max"),  # mode-like; same firm-quarter usually shares cohort
    ).reset_index()
    panel["commitment_score_norm"] = panel["commitment_score_raw"] / panel["total_award"].replace(0, np.nan)
    return panel


def quintile_sort(panel: pd.DataFrame) -> pd.DataFrame:
    """Per-quarter cross-section quintile rank by commitment_score_norm."""
    if panel.empty:
        return panel
    out_rows = []
    for q, grp in panel.groupby("quarter"):
        if len(grp) < 5:
            grp = grp.assign(quintile=np.nan)
        else:
            grp = grp.copy()
            try:
                grp["quintile"] = pd.qcut(grp["commitment_score_norm"], 5, labels=[1, 2, 3, 4, 5])
            except Exception:
                # Ties — fallback to rank-based 5-bucket.
                ranks = grp["commitment_score_norm"].rank(method="first")
                grp["quintile"] = pd.cut(ranks, 5, labels=[1, 2, 3, 4, 5])
        out_rows.append(grp)
    out = pd.concat(out_rows, ignore_index=True)
    out["quintile"] = pd.to_numeric(out["quintile"], errors="coerce")
    return out


def join_with_car(panel: pd.DataFrame) -> pd.DataFrame:
    """CAR source priority (highest first):
       1. WRDS event panel (CRSP daily + IBES anndats; multi-decade 2000+)
       2. SEC 8-K event panel (SEC filed_date + yfinance prices; 2009+)
       3. yfinance CAR (5yr cap)
    """
    wrds_panel = DATA_DIR / "wrds_event_panel.json"
    if wrds_panel.exists():
        wrds = json.loads(wrds_panel.read_text(encoding="utf-8")).get("rows", [])
        if wrds:
            w_df = pd.DataFrame(wrds)
            # Aggregate to firm-quarter (multiple announcements per quarter possible).
            w_q = w_df.groupby(["ticker", "quarter"]).agg(
                event_car_3d=("event_car_3d", "mean"),
                forward_car_3m=("forward_car_3m", "mean"),
                surprise_z=("surprise_z", "mean"),
            ).reset_index()
            return panel.merge(
                w_q[["ticker", "quarter", "event_car_3d", "forward_car_3m", "surprise_z"]],
                on=["ticker", "quarter"], how="left",
            )

    sec_panel = DATA_DIR / "sec_event_panel.json"
    if sec_panel.exists():
        sec = json.loads(sec_panel.read_text(encoding="utf-8")).get("rows", [])
        if sec:
            sec_df = pd.DataFrame(sec)
            return panel.merge(
                sec_df[["ticker", "quarter", "event_car_3d", "forward_car_3m"]],
                on=["ticker", "quarter"], how="left",
            )
    if not CAR_JSON.exists():
        return panel.assign(event_car_3d=np.nan, forward_car_3m=np.nan)
    car = json.loads(CAR_JSON.read_text(encoding="utf-8")).get("car", [])
    car_df = pd.DataFrame(car)
    if car_df.empty:
        return panel.assign(event_car_3d=np.nan, forward_car_3m=np.nan)
    car_df["earnings_ts"] = pd.to_datetime(car_df["earnings_date"], errors="coerce", utc=True).dt.tz_localize(None)
    car_df["quarter"] = car_df["earnings_ts"].dt.to_period("Q").astype(str)
    car_q = car_df.groupby(["ticker", "quarter"]).agg(
        event_car_3d=("event_car_3d", "mean"),
        forward_car_3m=("forward_car_3m", "mean"),
    ).reset_index()
    return panel.merge(car_q, on=["ticker", "quarter"], how="left")


def compute_spread_return(panel_with_car: pd.DataFrame) -> dict:
    """Quintile spread = mean(Q1 forward CAR) - mean(Q5 forward CAR), per quarter."""
    if "quintile" not in panel_with_car.columns or panel_with_car["quintile"].isna().all():
        return {"error": "no_quintile_assignments"}
    valid = panel_with_car.dropna(subset=["quintile", "forward_car_3m"])
    if valid.empty:
        return {"error": "no_valid_car_x_quintile_rows", "n_panel_rows": int(len(panel_with_car))}
    spread_rows = []
    for q, grp in valid.groupby("quarter"):
        q1 = grp.loc[grp["quintile"] == 1, "forward_car_3m"].mean()
        q5 = grp.loc[grp["quintile"] == 5, "forward_car_3m"].mean()
        if pd.notna(q1) and pd.notna(q5):
            spread_rows.append({
                "quarter": q,
                "q1_mean": round(float(q1), 6),
                "q5_mean": round(float(q5), 6),
                "spread":  round(float(q1 - q5), 6),
                "n_q1":    int((grp["quintile"] == 1).sum()),
                "n_q5":    int((grp["quintile"] == 5).sum()),
            })
    if not spread_rows:
        return {"error": "no_paired_quintiles"}
    spreads = np.array([r["spread"] for r in spread_rows])
    sharpe_q = float(spreads.mean() / spreads.std(ddof=1)) if len(spreads) > 1 and spreads.std(ddof=1) > 0 else 0.0
    sharpe_annualized = sharpe_q * (4 ** 0.5)  # quarterly -> annual
    return {
        "n_quarters":              len(spread_rows),
        "spread_mean":             round(float(spreads.mean()), 6),
        "spread_std":              round(float(spreads.std(ddof=1)), 6),
        "sharpe_quarterly":        round(sharpe_q, 4),
        "sharpe_annualized":       round(sharpe_annualized, 4),
        "t_stat":                  round(sharpe_q * (len(spreads) ** 0.5), 4),
        "rows":                    spread_rows,
    }


def main() -> int:
    panel = build_firm_quarter_panel()
    print(f"firm-quarter panel: {len(panel)} rows, {panel['ticker'].nunique() if not panel.empty else 0} tickers")
    sorted_panel = quintile_sort(panel)
    joined = join_with_car(sorted_panel)
    print(f"after CAR join: {len(joined)} rows, {joined['forward_car_3m'].notna().sum()} with CAR")
    spread = compute_spread_return(joined)
    summary = {
        "n_panel_rows":     int(len(panel)),
        "n_distinct_tickers": int(panel["ticker"].nunique() if not panel.empty else 0),
        "n_distinct_quarters": int(panel["quarter"].nunique() if not panel.empty else 0),
        "n_with_car":       int(joined["forward_car_3m"].notna().sum() if "forward_car_3m" in joined.columns else 0),
        "spread_summary":   spread,
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "spread_summary"}, indent=2, default=str))
    if isinstance(spread, dict) and "error" not in spread:
        print("spread summary:")
        print(json.dumps({k: v for k, v in spread.items() if k != "rows"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
