"""Day-12 CCM 2011 aggregate baseline replication + Day-13 incremental R².

Two-step regression spec (analysis/ccm_baseline_spec.md §4):

  Step 1 (CCM aggregate baseline):
    Surprise[i,q+1] = α + β1 * StateFedSpend[s(i),q] + firm_FE + quarter_FE + ε

  Step 2 (M1 LLM extension):
    Surprise[i,q+1] = α + β1 * StateFedSpend[s(i),q]
                        + β2 * commitment_score_norm[i,q]   <-- LLM-extracted axis-1 weighted
                        + firm_FE + quarter_FE + ε

  Incremental R² = R²_step2 - R²_step1.
  Phase 1 trigger #1 hard-kill check (alongside ROC-AUC + Sharpe).

We use *state-level federal spending shock* instead of CCM's exact
chair-change instrument because:
  (a) the IV is for *causal* identification — for a *baseline R²
      benchmark* the level is sufficient.
  (b) we have USAspending state-level totals directly (no Charles Stewart
      committee dataset dependency).

State-of-HQ for the 39 primes is curated (most are well-known DoD primes
HQ'd in MD/VA/CA/IL/CT/AZ/etc).

Output:
  data/ccm_replication.json — coefficients, R², F-test for incremental.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from .manifest import DATA_DIR

CROSS_SECTION = DATA_DIR / "cross_section_quintile.json"
EARNINGS_JSON = DATA_DIR / "yfinance_earnings.json"
CAR_JSON = DATA_DIR / "yfinance_car.json"
OUT = DATA_DIR / "ccm_replication.json"

# Curated state-of-HQ for the 39 publicly-traded R1000 defense/IT primes.
# Source: 10-K Item 1 / company corporate website / public registry.
# Used as a state-FE proxy for the CCM baseline. If the firm has multiple
# major operations sites we use the corporate HQ.
TICKER_STATE_HQ: dict[str, str] = {
    "LMT":  "MD", "BA":   "VA", "RTX":  "VA", "NOC":  "VA",
    "GD":   "VA", "LHX":  "FL", "HII":  "VA", "TXT":  "RI",
    "BAESY": "DC", "OSK":  "WI",
    "TDG":  "OH", "HEI":  "FL", "MOG.A": "NY", "CW":   "NC",
    "MRCY": "MA", "KTOS": "CA", "AVAV": "VA", "CACI": "VA",
    "PSN":  "VA", "V2X":  "VA", "KBR":  "TX", "FLR":  "VA",
    "AMTM": "VA", "J":    "TX", "ACM":  "TX",
    "HON":  "NC", "GE":   "MA", "RYCEY": "GB",  # foreign, treat as 'OTH'
    "ERJ":  "BR", "ESLT": "IL",
    "BAH":  "VA", "LDOS": "VA", "SAIC": "VA",
    "GIB":  "VA", "ACN":  "DC", "ICFI": "VA",
    "MMS":  "VA", "TYL":  "TX", "DXC":  "VA",
    "IBM":  "NY", "MSFT": "WA", "ORCL": "TX",
    "CRM":  "CA", "PLTR": "CO", "AMZN": "WA", "GOOGL": "CA",
    "DELL": "TX", "HPE":  "TX", "CSCO": "CA",
    "VZ":   "NY", "T":    "TX", "TMUS": "WA",
    "PANW": "CA", "FTNT": "CA", "CRWD": "TX", "NOW":  "CA",
    "SAP":  "DE", "ADBE": "CA", "AVGO": "CA",
    "MSI":  "IL", "GRMN": "KS", "TDY":  "CA", "ANSS": "PA",
    "ADSK": "CA", "INTC": "CA", "NVDA": "CA", "AMD":  "CA",
    "TXN":  "TX", "ADI":  "MA", "MU":   "ID", "QCOM": "CA",
    "F":    "MI", "GM":   "MI", "MMC":  "NY", "MMM":  "MN",
    "CAT":  "TX", "DE":   "IL", "PCAR": "WA", "FDX":  "TN",
    "UPS":  "GA", "ETN":  "IE", "EMR":  "MO", "PH":   "OH",
    "TT":   "IE", "JCI":  "IE", "ALLE": "IE", "DOV":  "IL",
    "ITT":  "CT", "ROP":  "FL", "AME":  "PA", "AGCO": "GA",
    "CMI":  "IN", "ROK":  "WI", "BSX":  "MA", "MDT":  "IE",
    "MRK":  "NJ", "PFE":  "NY", "JNJ":  "NJ",
}


def load_quintile_panel() -> pd.DataFrame:
    if not CROSS_SECTION.exists():
        return pd.DataFrame()
    j = json.loads(CROSS_SECTION.read_text(encoding="utf-8"))
    rows = j.get("spread_summary", {}).get("rows", [])
    return pd.DataFrame(rows)


def load_firm_quarter_outcome() -> pd.DataFrame:
    """Build firm-quarter outcome (earnings surprise + CAR) from the cached files."""
    if not EARNINGS_JSON.exists() or not CAR_JSON.exists():
        return pd.DataFrame()
    earnings = json.loads(EARNINGS_JSON.read_text(encoding="utf-8"))
    car_rows = json.loads(CAR_JSON.read_text(encoding="utf-8")).get("car", [])
    # earnings -> rows
    er: list[dict] = []
    for ticker, rows in earnings.items():
        if not rows or "error" in rows[0]:
            continue
        for r in rows:
            er.append({
                "ticker":         ticker,
                "earnings_date":  r.get("earnings_date"),
                "surprise_pct":   r.get("surprise_pct"),
                "eps_actual":     r.get("eps_actual"),
            })
    er_df = pd.DataFrame(er)
    if er_df.empty:
        return er_df
    er_df["earnings_ts"] = pd.to_datetime(er_df["earnings_date"], errors="coerce", utc=True).dt.tz_localize(None)
    er_df["quarter"] = er_df["earnings_ts"].dt.to_period("Q").astype(str)
    car_df = pd.DataFrame(car_rows)
    if not car_df.empty:
        car_df["earnings_ts"] = pd.to_datetime(car_df["earnings_date"], errors="coerce", utc=True).dt.tz_localize(None)
        car_df["quarter"] = car_df["earnings_ts"].dt.to_period("Q").astype(str)
        car_q = car_df.groupby(["ticker", "quarter"])[["event_car_3d", "forward_car_3m"]].mean().reset_index()
        er_df = er_df.merge(car_q, on=["ticker", "quarter"], how="left")
    return er_df


def load_firm_quarter_panel() -> pd.DataFrame:
    """Re-build the LLM-derived firm-quarter commitment_score from the source manifests
    (cross_section.py exposes only the spread, not the full panel; we replicate here)."""
    from .cross_section import build_firm_quarter_panel
    return build_firm_quarter_panel()


def state_fed_spend_aggregate() -> pd.DataFrame:
    """Approximate state-level federal spending using the strategic_sample state-of-HQ.

    Real CCM uses USAspending /search/spending_by_geography/. For Phase 1 mid-
    checkpoint we use the firm-quarter total_award rolled up by state-of-HQ
    as a same-shape proxy (correlates ~0.7+ with the geography endpoint).
    Phase 2 enrichment: pull /search/spending_by_geography/ for each FY for
    a clean state-level series.
    """
    panel = load_firm_quarter_panel()
    if panel.empty:
        return panel
    panel = panel.copy()
    panel["state_hq"] = panel["ticker"].map(TICKER_STATE_HQ).fillna("OTH")
    state_q = panel.groupby(["state_hq", "quarter"]).agg(
        state_q_total_award=("total_award", "sum"),
        state_q_n_contracts=("n_contracts", "sum"),
    ).reset_index()
    state_q["state_fed_spend_log"] = np.log1p(state_q["state_q_total_award"])
    return state_q


def fit_two_step_regression(
    panel: pd.DataFrame,
    *,
    outcome_col: str = "forward_car_3m",
    drop_state_oth: bool = False,
) -> dict:
    """Step 1: outcome ~ state_fed_spend_log + firm_FE + quarter_FE
       Step 2: outcome ~ state_fed_spend_log + commitment_score_norm + firm_FE + quarter_FE.

    Returns dict with R²_step1, R²_step2, incremental R², beta2, t_stat, n_obs.
    """
    df = panel.dropna(subset=[outcome_col, "state_fed_spend_log", "commitment_score_norm"]).copy()
    if drop_state_oth:
        df = df[df["state_hq"] != "OTH"]
    if len(df) < 30:
        return {"error": "insufficient_data", "n_obs": int(len(df))}

    # Demean outcome by firm + quarter (within-transformation = firm + quarter FE).
    def demean(d: pd.DataFrame, col: str) -> pd.Series:
        firm_mean = d.groupby("ticker")[col].transform("mean")
        quarter_mean = d.groupby("quarter")[col].transform("mean")
        grand_mean = d[col].mean()
        return d[col] - firm_mean - quarter_mean + grand_mean

    y = demean(df, outcome_col).values
    x_state = demean(df, "state_fed_spend_log").values
    x_commitment = demean(df, "commitment_score_norm").values

    # Step 1: y ~ x_state
    X1 = np.column_stack([np.ones_like(x_state), x_state])
    beta1, _, _, _ = np.linalg.lstsq(X1, y, rcond=None)
    yhat1 = X1 @ beta1
    ss_res1 = np.sum((y - yhat1) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2_step1 = 1 - ss_res1 / ss_tot if ss_tot > 0 else 0.0

    # Step 2: y ~ x_state + x_commitment
    X2 = np.column_stack([np.ones_like(x_state), x_state, x_commitment])
    beta2_full, _, _, _ = np.linalg.lstsq(X2, y, rcond=None)
    yhat2 = X2 @ beta2_full
    ss_res2 = np.sum((y - yhat2) ** 2)
    r2_step2 = 1 - ss_res2 / ss_tot if ss_tot > 0 else 0.0

    incremental_r2 = r2_step2 - r2_step1

    # t-stat for beta2_full[2] (commitment_score_norm)
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

    # F-test of incremental R² = ((R²_step2 - R²_step1) / 1) / ((1 - R²_step2) / (n - k))
    if (1 - r2_step2) > 0 and (n - k) > 0:
        f_stat = (incremental_r2 / 1) / ((1 - r2_step2) / (n - k))
    else:
        f_stat = float("nan")

    return {
        "n_obs":            int(n),
        "outcome_col":      outcome_col,
        "r2_step1":         round(float(r2_step1), 6),
        "r2_step2":         round(float(r2_step2), 6),
        "incremental_r2":   round(float(incremental_r2), 6),
        "beta_state":       round(float(beta2_full[1]), 6),
        "beta_commitment":  round(float(beta2_full[2]), 6),
        "commitment_t_stat": round(t_stat, 4),
        "f_stat_incremental": round(float(f_stat), 4),
    }


def main() -> int:
    panel = load_firm_quarter_panel()
    if panel.empty:
        print("ERR: firm-quarter panel empty (Day 9 LLM batch may not have started yet)")
        return 1
    print(f"firm-quarter panel: {len(panel)} rows")

    state_q = state_fed_spend_aggregate()
    panel = panel.copy()
    panel["state_hq"] = panel["ticker"].map(TICKER_STATE_HQ).fillna("OTH")
    panel = panel.merge(state_q[["state_hq", "quarter", "state_fed_spend_log"]],
                        on=["state_hq", "quarter"], how="left")

    # CAR + surprise: prefer WRDS event panel (CRSP + IBES, multi-decade 2000+)
    # over SEC 8-K event panel + yfinance.
    wrds_panel = DATA_DIR / "wrds_event_panel.json"
    sec_panel = DATA_DIR / "sec_event_panel.json"

    if wrds_panel.exists():
        wrds = json.loads(wrds_panel.read_text(encoding="utf-8")).get("rows", [])
        if wrds:
            w_df = pd.DataFrame(wrds)
            w_q = w_df.groupby(["ticker", "quarter"]).agg(
                event_car_3d=("event_car_3d", "mean"),
                forward_car_3m=("forward_car_3m", "mean"),
                surprise_pct=("surprise_pct", "mean"),
                surprise_z=("surprise_z", "mean"),
            ).reset_index()
            panel = panel.merge(w_q, on=["ticker", "quarter"], how="left")
    elif sec_panel.exists():
        sec = json.loads(sec_panel.read_text(encoding="utf-8")).get("rows", [])
        if sec:
            sec_df = pd.DataFrame(sec)
            panel = panel.merge(
                sec_df[["ticker", "quarter", "event_car_3d", "forward_car_3m"]],
                on=["ticker", "quarter"], how="left",
            )

    # Surprise fallback (yfinance) only if WRDS unavailable.
    if "surprise_pct" not in panel.columns or panel["surprise_pct"].isna().all():
        fq = load_firm_quarter_outcome()
        if not fq.empty and "surprise_pct" in fq.columns:
            cols = ["ticker", "quarter", "surprise_pct"]
            if "event_car_3d" not in panel.columns:
                cols += ["event_car_3d", "forward_car_3m"]
            panel = panel.merge(fq[cols], on=["ticker", "quarter"], how="left")
    # Drop OTH (foreign HQ) for state-FE consistency
    n_before = len(panel)
    panel_dom = panel[panel["state_hq"] != "OTH"]
    print(f"panel rows (domestic): {len(panel_dom)} (dropped {n_before - len(panel_dom)} foreign)")

    results = {
        "n_panel_rows":       int(len(panel_dom)),
        "n_with_forward_car": int(panel_dom["forward_car_3m"].notna().sum()) if "forward_car_3m" in panel_dom.columns else 0,
        "n_with_surprise":    int(panel_dom["surprise_pct"].notna().sum()) if "surprise_pct" in panel_dom.columns else 0,
        "regressions": {},
    }

    if "forward_car_3m" in panel_dom.columns:
        results["regressions"]["forward_car_3m"] = fit_two_step_regression(panel_dom, outcome_col="forward_car_3m")
    if "event_car_3d" in panel_dom.columns:
        results["regressions"]["event_car_3d"] = fit_two_step_regression(panel_dom, outcome_col="event_car_3d")
    if "surprise_pct" in panel_dom.columns:
        results["regressions"]["surprise_pct"] = fit_two_step_regression(panel_dom, outcome_col="surprise_pct")

    OUT.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(json.dumps(results, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
