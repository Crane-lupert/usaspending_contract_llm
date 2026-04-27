"""Day-4 oracle ensemble run + Fleiss kappa + accuracy-vs-oracle.

Reads `data/oracle_n20.json` (Claude-anchored gold standard) + the
manifest_parse.jsonl rows referenced by oracle contract_ids, runs the
3-vendor ensemble in parallel, and produces `data/ensemble_kappa_n20.json`.

Phase 0 trigger #3 binding metric: 3-axis Fleiss kappa >= 0.6.
Fallback: 2-axis (axis1 + axis2 collapsed to committed-vs-conditional).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from .ensemble import DEFAULT_VENDORS, EnsembleLabel, classify_batch
from .manifest import DATA_DIR, read_jsonl, write_json

ORACLE_PATH = DATA_DIR / "oracle_n20.json"
ENSEMBLE_PATH = DATA_DIR / "ensemble_kappa_n20.json"


# ---------------------------------------------------------------------------
# Fleiss kappa for k raters x N items x C categories.
# Reference: https://en.wikipedia.org/wiki/Fleiss%27_kappa
# ---------------------------------------------------------------------------
def fleiss_kappa(ratings: list[list[str]], categories: list[str]) -> dict:
    """ratings[i] = list of k labels (one per rater) for item i.

    All items must have the same number of raters. Items with any None rater
    label are dropped (cannot compute). Returns dict with kappa + intermediates.
    """
    valid = [row for row in ratings if all(r is not None for r in row)]
    n = len(valid)
    if n == 0:
        return {"kappa": None, "n_items": 0, "n_dropped": len(ratings), "categories": categories}

    k = len(valid[0])
    if any(len(r) != k for r in valid):
        raise ValueError("ragged ratings rows")

    cat_index = {c: i for i, c in enumerate(categories)}
    # n_ij = count of raters assigning category j to item i
    n_ij = [[0] * len(categories) for _ in range(n)]
    for i, row in enumerate(valid):
        for r in row:
            if r in cat_index:
                n_ij[i][cat_index[r]] += 1

    # P_i = (sum_j n_ij^2 - k) / (k*(k-1))   per-item agreement
    P_i = []
    for i in range(n):
        s = sum(c * c for c in n_ij[i])
        if k > 1:
            P_i.append((s - k) / (k * (k - 1)))
        else:
            P_i.append(1.0)
    P_bar = sum(P_i) / n

    # p_j = sum_i n_ij / (n*k)   marginal category proportion
    p_j = [sum(n_ij[i][j] for i in range(n)) / (n * k) for j in range(len(categories))]
    Pe = sum(p * p for p in p_j)

    if Pe >= 1.0:
        # All raters agree on one category -> kappa undefined (treated as 1.0).
        kappa = 1.0
    else:
        kappa = (P_bar - Pe) / (1.0 - Pe)

    return {
        "kappa": round(kappa, 4),
        "P_bar": round(P_bar, 4),
        "Pe":    round(Pe, 4),
        "n_items": n,
        "n_dropped": len(ratings) - n,
        "k_raters": k,
        "categories": categories,
        "marginal_p": [round(p, 4) for p in p_j],
    }


def _load_oracle() -> dict:
    return json.loads(ORACLE_PATH.read_text(encoding="utf-8"))


def _load_contracts(contract_ids: list[str]) -> dict[str, dict]:
    """Pull the parsed-row dicts referenced by the oracle from manifest_parse."""
    rows = list(read_jsonl("parse"))
    by_id = {r["generated_internal_id"]: r for r in rows}
    return {cid: by_id[cid] for cid in contract_ids if cid in by_id}


def main() -> int:
    oracle = _load_oracle()
    items = oracle["items"]
    cids = [it["contract_id"] for it in items]
    contracts = _load_contracts(cids)
    if len(contracts) != len(items):
        print(f"WARN: oracle has {len(items)} items but only {len(contracts)} found in manifest_parse")

    contract_list = [contracts[cid] for cid in cids if cid in contracts]
    print(f"Running 3-vendor ensemble on n={len(contract_list)} contracts")
    print(f"Vendors: {DEFAULT_VENDORS}")

    batch = classify_batch(contracts=contract_list, vendors=DEFAULT_VENDORS, max_concurrent_contracts=3)

    # Tabulate ratings per axis
    axes = ["axis1", "axis2", "axis3"]
    cats_per_axis = {
        "axis1": ["FFP", "IDIQ_CEILING", "OPTION_PERIOD", "COST_PLUS"],
        "axis2": ["EXPANSION", "DESCOPE", "TERMINATION"],
        "axis3": ["PROTESTED_RISK", "CLEAN"],
    }
    ratings_per_axis: dict[str, list[list[str | None]]] = {a: [] for a in axes}
    oracle_per_axis: dict[str, list[str]] = {a: [] for a in axes}
    by_vendor_match: dict[str, list[bool]] = {m: [] for m in DEFAULT_VENDORS}
    cost_total = 0.0

    for it in items:
        cid = it["contract_id"]
        labels: list[EnsembleLabel] = batch.get(cid, [])
        if not labels:
            continue
        # For each axis, collect 3 vendor labels
        for axis_key in axes:
            vendor_labels = [getattr(l, axis_key) for l in labels]
            ratings_per_axis[axis_key].append(vendor_labels)
            # Oracle key naming reuse
            oracle_axis = it["label"][f"{axis_key}_" + {
                "axis1": "forward_revenue_commitment",
                "axis2": "program_continuity",
                "axis3": "protested_vs_clean",
            }[axis_key]]
            oracle_per_axis[axis_key].append(oracle_axis)
        # Per-vendor accuracy vs oracle (axis 1 only -- the binding axis)
        for lbl in labels:
            cost_total += lbl.cost_usd
            oracle_axis1 = it["label"]["axis1_forward_revenue_commitment"]
            by_vendor_match[lbl.model].append(lbl.axis1 == oracle_axis1)

    # Fleiss kappa per axis
    kappa_per_axis = {
        a: fleiss_kappa(ratings_per_axis[a], cats_per_axis[a])
        for a in axes
    }

    # Vendor accuracy vs oracle (axis 1)
    vendor_accuracy = {
        m: round(sum(matches) / len(matches), 3) if matches else None
        for m, matches in by_vendor_match.items()
    }

    # Vendor-by-vendor agreement matrix (Cohen-style proxy across axes 1)
    # Just record dispatched ratings for inspection.
    dispatch = []
    for it in items:
        cid = it["contract_id"]
        labels = batch.get(cid, [])
        row = {
            "contract_id": cid,
            "oracle_axis1": it["label"]["axis1_forward_revenue_commitment"],
            "oracle_axis2": it["label"]["axis2_program_continuity"],
            "oracle_axis3": it["label"]["axis3_protested_vs_clean"],
        }
        for lbl in labels:
            row[f"{lbl.model}_a1"] = lbl.axis1
            row[f"{lbl.model}_a2"] = lbl.axis2
            row[f"{lbl.model}_a3"] = lbl.axis3
            row[f"{lbl.model}_err"] = lbl.error
        dispatch.append(row)

    summary = {
        "n_items": len(items),
        "n_with_full_ensemble": sum(1 for it in items if len(batch.get(it["contract_id"], [])) == 3),
        "vendors": list(DEFAULT_VENDORS),
        "kappa_per_axis": kappa_per_axis,
        "vendor_axis1_accuracy_vs_oracle": vendor_accuracy,
        "total_ensemble_cost_usd": round(cost_total, 4),
        "trigger_3_threshold": 0.6,
        "trigger_3_pass_axis1": kappa_per_axis["axis1"]["kappa"] is not None and kappa_per_axis["axis1"]["kappa"] >= 0.6,
        "dispatch": dispatch,
    }
    ENSEMBLE_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "dispatch"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
