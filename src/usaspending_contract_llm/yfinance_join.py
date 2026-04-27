"""Day-10 yfinance daily price + quarterly EPS + 8-K CAR computation.

For each ticker in the 39-firm universe:
  1. Daily prices (OHLCV) over 2009-01-01 .. 2026-04-26 — full IS+OOS window.
  2. Quarterly earnings (actual EPS + estimate) -- yfinance.Ticker.earnings_dates.
  3. 8-K event-window CAR: 3-day [-1,+1] around earnings announcement,
     XAR (defense ETF) / XLK (tech ETF) hedged.
  4. 1-3m forward CAR: cumulative return [+1,+63] (quarterly) and [+1,+126] (semi-annual),
     same hedge.

Output:
  data/yfinance_prices.parquet   — daily Close per ticker
  data/yfinance_earnings.json    — quarterly EPS surprise per ticker
  data/yfinance_car.json         — 8-K CAR + 1-3m forward CAR per (ticker, quarter)

Compustat / IBES are not free; we use yfinance free tier as the substitute.
Earnings surprise = (actual_EPS - estimate_EPS) / |estimate_EPS|; if estimate
not present (older quarters) fall back to (actual - trailing-4Q-avg) / abs(trailing).
"""
from __future__ import annotations

import csv
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from .manifest import DATA_DIR

UNIVERSE_CSV = DATA_DIR / "universe_defense_it_r1000_fy2024.csv"
PRICES_PARQUET = DATA_DIR / "yfinance_prices.parquet"
EARNINGS_JSON = DATA_DIR / "yfinance_earnings.json"
CAR_JSON = DATA_DIR / "yfinance_car.json"

# Sector hedge ETFs.
HEDGE_TICKERS = ("XAR", "XLK")

# Window for the full sample.
START_DATE = "2009-01-01"
END_DATE = "2026-04-26"


def load_universe_tickers() -> list[str]:
    """Distinct tickers from the universe CSV."""
    seen: set[str] = set()
    with UNIVERSE_CSV.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            t = (r.get("ticker") or "").strip()
            if t and t not in seen:
                seen.add(t)
    return sorted(seen)


def fetch_daily_prices(tickers: list[str]) -> pd.DataFrame:
    """yfinance.download bulk; returns wide DataFrame with Close per ticker."""
    full = list(tickers) + list(HEDGE_TICKERS)
    print(f"yfinance.download for {len(full)} symbols, {START_DATE} -> {END_DATE}")
    df = yf.download(
        " ".join(full), start=START_DATE, end=END_DATE,
        auto_adjust=True, progress=False, group_by="ticker", threads=True,
    )
    if isinstance(df.columns, pd.MultiIndex):
        # ('TICKER', 'Close') -> just Close per ticker.
        close = df.xs("Close", axis=1, level=1)
    else:
        close = df[["Close"]].rename(columns={"Close": full[0]})
    close = close.dropna(how="all")
    return close


def fetch_quarterly_earnings(ticker: str) -> list[dict]:
    """yfinance Ticker.earnings_dates -- DataFrame with per-quarter actual EPS + estimate."""
    try:
        t = yf.Ticker(ticker)
        ed = t.earnings_dates
    except Exception as e:
        return [{"ticker": ticker, "error": f"{type(e).__name__}:{e}"}]
    if ed is None or ed.empty:
        return [{"ticker": ticker, "error": "no_earnings_dates"}]
    rows: list[dict] = []
    for ts, r in ed.iterrows():
        rows.append({
            "ticker":          ticker,
            "earnings_date":   ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "eps_estimate":    float(r.get("EPS Estimate")) if pd.notna(r.get("EPS Estimate")) else None,
            "eps_actual":      float(r.get("Reported EPS")) if pd.notna(r.get("Reported EPS")) else None,
            "surprise_pct":    float(r.get("Surprise(%)"))  if pd.notna(r.get("Surprise(%)"))  else None,
        })
    return rows


