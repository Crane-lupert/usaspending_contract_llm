"""WRDS data access (Recovery 2026-05-04).

Replaces yfinance free-tier (~5yr cap) with:
  - CRSP daily stock file (1925+ multi-decade) via wrds_courier_client.
  - IBES analyst forecasts (consensus + actuals) via direct DuckDB read_csv
    (the courier strict_mode rejects IBES quoting; we use ignore_errors).

CCM (crsp_a_ccm) is BLOCKED at WRDS USAGE permission level. We bypass via
ticker -> CUSIP -> CRSP permno chain (no CCM linktable needed).

Project M1 universe: 39 publicly-traded R1000 defense/IT primes.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd

# WRDS courier client (CRSP path).
sys.path.insert(0, "e:/wrds-data-courier/src")
from wrds_courier_client import query as courier_query  # type: ignore

WRDS_DUMP_ROOT = Path("E:/wrds-data-courier/output/dump")

IBES_STATSUMU = WRDS_DUMP_ROOT / "tr_ibes.statsumu_epsus.csv.gz"
IBES_ACTXEPS = WRDS_DUMP_ROOT / "tr_ibes.act_xepsus.csv.gz"


IBES_NDET = WRDS_DUMP_ROOT / "tr_ibes.ndet_epsus.csv.gz"


@lru_cache(maxsize=1)
def _ibes_con() -> duckdb.DuckDBPyConnection:
    """Local DuckDB connection with permissive views for IBES (ignore_errors).

    `ndet_epsus` (35M rows) is the analyst-detail file — has both `value`
    (estimate) and `actual` (EPS reported). `statsumu_epsus` is pre-aggregated
    consensus. `act_xepsus` covers non-EPS measures (sales, BPS, etc.).
    """
    con = duckdb.connect()
    for name, path in [
        ("ibes_statsumu", IBES_STATSUMU),
        ("ibes_actxeps",  IBES_ACTXEPS),
        ("ibes_ndet",     IBES_NDET),
    ]:
        con.execute(f"""
            CREATE VIEW {name} AS
            SELECT * FROM read_csv(
                '{path.as_posix()}',
                ignore_errors = true,
                strict_mode = false,
                null_padding = true,
                header = true,
                all_varchar = false
            )
        """)
    return con


def crsp_query(sql: str) -> pd.DataFrame:
    """Run query on CRSP / Compustat via wrds_courier_client (DuckDB views over CSV)."""
    return courier_query(sql)


def ibes_query(sql: str) -> pd.DataFrame:
    """Run query on IBES via local DuckDB with ignore_errors."""
    return _ibes_con().execute(sql).df()


def crsp_returns_for_permnos(
    permnos: list[int],
    *,
    start_date: str = "2000-01-01",
    end_date: str = "2026-04-30",
) -> pd.DataFrame:
    """Daily returns from CRSP modern stkdlysecuritydata for given permnos."""
    if not permnos:
        return pd.DataFrame(columns=["permno", "date", "ret", "prc"])
    permno_list = ",".join(str(int(p)) for p in permnos)
    return crsp_query(f"""
        SELECT permno, dlycaldt AS date, dlyret AS ret, dlyprc AS prc
        FROM crsp_a_stock.stkdlysecuritydata
        WHERE permno IN ({permno_list})
          AND dlycaldt BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY permno, dlycaldt
    """)


def crsp_permno_for_cusip_prefix(cusip6: str) -> list[dict]:
    """Resolve CUSIP-6 prefix to all matching CRSP permnos + date ranges."""
    return crsp_query(f"""
        SELECT permno, MIN(date) AS min_d, MAX(date) AS max_d, COUNT(*) AS n
        FROM crsp_a_stock.dsf
        WHERE cusip LIKE '{cusip6}%'
        GROUP BY permno
        ORDER BY n DESC
    """).to_dict(orient="records")


def ibes_eps_summary_for_oftic(
    oftic: str,
    *,
    fiscalp: str = "QTR",
    measure: str = "EPS",
) -> pd.DataFrame:
    """Per-quarter consensus EPS (median + mean + n) for an exchange ticker."""
    return ibes_query(f"""
        SELECT statpers, fpi, numest, medest, meanest, stdev, highest, lowest
        FROM ibes_statsumu
        WHERE oftic = '{oftic}'
          AND fiscalp = '{fiscalp}'
          AND measure = '{measure}'
          AND fpi = 6  -- forward 1 quarter
        ORDER BY statpers
    """)


def ibes_eps_actual_for_oftic(
    oftic: str,
    *,
    pdicity: str = "QTR",
    measure: str = "EPS",
) -> pd.DataFrame:
    """Per-quarter actual EPS (announced) for an exchange ticker."""
    return ibes_query(f"""
        SELECT pends, anndats, value AS actual_eps
        FROM ibes_actxeps
        WHERE oftic = '{oftic}'
          AND pdicity = '{pdicity}'
          AND measure = '{measure}'
        ORDER BY pends
    """)


def smoke_test() -> dict:
    """Day 1 smoke: LMT permno + IBES oftic resolution."""
    out: dict = {"crsp": None, "ibes": None}
    crsp_df = crsp_query("""
        SELECT permno, MIN(dlycaldt) AS min_d, MAX(dlycaldt) AS max_d, COUNT(*) AS n
        FROM crsp_a_stock.stkdlysecuritydata
        WHERE permno IN (SELECT DISTINCT permno FROM crsp_a_stock.dsf WHERE cusip LIKE '53983%')
        GROUP BY permno
        ORDER BY n DESC
        LIMIT 3
    """)
    out["crsp"] = crsp_df.to_dict(orient="records")

    ibes_df = ibes_query("""
        SELECT ticker, oftic, cname, COUNT(*) n, MIN(statpers) min_d, MAX(statpers) max_d
        FROM ibes_statsumu
        WHERE oftic = 'LMT' AND fiscalp = 'QTR' AND measure = 'EPS'
        GROUP BY ticker, oftic, cname
    """)
    out["ibes"] = ibes_df.to_dict(orient="records")
    return out


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(smoke_test(), indent=2, default=str))
