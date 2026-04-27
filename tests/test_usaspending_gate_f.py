"""Gate F (PURE daemon-free) static guard tests.

These tests verify that:
1. The SEC_HOSTS_DENY guard fires on any deny-listed URL.
2. No SEC EDGAR hostname appears as a hard-coded constant in the package source.

If any test in this file ever fails, Project M1 has lost daemon-free status
and overnight execution must abort.
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


def test_no_sec_hostname_in_source():
    """Walk the package source — no SEC EDGAR hostname allowed except the deny list literal."""
    src_root = Path(__file__).resolve().parents[1] / "src" / "usaspending_contract_llm"
    forbidden = ("data.sec.gov", "efts.sec.gov", "www.sec.gov")
    offenders: list[str] = []
    for py in src_root.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        # The guard module is allowed to mention these for the deny list itself.
        if py.name == "usaspending_client.py":
            continue
        for needle in forbidden:
            if needle in text:
                offenders.append(f"{py}: {needle!r}")
    assert not offenders, f"Gate F violation candidates: {offenders}"
