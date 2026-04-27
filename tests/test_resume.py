"""resume.py runs cleanly on empty manifests (Day 1 cold-start invariant)."""
from __future__ import annotations

from usaspending_contract_llm import resume as R


def test_phase_summary_defaults_when_no_global(tmp_path, monkeypatch):
    from usaspending_contract_llm import manifest as M
    monkeypatch.setattr(M, "DATA_DIR", tmp_path)
    monkeypatch.setattr(M, "MANIFESTS", {k: tmp_path / v.name for k, v in M.MANIFESTS.items()})
    s = R._phase_summary()
    assert s["phase"] == "Phase 0 -- Day 1" or "Phase 0" in s["phase"]
    assert s["abandoned"] is False


def test_main_returns_zero(tmp_path, monkeypatch, capsys):
    from usaspending_contract_llm import manifest as M
    monkeypatch.setattr(M, "DATA_DIR", tmp_path)
    monkeypatch.setattr(M, "MANIFESTS", {k: tmp_path / v.name for k, v in M.MANIFESTS.items()})
    rc = R.main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Project M1" in out
    assert "resume.py" in out
