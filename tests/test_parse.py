"""parse.parse_award_row + parse_page yield."""
from __future__ import annotations

from usaspending_contract_llm.parse import parse_award_row, parse_page, yield_pct


VALID_ROW = {
    "Award ID": "FA8721-25-D-0001",
    "generated_internal_id": "CONT_AWD_TEST_001",
    "Recipient Name": "LOCKHEED MARTIN CORPORATION",
    "Recipient UEI": "G4KDGE4JFFK7",
    "Description": "F-35 LRIP LOT 17 PRODUCTION",
    "psc_code": "1510",
    "psc_description": "Aircraft, fixed wing",
    "Awarding Sub Agency": "AIR FORCE LIFE CYCLE MGMT CTR",
    "naics_code": "336411",
    "Award Amount": 9876543210.0,
    "Base Obligation Date": "2024-09-15",
    "Last Modified Date": "2026-04-25 12:00:00",
    "Start Date": "2024-09-15",
    "End Date": "2027-12-31",
    "Contract Award Type": "DEFINITIVE CONTRACT",
}


def test_parse_award_row_happy_path():
    p = parse_award_row(VALID_ROW)
    assert p is not None
    assert p.award_id == "FA8721-25-D-0001"
    assert p.recipient_uei == "G4KDGE4JFFK7"
    assert p.description.startswith("F-35")
    assert p.psc_code == "1510"
    assert p.award_amount == 9876543210.0


def test_parse_award_row_missing_required_returns_none():
    bad = dict(VALID_ROW)
    del bad["generated_internal_id"]
    assert parse_award_row(bad) is None

    bad2 = dict(VALID_ROW)
    del bad2["Description"]
    assert parse_award_row(bad2) is None


def test_parse_page_yield_100pct(tmp_path, monkeypatch):
    from usaspending_contract_llm import manifest as M
    monkeypatch.setattr(M, "DATA_DIR", tmp_path)
    monkeypatch.setattr(M, "MANIFESTS", {k: tmp_path / v.name for k, v in M.MANIFESTS.items()})
    rows = [VALID_ROW, dict(VALID_ROW), dict(VALID_ROW)]
    parsed, skipped = parse_page(rows)
    assert len(parsed) == 3
    assert skipped == 0
    assert yield_pct(parsed, skipped) == 100.0


def test_parse_page_drops_invalid(tmp_path, monkeypatch):
    from usaspending_contract_llm import manifest as M
    monkeypatch.setattr(M, "DATA_DIR", tmp_path)
    monkeypatch.setattr(M, "MANIFESTS", {k: tmp_path / v.name for k, v in M.MANIFESTS.items()})
    rows = [VALID_ROW, {"Award ID": "broken"}, dict(VALID_ROW)]
    parsed, skipped = parse_page(rows)
    assert len(parsed) == 2
    assert skipped == 1
    assert yield_pct(parsed, skipped) == 66.67
