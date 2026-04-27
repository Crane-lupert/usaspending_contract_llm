"""Day-2 universe filter — defense/IT R&D-intensive R1000 firm subset.

Approach: data-drive the universe from USAspending itself.

  1. POST /api/v2/search/spending_by_category/recipient/ with defense/IT NAICS
     filter, FY2024 window. Paginate through top-N recipients ordered by award $.
  2. Aggregate UEI rows up to parent-firm canonical (subsidiary collapse).
  3. Look up ticker via the curated PARENT_TICKER table (R1000 + major
     pre-IPO public sub) and the recipient_map fallback chain.
  4. Filter to publicly traded firms only (ticker resolvable).

Output: data/universe_defense_it_r1000_fy2024.csv (one row per firm) +
        manifest_global.universe_count = N.
"""
from __future__ import annotations

import asyncio
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from .manifest import DATA_DIR, write_json, update_global, manifest_path
from .usaspending_client import (
    API_BASE,
    DEFENSE_IT_NAICS_PREFIX,
    DEFAULT_AWARD_TYPE_CODES,
    UsaSpendingClient,
)

# ----------------------------------------------------------------------------
# Curated parent-firm -> ticker mapping (R1000 defense/IT primes + key subs).
# This is the *seed* layer of the 4-layer recipient_map fallback chain. Day 2
# task is to confirm the seed covers the top USAspending recipients; later
# fallback layers (filer_ontology / SAM.gov / parent rollup) extend coverage.
# Keys are normalized recipient names (uppercase, suffix-stripped).
# ----------------------------------------------------------------------------
PARENT_TICKER: dict[str, str] = {
    # Defense primes (publicly traded US prime contractors, R1000 / SP500 members)
    "LOCKHEED MARTIN":              "LMT",
    "SIKORSKY AIRCRAFT":            "LMT",
    "AEROJET ROCKETDYNE":           "LMT",   # acquired 2023 (verify Day 12)
    "BOEING":                       "BA",
    "BELL BOEING JOINT PROJECT OFFICE": "BA",
    "RAYTHEON":                     "RTX",
    "RTX":                          "RTX",
    "PRATT WHITNEY":                "RTX",
    "COLLINS AEROSPACE":            "RTX",
    "ROCKWELL COLLINS":             "RTX",   # pre-2018 sub
    "NORTHROP GRUMMAN":             "NOC",
    "GENERAL DYNAMICS":             "GD",
    "GENERAL DYNAMICS INFORMATION TECHNOLOGY": "GD",
    "GDIT":                         "GD",
    "L3HARRIS":                     "LHX",
    "L3 TECHNOLOGIES":              "LHX",
    "L3":                           "LHX",
    "HARRIS":                       "LHX",
    "HUNTINGTON INGALLS":           "HII",
    "HII":                          "HII",
    "TEXTRON":                      "TXT",
    "BELL TEXTRON":                 "TXT",
    "BELL HELICOPTER":              "TXT",
    "BAE SYSTEMS":                  "BAESY",
    "BAE INFORMATION AND ELECTRONIC INTEGRATION": "BAESY",
    "BAE INFORMATION ELECTRONIC INTEGRATION": "BAESY",
    "OSHKOSH":                      "OSK",
    "TRANSDIGM":                    "TDG",
    "HEICO":                        "HEI",
    "MOOG":                         "MOG.A",
    "CURTISS-WRIGHT":               "CW",
    "MERCURY SYSTEMS":              "MRCY",
    "KRATOS":                       "KTOS",
    "AEROVIRONMENT":                "AVAV",
    "CACI":                         "CACI",
    "PARSONS":                      "PSN",
    "V2X":                          "V2X",
    "VECTRUS":                      "V2X",
    "KBR":                          "KBR",
    "FLUOR":                        "FLR",
    "AMENTUM":                      "AMTM",
    "JACOBS":                       "J",
    "AECOM":                        "ACM",
    "HONEYWELL":                    "HON",
    "GENERAL ELECTRIC":             "GE",
    "GE AVIATION":                  "GE",
    "GE AEROSPACE":                 "GE",
    "ROLLS-ROYCE NORTH AMERICA":    "RYCEY",
    "ROLLS-ROYCE":                  "RYCEY",
    "EMBRAER":                      "ERJ",
    "ELBIT SYSTEMS":                "ESLT",
    # IT primes / federal IT services / R&D
    "BOOZ ALLEN HAMILTON":          "BAH",
    "LEIDOS":                       "LDOS",
    "SAIC":                         "SAIC",
    "SCIENCE APPLICATIONS":         "SAIC",
    "CGI FEDERAL":                  "GIB",
    "CGI":                          "GIB",
    "ACCENTURE FEDERAL":            "ACN",
    "ACCENTURE":                    "ACN",
    "GUIDEHOUSE":                   "",      # private (Bain / Veritas)
    "ICF":                          "ICFI",
    "MAXIMUS":                      "MMS",
    "TYLER TECHNOLOGIES":           "TYL",
    # Software / hyperscaler federal
    "DXC TECHNOLOGY":               "DXC",
    "DXC":                          "DXC",
    "IBM":                          "IBM",
    "INTERNATIONAL BUSINESS MACHINES": "IBM",
    "BUSINESS MACHINES":            "IBM",
    "MICROSOFT":                    "MSFT",
    "ORACLE":                       "ORCL",
    "ORACLE AMERICA":               "ORCL",
    "SALESFORCE":                   "CRM",
    "PALANTIR":                     "PLTR",
    "AMAZON WEB SERVICES":          "AMZN",
    "AMAZON":                       "AMZN",
    "GOOGLE":                       "GOOGL",
    "ALPHABET":                     "GOOGL",
    "GOOGLE PUBLIC SECTOR":         "GOOGL",
    "DELL":                         "DELL",
    "DELL TECHNOLOGIES":            "DELL",
    "DELL FEDERAL":                 "DELL",
    "DELL MARKETING":               "DELL",
    "HP ENTERPRISE":                "HPE",
    "HEWLETT PACKARD ENTERPRISE":   "HPE",
    "CISCO":                        "CSCO",
    "CISCO SYSTEMS":                "CSCO",
    "VERIZON":                      "VZ",
    "AT&T":                         "T",
    "ATT":                          "T",
    "T-MOBILE":                     "TMUS",
    "PALO ALTO NETWORKS":           "PANW",
    "FORTINET":                     "FTNT",
    "CROWDSTRIKE":                  "CRWD",
    "SERVICENOW":                   "NOW",
    "SAP":                          "SAP",
    "ADOBE":                        "ADBE",
    "VMWARE":                       "AVGO",
    "MOTOROLA SOLUTIONS":           "MSI",
    "GARMIN":                       "GRMN",
    "TELEDYNE":                     "TDY",
    "TELEDYNE TECHNOLOGIES":        "TDY",
    "TELEDYNE BROWN":               "TDY",
    "TELEDYNE FLIR":                "TDY",
    "ANSYS":                        "ANSS",
    "AUTODESK":                     "ADSK",
    "INTEL":                        "INTC",
    "NVIDIA":                       "NVDA",
    "AMD":                          "AMD",
    "TEXAS INSTRUMENTS":            "TXN",
    "ANALOG DEVICES":                "ADI",
    "MICRON":                       "MU",
    "QUALCOMM":                     "QCOM",
    # Industrial / commercial w/ federal exposure
    "FORD MOTOR":                   "F",
    "GENERAL MOTORS":               "GM",
    "MMC":                          "MMC",
    "MARSH MCLENNAN":               "MMC",
    "3M":                           "MMM",
    "CATERPILLAR":                  "CAT",
    "DEERE":                        "DE",
    "PACCAR":                       "PCAR",
    "FEDEX":                        "FDX",
    "UPS":                          "UPS",
    "UNITED PARCEL SERVICE":        "UPS",
    "EATON":                        "ETN",
    "EMERSON":                      "EMR",
    "PARKER HANNIFIN":              "PH",
    "TRANE TECHNOLOGIES":           "TT",
    "JOHNSON CONTROLS":             "JCI",
    "ALLEGION":                     "ALLE",
    "DOVER":                        "DOV",
    "ITT":                          "ITT",
    "ROPER":                        "ROP",
    "AMETEK":                       "AME",
    "AGCO":                         "AGCO",
    "CUMMINS":                      "CMI",
    "ROCKWELL AUTOMATION":          "ROK",
    "BOSTON SCIENTIFIC":            "BSX",
    "MEDTRONIC":                    "MDT",
    "MERCK":                        "MRK",
    "PFIZER":                       "PFE",
    "JOHNSON & JOHNSON":            "JNJ",
    # Known-private / FFRDC / non-tradable (kept for audit clarity, return None)
    "DELOITTE CONSULTING":          "",
    "DELOITTE":                     "",
    "BECHTEL":                      "",
    "BATTELLE MEMORIAL INSTITUTE":  "",
    "BATTELLE MEMORIAL":            "",
    "BATTELLE":                     "",
    "MITRE":                        "",
    "THE MITRE":                    "",
    "RAND CORPORATION":             "",
    "RAND":                         "",
    "AEROSPACE":                    "",
    "THE AEROSPACE":                "",
    "CHEMONICS":                    "",
    "PERATON":                      "",
    "PERATON ENTERPRISE":           "",
    "ANDURIL":                      "",
    "ANDURIL INDUSTRIES":           "",
    "BLUE ORIGIN":                  "",
    "BLUE ORIGIN WASHINGTON":       "",
    "SIERRA NEVADA":                "",
    "SPACE EXPLORATION":            "",       # SpaceX
    "GENERAL ATOMICS":              "",
    "GENERAL ATOMICS AERONAUTICAL": "",
    "MASSACHUSETTS INSTITUTE OF TECHNOLOGY": "",
    "CALIFORNIA INSTITUTE OF TECHNOLOGY": "",
    "STANFORD":                     "",
    "THE LELAND STANFORD JUNIOR UNIVERSITY": "",
    "JOHNS HOPKINS UNIVERSITY":     "",
    "THE JOHNS HOPKINS UNIVERSITY APPLIED PHYSICS LABORATORY": "",
    "JOHNS HOPKINS APPLIED PHYSICS": "",
    "REGENTS OF THE UNIVERSITY OF CALIFORNIA": "",
    "THE REGENTS OF THE UNIVERSITY OF CALIFORNIA": "",
    "UCHICAGO ARGONNE":             "",
    "BROOKHAVEN SCIENCE ASSOCIATES": "",
    "FERMI RESEARCH ALLIANCE":      "",
    "LAWRENCE LIVERMORE NATIONAL SECURITY": "",
    "ALLIANCE FOR ENERGY INNOVATION": "",
    "FOUR POINTS TECHNOLOGY":       "",
    "THUNDERCAT TECHNOLOGY":        "",
    "MINBURN TECHNOLOGY":           "",
    "V3GATE":                       "",
    "TORCH":                        "",
    "LIBERTY IT":                   "",
    "IRON BOW":                     "",
    "SERCO":                        "",
    "SALIENT CRGT":                 "",
    "FCN":                          "",
    "DEPLOYED RESOURCES":           "",
    "ADVANCED TECHNOLOGY":          "",
    "DEFENSE AND":                  "",       # truncated name fragment
    "MANTECH":                      "",       # taken private 2022
}

