"""universe.normalize_name + lookup_ticker + collapse_to_canonical."""
from __future__ import annotations

from usaspending_contract_llm import universe as U
from usaspending_contract_llm.universe import (
    PARENT_TICKER,
    RecipientRow,
    collapse_to_canonical,
    lookup_ticker,
    normalize_name,
)


def test_normalize_strips_corp_suffixes():
    assert normalize_name("LOCKHEED MARTIN CORPORATION") == "LOCKHEED MARTIN"
    assert normalize_name("Lockheed Martin Corp.") == "LOCKHEED MARTIN"
    assert normalize_name("L3 Technologies, INC") == "L3"
    assert normalize_name("THE BOEING COMPANY") == "BOEING"
    assert normalize_name("Hewlett Packard Enterprise") == "HEWLETT PACKARD ENTERPRISE"


def test_normalize_strips_leading_the():
    assert normalize_name("THE MITRE CORPORATION") == "MITRE"
    assert normalize_name("The Aerospace Corp") == "AEROSPACE"


def test_lookup_ticker_known_primes():
    assert lookup_ticker("LOCKHEED MARTIN CORPORATION") == "LMT"
    assert lookup_ticker("THE BOEING COMPANY") == "BA"
    assert lookup_ticker("Booz Allen Hamilton Inc") == "BAH"
    assert lookup_ticker("Palantir Technologies") == "PLTR"
    assert lookup_ticker("CGI Federal") == "GIB"


def test_lookup_ticker_subsidiary_rolls_to_parent():
    assert lookup_ticker("SIKORSKY AIRCRAFT CORPORATION") == "LMT"
    assert lookup_ticker("ROCKWELL COLLINS") == "RTX"
    assert lookup_ticker("BELL TEXTRON INC") == "TXT"


def test_lookup_ticker_known_private_returns_none():
    assert lookup_ticker("MITRE CORPORATION") is None
    assert lookup_ticker("BATTELLE MEMORIAL INSTITUTE") is None
    assert lookup_ticker("PERATON ENTERPRISE SOLUTIONS") is None or lookup_ticker("PERATON ENTERPRISE SOLUTIONS") == ""


def test_lookup_ticker_unknown_returns_none():
    assert lookup_ticker("ACME WIDGET CO LLC") is None
    assert lookup_ticker("XYZ SMALL BUSINESS INC") is None


def test_collapse_to_canonical_aggregates_amount():
    rows = [
        RecipientRow(name="LOCKHEED MARTIN CORPORATION", uei="A", recipient_id="r1", code="d1", amount_fy=1.0),
        RecipientRow(name="LOCKHEED MARTIN CORPORATION", uei="B", recipient_id="r2", code="d2", amount_fy=2.5),
        RecipientRow(name="THE BOEING COMPANY",          uei="C", recipient_id="r3", code="d3", amount_fy=10.0),
    ]
    out = collapse_to_canonical(rows)
    by_canon = {r.canonical: r for r in out}
    assert by_canon["LOCKHEED MARTIN"].amount_fy == 3.5
    assert by_canon["LOCKHEED MARTIN"].ticker == "LMT"
    assert by_canon["BOEING"].amount_fy == 10.0
    assert by_canon["BOEING"].ticker == "BA"
