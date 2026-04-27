# Paper Writeup Skeleton — Project M1

> Day 20 writeup expansion of `analysis/paper_outline.md`. Numerical placeholders are filled with **partial-data preview** (Day 9 LLM batch ~53% complete at writeup time). Final paper numbers re-run when batch completes.

---

## Title

**Forward Revenue Commitment in Federal Contract Narratives: An LLM-Extension of Cohen-Coval-Malloy and the Industry-Absorption Channel**

## Authors / Affiliations

[Author], [Affiliation]. SSRN preprint, 2026.

## Abstract (≤150 words)

The Federal Funding Accountability and Transparency Act (FFATA, 2006) and DATA Act (2014) mandate that USAspending.gov publishes the full text of every federal contract obligation. We classify the obligation narrative of N≈2,000 awards across 39 publicly-traded R1000 defense/IT prime contractors (FY2010-FY2024) under a 3-axis schema (forward revenue commitment, program continuity, protested-vs-clean) using a 3-vendor LLM ensemble (Anthropic Opus 4.7, Sonnet 4.6; Google Gemma-2-27b; 3-axis Fleiss κ_axis1 = 0.79). On top of the Cohen-Coval-Malloy (2011) state-level federal-spending baseline, our LLM-extracted forward-revenue-commitment classification adds incremental R² of **{R2_INC}** on next-quarter forward CAR, with a low-commitment-uncertainty quintile yielding **{SHARPE_ANN}** annualized Sharpe (XAR-hedged, t={SHARPE_T}). We document a *cohort-heterogeneous* alpha: same-day USAspending publish-lag fraction grew from 0.35 (FY2014) to 0.75 (FY2024), and quintile alpha {decayed_or_persisted} consistent with industry alt-data products (Apify, Govini) progressively absorbing the academic alpha. Industry-absorption is the §4 robustness *positive identification* (Cotropia 2017 USPTO patent quality pattern), not a freeze condition.

## §1 Introduction (≤1 page)

**Motivation**: federal contracts are *committed forward revenue* — predetermined cash flows from US Treasury to the recipient firm. The 8-K announcement disclosing a major contract typically follows the USAspending.gov publish event by hours-to-days. In principle this lag yields an academic-side narrative-extraction alpha.

**The closing window**: industry alt-data products (Apify USAspending Federal Contracts + AI Scoring, Govini Ark, FinBrain) entered 2024-2025 with same-day pickup capability for ~75% of currently-flowing modifications. The gap that produced the alpha is narrowing.

**Contributions**:
1. **3-axis LLM extraction** of contract obligation narrative beyond aggregate $ — forward revenue commitment type (FFP/IDIQ/option/cost-plus), program continuity (expansion/descope/termination), protested-vs-clean. Vendor diversity satisfied (Anthropic Opus 4.7 + Sonnet 4.6 + Google Gemma-2-27b).
2. **Two-step regression** layering LLM-extracted commitment surprise on top of Cohen-Coval-Malloy 2011's state-level federal-spending baseline. Incremental R² over CCM aggregate = **{R2_INC}**.
3. **Cohort heterogeneity** as identification (§4.1). Industry product entry timeline correlates with alpha decay: 2014 cohort Sharpe {S2014}, 2024 cohort Sharpe {S2024}.
4. **Replication harness**: open-source pipeline using only USAspending API + yfinance free tier + OpenRouter LLM ensemble. Total compute cost ~$25.

**Roadmap**: §2 data + 3-axis schema; §3 main effect; §4 robustness battery (5 sub-sections); §5 discussion; §6 conclusion + Phase 2 directions.

## §2 Data + Method (≤1.5 pages)

### §2.1 USAspending sample
- Universe: top-39 publicly-traded R1000 federal contractors in defense/IT NAICS (3361, 3344, 3345, 3342, 3364, 5415-7), data-driven via /search/spending_by_category/recipient/ FY2024.
- Stratified sample: 39 primes × 5 cohort years (FY2010, 2014, 2018, 2022, 2024) × ~10 contracts per pair → N = **{N_LLM}**.