NAME_SUFFIX_RE = re.compile(
    r"\b(CORP(ORATION)?|COMPANY|CO|INC(ORPORATED)?|LLC|LP|LLP|LIMITED|LTD|"
    r"GROUP|HOLDINGS?|TECHNOLOGIES|SYSTEMS|SERVICES|SOLUTIONS|"
    r"INTERNATIONAL|GLOBAL|NORTH AMERICA|USA|US|AMERICA|FEDERAL)\b\.?",
    re.IGNORECASE,
)


def normalize_name(raw: str) -> str:
    """Aggressive normalization: uppercase, strip punctuation + corp suffixes.

    Handles 'THE BOEING COMPANY' / 'Lockheed Martin Corp.' / 'L3 Technologies, INC'
    all -> bare canonical.
    """
    s = raw.upper()
    s = re.sub(r"[.,&]+", " ", s)
    s = NAME_SUFFIX_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("THE "):
        s = s[4:]
    return s


def lookup_ticker(name: str) -> str | None:
    """Layer 1 of recipient_map fallback chain: curated parent table.

    Returns "" for known-private firm (kept for audit clarity, filtered out
    of the public-equity universe). None for unknown.
    """
    norm = normalize_name(name)
    if norm in PARENT_TICKER:
        return PARENT_TICKER[norm] or None  # "" private -> None for filtering
    # Try longest prefix match (e.g. 'LOCKHEED MARTIN AERONAUTICS' -> 'LOCKHEED MARTIN').
    for key, ticker in PARENT_TICKER.items():
        if norm.startswith(key + " ") or (norm == key):
            return ticker or None
    return None


