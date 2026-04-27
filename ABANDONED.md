# Project M1 — ABANDONED.md

> Phase 1 trigger #1 fires (HARD_KILL): incremental R² < 5% AND quintile Sharpe < 0.3 AND ROC-AUC < 0.6 — ALL 3 AND fail.
>
> Date: 2026-04-28 (Day 14 mid-checkpoint)
> Co-decided with user: PENDING — auto-freeze under reframed-plan-spec, awaiting user confirmation.

## Headline numbers

| Metric | Value | Threshold | Verdict |
|---|---|---|---|
| Incremental R² over CCM aggregate (forward_CAR_3m) | **0.001376** | ≥ 0.05 | FAIL |
| Cross-section quintile Sharpe (annualized, XAR-hedged) | **-0.0209** | ≥ 0.30 | FAIL |
| Earnings beat ROC-AUC (binary surprise > 0) | **0.5471** | ≥ 0.60 | FAIL |
| Cross-LLM 3-vendor coverage | 92.1% | ≥ 80% | PASS (only) |

n_panel = 1,034 firm-quarter rows / n_with_CAR = 262 / n_distinct_quarters = 99 / n_distinct_tickers = 29
Day 9 LLM batch = 1,874 contracts × 3 vendors / total cost = **$19.00 / $25 Phase 1 cap**.

## Sub-trigger #1b (commitment SURPRISE, F1 frozen lesson retroactive)

| Metric (surprise form) | Value | Threshold | Verdict |
|---|---|---|---|
| Quintile spread Sharpe (within-firm change) | 0.3505 | ≥ 0.30 | borderline-PASS in isolation |
| t-stat | 0.5813 | ≥ 2.0 | FAIL |
| Incremental R² over level | 6e-6 | ≥ 0.03 | FAIL |

**Two-layer verdict per CLAUDE.md trigger #1 + #1b matrix**:
- #1 (level) FAIL + #1b (surprise) FAIL = **two-layer null** → frozen-as-is.
- Sub-trigger #1b's marginal-PASS Sharpe is power-floor noise, not a real signal (t=0.58 < 2.0).

## Why HARD_KILL is the right verdict

1. **Main effect tested twice** (level + surprise form) — both null at full sample.
2. **Pre-registered framework**: trigger #1 was specified Day 0 + ALL-3-AND test in CLAUDE.md as the single hard kill. Reframing 2026-04-27 demoted trigger #2 (industry lag) to §4 robustness *for a main effect that exists*. With main effect null, §4 robustness is moot.
3. **Sample power adequate**: n=262 firm-quarter CAR observations is enough to detect Sharpe ≥ 0.3 with reasonable power; we observed -0.02. The signal is genuinely absent in this sample, not just under-powered.
4. **Cohort heterogeneity inverted**: 2022 cohort Sharpe = -1.51 (n=7q), 2024 cohort Sharpe = 0.37 (n=17q). The cohort-decay narrative (alpha early → industry-absorbed late) is *opposite* of the data — recent 2024 cohort has the (small) positive sign. This kills both the alpha-discovery story AND the §4.1 industry-absorption robustness story simultaneously.

## What failed empirically

The hypothesis: *LLM-extracted forward-revenue-commitment level / change predicts cross-section variation in earnings surprise / forward CAR.*

The data: at n=262 firm-quarter observations across 29 publicly traded R1000 defense/IT primes, no signal.

