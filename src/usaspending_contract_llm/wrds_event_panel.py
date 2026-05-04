"""Day 2 — universe × CRSP × IBES 3-way join → multi-decade event-window CAR panel.

Replaces yfinance ~5yr-bound `yfinance_join.py` + `sec_event_panel.py` with:
  - CRSP daily returns (multi-decade) joined via PERMNO from `wrds_coverage_report.json`.
  - IBES earnings actuals (`act_xepsus`) + consensus (`statsumu_epsus`) for surprise.
  - Event date = IBES `anndats` (announcement date) — finer than 8-K filed date.

Output:
  data/wrds_event_panel.json — list of (ticker, anndats, quarter, eps_surprise_z,
                                event_car_3d, forward_car_3m).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .manifest import DATA_DIR
from .wrds_client import crsp_returns_for_permnos, ibes_query

COVERAGE_PATH = DATA_DIR / "wrds_coverage_report.json"
OUT_PATH = DATA_DIR / "wrds_event_panel.json"

# Hedge benchmark — CRSP S&P 500 ETF (SPY) permno = 84398 (alternative: VFINX).
# We use S&P 500 because XAR (defense ETF) only exists 2011+ and is itself
# a defense-only basket.
HEDGE_PERMNO = 84398


def _load_universe_with_permno() -> pd.DataFrame:
    """Read coverage report + filter to firms with both CRSP permno + IBES oftic."""
    if not COVERAGE_PATH.exists():
        raise RuntimeError("wrds_coverage_report.json missing -- run wrds_coverage first")
    j = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    rows = []
    for d in j.get("detail", []):
        if d.get("ibes_ok") and d.get("crsp_permno"):
            rows.append({
                "ticker":       d["ticker"],
                "permno":       d["crsp_permno"],
                "ibes_cusip":   d.get("ibes_cusip"),
            })
    return pd.DataFrame(rows)


def _ibes_actuals_consensus(ofitcs: list[str]) -> pd.DataFrame:
    """Per (oftic, fpedats) join actual EPS (from ndet_epsus) with consensus
    (from statsumu_epsus). `act_xepsus` covers non-EPS measures and is unused.
    """
    placeholders = ",".join(f"'{t}'" for t in ofitcs)

    # Actuals: take the (oftic, fpedats, anndats_act, actual) tuple from
    # ndet_epsus where actual is non-null and EPS measure. One row per analyst
    # so deduplicate by taking max(actual) per (oftic, fpedats) -- they should
    # all be the same value anyway.
    actuals = ibes_query(f"""
        SELECT oftic AS ticker,
               fpedats AS pends,
               MAX(anndats_act) AS anndats,
               MAX(actual) AS actual_eps
        FROM ibes_ndet
        WHERE oftic IN ({placeholders})
          AND measure = 'EPS'
          AND actual IS NOT NULL
          AND fpedats IS NOT NULL
          AND anndats_act IS NOT NULL
        GROUP BY oftic, fpedats
    """)

    # Consensus: pre-aggregated quarterly EPS forecast across all fpi codes.
    # Join to actuals at "most recent statpers BEFORE anndats" later.
    consensus = ibes_query(f"""
        SELECT oftic AS ticker, statpers, fpi, numest, medest, meanest, stdev
        FROM ibes_statsumu
        WHERE oftic IN ({placeholders})
          AND fiscalp = 'QTR'
          AND measure = 'EPS'
          AND numest >= 2
    """)

    if actuals.empty or consensus.empty:
        return pd.DataFrame()

    actuals["anndats_ts"] = pd.to_datetime(actuals["anndats"], errors="coerce")
    consensus["statpers_ts"] = pd.to_datetime(consensus["statpers"], errors="coerce")

    out_rows: list[dict] = []
    for ticker, g_act in actuals.groupby("ticker"):
        g_cons = consensus[consensus["ticker"] == ticker].sort_values("statpers_ts")
        for _, r in g_act.iterrows():
            ann_ts = r["anndats_ts"]
            if pd.isna(ann_ts):
                continue
            # Most recent consensus 30-90 days BEFORE announcement.
            mask = (g_cons["statpers_ts"] < ann_ts) & (g_cons["statpers_ts"] >= ann_ts - pd.Timedelta(days=120))
            window = g_cons[mask]
            if window.empty:
                continue
            latest = window.iloc[-1]
            actual = r["actual_eps"]
            medest = latest["medest"]
            stdev = latest["stdev"]
            if pd.isna(actual) or pd.isna(medest):
                continue
            denom = stdev if (pd.notna(stdev) and stdev > 0) else max(abs(medest), 0.01)
            surprise_z = (actual - medest) / denom
            out_rows.append({
                "ticker":           ticker,
                "anndats":          str(ann_ts.date()),
                "pends":            str(r["pends"])[:10],
                "actual_eps":       float(actual),
                "consensus_med":    float(medest),
                "consensus_stdev":  float(stdev) if pd.notna(stdev) else None,
                "n_estimates":      int(latest.get("numest") or 0),
                "surprise_z":       round(float(surprise_z), 4),
                "surprise_pct":     round(100 * (actual - medest) / max(abs(medest), 0.01), 2),
            })
    return pd.DataFrame(out_rows)


def _compute_car(events: pd.DataFrame, returns: pd.DataFrame, perm_map: dict[str, int]) -> pd.DataFrame:
    """For each event row, compute event-window + forward CAR using S&P-hedged returns."""
    if events.empty or returns.empty:
        return pd.DataFrame()
    returns = returns.copy()
    returns["date"] = pd.to_datetime(returns["date"], errors="coerce")
    pivot = returns.pivot_table(index="date", columns="permno", values="ret", aggfunc="first").sort_index()

    out_rows = []
    for _, ev in events.iterrows():
        ticker = ev["ticker"]
        if ticker not in perm_map:
            continue
        permno = perm_map[ticker]
        if permno not in pivot.columns:
            continue
        ann_ts = pd.Timestamp(ev["anndats"])
        try:
            i = pivot.index.get_indexer([ann_ts], method="nearest")[0]
        except Exception:
            continue
        if i < 1 or i + 63 >= len(pivot):
            continue
        evw = pivot.iloc[i - 1: i + 2][permno]
        fwd = pivot.iloc[i + 1: i + 64][permno]
        hedge_evw = pivot.iloc[i - 1: i + 2][HEDGE_PERMNO] if HEDGE_PERMNO in pivot.columns else pd.Series([0.0] * 3)
        hedge_fwd = pivot.iloc[i + 1: i + 64][HEDGE_PERMNO] if HEDGE_PERMNO in pivot.columns else pd.Series([0.0] * 63)
        if evw.isna().any():
            continue
        if fwd.isna().sum() > 5:
            continue
        car_evt = float((evw.fillna(0) - hedge_evw.fillna(0)).sum())
        car_fwd = float((fwd.fillna(0) - hedge_fwd.fillna(0)).sum())
        out_rows.append({
            "ticker":           ticker,
            "permno":           int(permno),
            "anndats":          ev["anndats"],
            "pends":            ev["pends"],
            "quarter":          str(pd.Timestamp(ev["pends"]).to_period("Q")),
            "actual_eps":       ev["actual_eps"],
            "consensus_med":    ev["consensus_med"],
            "surprise_z":       ev["surprise_z"],
            "surprise_pct":     ev["surprise_pct"],
            "event_car_3d":     round(car_evt, 6),
            "forward_car_3m":   round(car_fwd, 6),
        })
    return pd.DataFrame(out_rows)


def main() -> int:
    universe = _load_universe_with_permno()
    print(f"Universe with permno + IBES coverage: {len(universe)} firms")

    perm_map = dict(zip(universe["ticker"], universe["permno"].astype(int)))
    permnos = sorted(set(perm_map.values()) | {HEDGE_PERMNO})
    print(f"Fetching CRSP returns for {len(permnos)} permnos (incl. hedge)...")
    returns = crsp_returns_for_permnos(permnos, start_date="2000-01-01", end_date="2026-04-30")
    print(f"  -> {len(returns):,} daily-return rows.")

    print(f"Building IBES actual+consensus join...")
    events = _ibes_actuals_consensus(list(perm_map.keys()))
    print(f"  -> {len(events):,} (ticker, anndats) event rows with surprise.")

    print(f"Computing event-window + forward CAR (S&P hedged)...")
    panel = _compute_car(events, returns, perm_map)
    print(f"  -> {len(panel):,} firm-event CAR rows.")

    summary = {
        "n_universe":      int(len(universe)),
        "n_permnos":       len(permnos) - 1,
        "n_events_raw":    int(len(events)),
        "n_with_car":      int(len(panel)),
        "n_distinct_quarters": int(panel["quarter"].nunique()) if not panel.empty else 0,
        "n_distinct_tickers": int(panel["ticker"].nunique()) if not panel.empty else 0,
        "earliest_anndats": str(panel["anndats"].min()) if not panel.empty else None,
        "latest_anndats":   str(panel["anndats"].max()) if not panel.empty else None,
        "rows":            panel.to_dict(orient="records"),
    }
    OUT_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults at {OUT_PATH}")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