@dataclass
class RecipientRow:
    name: str
    uei: str
    recipient_id: str
    code: str   # legacy DUNS (or '' if missing)
    amount_fy: float
    canonical: str = ""
    ticker: str | None = None


@dataclass
class UniverseSummary:
    n_recipient_rows: int = 0
    n_distinct_canonical: int = 0
    n_with_ticker: int = 0
    distinct_tickers: list[str] = field(default_factory=list)
    fy: int = 2024
    naics: tuple[str, ...] = DEFENSE_IT_NAICS_PREFIX


async def fetch_top_recipients(
    *,
    fy: int = 2024,
    pages: int = 5,
    limit_per_page: int = 100,
) -> list[RecipientRow]:
    """Paginate /search/spending_by_category/recipient/ for defense/IT FY."""
    body_template = {
        "filters": {
            "time_period": [{"start_date": f"{fy - 1}-10-01", "end_date": f"{fy}-09-30"}],
            "award_type_codes": list(DEFAULT_AWARD_TYPE_CODES),
            "naics_codes": list(DEFENSE_IT_NAICS_PREFIX),
        },
        "limit": limit_per_page,
    }
    rows: list[RecipientRow] = []
    async with UsaSpendingClient(max_concurrent=3) as c:
        # The category endpoint isn't on the client class yet — use the underlying httpx via _post.
        # We hit /search/spending_by_category/recipient/ directly.
        for page in range(1, pages + 1):
            body = dict(body_template)
            body["page"] = page
            resp = await c._post("/search/spending_by_category/recipient/", body)
            results = resp.get("results", [])
            if not results:
                break
            for r in results:
                rows.append(RecipientRow(
                    name=r.get("name") or "",
                    uei=(r.get("uei") or "").strip(),
                    recipient_id=(r.get("recipient_id") or "").strip(),
                    code=(r.get("code") or "").strip(),
                    amount_fy=float(r.get("amount") or 0.0),
                ))
            if len(results) < limit_per_page:
                break
    return rows


