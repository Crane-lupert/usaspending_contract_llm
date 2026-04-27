"""Day-3 JSON 4-field extract from USAspending /search/spending_by_award/ rows.

The four fields the 3-axis LLM ensemble consumes:

  1. Description                  -- contract action_description (free text)
  2. psc_code + psc_description   -- product/service code (controlled vocabulary)
  3. Awarding Sub Agency          -- contracting officer's organizational scope
  4. transaction_description      -- per-modification narrative (fetched from
                                     /awards/<id>/transactions/ on Day 4+)

Day 3 scope: extract fields 1-3 from the search response itself (no extra
HTTP call). Field 4 (transaction_description for modifications) is deferred
to Day 4-5 since it needs /awards/<id>/transactions/ which is N=1 per award.

Yield target (reference-validation §4.5.3): >= 99% on JSON-direct access.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from .manifest import append_jsonl


@dataclass
class ParsedAward:
    award_id: str
    generated_internal_id: str
    recipient_name: str
    recipient_uei: str
    description: str           # free-text obligation narrative (LLM input #1)
    psc_code: str
    psc_description: str       # LLM input #2 (controlled vocab + free desc)
    awarding_sub_agency: str   # LLM input #3
    naics_code: str
    award_amount: float
    base_obligation_date: Optional[str]
    last_modified_date: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    contract_award_type: str

    def to_row(self) -> dict:
        return {
            "award_id":               self.award_id,
            "generated_internal_id":  self.generated_internal_id,
            "recipient_name":         self.recipient_name,
            "recipient_uei":          self.recipient_uei,
            "description":            self.description,
            "psc_code":               self.psc_code,
            "psc_description":        self.psc_description,
            "awarding_sub_agency":    self.awarding_sub_agency,
            "naics_code":             self.naics_code,
            "award_amount":           self.award_amount,
            "base_obligation_date":   self.base_obligation_date,
            "last_modified_date":     self.last_modified_date,
            "start_date":             self.start_date,
            "end_date":               self.end_date,
            "contract_award_type":    self.contract_award_type,
        }


def parse_award_row(row: dict) -> Optional[ParsedAward]:
    """Single-row parser. Returns None on missing required fields.

    Required: generated_internal_id (idempotent key) + Description (LLM input).
    """
    gen_id = row.get("generated_internal_id") or row.get("internal_id")
    description = row.get("Description")
    if not gen_id or not description:
        return None

    return ParsedAward(
        award_id=row.get("Award ID") or "",
        generated_internal_id=gen_id,
        recipient_name=row.get("Recipient Name") or "",
        recipient_uei=row.get("Recipient UEI") or "",
        description=description,
        psc_code=row.get("psc_code") or "",
        psc_description=row.get("psc_description") or "",
        awarding_sub_agency=row.get("Awarding Sub Agency") or "",
        naics_code=row.get("naics_code") or "",
        award_amount=float(row.get("Award Amount") or 0.0),
        base_obligation_date=row.get("Base Obligation Date"),
        last_modified_date=row.get("Last Modified Date"),
        start_date=row.get("Start Date"),
        end_date=row.get("End Date"),
        contract_award_type=row.get("Contract Award Type") or "",
    )


def parse_page(rows: Iterable[dict], *, log_to_manifest: bool = True) -> tuple[list[ParsedAward], int]:
    """Parse a list of /search/spending_by_award/ result rows.

    Returns (parsed_list, n_skipped). Yield = len(parsed_list) / total.
    """
    out: list[ParsedAward] = []
    skipped = 0
    for r in rows:
        p = parse_award_row(r)
        if p is None:
            skipped += 1
            continue
        out.append(p)
        if log_to_manifest:
            append_jsonl("parse", p.to_row())
    return out, skipped


def yield_pct(parsed: list[ParsedAward], skipped: int) -> float:
    total = len(parsed) + skipped
    return round(100 * len(parsed) / total, 2) if total else 0.0