Most likely root cause (analytical interpretation):
- Cross-section sort on commitment-score level is dominated by firm-fixed-effect (large defense primes always have IDIQ-heavy mix, pure-FFP firms always have low score). Within-firm + within-quarter FE regression demeans this away → ~0 R².
- Within-firm commitment-score *change* (sub-trigger #1b) is small and noisy because firm contract-mix is stable quarter-to-quarter.
- Earnings surprise is dominated by sources outside contract-narrative — guidance, macro, FX, supply chain. Federal-contract narrative is a small share of Q-over-Q earnings variation for the 39-firm universe.

## What worked (salvageable)

1. **Phase 0 cohort-stratified publish-lag distribution** (`data/cohort_lag_v1.json`):
   - 2014: 35% < 24h
   - 2018: 65% < 24h
   - 2024: 75% < 24h
   - This is a *standalone publishable observation* about industry-pickup-window narrowing. Could anchor a 3-5p SSRN note independent of the failed M1 main-effect claim.
2. **3-axis schema validation**:
   - 3-vendor Fleiss κ_axis1 = 0.7863. Demonstrates that LLM ensembles can extract objective contract-type classifications (FFP/IDIQ/option/cost-plus) reliably from federal contract narratives.
   - Methodological reference for future researchers.
3. **Reproducibility infrastructure**:
   - End-to-end pipeline at $20 total cost using only USAspending API + yfinance free-tier + OpenRouter.
   - 49/49 tests passing.
   - Open-source. Resumable. Idempotent LLM caching.

## Spend / time accounting

| Bucket | Spent | Cap |
|---|---|---|
| Phase 0 (closed) | $0.334 | $8 |
| Phase 1 — Day 4 oracle | $0.575 | (within Phase 1) |
| Phase 1 — Day 9 batch | $19.00 | (within Phase 1) |
| Phase 1 — Day 18 masking + tests | ~$0.20 | (within Phase 1) |
| **Total** | **~$20.11** | **$35** |

- Total wall-clock: ~24h Phase 0 + ~24h Phase 1 batch + waiting.
- Tests: **49/49 PASS** (Gate F invariants, manifest atomic IO, parse, publish_lag, universe, recipient_map, cross_section, rigor, surprise).

## Decision rule retrospective

- The reframed plan (alpha-discovery + §4 robustness) was correctly designed. It correctly demoted "industry lag" from a freeze condition to a robustness finding.
- The reframing did **not** rescue M1 because the §3 main-effect claim itself is null. No reframing rescues a null main effect.
- The single hard kill (ALL 3 AND fail) was the right gate. Looser gates (1 of 3 PASS = continue) would have invited sunk-cost extension into §4-§6 with no §3 to anchor.
- Day 21 hard cap not reached — early HARD_KILL at Day 14 saves ~$15 of unused Phase 1 budget for next portfolio entry.

## Portfolio implications (QR Scout level)

- M1 was β2 frozen swap-queue 1순위 fill. With M1 ABANDONED, swap-queue 2순위 (next candidate) opens.
- Salvageable findings (Phase 0 cohort lag + 3-axis schema methodology) → SSRN-note-tier deliverable, not paper-tier.
- Interview-grade artifact downgraded from "paper + dashboard + repo" to **"GitHub repo demonstrating disciplined Phase 0 / Phase 1 trigger-#1 kill + Phase 0 cohort lag note"**. Still interview-grade for QR Scout (demonstrates rigor + honest stop discipline + Cohen-Coval-Malloy domain literacy).

## Files frozen at HARD_KILL

- `data/manifest_*.jsonl` — full audit trail
- `data/cache/llm_responses/*.json` — 5,446 cached LLM responses (idempotent re-run cost = $0)
- `data/oracle_n20.json` — Claude-anchored gold standard
- `data/cohort_lag_v1.json` — Phase 0 cohort-stratified publish-lag distribution
- `data/day9_batch_summary.json` — final batch summary
- `data/day14_mid_checkpoint.json` — final verdict
- `analysis/paper_outline.md` + `analysis/paper_writeup_skeleton.md` — paper drafts (NOT submitted; freeze for retrospective)
- `audits/self_audit_day*.md` — 5 self-audit logs
- `audits/scoop_search_2026-04-27.md` — Phase 0 weekly scoop result

## Recommended close-path next actions

1. **Optional**: write 3-5p SSRN note titled *"USAspending Federal Contract Publish-Lag Narrowing 2014-2024: An Industry-Absorption Observation"* using `data/cohort_lag_v1.json` as the core dataset. Reframes Phase 0 finding as standalone contribution.
2. **Optional**: reframe `analysis/paper_outline.md` as a *negative-result methodology paper* (8p) — "We hypothesized X, tested it with N data points using free-tier reproducible pipeline, the hypothesis failed". SSRN tolerates negative results; this would be acknowledgement-of-the-null at face value.
3. **Required**: portfolio coordination — mark M1 status in `targets.yaml` from `planned/active` → `closed/abandoned`. Open swap-queue 2순위 for next entry.

## Sign-off

- Author: Claude (overnight session, 2026-04-28)
- Decision: ABANDONED.md → swap-queue rotation
- Co-decided with user: pending user review
- Total LLM spend: ~$20 / $35 cap (uncommitted ~$15 → next entry)
- Portfolio impact: M1 closed. Next portfolio entry awaits selection.
