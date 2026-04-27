"""Publish-lag measurement (M1-specific, Phase 0 trigger #6 prerequisite).

We measure the gap between when a contract is *signed* (action_date /
base_obligation_date / period_of_performance_start) and when USAspending
actually *publishes* the record (last_modified_date is the closest proxy
without scraping the data dictionary).

Why this matters: the entire industry-lead-time-risk gate (Phase 1 trigger
#2) hinges on what fraction of awards reach USAspending in <24h vs >7d.
If <24h sample fraction >= 50%, academic alpha is dead because Palantir/
Govini/Apify pickup is same-day. If alpha decay (OOS-IS)/IS < -0.5,
industry has already absorbed the alpha (=> writeup-only freeze).

Day 3 scope: scaffolding + a 100-award sample distribution measurement
attached to the same fetch path. Real Day-5/6/7 measurement runs on the
full Phase 0 dry-run sample and the 5-bin distribution that satisfies
trigger #6.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional

from .manifest import append_jsonl


# 5-bin distribution per reference-validation §7.2 + phase plan §7.1.
LAG_BINS_HOURS = [
    ("<24h",   0,    24),
    ("24-72h", 24,   72),
    ("72h-7d", 72,   168),
    ("7-30d",  168,  720),
    (">30d",   720,  10**9),
]


@dataclass
class LagMeasurement:
    award_id: str
    generated_internal_id: str
    action_date: Optional[str]
    base_obligation_date: Optional[str]
    last_modified_date: Optional[str]
    lag_hours: Optional[float]
    bin: Optional[str]
    notes: str = ""

    def to_row(self) -> dict:
        return {
            "award_id":               self.award_id,
            "generated_internal_id":  self.generated_internal_id,
            "action_date":            self.action_date,
            "base_obligation_date":   self.base_obligation_date,
            "last_modified_date":     self.last_modified_date,
            "lag_hours":              self.lag_hours,
            "bin":                    self.bin,
            "notes":                  self.notes,
        }


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    s = s.strip()
    # Common shapes: "2024-03-15", "2024-03-15T12:34:56", "2024-03-15T12:34:56Z"
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _bin_for_hours(hours: float) -> str:
    for label, lo, hi in LAG_BINS_HOURS:
        if lo <= hours < hi:
            return label
    return ">30d"


def measure_lag_from_transaction(
    *,
    award_row: dict,
    most_recent_transaction: dict,
) -> LagMeasurement:
    """Per-transaction publish lag.

    Inputs:
      - award_row: a /search/spending_by_award/ result row
                   (we use Last Modified Date as the publish proxy)
      - most_recent_transaction: top row from /transactions/ POST result
                   (we use action_date as the per-mod signing date)

    Lag = (Last Modified Date) - (most_recent action_date), in hours.

    This is the *correct* publish-lag measurement -- the previous version
    that used Base Obligation Date was wrong (it gave the age of the
    earliest transaction, not the gap between latest mod and publish).
    """
    award_id = award_row.get("Award ID") or ""
    gen_id = award_row.get("generated_internal_id") or ""

    action_date_str = most_recent_transaction.get("action_date")
    sign = _parse_iso(action_date_str)
    publish = _parse_iso(award_row.get("Last Modified Date"))

    notes_parts = []
    if sign is None:
        notes_parts.append("missing_action_date")
    if publish is None:
        notes_parts.append("missing_publish_date")

    if sign is None or publish is None:
        return LagMeasurement(
            award_id=award_id,
            generated_internal_id=gen_id,
            action_date=action_date_str,
            base_obligation_date=award_row.get("Base Obligation Date"),
            last_modified_date=award_row.get("Last Modified Date"),
            lag_hours=None,
            bin=None,
            notes=";".join(notes_parts),
        )

    delta = publish - sign
    lag_hours = delta.total_seconds() / 3600.0
    if lag_hours < 0:
        # action_date is per-day; publish has time-of-day so a same-day
        # publish at 00:00:01 vs action_date 00:00:00 is fine. Negative
        # values flag retroactive publish (rare).
        notes_parts.append("publish_before_sign")
        lag_hours = abs(lag_hours)
    bin_label = _bin_for_hours(lag_hours)
    return LagMeasurement(
        award_id=award_id,
        generated_internal_id=gen_id,
        action_date=action_date_str,
        base_obligation_date=award_row.get("Base Obligation Date"),
        last_modified_date=award_row.get("Last Modified Date"),
        lag_hours=round(lag_hours, 1),
        bin=bin_label,
        notes=";".join(notes_parts),
    )


def measure_lag(row: dict) -> LagMeasurement:
    """DEPRECATED -- coarse Base-Obligation-Date proxy. Kept for back-compat
    with Day-3 smoke pre-fix; new code should use measure_lag_from_transaction.

    The Base Obligation Date proxy gives the age of the *earliest* transaction
    on a multi-modification contract, not the publish lag of the most recent
    modification, so it always lands in the >30d bin for long-running contracts.
    """
    award_id = row.get("Award ID") or row.get("award_id") or ""
    gen_id = row.get("generated_internal_id") or row.get("internal_id") or ""

    sign = (
        _parse_iso(row.get("Base Obligation Date"))
        or _parse_iso(row.get("Start Date"))
    )
    publish = _parse_iso(row.get("Last Modified Date"))

    notes_parts = ["coarse_baseobl_proxy"]
    if sign is None:
        notes_parts.append("missing_sign_date")
    if publish is None:
        notes_parts.append("missing_publish_date")

    if sign is None or publish is None:
        return LagMeasurement(
            award_id=award_id, generated_internal_id=gen_id,
            action_date=None,
            base_obligation_date=row.get("Base Obligation Date"),
            last_modified_date=row.get("Last Modified Date"),
            lag_hours=None, bin=None, notes=";".join(notes_parts),
        )

    delta = publish - sign
    lag_hours = abs(delta.total_seconds() / 3600.0)
    return LagMeasurement(
        award_id=award_id, generated_internal_id=gen_id,
        action_date=None,
        base_obligation_date=row.get("Base Obligation Date"),
        last_modified_date=row.get("Last Modified Date"),
        lag_hours=round(lag_hours, 1),
        bin=_bin_for_hours(lag_hours),
        notes=";".join(notes_parts),
    )


@dataclass
class LagDistribution:
    n_total: int = 0
    n_with_lag: int = 0
    bin_counts: dict[str, int] = field(default_factory=lambda: {b[0]: 0 for b in LAG_BINS_HOURS})

    def add(self, m: LagMeasurement) -> None:
        self.n_total += 1
        if m.lag_hours is not None and m.bin is not None:
            self.n_with_lag += 1
            self.bin_counts[m.bin] = self.bin_counts.get(m.bin, 0) + 1

    def fractions(self) -> dict[str, float]:
        if not self.n_with_lag:
            return {b[0]: 0.0 for b in LAG_BINS_HOURS}
        return {k: round(v / self.n_with_lag, 4) for k, v in self.bin_counts.items()}

    def lt_24h_fraction(self) -> float:
        """Phase 1 trigger #2a key metric -- fraction of sample with publish-lag <24h."""
        return self.fractions().get("<24h", 0.0)

    def lt_7d_fraction(self) -> float:
        """Realistic-execution baseline -- fraction publishable within 7d."""
        f = self.fractions()
        return f.get("<24h", 0.0) + f.get("24-72h", 0.0) + f.get("72h-7d", 0.0)


def measure_page(rows: Iterable[dict], dist: Optional[LagDistribution] = None,
                 *, log_to_manifest: bool = True) -> LagDistribution:
    """Measure publish lag on every row in a /search/spending_by_award/ page."""
    if dist is None:
        dist = LagDistribution()
    for r in rows:
        m = measure_lag(r)
        dist.add(m)
        if log_to_manifest:
            append_jsonl("publish_lag", m.to_row())
    return dist
