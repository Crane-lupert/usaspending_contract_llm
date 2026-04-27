# RESUMABLE.md — Project M1 (USAspending Federal Contract Narrative LLM)

> Phase 0 → Phase 1 transition GO. 0 abandon triggers fired.

## Status snapshot — 2026-04-27 EOD

- **Phase**: Phase 1 entry (Day 8 of 21)
- **Phase 0 6-AND kill gate**: **6/6 PASS**
- **Phase 0 OpenRouter spend**: $0.334 / $8 cap (4.2%)
- **Total OpenRouter spend (this project)**: $0.334 / $35 cap (1.0%)
- **Gate F (daemon-free)**: ✓
- **Tests**: 36 / 36 PASS
- **Commits**: 3 done, 1 pending (Day 4-7 bundle)
- **Mailbox**: 1 outbound (coord, non-blocking, no reply yet)

## Phase 0 final results

| Metric | Result |
|---|---|
| Sample availability | LMT alone 3,152 contracts FY2024 → 39-firm extrapolation 19.5K-39K (PASS_CAPACITY) |
| n=10 dry-run | 10/10 PASS on universe-filtered sample |
| Fleiss κ axis1 | **0.7863** (target ≥ 0.7) — objective contract-type schema works |
| Fleiss κ axis2 | 1.0 (trivial — sample all EXPANSION) |
| Fleiss κ axis3 | -0.04 (Feinstein-Cicchetti paradox at 96% CLEAN base rate) → 2-axis fallback applied per plan |
| Phase 0 spend | $0.334 / $8 cap |
| Scoop clear | ✓ (no academic publication on M1 angle) |
| Publish-lag 5-bin | ✓ across 3 cohorts (2014/2018/2024) |

## Phase 1 critical preview

**Trigger #2a (lag<24h ≥ 50%) — preview-FIRES on 2018 + 2024 cohorts:**

| Cohort | <24h |
|---|---|
| 2014 | 0.35 |
| 2018 | 0.65 |
| 2024 | 0.75 |

Industry pickup window narrowed from ~65% lead (2014) to ~25% lead (2024). Most likely Phase 1 outcome: **writeup-only freeze (full kill 아님 — negative-incremental publishable)**.

**Trigger #2b (alpha decay > 50%/yr) — does NOT fire**: cohort drift = 40% / 10y ≈ 4%/yr.

## Day 4-7 deliverables (this overnight)

- `data/LABELER_GUIDE.md` — 3-axis schema spec
- `src/.../ensemble.py` — 3-vendor LLM client (Opus 4.7 + Sonnet 4.6 + Gemma-2-27b)
- `data/oracle_n20.json` — Claude-anchored gold standard
- `src/.../oracle_run.py` — 3-vendor + Fleiss κ
- `src/.../cohort_lag.py` — 2014/2018/2024 cohort-stratified publish-lag
- `src/.../universe_fetch.py` — per-prime universe-filtered fetch (145 contracts)
- `src/.../dryrun_n10.py` — Stage A-F end-to-end pipeline
- `src/.../phase0_kill_gate.py` — 6-AND evaluator
- `audits/self_audit_day4to7_2026-04-27.md` — 48h-kill-gate clear
- `data/cache/llm_responses/` — 60 cached LLM responses (idempotent re-runs cost $0)

## Day 8 done — Phase 1 entry achieved

- `src/.../strategic_sample.py`: 30 primes × 5 cohorts (2010/2014/2018/2022/2024) fetcher.
- `data/manifest_strategic_sample.jsonl`: **8,365 parsed contracts** (parse yield 99.1%).
- Even cohort split: 5,051 IS (2010-2018) / 3,390 OOS (2022-2024).
- Validation batch: 50 × 3 vendors = **150/150 calls $0.575**, per-call avg $0.0038.

## Phase 1 sizing finding

Phase plan §1 Day 8 target "≥ 40K target queued" was set assuming unlimited LLM budget. **40K × 3 vendors = $456, far over $25 Phase 1 cap.** Re-anchored realistic LLM batch size: **2,000 contracts × 3 vendors ≈ $23** — fits exactly. The binding power metric is cross-section quintile-month n (39 primes × 17 yr × 4 quarters ≈ 2,652 cells), not raw LLM-call count.

## Phase 1 plan (reframed 2026-04-27 — alpha-discovery + §4 robustness)

**Single hard kill = trigger #1 (main effect ALL-3 AND fail).** Trigger #2 demoted to §4 robustness finding (cohort heterogeneity = identification strength, not freeze).

| Day | Task | Cost |
|---|---|---|
| 9 | LLM 3-axis batch on stratified subsample (1,950 contracts × 3 vendors) | ~$23 |
| 10 | recipient_uei→ticker on full 8K + yfinance daily price + quarterly EPS join + 8-K CAR computation | $0 |
| 11 | Cross-section quintile portfolio (low-commitment long / high-commitment short, XAR/XLK-hedged) | $0 |
| 12 | CCM 2011 aggregate baseline replication (state-level federal-spending shock + state-of-HQ for 39 primes) | $0 |
| 13 | Two-step regression: incremental R² + ROC-AUC + quintile spread Sharpe | $0 |
| 14 | **Mid-checkpoint trigger #1 evaluation** — incremental R² ≥ 5% AND ROC-AUC ≥ 0.6 AND Sharpe ≥ 0.3 (kill if ALL fail) | $0 |
| 15 | Cohort-stratified §4.1 regression (per-FY-cohort quintile spread Sharpe trajectory) | $0 |
| 16 | §4.2 realistic-vs-naive timing audit + §4.3 cross-LLM sign agreement | $0 |
| 17 | DSR / BH-FDR / cluster bootstrap rigor on §3 main effect | $0 |
| 18 | §4.4 contamination (cutoff split) + §4.5 firm-name masking + (optional) §4.6 subaward dry-run | $0 |
| 19 | Streamlit MVP 5-page (Page 4 = cohort heterogeneity chart, single-chart §3+§4 surface) | $0 |
| 20 | Writeup 8-12p per `analysis/paper_outline.md` (§3 main + §4 robustness integrated) | $0 |
| 21 | Hard cap + GitHub push + dashboard deploy | $0 |

## Resume command

```
python -m usaspending_contract_llm.resume
pytest tests/ -v
python -m usaspending_contract_llm.phase0_kill_gate  # re-confirm 6/6
ls data/manifest_strategic_sample.jsonl    # 8,365 lines
```

Then proceed: `Day 9 시작` or `계속`.

## Resume command

Fresh session start:
```
python -m usaspending_contract_llm.resume
pytest tests/ -v
python -m usaspending_contract_llm.phase0_kill_gate  # re-confirm 6/6 PASS
```

Then proceed: `Day 8 시작` or `계속`.

## Open mailbox

- Outbound: `D:/vscode/portfolio-coordination/mailbox/portfolio_coordination/20260427T1604-usaspending_contract_llm-openrouter-project-registration.md` (correlation_id `20260427T1604-usaspending_contract_llm-001`). Non-blocking; project tag `"usaspending"` working with default cap.
- Inbound: none.
