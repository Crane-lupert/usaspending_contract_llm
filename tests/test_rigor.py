"""rigor: DSR + Newey-West + cluster bootstrap + BH-FDR."""
from __future__ import annotations

import numpy as np
import pytest

from usaspending_contract_llm.rigor import (
    bh_fdr,
    cluster_bootstrap_t,
    deflated_sharpe,
    newey_west_se,
)


def test_deflated_sharpe_passes_strong_signal():
    out = deflated_sharpe(sr_observed=2.0, n_trials=10, n=60)
    assert out["psr"] > 0.95
    assert out["dsr_pass_p05"] is True


def test_deflated_sharpe_fails_weak_signal():
    out = deflated_sharpe(sr_observed=0.1, n_trials=10, n=60)
    assert out["psr"] < 0.5
    assert out["dsr_pass_p05"] is False


def test_bh_fdr_obvious_pass():
    out = bh_fdr([0.001, 0.002, 0.003], q=0.05)
    assert out["n_pass"] == 3


def test_bh_fdr_obvious_fail():
    out = bh_fdr([0.5, 0.6, 0.7], q=0.05)
    assert out["n_pass"] == 0


def test_cluster_bootstrap_excludes_zero_for_strong_signal():
    rng = np.random.RandomState(42)
    spreads = list(rng.normal(0.05, 0.01, 50))
    out = cluster_bootstrap_t(spreads, B=200, seed=1)
    assert out["boot_excludes_zero"] is True
    assert out["obs_t"] > 5


def test_cluster_bootstrap_includes_zero_for_null_signal():
    rng = np.random.RandomState(42)
    spreads = list(rng.normal(0.0, 0.05, 50))
    out = cluster_bootstrap_t(spreads, B=200, seed=1)
    assert abs(out["obs_t"]) < 2.5


def test_newey_west_se_basic():
    spreads = list(np.linspace(0.0, 0.1, 20))  # autocorrelated trend
    out = newey_west_se(spreads, lags=4)
    assert "nw_t" in out
    assert "nw_se" in out
    assert out["n"] == 20
    assert out["lags"] == 4


def test_newey_west_se_insufficient_data():
    out = newey_west_se([0.1, 0.2], lags=4)
    assert "error" in out