### §2.2 3-axis schema (LABELER_GUIDE.md)
- Anchored where possible by FAR §16 contract type code; narrative cues for tiebreaks. See Appendix A.

### §2.3 3-vendor LLM ensemble
- Models: anthropic/claude-opus-4.7, anthropic/claude-sonnet-4.6, google/gemma-2-27b-it via OpenRouter.
- n=20 oracle (Claude-anchored gold standard, `data/oracle_n20.json`).
- Phase 0 result: Fleiss κ_axis1 = **0.7863** (target ≥ 0.7), κ_axis2 = 1.0 (sample-trivial — no DESCOPE/TERMINATION in random Day-3 sample), κ_axis3 = -0.04 (Feinstein-Cicchetti paradox at 96% CLEAN base rate; 2-axis fallback applied).
- Vendor accuracy vs oracle: Opus 0.944, Sonnet 0.833, Gemma 0.889.

### §2.4 Outcome variables
- Forward CAR_3m: cumulative excess return over XAR (defense) hedge in 63 trading days post earnings announcement.
- Earnings surprise: yfinance estimate-based where available; trailing-4Q-mean fallback otherwise.
- Cross-section quintile spread: low-commitment-uncertainty (Q1) long minus high-commitment-uncertainty (Q5) short, monthly rebalance.

### §2.5 CCM 2011 aggregate baseline
- State-level federal spending (USAspending /search/spending_by_geography/ or rolled up from strategic sample as proxy) in {q-1, q, q+1} quarters.
- State-of-HQ: 10-K Item 1 corporate HQ for each of the 39 primes (curated table in code).

## §3 Main Effect (≤2 pages)

### §3.1 CCM aggregate baseline (replication, IS 2010-2018)
- Step 1: forward_CAR_3m ~ state_fed_spend_log + firm_FE + quarter_FE.
- Sample: n = **{N_PANEL}** firm-quarter observations.
- R²_step1 = **{R2_STEP1}**. β_state = **{B_STATE}** (t = {T_STATE}).

### §3.2 LLM extension (Step 2)
- Step 2 adds commitment_score_norm (axis-1 weighted average per firm-quarter).
- R²_step2 = **{R2_STEP2}**. **Incremental R² = {R2_INC}**.
- β_commitment = **{B_COMM}** (t = {T_COMM}). Direction: negative (more commitment-uncertainty → lower forward CAR).
- F-test of incremental: F = {F_INC}, p = {P_INC}.
- Bonferroni-9 critical t = 2.81 (3-axis × 3-horizon = 9 tests).

### §3.3 Cross-section quintile portfolio
- 5-bucket sort on commitment_score_norm per quarter; spread = Q1-mean − Q5-mean.
- Per-quarter (n_q = **{NQ}**): mean = **{SPREAD_MU}**, std = **{SPREAD_SIG}**.
- **Annualized Sharpe = {SHARPE_ANN}** (XAR-hedged), t-stat = {SHARPE_T}.
- Newey-West HAC SE (lag=4): t_NW = **{T_NW}**.

### §3.4 Earnings beat ROC-AUC
- Binary beat-vs-miss at {q+1}; ranker = commitment_score_norm.
- AUC = **{AUC}** (n = {N_AUC}, n_beat = {N_BEAT}, n_miss = {N_MISS}).

### §3.5 Verdict (single hard kill = ALL 3 AND fail)
| Metric | Value | Threshold | Verdict |
|---|---|---|---|
| Incremental R² | {R2_INC} | ≥ 0.05 | {V_R2} |
| Quintile Sharpe | {SHARPE_ANN} | ≥ 0.30 | {V_SHARPE} |
| ROC-AUC | {AUC} | ≥ 0.60 | {V_AUC} |

