"""Day-19 Streamlit MVP — 5 pages.

Run:
    streamlit run dashboard/app.py

Pages:
  1 Universe         — 39 publicly-traded primes + cohort stratified sample shape
  2 3-axis Distribution — axis1 / axis2 / axis3 label counts + Fleiss kappa
  3 Cross-Section Quintile — Q1 minus Q5 spread + per-quarter rows
  4 Cohort Heterogeneity (§4.1) — per-FY-cohort Sharpe trajectory + alpha decay
  5 Methodology + Limits — yfinance ~5yr earnings cap, 39-firm universe, etc.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


@st.cache_data
def load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def page_1_universe() -> None:
    st.header("Page 1 — Universe")
    st.markdown("39 publicly-traded R1000 defense/IT prime contractors, FY2010-FY2024.")
    csv = DATA / "universe_defense_it_r1000_fy2024.csv"
    if csv.exists():
        df = pd.read_csv(csv)
        df = df[df["ticker"].notna() & (df["ticker"].astype(str).str.strip() != "")]
        st.write(f"Distinct tickers: {df['ticker'].nunique()}")
        st.dataframe(df[["canonical", "ticker", "amount_fy", "uei"]].sort_values("amount_fy", ascending=False))
    summary = load_json(DATA / "strategic_sample_summary.json")
    if summary:
        st.subheader("Strategic stratified sample (Day 8)")
        st.json({k: v for k, v in summary.items() if k != "by_pair_count"})


def page_2_axis_distribution() -> None:
    st.header("Page 2 — 3-axis label distribution + Fleiss kappa")
    kappa = load_json(DATA / "ensemble_kappa_n20.json")
    if kappa:
        st.subheader("n=20 oracle Fleiss kappa")
        st.json(kappa.get("kappa_per_axis", {}))
        st.subheader("Vendor accuracy vs oracle (axis-1)")
        st.json(kappa.get("vendor_axis1_accuracy_vs_oracle", {}))
    day9 = load_json(DATA / "day9_batch_summary.json")
    if day9:
        st.subheader("Day 9 stratified batch")
        st.json({k: v for k, v in day9.items() if k != "dispatch"})


def page_3_cross_section() -> None:
    st.header("Page 3 — Cross-section quintile portfolio")
    j = load_json(DATA / "cross_section_quintile.json")
    if not j:
        st.warning("Run `python -m usaspending_contract_llm.cross_section` first.")
        return
    s = j.get("spread_summary", {})
    if "error" in s:
        st.warning(s)
        return
    col1, col2, col3 = st.columns(3)
    col1.metric("Sharpe (annualized)", s.get("sharpe_annualized"))
    col2.metric("t-stat", s.get("t_stat"))
    col3.metric("paired quarters", s.get("n_quarters"))
    rows = pd.DataFrame(s.get("rows", []))
    if not rows.empty:
        st.line_chart(rows.set_index("quarter")["spread"])
        st.dataframe(rows)


def page_4_cohort_heterogeneity() -> None:
    st.header("Page 4 — §4.1 Cohort heterogeneity (alpha decay)")
    j = load_json(DATA / "cohort_heterogeneity.json")
    if not j:
        st.warning("Run `python -m usaspending_contract_llm.cohort_heterogeneity` first.")
        return
    section = j.get("section_4_1_cohort_heterogeneity", {})
    by_cohort = section.get("by_cohort", [])
    if by_cohort:
        df = pd.DataFrame(by_cohort)
        df = df[df["sharpe_annualized"].notna() if "sharpe_annualized" in df.columns else slice(None)]
        if not df.empty:
            df = df.sort_values("cohort_fy")
            st.line_chart(df.set_index("cohort_fy")["sharpe_annualized"])
            st.dataframe(df)
    decay = j.get("section_4_1_alpha_decay_summary", {})
    if decay:
        st.subheader("Alpha decay summary")
        st.json(decay)
    lag = load_json(DATA / "cohort_lag_v1.json")
    if lag:
        st.subheader("Phase 0 cohort publish-lag distribution")
        rows = []
        for c in lag.get("cohorts", []):
            rows.append({"cohort_fy": c["label"], "lt_24h_fraction": c["lt_24h_fraction"]})
        if rows:
            df = pd.DataFrame(rows).sort_values("cohort_fy")
            st.line_chart(df.set_index("cohort_fy")["lt_24h_fraction"])


def page_5_methodology() -> None:
    st.header("Page 5 — Methodology + limits")
    st.markdown(
        """
