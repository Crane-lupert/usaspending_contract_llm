"""cross_section + commitment_surprise."""
from __future__ import annotations

import pandas as pd

from usaspending_contract_llm.commitment_surprise import add_surprise_column
from usaspending_contract_llm.cross_section import (
    AXIS1_WEIGHT,
    quintile_sort,
    compute_spread_return,
)


def test_axis1_weights_consistency():
    assert AXIS1_WEIGHT["FFP"] == 0.0
    assert AXIS1_WEIGHT["COST_PLUS"] > AXIS1_WEIGHT["IDIQ_CEILING"]
    assert AXIS1_WEIGHT["IDIQ_CEILING"] > AXIS1_WEIGHT["OPTION_PERIOD"]
    assert AXIS1_WEIGHT[None] is None


def test_quintile_sort_assigns_5_buckets():
    panel = pd.DataFrame({
        "ticker": [f"T{i}" for i in range(15)] * 1,
        "quarter": ["2024Q1"] * 15,
        "commitment_score_norm": [i * 0.1 for i in range(15)],
        "n_contracts": [1] * 15,
        "total_award": [100.0] * 15,
    })
    out = quintile_sort(panel)
    assert "quintile" in out.columns
    assert out["quintile"].nunique() == 5


def test_quintile_sort_skips_small_quarter():
    panel = pd.DataFrame({
        "ticker": ["A", "B", "C"],
        "quarter": ["2024Q1"] * 3,
        "commitment_score_norm": [0.0, 0.5, 1.0],
        "n_contracts": [1, 1, 1],
        "total_award": [100.0, 100.0, 100.0],
    })
    out = quintile_sort(panel)
    assert out["quintile"].isna().all()


def test_compute_spread_return_no_quintile_or_no_car():
    panel = pd.DataFrame({"ticker": ["A"], "quarter": ["2024Q1"]})
    out = compute_spread_return(panel)
    assert "error" in out


def test_add_surprise_column_subtracts_rolling_mean():
    panel = pd.DataFrame({
        "ticker": ["A", "A", "A", "A", "A"],
        "quarter": ["2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1"],
        "commitment_score_norm": [0.5, 0.5, 0.5, 0.5, 0.9],
    })
    out = add_surprise_column(panel, lookback=4)
    last = out[out["quarter"] == "2024Q1"].iloc[0]
    # rolling 4q mean of [0.5]*4 = 0.5; surprise = 0.9 - 0.5 = 0.4
    assert abs(last["commitment_surprise"] - 0.4) < 1e-9
    # First quarter has no prior history -> surprise should be NaN.
    first = out[out["quarter"] == "2023Q1"].iloc[0]
    assert pd.isna(first["commitment_surprise"])
