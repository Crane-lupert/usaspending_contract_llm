# Project M1 — FREEZE NOTICE

> **Date frozen**: 2026-04-28
> **Frozen by**: user decision
> **Status**: paused, awaiting paid-data-vendor decision at portfolio level
> **Type**: temporary freeze (not abandoned, not closed) — work resumes when vendor decision made

## Why frozen

M1 cannot progress further on free-tier data:

- Phase 1 trigger #1 still fires (3-of-3 main metrics fail) at proper power post-Gate-F-lift.
- Phase 1 trigger #4 (data-validity / power) also fires: n_panel = 1,034 < 1,500 floor.
- yfinance ~5yr `earnings_dates` cap is the binding constraint for ROC-AUC + surprise computation.
- §4 cohort heterogeneity shows positive signal in 3 of 4 cohorts (2014: +0.34, 2018: +0.37, 2024: +0.51) but pooled is washed by 2022 outlier (-0.34). Confirming the cohort-specific signal at proper power requires IBES consensus + Compustat actuals.

The path forward depends on a paid-data-vendor decision (FMP / WRDS / stay-free-with-§12-alternatives) that is **portfolio-coordination level**, not M1-internal.

## State at freeze

- **Commit**: `a801933` (Gate F LIFTED + SEC EDGAR + 8-K event panel + multi-decade upgrade)
- **Tests**: 49/49 PASS
- **Spend**: ~$20.11 / $35 cap (~57%; ~$15 unused budget)
- **Working tree**: clean

### Phase scorecard

| Phase | Status |
|---|---|
| Phase 0 (Day 1-7) | ✅ 6/6 PASS |
| Phase 1 main effect (Day 8-14) | ❌ 3/3 main metrics FAIL (HARD_KILL trigger #1) |
| Phase 1 §4 cohort heterogeneity | ✅ 3/4 cohorts ≥ 0.30 threshold |
| Phase 1 power gate (trigger #4) | ❌ n=1,034 < 1,500 floor |
| Day 21 hard cap | not reached (early freeze) |

### Deliverables already produced

- GitHub-ready repo (14 commits, 49/49 tests).
- `FROZEN_WITH_CAVEAT.md` — verdict reframe.
- `analysis/paper_v1.md` — 8-12p SSRN draft (cohort-specific positive + pool null + power caveat).
- `dashboard/app.py` — 5-page Streamlit MVP with full data.
- `audits/postmortem_template.md` + 5 self-audit logs.
- Mailbox notifications to `portfolio_coordination`.

## What unfreezes M1

Any one of these triggers M1 resumption:

1. **Vendor decision (FMP $237 trial)** approved by portfolio coordination → M1 §12 free-alternatives + FMP integration phase begins.
2. **Vendor decision (WRDS academic seat)** approved → full M1 + portfolio-wide unblock.
3. **Vendor decision (stay-free)** approved → M1 §12 free-alternatives only (subaward layer + 10-Q XBRL + indirect-federal expansion).
4. **User direct override** ("계속 free-tier-with-§12-alternatives" or similar).

## What does NOT unfreeze M1

- Time alone (no scheduled wakeup).
- New academic publication on USAspending narrative LLM (would trigger ABANDONED, not unfreeze).
- New industry alt-data product launch (logged, but Phase 0 §3 publish-lag finding is independent).

## Reference (for whoever resumes)

When unfreezing, read in order:

1. This `FREEZE_NOTICE.md`.
2. `FROZEN_WITH_CAVEAT.md` (close-path verdict).
3. `analysis/paper_v1.md` (paper draft to extend or finalize).
4. `D:/vscode/meta-harness/audits/2026-04-28-M1-paid-data-vendor-needs.md` §11-§16 (post-Gate-F evidence + decision tree).
5. `RESUMABLE.md` (per-section resume hooks).
6. `python -m usaspending_contract_llm.resume` to verify state.
7. `python -m pytest tests/` to verify integrity (target: 49/49 PASS).

## Sign-off

- Author: Claude (M1 session, 2026-04-28)
- User decision: freeze pending paid-vendor decision.
- Estimated time-to-unfreeze: depends on portfolio-coordination decision speed (likely 1-7 days for FMP trial; 1-3 months for WRDS).
- M1 status post-freeze: same as `FROZEN_WITH_CAVEAT.md` — repo + paper draft + dashboard preserved.
