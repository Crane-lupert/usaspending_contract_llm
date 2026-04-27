"""SEC EDGAR submissions/filings client (Gate F LIFTED 2026-04-28).

Free public API:
  https://www.sec.gov/files/company_tickers.json   (ticker -> CIK)
  https://data.sec.gov/submissions/CIK{cik}.json   (all filings for CIK)
  https://www.sec.gov/Archives/edgar/data/{cik}/{accession}-index.htm   (per-filing)

Used to fetch:
  - 8-K filed dates per ticker (multi-decade coverage 1994+).
  - 10-Q filed dates + accession (for future XBRL EPS extraction).

Rate limit: 10 rps per User-Agent. We self-throttle at 5 rps.
NOT a daemon: synchronous httpx requests; no shared queue.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from .manifest import DATA_DIR

EDGAR_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
USER_AGENT = "M1 Research <research@m1.local>"
RATE_LIMIT_RPS = 5.0  # self-throttle, well below SEC's 10 rps cap

CIK_MAP_CACHE = DATA_DIR / "sec_ticker_cik_map.json"
FILINGS_CACHE_DIR = DATA_DIR / "cache" / "sec_edgar_submissions"
FILINGS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Filing:
    cik: int
    ticker: str
    form: str            # "8-K", "10-Q", "10-K", etc.
    filed_date: str      # "2024-09-15"
    accession: str       # "0001234567-24-000123"
    primary_document: str
    items: str = ""       # 8-K items (e.g. "1.01,9.01")


def fetch_ticker_cik_map() -> dict[str, int]:
    """Returns {ticker_upper: cik_int}. Cached on disk after first fetch."""
    if CIK_MAP_CACHE.exists():
        cached = json.loads(CIK_MAP_CACHE.read_text(encoding="utf-8"))
        return {k.upper(): int(v) for k, v in cached.items()}
    r = httpx.get(EDGAR_TICKER_MAP_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    data = r.json()
    out: dict[str, int] = {}
    for entry in data.values():
        ticker = (entry.get("ticker") or "").upper().strip()
        cik = int(entry.get("cik_str") or 0)
        if ticker and cik:
            out[ticker] = cik
    CIK_MAP_CACHE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def fetch_submissions(cik: int) -> dict:
    """Returns full /submissions/CIK{cik}.json dict. Disk-cached."""
    cache = FILINGS_CACHE_DIR / f"CIK{cik:010d}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    url = EDGAR_SUBMISSIONS_URL.format(cik=cik)
    time.sleep(1.0 / RATE_LIMIT_RPS)
    r = httpx.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    cache.write_text(json.dumps(data), encoding="utf-8")
    return data


def extract_filings(submissions: dict, *, ticker: str, forms: tuple[str, ...] = ("8-K", "10-Q", "10-K")) -> list[Filing]:
    """Pull filings of given form types from submissions JSON."""
    cik = int(submissions.get("cik", 0))
    out: list[Filing] = []
    recent = submissions.get("filings", {}).get("recent", {})
    rec_form = recent.get("form", [])
    rec_date = recent.get("filingDate", [])
    rec_acc = recent.get("accessionNumber", [])
    rec_doc = recent.get("primaryDocument", [])
    rec_items = recent.get("items", [])
    for i, form in enumerate(rec_form):
        if form not in forms:
            continue
        out.append(Filing(
            cik=cik, ticker=ticker, form=form,
            filed_date=rec_date[i] if i < len(rec_date) else "",
            accession=rec_acc[i] if i < len(rec_acc) else "",
            primary_document=rec_doc[i] if i < len(rec_doc) else "",
            items=(rec_items[i] if i < len(rec_items) else "") or "",
        ))
    # Older filings sit in additional files — submissions["filings"]["files"][i]["name"]
    for older in submissions.get("filings", {}).get("files", []):
        # older["name"] is e.g. "CIK0001234567-submissions-001.json"
        name = older.get("name", "")
        if not name:
            continue
        cache = FILINGS_CACHE_DIR / name
        if cache.exists():
            data = json.loads(cache.read_text(encoding="utf-8"))
        else:
            url = f"https://data.sec.gov/submissions/{name}"
            time.sleep(1.0 / RATE_LIMIT_RPS)
            try:
                r = httpx.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=30)
                r.raise_for_status()
                data = r.json()
                cache.write_text(json.dumps(data), encoding="utf-8")
            except Exception:
                continue
        rec_form = data.get("form", [])
        rec_date = data.get("filingDate", [])
        rec_acc = data.get("accessionNumber", [])
        rec_doc = data.get("primaryDocument", [])
        rec_items = data.get("items", [])
        for i, form in enumerate(rec_form):
            if form not in forms:
                continue
            out.append(Filing(
                cik=cik, ticker=ticker, form=form,
                filed_date=rec_date[i] if i < len(rec_date) else "",
                accession=rec_acc[i] if i < len(rec_acc) else "",
                primary_document=rec_doc[i] if i < len(rec_doc) else "",
                items=(rec_items[i] if i < len(rec_items) else "") or "",
            ))
    return out


def fetch_all_filings(tickers: list[str], *, forms: tuple[str, ...] = ("8-K", "10-Q", "10-K")) -> dict[str, list[Filing]]:
    """Returns {ticker: [Filing, ...]} for the universe. Cached per-CIK."""
    cik_map = fetch_ticker_cik_map()
    out: dict[str, list[Filing]] = {}
    for t in tickers:
        t_upper = t.upper().replace(".", "-").replace("-A", "")  # MOG.A -> MOGA-style; SEC uses MOG-A
        # Try multiple normalizations.
        cik = cik_map.get(t_upper) or cik_map.get(t.upper())
        if not cik:
            out[t] = []
            continue
        try:
            sub = fetch_submissions(cik)
        except Exception:
            out[t] = []
            continue
        out[t] = extract_filings(sub, ticker=t, forms=forms)
    return out


def main() -> int:
    """Smoke: fetch 8-K + 10-Q for our 39-ticker universe."""
    import csv
    universe_csv = DATA_DIR / "universe_defense_it_r1000_fy2024.csv"
    tickers: list[str] = []
    with universe_csv.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            t = (r.get("ticker") or "").strip()
            if t and t not in tickers:
                tickers.append(t)
    print(f"universe tickers: {len(tickers)}")
    t0 = time.monotonic()
    filings = fetch_all_filings(tickers, forms=("8-K", "10-Q", "10-K"))
    dt = time.monotonic() - t0
    summary: dict[str, dict] = {}
    for t, fs in filings.items():
        if not fs:
            summary[t] = {"n_filings": 0, "n_8k": 0, "n_10q": 0, "n_10k": 0}
            continue
        forms_count: dict[str, int] = {}
        for f in fs:
            forms_count[f.form] = forms_count.get(f.form, 0) + 1
        # filed_date range
        dates = sorted([f.filed_date for f in fs if f.filed_date])
        summary[t] = {
            "n_filings": len(fs),
            "n_8k":     forms_count.get("8-K", 0),
            "n_10q":    forms_count.get("10-Q", 0),
            "n_10k":    forms_count.get("10-K", 0),
            "earliest": dates[0] if dates else "",
            "latest":   dates[-1] if dates else "",
        }
    out_path = DATA_DIR / "sec_edgar_filings_summary.json"
    out_path.write_text(json.dumps({"elapsed_sec": round(dt, 1), "by_ticker": summary},
                                    indent=2, default=str), encoding="utf-8")
    print(f"elapsed: {dt:.1f}s")
    print(json.dumps(summary, indent=2, default=str)[:2000])
    # Save filings to a flat manifest
    flat = []
    for t, fs in filings.items():
        for f in fs:
            flat.append({
                "ticker":             f.ticker,
                "cik":                f.cik,
                "form":               f.form,
                "filed_date":         f.filed_date,
                "accession":          f.accession,
                "primary_document":   f.primary_document,
                "items":              f.items,
            })
    flat_path = DATA_DIR / "sec_edgar_filings.jsonl"
    with flat_path.open("w", encoding="utf-8") as fh:
        for r in flat:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"wrote {len(flat)} filings to {flat_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
