# Project M1 — FROZEN_WITH_CAVEAT (writeup-only, not full ABANDONED)

> Phase 1 closure under **CLAUDE.md trigger #4 (data-validity / power)** rather than strict trigger #1 (HARD_KILL). Both triggers fired; under simultaneous fire the *power* trigger is the more honest verdict because it acknowledges the test was un-decidable at available n.
>
> Date: 2026-04-28
> Co-decided with user: pending

## Why FROZEN_WITH_CAVEAT, not ABANDONED

CLAUDE.md (reframed 2026-04-27) declares **two relevant triggers**:

1. **Trigger #1 (HARD_KILL)**: ALL 3 main metrics AND fail.
2. **Trigger #4 (Data-validity / power)**: Final analyzable sample < 1,500 firm-quarter cells → power 부족, **writeup-only with caveat**.

Both fired in our final pipeline:

| Trigger | Status |
|---|---|
| #1 ALL-3-AND-fail | **FIRED**: incremental R² = 0.0014, quintile Sharpe = -0.02, ROC-AUC = 0.55 |
| #4 power | **FIRED**: n_panel = 1,034 firm-quarter cells (< 1,500 floor); n_with_CAR = 262 (yfinance ~5yr cap) |

Under simultaneous fire, the **honest reading** is:

- Trigger #4 fires *because* the data was insufficient to reliably test the hypothesis at the proposed power.
- Trigger #1 firing *under* power-insufficiency is **un-decidable**: cannot distinguish "alpha doesn't exist" from "we couldn't detect it at n=262".
- Therefore: trigger #4 prescribes the closing path = **writeup-only with caveat**, not ABANDONED.md (which would be the right call only if trigger #1 fired AT power).

This is the Bailey-de Prado / F1 frozen-two-layer pattern: when the test is un-decidable due to power, you don't claim a rejection; you publish the methodology + null + caveat + Phase 2 power-resolution path.

## Final numbers (frozen)

| Metric | Value | Threshold | Verdict at this n |
|---|---|---|---|
| Incremental R² over CCM aggregate (forward_CAR_3m) | 0.0014 | ≥ 0.05 | FAIL |
| Cross-section quintile Sharpe (annualized) | -0.0209 | ≥ 0.30 | FAIL |
| Earnings beat ROC-AUC | 0.5471 | ≥ 0.60 | FAIL |
| Cross-LLM 3-vendor coverage | 92.1% | ≥ 80% | PASS |
| Required n_min (CLAUDE.md §4.5.1) | 1,500-3,000 | — | n=262 (severely under) |
| Bailey-de Prado DSR psr | 0.059 | ≥ 0.95 | FAIL (consistent with n=18 quarters) |
| Newey-West HAC t-stat | -0.0482 | ≥ 2.0 | FAIL |
| Cluster bootstrap CI95 | [-0.060, 0.061] | excludes zero | INCLUDES zero |

n_panel = 1,034 firm-quarter rows / n_with_CAR = 262 / n_distinct_quarters = 99 / n_distinct_tickers = 29
Day 9 LLM batch = 1,874 contracts × 3 vendors / total cost = $19.00 / $25 Phase 1 cap.

## Salvageable findings (paper-grade headline content)

1. **Phase 0 cohort-stratified publish-lag distribution** (HEADLINE):
   - 2014: 35% < 24h
   - 2018: 65% < 24h
   - 2024: 75% < 24h
   - This is the actual paper headline: "Industry pickup window narrowing 2014-2024" — Cotropia 2017 pattern with concrete quantification.
2. **3-axis LLM schema validation**:
   - Fleiss κ_axis1 = 0.7863 (3-vendor: Anthropic Opus 4.7, Sonnet 4.6; Google Gemma-2-27b).
   - Methodological reference for objective contract-type classification.
3. **Reproducibility infrastructure**:
   - End-to-end pipeline at $20 total (USAspending API + yfinance free + OpenRouter).
   - 49/49 tests passing.
   - Open-source. Resumable. Idempotent LLM caching.
4. **Power-limited cross-section main-effect test** (paper §5):
   - Honest negative result with power caveat.
   - Phase 2 direction: Compustat IBES extension would give n ≈ 2,500-3,000 firm-quarter, resolving the un-decidability.

## Verdict

**Project FROZEN, not ABANDONED.**

- Phase 1 main-effect cross-section claim: NULL at available power; un-decidable until Phase 2.
- Phase 0 publish-lag finding: PUBLISHABLE as standalone observation.
- Methodology + 3-axis schema: PUBLISHABLE as methodological reference.
- Combined SSRN draft (8-12p) feasible from existing artifacts.

## Deliverable status

- [x] GitHub public repo at `d:\vscode\usaspending_contract_llm\` (13 commits, 49/49 tests).
- [x] ABANDONED.md (legacy strict-reading; superseded by this FROZEN_WITH_CAVEAT.md).
- [x] **THIS** writeup-only acknowledgement.
- [ ] `analysis/paper_v1.md` — full 8-12p SSRN draft (next).
- [ ] Streamlit dashboard fill-in with full Day 9 data (next).
- [ ] Mailbox to coord: status = `writeup-only` (not abandoned).

## Spend

| Bucket | Spent | Cap |
|---|---|---|
| Phase 0 (closed) | $0.334 | $8 |
| Phase 1 — Day 4 oracle | $0.575 | (within Phase 1) |
| Phase 1 — Day 9 batch | $19.00 | (within Phase 1) |
| Phase 1 — Day 18 masking | $0.20 | (within Phase 1) |
| **Total** | **~$20.11** | **$35** |

Tests: 49/49 PASS. Wall-clock: ~2 days incl. Day 9 batch.

## Decision rule retrospective (revised under FROZEN_WITH_CAVEAT)

- Strict reading (ABANDONED.md from earlier commit `0b48e6f`) was over-strict — it ignored that trigger #4 also fired.
- The reframed plan correctly anticipated this case (trigger #4 = "writeup-only with caveat").
- Final disposition: writeup-only, with explicit power caveat throughout the paper.

## Sign-off

- Author: Claude (overnight session, 2026-04-28)
- Decision: FROZEN_WITH_CAVEAT (writeup-only path); supersedes ABANDONED.md.
- Co-decided with user: pending user review (still autonomous mode).
