"""Gate F (USAspending guard) static tests.

Originally Gate F = PURE daemon-free (no SEC EDGAR access at all).
**As of 2026-04-28 user lifted Gate F**: SEC EDGAR submissions/filings API now
allowed (free public API, rate-limit 10rps + User-Agent). The remaining
*invariant* is: USAspending client must NOT route through SEC hostnames.
SEC EDGAR is now its own dedicated module (sec_edgar_client.py).

These tests verify:
1. usaspending_client.py SEC_HOSTS_DENY guard still fires on SEC URLs --
   USAspending API is *separate* from SEC; the deny list inside USAspending
   client prevents accidental SEC routing through that client.
2. Outside usaspending_client + sec_edgar_client, no SEC hostname constants.

The semantic invariant has shifted from "no SEC at all" to "SEC and USAspending
are separated infrastructure".
"""
from __future__ import annotations

from pathlib import Path

import pytest

from usaspending_contract_llm.usaspending_client import (
    SEC_HOSTS_DENY,
    _assert_no_sec_url,
)


def test_sec_hosts_deny_list_complete():
    assert "data.sec.gov" in SEC_HOSTS_DENY
    assert "efts.sec.gov" in SEC_HOSTS_DENY
    assert "www.sec.gov" in SEC_HOSTS_DENY


def test_assert_no_sec_url_raises_on_data_sec():
    with pytest.raises(RuntimeError, match="Gate F violation"):
        _assert_no_sec_url("https://data.sec.gov/api/foo")


def test_assert_no_sec_url_raises_on_efts():
    with pytest.raises(RuntimeError, match="Gate F violation"):
        _assert_no_sec_url("https://efts.sec.gov/search")


def test_assert_no_sec_url_raises_on_www():
    with pytest.raises(RuntimeError, match="Gate F violation"):
        _assert_no_sec_url("https://www.sec.gov/cgi-bin/browse-edgar")


def test_assert_no_sec_url_passes_usaspending():
    _assert_no_sec_url("https://api.usaspending.gov/api/v2/search/")


def test_no_sec_hostname_outside_dedicated_modules():
    """Walk the package source -- SEC hostnames allowed only in usaspending_client
    (deny-list literal) + sec_edgar_client (the dedicated SEC module post-Gate-F-lift)."""
    src_root = Path(__file__).resolve().parents[1] / "src" / "usaspending_contract_llm"
    forbidden = ("data.sec.gov", "efts.sec.gov", "www.sec.gov")
    allowed_modules = {"usaspending_client.py", "sec_edgar_client.py", "sec_event_panel.py"}
    offenders: list[str] = []
    for py in src_root.rglob("*.py"):
        if py.name in allowed_modules:
            continue
        text = py.read_text(encoding="utf-8")
        for needle in forbidden:
            if needle in text:
                offenders.append(f"{py}: {needle!r}")
    assert not offenders, f"SEC hostname leak (must be in dedicated module): {offenders}"
