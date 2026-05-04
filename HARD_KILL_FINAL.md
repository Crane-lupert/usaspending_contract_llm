# Project M1 — HARD_KILL_FINAL (closed)

> **Date**: 2026-05-04
> **Closed by**: user decision after WRDS recovery (audit `D:/vscode/meta-harness/audits/2026-05-04-M1-recovery-results-verdict-reframe.md`)
> **Status**: closed/hard-kill-final. **No paper_v2**. QR Scout purpose = ship alpha, not null-results writeup.

## Summary

`FROZEN_WITH_CAVEAT.md` (commit `e865d26`) used the trigger #4 (power) caveat to defer the kill. WRDS recovery (2026-05-04) gave us 3× more data; **all 3 main metrics moved cleaner-null, not toward signal**.

The original strict-reading `ABANDONED.md` (commit `0b48e6f`) was correct. This file makes that the canonical close.

## Final numbers (post-WRDS, n_obs = 797)

| Metric | Pre-WRDS | Post-WRDS | Threshold | Verdict |
|---|---|---|---|---|
| Incremental R² (forward CAR_3m) | 0.0014 (n=262) | **6e-05** (n=797) | ≥ 0.05 | FAIL clean |
| Quintile Sharpe (annualized) | -0.0209 (n_q=18) | **-0.2014** (n_q=66) | ≥ 0.30 | FAIL clean |
| ROC-AUC (binary beat) | 0.5471 (n=262) | **0.5161** (n=797) | ≥ 0.60 | FAIL clean |

3-of-3 main metrics fail at proper power. Trigger #1 fires unambiguously. No power-caveat available.

## Cohort heterogeneity (5 cohorts post-WRDS)

3 of 5 cohorts pass 0.30 threshold individually (2014: +0.35, 2018: +0.84, 2024: +0.48). 2 fail (2010: -1.93 small-n outlier; 2022: -0.20). Pool = -0.20.

Multiple-testing assessment: P(3-of-5 above 0.30 by chance under H0) ≈ 31%. Bonferroni-5 critical Sharpe ≈ 0.74 — only 2018 (+0.84) marginally clears. Not strong enough to anchor a paper headline; not unusual under null.

## Decision: no paper_v2

- QR Scout's primary objective is **shipping working alpha** for HF QR pod placement.
- A null-result methodology paper does not advance that objective.
- M1's salvageable findings (Phase 0 publish-lag cohort trajectory + 3-axis κ_axis1=0.79) remain in the repo as documentation. Anyone wanting to extend can fork.

## Close-path actions

1. ✅ `HARD_KILL_FINAL.md` written (this file).
2. ✅ Mailbox to `portfolio_coordination` requesting registry update `frozen-pending-vendor-decision` → `closed/hard-kill-final`.
3. ✅ Final commit with all WRDS recovery code + this verdict.
4. ❌ `paper_v2` — skipped per user decision.
5. ❌ Phase 2 / cohort-deep-dive — skipped (post-hoc cohort selection risk).

## Spend

| Bucket | Spent | Cap |
|---|---|---|
| Phase 0 | $0.334 | $8 |
| Phase 1 LLM batch | $19.78 | $25 |
| Recovery (WRDS) | $0 (no LLM) | — |
| **Total** | **$20.11** | **$35** ($14.89 unused) |

WRDS data delivered courtesy of `wrds-data-courier` sister project — 0 marginal cost.

## What's preserved (audit trail)

- 15 commits (Day 1 → freeze → recovery).
- 49/49 tests PASS.
- `analysis/paper_v1.md` (FROZEN-era draft) — preserved as historical artifact, NOT promoted to v2.
- `dashboard/app.py` — preserved.
- 5,446 LLM response cache.
- Universe + recipient mapping infrastructure.
- WRDS event panel (`data/wrds_event_panel.json` 2,777 rows).
- Audits: `audits/postmortem_template.md`, 5 self-audit logs.
- Meta-harness audit: `D:/vscode/meta-harness/audits/2026-05-04-M1-recovery-results-verdict-reframe.md`.

## What supersedes what

| File | Status |
|---|---|
| `ABANDONED.md` (commit `0b48e6f`) | original strict-reading kill — **promoted to canonical** |
| `FROZEN_WITH_CAVEAT.md` (commit `e865d26`) | power-caveat reframe — **superseded** by this file |
| `FREEZE_NOTICE.md` (commit `f710b52`) | freeze pending vendor — **resolved**: vendor data arrived, killed at proper power |
| `RECOVERY_PHASE0.md` | Day 1-2 verification — **closed**: recovery completed, verdict = HARD_KILL |
| `HARD_KILL_FINAL.md` (this file) | **canonical close** |

## Sign-off

- Author: Claude (M1 session, 2026-05-04)
- User decision: HARD_KILL_FINAL, no paper_v2, registry → closed/hard-kill-final.
- Project status: **closed**. No further work.
- Repo preserved at HEAD; portfolio-coordination notified.
