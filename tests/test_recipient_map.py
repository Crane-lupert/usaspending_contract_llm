"""recipient_map.map_recipient + 4-layer fallback dispatch."""
from __future__ import annotations

from usaspending_contract_llm.recipient_map import (
    MapResult,
    _layer1_curated,
    _layer3_parent_rollup,
    map_recipient,
    yield_summary,
)


def test_layer1_curated_known_prime():
    assert _layer1_curated("LOCKHEED MARTIN CORPORATION") == "LMT"


def test_layer1_curated_unknown_returns_none():
    assert _layer1_curated("NEVER HEARD OF THIS FIRM CO") is None


def test_layer3_parent_rollup_token_subsequence_match():
    # Layer 3 catches multi-token keys whose tokens appear in the canonical
    # name in order but NOT as a strict prefix. 'L3 TECHNOLOGIES' is a 2-token
    # parent; a name like 'INTEGRATED L3 TECHNOLOGIES SUBSIDIARY' has both
    # tokens in order with a leading word that breaks prefix-match in layer 1.
    out = _layer3_parent_rollup("INTEGRATED L3 TECHNOLOGIES SUBSIDIARY")
    assert out == "LHX"


def test_layer3_skips_single_token_keys():
    # Single-token keys ('BOEING') would over-match if layer 3 used them, so
    # layer 3 skips them. Layer 1 (prefix-match) handles them already.
    out = _layer3_parent_rollup("ACME UNRELATED CO")
    assert out is None


def test_map_recipient_uses_layer1_first(tmp_path, monkeypatch):
    from usaspending_contract_llm import manifest as M
    monkeypatch.setattr(M, "DATA_DIR", tmp_path)
    monkeypatch.setattr(M, "MANIFESTS", {k: tmp_path / v.name for k, v in M.MANIFESTS.items()})
    res = map_recipient("UEI123", "BOEING COMPANY")
    assert res.ticker == "BA"
    assert res.layer == "curated"


def test_map_recipient_falls_through_to_unmapped(tmp_path, monkeypatch):
    from usaspending_contract_llm import manifest as M
    monkeypatch.setattr(M, "DATA_DIR", tmp_path)
    monkeypatch.setattr(M, "MANIFESTS", {k: tmp_path / v.name for k, v in M.MANIFESTS.items()})
    res = map_recipient("UEI999", "UNKNOWN SMALL FIRM LLC")
    assert res.ticker is None
    assert res.layer == "unmapped"


def test_yield_summary_basic():
    rows = [
        {"layer": "curated"}, {"layer": "curated"},
        {"layer": "parent_rollup"},
        {"layer": "unmapped"}, {"layer": "unmapped"}, {"layer": "unmapped"},
    ]
    s = yield_summary(rows)
    assert s["n_total"] == 6
    assert s["n_mapped"] == 3
    assert s["yield_pct"] == 50.0
    assert s["by_layer"]["unmapped"] == 3