## Final verdict

**FROZEN_WITH_CAVEAT** under CLAUDE.md trigger #4 (data-validity / power).
Both trigger #1 (HARD_KILL: ALL-3-AND main metrics fail) AND trigger #4
(power: n_panel < 1,500 floor) fired. Under simultaneous fire the test is
*un-decidable*; we publish methodology + null + caveat + Phase 2 path.

| Metric | Value | Threshold | Verdict at n=262 |
|---|---|---|---|
| Incremental R² over CCM | 0.0014 | ≥ 0.05 | FAIL |
| Quintile Sharpe (annualized) | -0.0209 | ≥ 0.30 | FAIL |
| ROC-AUC (binary beat) | 0.5471 | ≥ 0.60 | FAIL |
| Required n_min (CLAUDE.md §4.5.1) | 1,500-3,000 | n=262 | severely under |
| Bailey-de Prado DSR psr | 0.059 | ≥ 0.95 | FAIL |
| Newey-West HAC t-stat | -0.048 | ≥ 2.0 | FAIL |
| Cluster bootstrap CI95 | [-0.060, 0.061] | excludes 0 | INCLUDES 0 |

## Reproducibility

- Total LLM cost: $20 / $35 cap.
- 49 / 49 tests passing.
- Open-source pipeline. Idempotent LLM cache (re-runs $0).
- Data: USAspending API + yfinance free + OpenRouter pay-as-you-go.

## Limits

- yfinance free-tier `earnings_dates` ~5yr history → §4.1 cohort
  heterogeneity test power-limited to 2022 + 2024 cohorts; 2010/2014/2018
  cohorts have no CAR-joined observations.
- 39-firm publicly-traded universe (data-driven cap from USAspending recipient
  pivot for defense/IT NAICS); cross-section quintile = 5 buckets × 5-8 firms.
- LLM training cutoff = 2026-01-01 (Anthropic Opus 4.7 / Sonnet 4.6) — see
  §4.4 contamination check (`data/contamination_masking.json` if available).
- State-of-HQ for 39 primes is curated (10-K Item 1); state-level federal
  spending aggregate is rolled up from strategic sample (Phase 2 enrichment:
  `/search/spending_by_geography/`).

## Not in scope (Phase 2 directions)

- Compustat / IBES paid-tier earnings history (would extend §4.1 to all 5
  cohorts + clear the n_min ≈ 1,500 floor).
- Subaward layer (industry products focus on prime; subaward narrative may
  have a fresher signal window).
- Real-time / streaming inference for true publish-event latency.
- Schema axis-4 (small-business set-aside vs. full-and-open competition).
        """
    )
    rigor = load_json(DATA / "rigor.json")
    if rigor:
        st.subheader("Statistical rigor (DSR + NW + bootstrap + BH-FDR)")
        st.json(rigor)


def main() -> None:
    st.set_page_config(page_title="Project M1 — USAspending Contract LLM", layout="wide")
    st.sidebar.title("Project M1")
    page = st.sidebar.radio(
        "Page",
        ["1 Universe", "2 3-axis Distribution", "3 Cross-Section Quintile",
         "4 Cohort Heterogeneity (§4.1)", "5 Methodology + Limits"],
    )
    if page == "1 Universe":
        page_1_universe()
    elif page == "2 3-axis Distribution":
        page_2_axis_distribution()
    elif page == "3 Cross-Section Quintile":
        page_3_cross_section()
    elif page == "4 Cohort Heterogeneity (§4.1)":
        page_4_cohort_heterogeneity()
    elif page == "5 Methodology + Limits":
        page_5_methodology()


if __name__ == "__main__":
    main()
