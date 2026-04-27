"""Phase 1 final pipeline runner — Day 9 batch -> Day 14 verdict in one command.

Run this when day9_batch_summary.json appears (i.e. Day 9 LLM batch completed):

    python -m usaspending_contract_llm.final_pipeline

Sequence:
  1. cross_section       (firm-quarter panel + quintile spread)
  2. ccm_baseline        (state-FE 2-step regression + incremental R²)
  3. cohort_heterogeneity (§4.1 per-cohort Sharpe trajectory)
  4. rigor               (DSR + NW + cluster bootstrap)
  5. timing_audit        (§4.2 first-order industry-absorption haircut)
  6. contamination_masking (§4.4 + §4.5; ~$0.20 LLM cost for masking re-run)
  7. day14_mid_checkpoint (final trigger #1 verdict)

Each step is idempotent: re-runs read from disk + re-write summary JSONs.
"""
from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path

from .manifest import DATA_DIR

DAY9_SUMMARY = DATA_DIR / "day9_batch_summary.json"
DAY14_OUT = DATA_DIR / "day14_mid_checkpoint.json"

STEPS = [
    ("cross_section",          "Cross-section quintile portfolio"),
    ("ccm_baseline",           "CCM 2-step regression"),
    ("cohort_heterogeneity",   "§4.1 cohort heterogeneity"),
    ("rigor",                  "Statistical rigor (DSR / NW / bootstrap)"),
    ("timing_audit",           "§4.2 naive-vs-realistic timing"),
    ("contamination_masking",  "§4.4 contamination + §4.5 firm-name masking"),
    ("day14_mid_checkpoint",   "Trigger #1 final verdict"),
]


def main() -> int:
    if not DAY9_SUMMARY.exists():
        print(f"WARN: {DAY9_SUMMARY.name} not present -- Day 9 batch may not be complete.")
        print("Running on PARTIAL data anyway (preview-style).")
    else:
        print(f"OK: {DAY9_SUMMARY.name} present.")

    results: dict[str, dict] = {}
    failed: list[str] = []
    t0 = time.monotonic()

    for mod_name, label in STEPS:
        full_mod = f"usaspending_contract_llm.{mod_name}"
        print(f"\n[{mod_name}] {label}")
        print("-" * 72)
        t_step0 = time.monotonic()
        try:
            mod = importlib.import_module(full_mod)
            rc = mod.main()
            elapsed = time.monotonic() - t_step0
            print(f"... done rc={rc} ({elapsed:.1f}s)")
            results[mod_name] = {"rc": rc, "elapsed_sec": round(elapsed, 1)}
            if rc != 0:
                failed.append(mod_name)
        except Exception as e:
            elapsed = time.monotonic() - t_step0
            print(f"... ERROR ({elapsed:.1f}s): {type(e).__name__}: {e}")
            results[mod_name] = {"rc": -1, "error": str(e), "elapsed_sec": round(elapsed, 1)}
            failed.append(mod_name)

    total = time.monotonic() - t0

    # Final summary
    print("\n" + "=" * 72)
    print(f"Final pipeline complete in {total:.1f}s")
    print(f"Steps run: {len(STEPS)}, failed: {len(failed)}")
    if failed:
        print(f"Failed steps: {failed}")
    print("=" * 72)

    # Read Day 14 verdict
    if DAY14_OUT.exists():
        d14 = json.loads(DAY14_OUT.read_text(encoding="utf-8"))
        print(f"\nDay 14 verdict: {d14.get('verdict', 'UNKNOWN')}")
        print(f"Next action:    {d14.get('next_action', '')}")
        for m in d14.get("metrics", []):
            metric = m.get("metric", "?")
            value = m.get("value", "?")
            verdict = m.get("verdict", "?")
            print(f"  {metric:30s} = {value!s:>10s}  -> {verdict}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