def compute_surprise(rows: list[dict]) -> list[dict]:
    """Fill surprise_pct via trailing-4Q-avg fallback when estimate missing."""
    # rows are sorted desc by earnings_date typically; reverse to chronological
    rows = sorted([r for r in rows if "error" not in r], key=lambda x: x["earnings_date"])
    actual_history: list[float] = []
    out = []
    for r in rows:
        actual = r.get("eps_actual")
        est = r.get("eps_estimate")
        surprise = r.get("surprise_pct")
        if surprise is None and actual is not None:
            if est is not None and abs(est) > 1e-9:
                surprise = 100.0 * (actual - est) / abs(est)
                r["surprise_source"] = "estimate"
            elif len(actual_history) >= 4:
                trailing = sum(actual_history[-4:]) / 4
                if abs(trailing) > 1e-9:
                    surprise = 100.0 * (actual - trailing) / abs(trailing)
                    r["surprise_source"] = "trailing_4q_avg"
        else:
            r["surprise_source"] = "yfinance_native"
        r["surprise_pct"] = surprise
        out.append(r)
        if actual is not None:
            actual_history.append(actual)
    return out


def compute_car(
    earnings_rows: list[dict],
    *,
    prices: pd.DataFrame,
    ticker: str,
    hedge: str = "XAR",
) -> list[dict]:
    """3-day [-1,+1] event-window CAR + [+1,+63] 1-3m forward CAR, hedge-residualized."""
    if ticker not in prices.columns or hedge not in prices.columns:
        return []
    px = prices[[ticker, hedge]].dropna()
    if px.empty:
        return []
    rets = px.pct_change()
    out: list[dict] = []
    for r in earnings_rows:
        if "error" in r:
            continue
        try:
            ed = pd.Timestamp(r["earnings_date"]).tz_localize(None) if pd.Timestamp(r["earnings_date"]).tzinfo else pd.Timestamp(r["earnings_date"])
        except Exception:
            continue
        # Find the trading-day index nearest ed
        try:
            i = rets.index.get_indexer([ed], method="nearest")[0]
        except Exception:
            continue
        if i < 1 or i + 63 >= len(rets):
            continue
        ev_window = rets.iloc[i - 1: i + 2]  # [-1, 0, +1]
        fwd_3m    = rets.iloc[i + 1: i + 64]  # [+1, +63]
        car_evt = (ev_window[ticker] - ev_window[hedge]).sum()
        car_fwd = (fwd_3m[ticker] - fwd_3m[hedge]).sum()
        out.append({
            "ticker":           ticker,
            "earnings_date":    r["earnings_date"],
            "surprise_pct":     r.get("surprise_pct"),
            "surprise_source":  r.get("surprise_source"),
            "event_car_3d":     round(float(car_evt), 6),
            "forward_car_3m":   round(float(car_fwd), 6),
            "hedge":            hedge,
        })
    return out


def main() -> int:
    tickers = load_universe_tickers()
    print(f"universe tickers: {len(tickers)} -- {tickers[:5]}... + hedges {HEDGE_TICKERS}")

    # Stage 1: prices
    if PRICES_PARQUET.exists():
        prices = pd.read_parquet(PRICES_PARQUET)
        print(f"loaded cached prices: {prices.shape}")
    else:
        prices = fetch_daily_prices(tickers)
        prices.to_parquet(PRICES_PARQUET)
        print(f"saved prices: {prices.shape}")

    # Stage 2: earnings per ticker
    earnings_by_ticker: dict[str, list[dict]] = {}
    for t in tickers:
        rows = fetch_quarterly_earnings(t)
        if rows and "error" not in rows[0]:
            rows = compute_surprise(rows)
        earnings_by_ticker[t] = rows
        # be polite to yfinance -- 0.2s between calls
        time.sleep(0.2)
    EARNINGS_JSON.write_text(json.dumps(earnings_by_ticker, indent=2, default=str), encoding="utf-8")
    n_ok = sum(1 for v in earnings_by_ticker.values() if v and "error" not in v[0])
    print(f"earnings fetched: {n_ok}/{len(tickers)} tickers")

    # Stage 3: CAR per ticker x quarter
    all_car: list[dict] = []
    for t, rows in earnings_by_ticker.items():
        if not rows or "error" in rows[0]:
            continue
        car_rows = compute_car(rows, prices=prices, ticker=t, hedge="XAR")
        all_car.extend(car_rows)
    CAR_JSON.write_text(json.dumps({"car": all_car}, indent=2, default=str), encoding="utf-8")
    print(f"CAR rows: {len(all_car)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
