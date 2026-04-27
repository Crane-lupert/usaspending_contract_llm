# Project M1 Postmortem (TEMPLATE — fill on Day 14 final HARD_KILL verdict)

> Trigger: Phase 1 trigger #1 fires (incremental R² < 5% AND ROC-AUC < 0.6 AND quintile Sharpe < 0.3 — ALL 3 AND fail) at full Day 9 batch sample.

## Verdict

- Date: 2026-04-{XX}
- Sample at verdict: n_LLM = {N_LLM} contracts × 3 vendors, n_panel = {N_PANEL} firm-quarter, n_with_CAR = {N_CAR}
- Phase 0 → Phase 1: **GO** (6/6 PASS)
- Phase 1 trigger #1: **HARD_KILL_TRIGGER1_FIRES**

| Metric | Value | Threshold | Verdict |
|---|---|---|---|
| Incremental R² over CCM | {R2_INC} | ≥ 0.05 | FAIL |
| Cross-section quintile Sharpe (annualized) | {SHARPE_ANN} | ≥ 0.30 | FAIL |
| Earnings beat ROC-AUC | {AUC} | ≥ 0.60 | FAIL |
| Cross-LLM 3-vendor coverage | {COVERAGE}% | ≥ 80% | {V_COV} |

→ **ABANDONED.md.** Project freezes. Negative-incremental writeup is *not* a paper headline — Phase 0 evidence (industry pickup decay 2014→2024) was suggestive but Phase 1 main-effect failure means the §3 claim doesn't survive full sample.

## What worked

1. **Phase 0 design**: 6-AND single kill gate, daemon-free Gate F, scoop search, Fleiss κ.
2. **Reframing 2026-04-27**: would have collapsed industry-absorption into §4 robustness IF main effect existed. It didn't.
3. **Resumable infrastructure**: cache + manifest atomic writes meant 0 wasted LLM calls during multi-session work.
4. **Cost discipline**: $0.91 / $35 cap (~3%). HARD_KILL at low cost is the *right* outcome under this budget.
5. **Multi-axis schema design**: 3-axis Fleiss κ_axis1 = 0.79 (objective FFP/IDIQ/option/cost-plus is well-defined). Schema *itself* worked.

## What didn't work — the actual mechanism failure

1. **Forward revenue commitment LLM extraction did NOT predict next-quarter cross-section variation in earnings surprise / forward CAR / quintile spread when measured on full sample.**
   - The 30%-data preview (n=12 q, n_obs=97) showed Sharpe 1.03 / t=1.79 — *appeared* alpha-like.
   - The 60%-data preview (n=17 q, n_obs=178) collapsed to Sharpe ~0 / t≈0.
   - The full sample (n=??) confirmed.
2. **Most likely root cause** (analytical interpretation):
   - Federal contract narratives encode *committed* revenue, but firm-quarter aggregation diluted the per-contract signal across many low-information items (delivery orders, option exercises, FFP delivery purchases against existing IDIQs).
   - Cross-section ranking on average commitment-uncertainty-weighted score did not correlate with cross-section earnings-surprise dispersion — possibly because:
     (a) the 39-firm universe is too homogeneous in commitment-mix (most defense primes have similar FFP/IDIQ/cost-plus mix);
     (b) earnings surprise is dominated by sources outside contract-narrative — guidance, macro, FX, supply chain;
     (c) yfinance free-tier earnings_dates only gave ~5yr coverage → CAR sample biased to recent quarters where signal had already been industry-absorbed.

## Salvageable findings (paper-quality even without main effect)

1. **Cohort-stratified publish-lag distribution (Phase 0 finding)**:
   - 2014: 35% <24h
   - 2018: 65% <24h
   - 2024: 75% <24h
   - This is a *standalone publishable observation* about industry-pickup-window narrowing. Could anchor a short SSRN note (3-5p) on its own.
2. **3-axis LLM schema validation**:
   - κ_axis1 = 0.79 (3-vendor Fleiss) demonstrates contract-type LLM extraction works objectively.
   - This is a methodological reference future researchers may cite even without a tradable signal.
3. **Cost-bounded reproducibility**: the open-source pipeline ran end-to-end at $0.91. Methodological contribution.

## Decision rule retrospective

- The reframed plan (alpha-discovery + §4 robustness) was correctly framed but the *main effect itself was null*. No reframing rescues a null main effect.
- The single hard kill (ALL 3 AND fail) was the right gate. Looser gates (2 of 3, or 1 of 3) would have invited sunk-cost extension.
- Day 21 hard cap not reached — early HARD_KILL at Day 14 saves Phase 1 budget for next portfolio entry.

## Spend / time accounting

- Phase 0: $0.334 / $8 cap
- Phase 1 (Day 4 oracle + Day 9 batch + Day 18 masking): ${ACTUAL_PHASE1} / $25 cap
- Total: ${ACTUAL_TOTAL} / $35 cap
- Total wall-clock: 1 day overnight + ~3hr Day 9 batch
- Tests: 36/36 PASS (Gate F, manifest, resume, parse, publish_lag, universe, recipient_map)

## Portfolio implications (QR Scout level)

- M1 was β2 frozen swap-queue 1순위 fill. With M1 ABANDONED, swap-queue 2순위 (next candidate) opens.
- Salvageable findings (Phase 0 cohort lag, schema methodology) → SSRN-note-tier deliverable, not paper-tier.
- Interview-grade artifact downgraded from "paper + dashboard + repo" to "GitHub repo demonstrating disciplined kill + Phase 0 cohort lag note".

## Next portfolio entry

- Per QR Scout playbook: defer to next overnight session for swap-queue selection.
- Candidates from `audits/2026-04-27-sec-free-deep-brainstorm.md` ranked NARROW-NOVEL but not yet launched.

## Files frozen at HARD_KILL

- `data/manifest_*.jsonl` — full audit trail
- `data/cache/llm_responses/` — 5,850 cached LLM responses (idempotent re-run = $0)
- `analysis/paper_outline.md` + `analysis/paper_writeup_skeleton.md` — paper drafts (NOT submitted; freeze for retrospective reference)
- `audits/self_audit_day*.md` — 5 self-audit logs
- `audits/scoop_search_2026-04-27.md` — Phase 0 weekly scoop result

## Sign-off

- Author: Claude (overnight session, 2026-04-{XX})
- Decision: ABANDONED.md
- Co-decided with user: {YES/NO}
- Next portfolio: TBD
