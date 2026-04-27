"""Build firm-quarter event-window CAR panel using SEC 8-K filed_dates.

Replaces yfinance.earnings_dates (~5yr cap) with SEC EDGAR 8-K Item 2.02
(Results of Operations and Financial Condition) filed_dates. Multi-decade
coverage 1994/2000+ for most firms.

Output:
  data/sec_event_panel.json -- list of (ticker, filed_date, quarter,
                                event_car_3d, forward_car_3m).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .manifest import DATA_DIR

FILINGS_JSONL = DATA_DIR / "sec_edgar_filings.jsonl"
PRICES_PARQUET = DATA_DIR / "yfinance_prices.parquet"
OUT = DATA_DIR / "sec_event_panel.json"

HEDGE = "XAR"


def load_earnings_8ks() -> pd.DataFrame:
    rows: list[dict] = []
    with FILINGS_JSONL.open("r", encoding="utf-8") as fh:
        for ln in fh:
            r = json.loads(ln)
            if r["form"] != "8-K":
                continue
            items = (r.get("items") or "").replace(" ", "")
            if "2.02" not in items:
                continue
            rows.append({
                "ticker":        r["ticker"],
                "filed_date":    r["filed_date"],
                "accession":     r["accession"],
                "items":         items,
            })
    df = pd.DataFrame(rows)
    df["filed_ts"] = pd.to_datetime(df["filed_date"], errors="coerce")
    df = df.dropna(subset=["filed_ts"])
    df["quarter"] = df["filed_ts"].dt.to_period("Q").astype(str)
    return df


def compute_event_car(events: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    out_rows: list[dict] = []
    if HEDGE not in prices.columns:
        return pd.DataFrame()
    rets = prices.pct_change()
    for t in events["ticker"].unique():
        if t not in prices.columns:
            continue
        ticker_events = events[events["ticker"] == t]
        for _, ev in ticker_events.iterrows():
            ed = pd.Timestamp(ev["filed_ts"])
            try:
                i = rets.index.get_indexer([ed], method="nearest")[0]
            except Exception:
                continue
            if i < 1 or i + 63 >= len(rets):
                continue
            ev_window = rets.iloc[i - 1: i + 2]
            fwd_3m = rets.iloc[i + 1: i + 64]
            if ev_window[t].isna().any() or ev_window[HEDGE].isna().any():
                continue
            if fwd_3m[t].isna().sum() > 5:  # too many gaps
                continue
            car_evt = (ev_window[t] - ev_window[HEDGE]).sum()
            car_fwd = (fwd_3m[t] - fwd_3m[HEDGE]).sum()
            out_rows.append({
                "ticker":           t,
                "filed_date":       ev["filed_date"],
                "quarter":          ev["quarter"],
                "event_car_3d":     round(float(car_evt), 6),
                "forward_car_3m":   round(float(car_fwd), 6),
                "hedge":            HEDGE,
            })
    return pd.DataFrame(out_rows)


def aggregate_to_firm_quarter(car_df: pd.DataFrame) -> pd.DataFrame:
    """Multiple 8-Ks per quarter possible (corrections + restatements). Aggregate by mean."""
    if car_df.empty:
        return car_df
    g = car_df.groupby(["ticker", "quarter"]).agg(
        event_car_3d=("event_car_3d", "mean"),
        forward_car_3m=("forward_car_3m", "mean"),
        n_events_in_quarter=("filed_date", "count"),
    ).reset_index()
    return g


def main() -> int:
    if not FILINGS_JSONL.exists():
        print("ERR: sec_edgar_filings.jsonl missing -- run sec_edgar_client first")
        return 1
    if not PRICES_PARQUET.exists():
        print("ERR: yfinance_prices.parquet missing")
        return 1

    events = load_earnings_8ks()
    print(f"earnings 8-Ks (Item 2.02): {len(events)} rows; tickers={events['ticker'].nunique()}")
    print(f"date range: {events['filed_date'].min()} to {events['filed_date'].max()}")

    prices = pd.read_parquet(PRICES_PARQUET)
    print(f"yfinance prices shape: {prices.shape}")

    car_df = compute_event_car(events, prices)
    print(f"CAR computed for {len(car_df)} events")

    car_q = aggregate_to_firm_quarter(car_df)
    print(f"firm-quarter aggregated: {len(car_q)} rows")
    print(f"distinct tickers: {car_q['ticker'].nunique() if not car_q.empty else 0}")
    print(f"distinct quarters: {car_q['quarter'].nunique() if not car_q.empty else 0}")

    OUT.write_text(json.dumps({
        "n_events_raw":           int(len(car_df)),
        "n_firm_quarter":         int(len(car_q)),
        "n_distinct_tickers":     int(car_q["ticker"].nunique()) if not car_q.empty else 0,
        "n_distinct_quarters":    int(car_q["quarter"].nunique()) if not car_q.empty else 0,
        "earliest_quarter":       car_q["quarter"].min() if not car_q.empty else None,
        "latest_quarter":         car_q["quarter"].max() if not car_q.empty else None,
        "rows":                   car_q.to_dict(orient="records"),
    }, indent=2, default=str), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