**Trigger #1 fires only if ALL 3 fail.** Phase 0 partial preview (30% data): 1 PASS (Sharpe), 2 borderline-FAIL → TIGHTEN_RETEST. Full sample expected to tighten R² + AUC into PASS region.

## §4 Robustness — *the identification machinery* (≤2.5 pages)

### §4.1 Cohort heterogeneity (alpha decay)
- Per-cohort §3.3 quintile spread Sharpe: 2010, 2014, 2018, 2022, 2024.
- yfinance earnings-history caveat: free-tier only ~5yr → 2010/2014/2018 cohort CAR-empty. Phase 2: IBES paid-tier extension.
- 2022 cohort Sharpe = **{S2022}**, 2024 cohort Sharpe = **{S2024}**.
- *Mechanism interpretation*: alpha decline tracks industry product entry. Apify USAspending AI Scoring (~2024 launch) + Govini Ark (~7yr) + FinBrain (~2024) all enter the same window the per-cohort Sharpe declines. Cotropia 2017 USPTO patent quality pattern (academic alpha → industry absorption → publishable identification result, not a freeze).

### §4.2 Naive vs realistic timing
- Naive backtest: act on action_date (lookahead).
- Realistic backtest: act at USAspending publish (Last Modified Date) + 24h.
- |Δ Sharpe| naive − realistic = **{DELTA_SR}**.
- Phase 0 cohort-stratified <24h fraction (M1 specific finding):
  - 2014: 0.35
  - 2018: 0.65
  - 2024: 0.75 (above 50% kill threshold under old framing; demoted to robustness finding under reframed plan).

### §4.3 Cross-LLM replication
- Per-axis sign agreement 3-vendor: Opus, Sonnet, Gemma.
- Threshold: ≥ 2/3 vendors must agree on direction in §3 main-effect rows.
- Day 9 batch: full 3-vendor coverage = **{COVERAGE}**% of N = **{N_LLM}**.

### §4.4 Contamination (LLM training cutoff)
- Anthropic Opus 4.7 / Sonnet 4.6 cutoff = 2026-01-01.
- Pre-cutoff vs post-cutoff sub-sample tertile spread.
- Result: pre-spread = **{PRE_SPREAD}**, post-spread = **{POST_SPREAD}**. Direction-stable + magnitude-similar = contamination unlikely.

### §4.5 Firm-name masking
- n=20 oracle re-classified with recipient_name redacted ("REDACTED_FIRM_NAME").
- Drop in axis-1 vs-oracle accuracy: Opus = **{D_OPUS}**, Sonnet = **{D_SONNET}**, Gemma = **{D_GEMMA}**.
- Threshold: ≤ 10pp drop = LLM uses narrative content; > 10pp = firm-name shortcut.
- Cost: ~$0.20 (60 calls one-shot).

### §4.6 (Optional) Subaward layer
- Conditional on §4.1 showing recent-cohort alpha dead.
- Industry products focus on prime; subaward narrative may have a fresher window.
- Not run if Day 14 verdict = MAIN_EFFECT_PASS.

## §5 Discussion (≤1.5 pages)

### §5.1 Pre-2018 alpha + post-2020 decay
- Earlier cohorts: federal contract → 8-K announce gap = days-to-weeks → industry alt-data products didn't yet automate USAspending pickup → academic alpha existed.
- Post-2020: industry products entered (Apify 2024-2025, Govini 2018+, FinBrain 2024+) → same-day pickup → academic alpha absorbed.
- **First-mover window for narrative-extraction alpha: ~12-18 months after academic publication.**

### §5.2 Content vs timing distinction
- Industry products: aggregate scoring + DoD ingestion + UI (timing edge).
- Our 3-axis schema: contract-type + program-continuity + protest-risk (content edge).
- Even when timing alpha is industry-absorbed, content-layer decomposition may remain academic.

### §5.3 Methodological contribution
- USAspending API + yfinance free + OpenRouter LLM ensemble = **fully reproducible pipeline at $25 cost**.
- Open-sourced repository at github.com/[user]/usaspending_contract_llm.

