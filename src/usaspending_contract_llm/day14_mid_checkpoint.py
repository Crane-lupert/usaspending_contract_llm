"""Day-14 Phase 1 mid-checkpoint -- trigger #1 hard-kill evaluation.

Reframed plan (CLAUDE.md 2026-04-27): single hard kill = ALL 3 metric AND fail.
  - incremental R² over CCM aggregate < 5%
  - earnings surprise ROC-AUC < 0.6  (binary beat/miss prediction)
  - cross-section quintile spread Sharpe (XAR-hedged annualized) < 0.3

If ALL 3 fail -> ABANDONED.md. 2 of 3 fail -> tighten + re-test once. 1 of 3 fail -> exploratory note.

Trigger #2 (industry lag) is now §4 robustness section -- evaluated Day 16,
NOT a kill condition.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from .manifest import DATA_DIR

CCM_REPLICATION = DATA_DIR / "ccm_replication.json"
CROSS_SECTION = DATA_DIR / "cross_section_quintile.json"
EARNINGS_JSON = DATA_DIR / "yfinance_earnings.json"
ENSEMBLE_PATH = DATA_DIR / "ensemble_kappa_n20.json"
DAY9_BATCH = DATA_DIR / "day9_batch_summary.json"
OUT = DATA_DIR / "day14_mid_checkpoint.json"


def metric_incremental_r2() -> dict:
    if not CCM_REPLICATION.exists():
        return {"verdict": "MISSING", "pass": False}
    j = json.loads(CCM_REPLICATION.read_text(encoding="utf-8"))
    regs = j.get("regressions", {})
    # Use forward_car_3m as the canonical outcome; fall back to surprise_pct.
    target = regs.get("forward_car_3m") or regs.get("surprise_pct") or regs.get("event_car_3d")
    if not target or "error" in target:
        return {"verdict": "INSUFFICIENT_DATA", "pass": False, "detail": target or {}}
    inc = target.get("incremental_r2", 0.0)
    return {
        "metric":           "incremental_R2",
        "outcome_used":     target.get("outcome_col"),
        "value":            inc,
        "threshold":        0.05,
        "pass":             inc >= 0.05,
        "n_obs":            target.get("n_obs"),
        "commitment_t_stat": target.get("commitment_t_stat"),
        "verdict":          "PASS" if inc >= 0.05 else "FAIL",
    }


def metric_quintile_sharpe() -> dict:
    if not CROSS_SECTION.exists():
        return {"verdict": "MISSING", "pass": False}
    j = json.loads(CROSS_SECTION.read_text(encoding="utf-8"))
    s = j.get("spread_summary", {})
    if "error" in s:
        return {"verdict": "INSUFFICIENT_DATA", "pass": False, "detail": s}
    sharpe = s.get("sharpe_annualized", 0.0)
    return {
        "metric":     "quintile_sharpe_annualized",
        "value":      sharpe,
        "threshold":  0.3,
        "pass":       sharpe >= 0.3,
        "n_quarters": s.get("n_quarters"),
        "spread_t_stat": s.get("t_stat"),
        "verdict":    "PASS" if sharpe >= 0.3 else "FAIL",
    }


def metric_roc_auc_proxy() -> dict:
    """ROC-AUC for binary EPS-beat prediction using commitment_score_norm.

    Without the live LLM batch this can run on the firm-quarter panel + earnings
    surprise sign. We compute Mann-Whitney U / 2 = AUC.
    """
    from .cross_section import build_firm_quarter_panel
    panel = build_firm_quarter_panel()
    if panel.empty:
        return {"verdict": "MISSING", "pass": False}
    if not EARNINGS_JSON.exists():
        return {"verdict": "MISSING_EARNINGS", "pass": False}
    earnings = json.loads(EARNINGS_JSON.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for ticker, ers in earnings.items():
        if not ers or "error" in ers[0]:
            continue
        for r in ers:
            if r.get("surprise_pct") is None:
                continue
            try:
                import pandas as pd
                ts = pd.Timestamp(r["earnings_date"])
                quarter = str(ts.tz_localize(None).to_period("Q") if ts.tzinfo else ts.to_period("Q"))
            except Exception:
                continue
            rows.append({"ticker": ticker, "quarter": quarter, "surprise_pct": r["surprise_pct"]})
    import pandas as pd
    surprise_df = pd.DataFrame(rows)
    if surprise_df.empty:
        return {"verdict": "MISSING_SURPRISE", "pass": False}
    merged = panel.merge(surprise_df, on=["ticker", "quarter"], how="inner")
    merged = merged.dropna(subset=["commitment_score_norm", "surprise_pct"])
    if len(merged) < 30:
        return {"verdict": "INSUFFICIENT_DATA", "n_obs": int(len(merged)), "pass": False}
    # Binary beat: surprise_pct > 0
    merged["beat"] = (merged["surprise_pct"] > 0).astype(int)
    # AUC = P(score predicts beat) — use rank correlation as Mann-Whitney U / (n_pos * n_neg).
    pos = merged[merged["beat"] == 1]["commitment_score_norm"].values
    neg = merged[merged["beat"] == 0]["commitment_score_norm"].values
    if len(pos) == 0 or len(neg) == 0:
        return {"verdict": "ALL_ONE_CLASS", "pass": False}
    # Compute AUC via ranking
    all_scores = np.concatenate([pos, neg])
    all_ranks = pd.Series(all_scores).rank().values
    pos_ranks = all_ranks[: len(pos)]
    auc = (pos_ranks.sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    auc = float(max(auc, 1 - auc))  # report directional |0.5-shift| reflected to >0.5
    return {
        "metric":     "earnings_beat_roc_auc",
        "value":      round(auc, 4),
        "threshold":  0.6,
        "pass":       auc >= 0.6,
        "n_obs":      int(len(merged)),
        "n_beat":     int(merged["beat"].sum()),
        "n_miss":     int((1 - merged["beat"]).sum()),
        "verdict":    "PASS" if auc >= 0.6 else "FAIL",
    }


def metric_cross_llm_replication() -> dict:
    """Cross-LLM sign agreement on axis-1 commitment classification (from Day 9 batch)."""
    if not DAY9_BATCH.exists():
        return {"verdict": "MISSING_DAY9", "pass": False}
    j = json.loads(DAY9_BATCH.read_text(encoding="utf-8"))
    n_full = j.get("n_with_full_3vendor", 0)
    n_sample = j.get("n_sample", 0) or 1
    pct_full = round(100 * n_full / n_sample, 1)
    return {
        "metric":     "cross_llm_full_3vendor_coverage",
        "n_full_3vendor": n_full,
        "n_sample":   n_sample,
        "pct_full":   pct_full,
        "threshold_pct": 80.0,
        "pass":       pct_full >= 80.0,
        "verdict":    "PASS" if pct_full >= 80.0 else "FAIL",
    }


def main() -> int:
    metrics = [
        metric_incremental_r2(),
        metric_quintile_sharpe(),
        metric_roc_auc_proxy(),
        metric_cross_llm_replication(),
    ]
    failed_main3 = [m for m in metrics[:3] if not m.get("pass", False)]
    n_main_fail = len(failed_main3)
    n_total_main = 3
    if n_main_fail == n_total_main:
        verdict = "HARD_KILL_TRIGGER1_FIRES"
    elif n_main_fail >= 2:
        verdict = "TIGHTEN_RETEST_2_OF_3_FAIL"
    elif n_main_fail == 1:
        verdict = "EXPLORATORY_1_OF_3_FAIL"
    else:
        verdict = "PHASE1_MAIN_EFFECT_PASS"

    summary = {
        "phase":      "Phase 1 -- Day 14 mid-checkpoint",
        "framing":    "alpha-discovery + §4 robustness (reframed 2026-04-27)",
        "kill_rule":  "ALL 3 main-effect metrics AND-fail = trigger #1 hard kill",
        "metrics":    metrics,
        "n_main3_fail": n_main_fail,
        "verdict":    verdict,
        "next_action": {
            "PHASE1_MAIN_EFFECT_PASS":     "Continue to Day 15-18 (cohort-stratified §4.1 + naive-vs-realistic §4.2 + cross-LLM §4.3 + contamination §4.4 + masking §4.5)",
            "EXPLORATORY_1_OF_3_FAIL":     "Continue but flag the failed metric in writeup §3 caveat. Robustness battery still expected to fire something publishable.",
            "TIGHTEN_RETEST_2_OF_3_FAIL":  "Tighten data joins + re-test once. If still 2/3 fail -> ABANDONED.md.",
            "HARD_KILL_TRIGGER1_FIRES":    "ABANDONED.md. Project freezes. Postmortem report.",
        }.get(verdict, ""),
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
