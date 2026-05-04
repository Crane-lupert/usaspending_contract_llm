"""Day 1 — universe × CRSP × IBES coverage measurement.

Determines how many of M1's 39-ticker universe can be resolved to:
  - CRSP permno (daily price/return for CAR computation)
  - IBES oftic (analyst forecast / actual EPS for surprise)

Phase 0 EOD kill-gate thresholds:
  - Compustat / CRSP coverage >= 95%
  - IBES coverage >= 80%

Output: data/wrds_coverage_report.json
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd

from .manifest import DATA_DIR
from .wrds_client import crsp_query, ibes_query

UNIVERSE_CSV = DATA_DIR / "universe_defense_it_r1000_fy2024.csv"
OUT = DATA_DIR / "wrds_coverage_report.json"


def load_distinct_tickers() -> list[str]:
    seen: list[str] = []
    with UNIVERSE_CSV.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            t = (r.get("ticker") or "").strip()
            if t and t not in seen:
                seen.append(t)
    return sorted(seen)


def resolve_ibes(tickers: list[str]) -> dict[str, dict | None]:
    """For each ticker -> (ibes_ticker, cusip, n_summary_rows, date_range) or None."""
    if not tickers:
        return {}
    placeholders = ",".join(f"'{t}'" for t in tickers)
    df = ibes_query(f"""
        SELECT oftic, ticker AS ibes_ticker, cusip, cname,
               COUNT(*) AS n,
               MIN(statpers) AS min_statpers,
               MAX(statpers) AS max_statpers
        FROM ibes_statsumu
        WHERE oftic IN ({placeholders}) AND fiscalp = 'QTR' AND measure = 'EPS'
        GROUP BY oftic, ibes_ticker, cusip, cname
    """)
    out: dict[str, dict | None] = {t: None for t in tickers}
    if df.empty:
        return out
    # If multiple rows per oftic (re-name history), keep the row with most n.
    df = df.sort_values("n", ascending=False)
    for _, r in df.iterrows():
        oft = r["oftic"]
        if out.get(oft) is None:
            out[oft] = {
                "ibes_ticker":   r["ibes_ticker"],
                "cusip":         r["cusip"],
                "cname":         r["cname"],
                "n_summary":     int(r["n"]),
                "min_statpers":  str(r["min_statpers"])[:10],
                "max_statpers":  str(r["max_statpers"])[:10],
            }
    return out


def resolve_crsp_via_dseall(tickers: list[str]) -> dict[str, dict | None]:
    """Direct ticker -> permno via crsp_a_stock.dseall (CRSP names file).

    Catches firms that the CUSIP-via-IBES path misses (recent IPO without
    IBES coverage, ADRs registered under different CUSIP, etc.).
    """
    if not tickers:
        return {}
    placeholders = ",".join(f"'{t}'" for t in tickers)
    df = crsp_query(f"""
        SELECT ticker, permno, comnam,
               COUNT(*) AS n, MIN(date) AS min_d, MAX(date) AS max_d
        FROM crsp_a_stock.dseall
        WHERE ticker IN ({placeholders})
        GROUP BY ticker, permno, comnam
        ORDER BY ticker, n DESC
    """)
    out: dict[str, dict | None] = {t: None for t in tickers}
    for _, r in df.iterrows():
        t = r["ticker"]
        if out.get(t) is None:  # keep first (most-rows) per ticker
            out[t] = {
                "permno": int(r["permno"]),
                "comnam": r["comnam"],
                "n":      int(r["n"]),
                "min_d":  str(r["min_d"])[:10],
                "max_d":  str(r["max_d"])[:10],
            }
    return out


def resolve_crsp_via_cusip(cusip6_list: list[str]) -> dict[str, list[dict]]:
    """For each CUSIP-6 prefix -> [{permno, min_d, max_d, n}] in CRSP dsf."""
    if not cusip6_list:
        return {}
    placeholders = ",".join(f"'{c}'" for c in cusip6_list)
    df = crsp_query(f"""
        SELECT permno, SUBSTR(cusip, 1, 6) AS cusip6,
               MIN(date) AS min_d, MAX(date) AS max_d, COUNT(*) AS n
        FROM crsp_a_stock.dsf
        WHERE SUBSTR(cusip, 1, 6) IN ({placeholders})
        GROUP BY permno, cusip6
        HAVING n >= 100
        ORDER BY n DESC
    """)
    out: dict[str, list[dict]] = {c: [] for c in cusip6_list}
    for _, r in df.iterrows():
        out[r["cusip6"]].append({
            "permno": int(r["permno"]),
            "min_d":  str(r["min_d"])[:10],
            "max_d":  str(r["max_d"])[:10],
            "n":      int(r["n"]),
        })
    return out


def main() -> int:
    tickers = load_distinct_tickers()
    print(f"distinct tickers in universe: {len(tickers)}")
    print(f"sample: {tickers[:8]}...")

    # Stage 1: IBES coverage via oftic.
    ibes = resolve_ibes(tickers)
    n_ibes_ok = sum(1 for v in ibes.values() if v is not None)
    pct_ibes = round(100 * n_ibes_ok / len(tickers), 1)
    print(f"\nIBES coverage: {n_ibes_ok}/{len(tickers)} = {pct_ibes}%")

    # Stage 2a: CRSP coverage via CUSIP-6 from IBES.
    cusip6_to_tickers: dict[str, list[str]] = {}
    for t, info in ibes.items():
        if info and info.get("cusip"):
            cusip6 = info["cusip"][:6]
            cusip6_to_tickers.setdefault(cusip6, []).append(t)
    crsp_by_cusip6 = resolve_crsp_via_cusip(list(cusip6_to_tickers.keys()))
    crsp_by_ticker: dict[str, list[dict]] = {t: [] for t in tickers}
    for cusip6, ticker_list in cusip6_to_tickers.items():
        permnos = crsp_by_cusip6.get(cusip6, [])
        for t in ticker_list:
            crsp_by_ticker[t] = permnos

    # Stage 2b: direct ticker probe via dseall for tickers still unresolved.
    unresolved = [t for t, v in crsp_by_ticker.items() if not v]
    if unresolved:
        dseall_lookup = resolve_crsp_via_dseall(unresolved)
        for t, info in dseall_lookup.items():
            if info:
                crsp_by_ticker[t] = [{
                    "permno": info["permno"],
                    "min_d":  info["min_d"],
                    "max_d":  info["max_d"],
                    "n":      info["n"],
                    "source": "dseall",
                }]

    n_crsp_ok = sum(1 for v in crsp_by_ticker.values() if v)
    pct_crsp = round(100 * n_crsp_ok / len(tickers), 1)
    print(f"CRSP coverage (via IBES CUSIP): {n_crsp_ok}/{len(tickers)} = {pct_crsp}%")

    # Per-ticker detailed report
    detail = []
    for t in tickers:
        ibes_info = ibes.get(t)
        crsp_info = crsp_by_ticker.get(t, [])
        detail.append({
            "ticker":           t,
            "ibes_ok":          ibes_info is not None,
            "ibes_min_statpers": (ibes_info or {}).get("min_statpers"),
            "ibes_max_statpers": (ibes_info or {}).get("max_statpers"),
            "ibes_cusip":       (ibes_info or {}).get("cusip"),
            "n_ibes_summary":   (ibes_info or {}).get("n_summary"),
            "crsp_permno":      crsp_info[0]["permno"] if crsp_info else None,
            "crsp_min_d":       crsp_info[0]["min_d"] if crsp_info else None,
            "crsp_max_d":       crsp_info[0]["max_d"] if crsp_info else None,
            "n_crsp_dsf":       crsp_info[0]["n"] if crsp_info else None,
        })

    summary = {
        "n_universe":      len(tickers),
        "n_ibes_ok":       n_ibes_ok,
        "pct_ibes":        pct_ibes,
        "n_crsp_ok":       n_crsp_ok,
        "pct_crsp":        pct_crsp,
        "ibes_threshold":  80.0,
        "crsp_threshold":  95.0,
        "ibes_pass":       pct_ibes >= 80.0,
        "crsp_pass":       pct_crsp >= 95.0,
        "detail":          detail,
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nReport written to {OUT}")
    print(f"\nUnmapped tickers (no IBES): {[r['ticker'] for r in detail if not r['ibes_ok']]}")
    print(f"Unmapped tickers (no CRSP): {[r['ticker'] for r in detail if r['crsp_permno'] is None]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
