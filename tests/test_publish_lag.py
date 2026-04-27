"""publish_lag.measure_lag_from_transaction + LagDistribution bins."""
from __future__ import annotations

from usaspending_contract_llm.publish_lag import (
    LagDistribution,
    LAG_BINS_HOURS,
    _bin_for_hours,
    measure_lag_from_transaction,
)


def test_bin_thresholds():
    assert _bin_for_hours(0) == "<24h"
    assert _bin_for_hours(23.9) == "<24h"
    assert _bin_for_hours(24) == "24-72h"
    assert _bin_for_hours(72) == "72h-7d"
    assert _bin_for_hours(168) == "7-30d"
    assert _bin_for_hours(720) == ">30d"
    assert _bin_for_hours(10000) == ">30d"


def test_measure_lag_same_day_under_24h():
    award = {
        "Award ID": "X",
        "generated_internal_id": "Y",
        "Base Obligation Date": "2020-01-01",
        "Last Modified Date": "2026-04-25 20:00:00",
    }
    tx = {"action_date": "2026-04-25", "modification_number": "P00008"}
    m = measure_lag_from_transaction(award_row=award, most_recent_transaction=tx)
    assert m.lag_hours is not None
    assert m.lag_hours <= 24.0
    assert m.bin == "<24h"


def test_measure_lag_one_week():
    award = {
        "Award ID": "X",
        "generated_internal_id": "Y",
        "Last Modified Date": "2026-04-25 12:00:00",
    }
    tx = {"action_date": "2026-04-22", "modification_number": "P0"}
    m = measure_lag_from_transaction(award_row=award, most_recent_transaction=tx)
    # 2026-04-22T00:00:00 -> 2026-04-25T12:00:00 = 84 hours -> 72h-7d
    assert m.bin == "72h-7d"
    assert 72 <= (m.lag_hours or 0) < 168


def test_measure_lag_missing_action_date():
    award = {"Award ID": "X", "generated_internal_id": "Y", "Last Modified Date": "2026-04-25"}
    tx = {"modification_number": "P0"}  # no action_date
    m = measure_lag_from_transaction(award_row=award, most_recent_transaction=tx)
    assert m.lag_hours is None
    assert m.bin is None
    assert "missing_action_date" in m.notes


def test_distribution_aggregates():
    dist = LagDistribution()
    award = {"Award ID": "X", "generated_internal_id": "Y", "Last Modified Date": "2026-04-25 12:00:00"}
    for ad, expected in [
        ("2026-04-25", "<24h"),
        ("2026-04-25", "<24h"),
        ("2026-04-23", "24-72h"),
        ("2026-03-25", ">30d"),
    ]:
        m = measure_lag_from_transaction(award_row=award, most_recent_transaction={"action_date": ad})
        assert m.bin == expected
        dist.add(m)
    assert dist.n_total == 4
    assert dist.n_with_lag == 4
    fr = dist.fractions()
    assert fr["<24h"] == 0.5
    assert fr["24-72h"] == 0.25
    assert fr[">30d"] == 0.25
    assert dist.lt_24h_fraction() == 0.5
    assert dist.lt_7d_fraction() == 0.75
