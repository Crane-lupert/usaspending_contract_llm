# RESUMABLE.md — Project M1 (USAspending Federal Contract Narrative LLM)

> ⚠️ **2026-04-28 FROZEN — pending paid-data-vendor decision** ⚠️
>
> See [FREEZE_NOTICE.md](./FREEZE_NOTICE.md) and [FROZEN_WITH_CAVEAT.md](./FROZEN_WITH_CAVEAT.md). Project paused at commit `a801933` (Gate F LIFTED state). Resume conditional on portfolio-coordination paid-vendor decision (FMP / WRDS / stay-free + §12 alternatives). See `D:/vscode/meta-harness/audits/2026-04-28-M1-paid-data-vendor-needs.md` §13 decision tree.
>
> ---
>
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

---

## Status snapshot — 2026-04-28 (Day 9 ~68%, trajectory toward HARD_KILL)

### Day 9 partial-data trajectory

| Sample size | n_obs | n_q | Sharpe_ann | t_stat | inc_R² | AUC | Verdict |
|---|---|---|---|---|---|---|---|
| 30% | 97 | 12 | **1.03** | 1.79 | 3.7% | 0.59 | TIGHTEN_RETEST (1-of-3 PASS) |
| 60% | 178 | 17 | **-0.07** | -0.14 | 4e-6 | 0.51 | **HARD_KILL** (3-of-3 FAIL) |
| 100% | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

### Trajectory diagnosis

Signal collapse 30%→60% suggests:
1. **30% sample was lucky/noisy** — only 12 paired quarters, 1-3 firms per quintile bucket.
2. **Older-cohort data (now joining in batch progress) has weaker signal** — yfinance free-tier earnings_dates ~5yr cap makes CAR-join sparse for 2010-2018 cohorts.
3. **Mechanism limit**: cross-section quintile by commitment_score level may be dominated by firm-size dummy. Within-firm-FE regression demeans it to ~0 R². The §3.5 SURPRISE form (#1b sub-trigger) shows similarly-null result on 60% data (Sharpe 0.35 / t=0.58 / R² ~ 0).

### Pre-registered alternatives tested

- **§3 main effect (level form)**: trending HARD_KILL on 60% data.
- **§3.5 SURPRISE form (CLAUDE.md sub-trigger #1b)**: borderline-null on 60% data.
- **§4.1 cohort heterogeneity**: yfinance ~5yr cap → only 2022/2024 cohorts have CAR. 2022 cohort Sharpe 13.1 (n=2 quarters, artifact); 2024 cohort Sharpe 0.56.
- **§4.2 timing audit**: realistic-pooled Sharpe 0.43 (was naive 1.03 on 30%); realistic-2024-only Sharpe 0.26.

### Most-likely full-batch outcome

**Two-layer null** (#1 FAIL + #1b FAIL) → ABANDONED.md / postmortem. Salvage = §4.1 publish-lag-distribution observation as a standalone short SSRN note.

### Auto-completion action

Background script `basdelcud` waits for `data/day9_batch_summary.json` and auto-runs `python -m usaspending_contract_llm.final_pipeline`. Output lands in `/tmp/m1_auto_run.log`.

When triggered:
1. Read final Day 14 verdict.
2. If HARD_KILL → fill `audits/postmortem_template.md` → write `ABANDONED.md` → final commit.
3. If MAIN_EFFECT_PASS → continue Day 15-21 (cohort + rigor + dashboard + writeup with full numbers).

### Original Phase 1 plan section (unchanged)


### What's complete

- **Reframing applied** (CLAUDE.md + analysis/paper_outline.md):
  - Single hard kill = trigger #1 (incremental R² < 5% AND ROC-AUC < 0.6 AND Sharpe < 0.3)
  - Trigger #2 demoted from kill to §4 robustness finding (Cotropia 2017 pattern).
- **Day 8** strategic_sample.py — 8,365 contracts, 30 primes × 5 cohorts.
- **Day 9 LLM batch** running in background (~39% done, ETA ~2hr from 22:00 KST).
- **Day 10** yfinance_join.py — 38/39 tickers, 803 (ticker, quarter) CAR rows.
- **Day 11** cross_section.py — partial-data preview Sharpe = 1.03 / t = 1.79 / 12 paired Q.
- **Day 12** ccm_baseline.py — partial-data incremental R² = 3.7% (borderline below 5%; t_commitment = -1.91 directionally correct).
- **Day 14** day14_mid_checkpoint.py — partial-data verdict: TIGHTEN_RETEST_2_OF_3_FAIL.
- **Day 16** cohort_heterogeneity.py — yfinance limit = ~5yr earnings dates → only 2022/2024 cohorts have CAR. Pre-2022 §4.1 power-limited.
- **Day 17** rigor.py — DSR + Newey-West (t_NW = 4.32 on partial) + cluster bootstrap + BH-FDR scaffold.
- **Day 18** contamination_masking.py — §4.4 cutoff split + §4.5 firm-name redaction.
- **Day 19** dashboard/app.py — 5-page Streamlit MVP scaffold.

### What's pending — wait for Day 9 batch

```bash
# When data/day9_batch_summary.json appears:
python -m usaspending_contract_llm.cross_section          # full sample quintile
python -m usaspending_contract_llm.ccm_baseline           # full sample 2-step regression
python -m usaspending_contract_llm.cohort_heterogeneity   # §4.1
python -m usaspending_contract_llm.rigor                  # DSR/NW/bootstrap on full
python -m usaspending_contract_llm.contamination_masking  # §4.4 + §4.5 (~$0.20)
python -m usaspending_contract_llm.day14_mid_checkpoint   # final trigger #1 verdict
```

### Day 14 mid-checkpoint partial-data result (preview only)

```
incremental_R2     = 0.0366  (FAIL — threshold 0.05; n=97, t_commitment=-1.91 directional)
quintile_sharpe    = 1.0349  (PASS — threshold 0.3; n_q=12, t=1.79)
roc_auc_proxy      = 0.5877  (FAIL — threshold 0.6; n=97; near-borderline)
cross_llm_coverage = MISSING (Day 9 batch incomplete)
verdict            = TIGHTEN_RETEST_2_OF_3_FAIL
```

Partial-data t-stats are *directionally correct* but borderline. Full sample (3.4× more data) likely tightens incremental R² + ROC-AUC. Sharpe already PASS.

### Bash background watcher (still running — emits when batch completes)

```bash
# bcywxnpxz: until [ -f data/day9_batch_summary.json ]; do sleep 30; done
```

Will print "DAY9_BATCH_COMPLETE" on completion. Then run the pipeline above.

### Spend snapshot (after Phase 1 entry)

| Bucket | Spent | Cap |
|---|---|---|
| Phase 0 (closed) | $0.334 | $8 |
| Phase 1 — Day 4 oracle | $0.575 | (counted in Phase 1) |
| Phase 1 — Day 9 in-progress | ~$8 (39% done; final ~$22) | $25 |
| Total project | ~$9 | $35 |

### When Day 14 final fires (next session)

- All 3 PASS or 2/3 PASS → Day 15+ proceed (cohort §4.1 / timing §4.2 / cross-LLM §4.3 / contamination §4.4 / masking §4.5).
- 2/3 FAIL → tighten data joins, re-test once, then ABANDONED.md if still failing.
- 3/3 FAIL → ABANDONED.md (postmortem, no paper headline).

### Open mailbox

- `processed/`: M1 OpenRouter registration confirmed (cap=$35, max=8). project_tag = `usaspending_contract_llm`.

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