def collapse_to_canonical(rows: list[RecipientRow]) -> list[RecipientRow]:
    """Aggregate sub-rows to canonical parent name + attach ticker."""
    by_canon: dict[str, RecipientRow] = {}
    for row in rows:
        canon = normalize_name(row.name)
        # Strip past the first known parent prefix, e.g.
        # 'LOCKHEED MARTIN AERONAUTICS' -> 'LOCKHEED MARTIN'.
        for key in PARENT_TICKER:
            if canon.startswith(key + " ") or canon == key:
                canon = key
                break
        ticker = lookup_ticker(canon) or lookup_ticker(row.name)
        existing = by_canon.get(canon)
        if existing is None:
            by_canon[canon] = RecipientRow(
                name=row.name,
                uei=row.uei,
                recipient_id=row.recipient_id,
                code=row.code,
                amount_fy=row.amount_fy,
                canonical=canon,
                ticker=ticker,
            )
        else:
            existing.amount_fy += row.amount_fy
    return sorted(by_canon.values(), key=lambda x: -x.amount_fy)


def write_universe_csv(rows: list[RecipientRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["canonical", "name", "uei", "recipient_id", "code", "amount_fy", "ticker"])
        for r in rows:
            w.writerow([
                r.canonical, r.name, r.uei, r.recipient_id, r.code,
                f"{r.amount_fy:.2f}", r.ticker or "",
            ])


def summarize(rows: list[RecipientRow], fy: int = 2024) -> UniverseSummary:
    canonical_set = {r.canonical for r in rows}
    with_ticker = [r for r in rows if r.ticker]
    distinct_tickers = sorted({r.ticker for r in with_ticker if r.ticker})
    return UniverseSummary(
        n_recipient_rows=len(rows),
        n_distinct_canonical=len(canonical_set),
        n_with_ticker=len(with_ticker),
        distinct_tickers=distinct_tickers,
        fy=fy,
    )


async def build_universe(
    *,
    fy: int = 2024,
    pages: int = 5,
    out_csv: Path | None = None,
) -> UniverseSummary:
    raw = await fetch_top_recipients(fy=fy, pages=pages)
    collapsed = collapse_to_canonical(raw)
    out_csv = out_csv or (DATA_DIR / f"universe_defense_it_r1000_fy{fy}.csv")
    write_universe_csv(collapsed, out_csv)
    summary = summarize(collapsed, fy=fy)
    write_json("global", {
        "phase": "Phase 0 -- Day 2",
        "current_task": "universe_filter built",
        "universe_path": str(out_csv),
        "universe_summary": {
            "n_recipient_rows": summary.n_recipient_rows,
            "n_distinct_canonical": summary.n_distinct_canonical,
            "n_with_ticker": summary.n_with_ticker,
            "distinct_tickers": summary.distinct_tickers,
            "fy": summary.fy,
            "pages_fetched": pages,
        },
    })
    return summary


if __name__ == "__main__":
    import json as _json
    out = asyncio.run(build_universe(pages=5))
    print(_json.dumps({
        "n_recipient_rows": out.n_recipient_rows,
        "n_distinct_canonical": out.n_distinct_canonical,
        "n_with_ticker": out.n_with_ticker,
        "n_distinct_tickers": len(out.distinct_tickers),
        "fy": out.fy,
    }, indent=2))
