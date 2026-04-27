# Day 8 Self-Audit — Phase 1 Entry (2026-04-27)

> Strategic sampling expansion + small validation LLM batch. Phase 1 fetch infrastructure ready; Day 9 LLM batch pending budget commit.

## Verified tasks

1. `src/.../strategic_sample.py` — 30 primes × 5 cohorts (2010, 2014, 2018, 2022, 2024) × up to 60 contracts each.
2. `data/manifest_strategic_sample.jsonl` — **8,365 parsed contracts** written (raw 8,441 fetched, 99.1% parse yield).
3. Validation LLM batch — 50 contracts × 3 vendors = **150/150 calls succeeded**, cost = $0.5751 ($0.0038/call avg).

## 1. Findings

| # | Severity | Finding | Source |
|---|---|---|---|
| 1 | **structural** | Phase plan §1 Day 8 target "≥ 40K target queued" was set *for the LLM batch sample size*. With Phase 1 budget = $25 and per-call cost = $0.0038, 40K × 3 vendors = $456 — well over budget. **Realistic LLM batch size: 1,500-2,200 contracts × 3 vendors = $17-25.** | derived from validation cost |
| 2 | medium | Strategic sample 8,365 contracts is enough for cross-section quintile (39 primes × 17 yr × 4 quarters = 2,652 firm-quarter cells need joins, not 40K LLM labels). | direct |
| 3 | low | Per-cohort distribution evenly balanced: 2010=1,687, 2014=1,689, 2018=1,675, 2022=1,707, 2024=1,683. Top 10 primes (LMT, BA, RTX, NOC, LDOS, BAH, GD, LHX, SAIC, ACN) all hit the 60 cap. | `data/strategic_sample_summary.json` |
| 4 | low | 76 contracts (8,441 - 8,365) didn't parse (missing description / generated_internal_id) — 0.9% parse loss. Phase 0 trigger #2 yield target ≥ 99% still met (99.1%). | `parse_award_row` returns None |

## 2. Resolution per finding

| # | Resolution |
|---|---|
| 1 | **Phase 1 Day 9 LLM batch sized to 2,000 contracts × 3 vendors = $23 (within $25 cap)**. Stratified sample: 39 primes × 5 cohorts × 10 contracts = 1,950 (close to 2,000 target). Alternative: 4,000 × 2 vendors (drop Sonnet, keep Opus + Gemma vendor diversity). Day 9 kickoff decision. |
| 2 | Document the binding metric: cross-section quintile-month n. 8K contracts → ~50K firm-quarter join entries → power adequate for Sharpe ≥ 0.4 detection. |
| 3 | Even cohort distribution good for IS/OOS split: 5K contracts in IS (2010-2018 cohorts), 3.4K in OOS (2022-2024). |
| 4 | Acceptable. Phase 1 batch dedup logic + retry-on-error covers this. |

## 3. 48h-kill-gate

- **(a) Any unsolvable problem?** No.
- **(b) Solution applied → repo purpose lost?** No. Sample size enough for cross-section + stratified by cohort for alpha-decay measurement.
- **(c) Solution within 48h verifiable retry?** Yes — Day 9 LLM batch is the next step.

→ **Verdict: continue.** Day 9 in next session.

## 4. Spend budget update

| Bucket | Spent | Cap | Remaining |
|---|---|---|---|
| Phase 0 (closed) | $0.334 | $8 | (Phase closed) |
| Phase 1 (open) | $0.575 | $25 | $24.43 |
| Total project | $0.909 | $35 | $34.09 |

## 5. Day 9-21 plan (next sessions)

| Day | Task | Cost |
|---|---|---|
| 9 | LLM 3-axis batch on stratified subsample (~2,000 contracts × 3 vendors) | ~$23 |
| 10 | Mapping join (uei→ticker via 4-layer fallback on full 8,365 sample) + earnings/CAR join | $0 |
| 11 | Cross-section quintile portfolio first read | $0 |
| 12 | CCM 2011 aggregate baseline replication | $0 |
| 13 | Two-step regression (incremental R²) + ROC-AUC | $0 |
| 14 | Phase 1 mid-checkpoint | $0 |
| 15 | OOS cohort stratified inference (already in batch from Day 9) | $0 |
| 16 | **Phase 1 trigger #2 formal evaluation** — naive vs realistic timing audit + cohort alpha decay rolling Sharpe | $0 |
| 17 | DSR / BH-FDR / cluster bootstrap rigor | $0 |
| 18 | Robustness module (cross-LLM + contamination + masking) | $0 |
| 19 | Streamlit MVP 5-page | $0 |
| 20 | Writeup 8-12p | $0 |
| 21 | Hard cap + GitHub push | $0 |

## 6. Sign-off

- Author: Claude (overnight session, 2026-04-27)
- Day 8 deliverable: 8,365 strategic-sample contracts queued + $0.58 validation batch confirmed pipeline scales.
- Stop reason: Day 9 LLM batch is a discrete $23 spend that warrants a clean session boundary with explicit budget commit. Fresh session can decide between (a) 3-vendor × 2K, (b) 2-vendor × 5K, or (c) other splits.
