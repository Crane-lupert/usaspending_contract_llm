"""Day-18 §4.4 contamination + §4.5 firm-name masking.

§4.4 Contamination: split sample by LLM training cutoff (Jan 2026).
       Pre-cutoff awards may be in LLM training data;
       post-cutoff awards are clean.
       The §3 main-effect coefficient should be invariant; if pre-cutoff
       β is much larger, that's a contamination flag.

§4.5 Firm-name masking: rerun classify on the same n=20 oracle sample with
       recipient_name field redacted. Drop in Fleiss kappa = how much LLM
       was relying on firm-name shortcut vs the actual narrative.

Output: data/contamination_masking.json
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from .ensemble import DEFAULT_VENDORS, classify_one
from .manifest import DATA_DIR

CONTAMINATION_OUT = DATA_DIR / "contamination_masking.json"
ORACLE_PATH = DATA_DIR / "oracle_n20.json"
LLM_TRAINING_CUTOFF = pd.Timestamp("2026-01-01")  # claude-opus-4.7-1m cutoff


def _split_by_cutoff(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = panel.copy()
    panel["start_ts"] = pd.to_datetime(panel.get("start_date"), errors="coerce")
    pre = panel[panel["start_ts"] < LLM_TRAINING_CUTOFF]
    post = panel[panel["start_ts"] >= LLM_TRAINING_CUTOFF]
    return pre, post


def contamination_subsample_compare() -> dict:
    """Run §3 quintile spread on pre-cutoff vs post-cutoff sub-samples."""
    from .cross_section import build_firm_quarter_panel, join_with_car
    panel = build_firm_quarter_panel()
    if panel.empty:
        return {"error": "empty_panel"}
    panel_with_car = join_with_car(panel)
    # quarter is "YYYYQn" string. Convert to start of quarter for cutoff.
    panel_with_car["quarter_ts"] = pd.PeriodIndex(panel_with_car["quarter"], freq="Q").to_timestamp()
    pre = panel_with_car[panel_with_car["quarter_ts"] < LLM_TRAINING_CUTOFF]
    post = panel_with_car[panel_with_car["quarter_ts"] >= LLM_TRAINING_CUTOFF]

    def _spread_summary(df: pd.DataFrame) -> dict:
        valid = df.dropna(subset=["forward_car_3m", "commitment_score_norm"])
        if len(valid) < 10:
            return {"n": int(len(valid)), "skipped": "too_small"}
        # Crude tertile (3-bucket) split since pre/post sample sizes are smaller.
        try:
            valid = valid.assign(tertile=pd.qcut(valid["commitment_score_norm"], 3, labels=[1, 2, 3], duplicates="drop"))
        except Exception:
            return {"n": int(len(valid)), "skipped": "qcut_failed"}
        valid["tertile"] = pd.to_numeric(valid["tertile"], errors="coerce")
        q1 = valid[valid["tertile"] == 1]["forward_car_3m"].mean()
        q3 = valid[valid["tertile"] == 3]["forward_car_3m"].mean()
        return {
            "n":            int(len(valid)),
            "low_t_mean":   round(float(q1), 6) if pd.notna(q1) else None,
            "high_t_mean":  round(float(q3), 6) if pd.notna(q3) else None,
            "spread":       round(float(q1 - q3), 6) if pd.notna(q1) and pd.notna(q3) else None,
        }

    pre_s = _spread_summary(pre)
    post_s = _spread_summary(post)
    return {
        "cutoff_date":      LLM_TRAINING_CUTOFF.isoformat(),
        "n_pre_cutoff":     int(len(pre)),
        "n_post_cutoff":    int(len(post)),
        "pre_spread":       pre_s,
        "post_spread":      post_s,
        "interpretation":   "If pre-cutoff |spread| >> post-cutoff |spread|, this flags potential LLM contamination (training-data leakage). Direction-stable + magnitude-similar = contamination unlikely.",
    }


def masking_kappa_drop() -> dict:
    """Re-run 3-vendor ensemble on the n=20 oracle with recipient_name redacted.

    Compares:
      - axis1 voted label with recipient_name visible (Day 4 cached result),
      - axis1 voted label with recipient_name redacted (this run).

    Drop in agreement vs oracle = how much firm-name was driving classification.
    """
    if not ORACLE_PATH.exists():
        return {"error": "oracle_missing"}
    oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    items = oracle["items"]

    # Load contracts referenced by oracle
    from .manifest import read_jsonl
    parse_rows = list(read_jsonl("parse"))
    by_id = {r["generated_internal_id"]: r for r in parse_rows}

    # Run masked ensemble (recipient_name -> "REDACTED").
    # We don't write to manifest -- the masked run is a one-shot diagnostic.
    n_correct_masked: dict[str, int] = {m: 0 for m in DEFAULT_VENDORS}
    n_evaluated:       dict[str, int] = {m: 0 for m in DEFAULT_VENDORS}
    masked_cost = 0.0

    for it in items:
        cid = it["contract_id"]
        if cid not in by_id:
            continue
        contract = copy.deepcopy(by_id[cid])
        contract["recipient_name"] = "REDACTED_FIRM_NAME"
        oracle_a1 = it["label"]["axis1_forward_revenue_commitment"]
        for m in DEFAULT_VENDORS:
            # Bypass cache to force a fresh masked call.
            label = classify_one(
                contract=contract, model=m, use_cache=False, log_to_manifest=False,
                max_tokens=512, temperature=0.0,
            )
            masked_cost += label.cost_usd
            n_evaluated[m] += 1
            if label.axis1 == oracle_a1:
                n_correct_masked[m] += 1
    masked_acc = {
        m: round(n_correct_masked[m] / n_evaluated[m], 3) if n_evaluated[m] else None
        for m in DEFAULT_VENDORS
    }
    # Compare with Day-4 unmasked accuracy from data/ensemble_kappa_n20.json
    eu_path = DATA_DIR / "ensemble_kappa_n20.json"
    unmasked_acc = {}
    if eu_path.exists():
        eu = json.loads(eu_path.read_text(encoding="utf-8"))
        unmasked_acc = eu.get("vendor_axis1_accuracy_vs_oracle", {})
    drops = {
        m: round((unmasked_acc.get(m, 0.0) or 0.0) - (masked_acc.get(m, 0.0) or 0.0), 3)
        for m in DEFAULT_VENDORS
    }
    return {
        "n_oracle_items":    len(items),
        "n_evaluated":       n_evaluated,
        "masked_axis1_accuracy_vs_oracle": masked_acc,
        "unmasked_axis1_accuracy_vs_oracle": unmasked_acc,
        "drop_in_accuracy":   drops,
        "max_drop":           max(drops.values()) if drops else None,
        "threshold_drop":     0.10,
        "pass":               max(drops.values()) <= 0.10 if drops and all(v is not None for v in drops.values()) else None,
        "masked_cost_usd":    round(masked_cost, 4),
        "interpretation":     "Drop > 10pp = LLM was using firm-name shortcut; <= 10pp = decision driven by narrative content per LABELER_GUIDE.",
    }


def main() -> int:
    out = {
        "section_4_4_contamination":    contamination_subsample_compare(),
        "section_4_5_masking":           masking_kappa_drop(),
    }
    CONTAMINATION_OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
