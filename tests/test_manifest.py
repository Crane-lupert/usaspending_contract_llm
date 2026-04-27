"""Manifest atomic-IO tests — append_jsonl, write_json, read paths."""
from __future__ import annotations

import os

import pytest

from usaspending_contract_llm import manifest as M


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "DATA_DIR", tmp_path)
    monkeypatch.setattr(M, "MANIFESTS", {k: tmp_path / v.name for k, v in M.MANIFESTS.items()})


def test_append_jsonl_round_trip(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    M.append_jsonl("fetch", {"award_id": "ABC", "status": "ok"})
    M.append_jsonl("fetch", {"award_id": "DEF", "status": "ok"})
    rows = list(M.read_jsonl("fetch"))
    assert len(rows) == 2
    assert rows[0]["award_id"] == "ABC"
    assert rows[1]["award_id"] == "DEF"


def test_write_json_round_trip(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    M.write_json("global", {"phase": "Phase 0", "day": 1})
    g = M.read_json("global")
    assert g["phase"] == "Phase 0"
    assert g["day"] == 1


def test_update_global_merges(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    M.write_json("global", {"phase": "Phase 0", "day": 1})
    M.update_global(day=2, current_task="api fetch")
    g = M.read_json("global")
    assert g["phase"] == "Phase 0"
    assert g["day"] == 2
    assert g["current_task"] == "api fetch"


def test_unknown_key_raises():
    with pytest.raises(KeyError):
        M.manifest_path("not_a_real_key")


def test_empty_jsonl_yields_nothing(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    rows = list(M.read_jsonl("fetch"))
    assert rows == []