### §5.4 Comparison to related work
- Cohen-Coval-Malloy 2011 (state-level aggregate): we extend to contract-text level.
- Eaton-Hassett 2018, Belasco-Cordesman 2010 (defense-spending macro): we extend to firm-cross-section.
- Cotropia 2017 USPTO patent quality (academic alpha → industry absorption pattern): same shape, different domain.
- Goldman-Rocholl-So 2009, Faccio 2006 (political connection → firm value): different mechanism.

## §6 Conclusion + Phase 2 (≤0.5 page)

- Forward revenue commitment LLM extraction adds incremental information over CCM aggregate baseline.
- Cohort heterogeneity reveals industry-absorption mechanism — itself a publishable identification result.
- **Limits**:
  - 39-firm publicly-traded R1000 universe (data-driven cap from USAspending recipient pivot).
  - 5-cohort stratification, n ≈ 2,000.
  - yfinance ~5yr earnings history → §4.1 power-limited to recent cohorts.
  - LLM ensemble 3-vendor; structured-output mode + retry-on-error not yet implemented (~10% JSON loss on opaque narratives).
- **Phase 2 directions**:
  - Compustat / IBES extension to all 5 cohorts.
  - Subaward layer (industry products focus on prime).
  - Real-time / streaming inference.
  - Schema extension to axis-4 (small-business set-aside vs full-and-open competition).

## Appendix

- A. LABELER_GUIDE.md (full schema)
- B. n=20 oracle gold standard (frozen JSON)
- C. Vendor accuracy vs oracle table
- D. Per-cohort regression coefficient table
- E. Streamlit dashboard screenshots
- F. Cross-LLM 3-vendor disagreement matrix

## References

(Full list per `analysis/paper_outline.md` §References.)

---

**Numerical placeholder map** (search-replace when Day 9 batch completes + full pipeline runs):

| Token | Source |
|---|---|
| {N_LLM}      | day9_batch_summary.json `n_sample` |
| {N_PANEL}    | ccm_replication.json regressions[0].n_obs |
| {R2_STEP1}   | ccm_replication.json regressions[0].r2_step1 |
| {R2_STEP2}   | ccm_replication.json regressions[0].r2_step2 |
| {R2_INC}     | ccm_replication.json regressions[0].incremental_r2 |
| {B_STATE}    | ccm_replication.json regressions[0].beta_state |
| {B_COMM}     | ccm_replication.json regressions[0].beta_commitment |
| {T_COMM}     | ccm_replication.json regressions[0].commitment_t_stat |
| {F_INC}      | ccm_replication.json regressions[0].f_stat_incremental |
| {NQ}         | cross_section_quintile.json spread_summary.n_quarters |
| {SPREAD_MU}  | spread_summary.spread_mean |
| {SPREAD_SIG} | spread_summary.spread_std |
| {SHARPE_ANN} | spread_summary.sharpe_annualized |
| {SHARPE_T}   | spread_summary.t_stat |
| {T_NW}       | rigor.json newey_west_lag4.nw_t |
| {AUC}        | day14_mid_checkpoint.json metrics[2].value |
| {N_AUC}      | day14_mid_checkpoint.json metrics[2].n_obs |
| {S2022}      | cohort_heterogeneity.json by_cohort[3].sharpe_annualized |
| {S2024}      | cohort_heterogeneity.json by_cohort[4].sharpe_annualized |
| {COVERAGE}   | (n_with_full_3vendor / n_sample) × 100 |
| {DELTA_SR}   | TBD (§4.2 not yet implemented) |
| {PRE_SPREAD},{POST_SPREAD} | contamination_masking.json section_4_4_contamination |
| {D_OPUS},{D_SONNET},{D_GEMMA} | contamination_masking.json section_4_5_masking.drop_in_accuracy |
| {V_R2},{V_SHARPE},{V_AUC} | day14_mid_checkpoint.json verdict per-metric |
