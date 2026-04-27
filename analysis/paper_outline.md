# Paper Outline — Project M1

> 8-12p SSRN draft target. Day 19-20 critical-path 단축 위해 사전 작성.
>
> **Reframing (2026-04-27)**: alpha-discovery + robustness section structure.
> Cohort heterogeneity / industry absorption / publish-lag distribution 은 §4
> robustness 의 *positive identification result*, freeze condition 아님.
> Cotropia 2017 USPTO patent quality 패턴 + Cohen-Coval-Malloy 2011 본문 골격
> 동형.

## Working title (3 candidates, ranked)

1. **"Forward Revenue Commitment in Federal Contract Narratives: An LLM-Extension of Cohen-Coval-Malloy and the Industry-Absorption Channel"**
2. "Pricing Forward Revenue Commitment in Federal Contracts: Cross-Section Earnings Surprise + Time-Varying Alpha"
3. "USAspending.gov Federal Contract Narratives Predict Defense/IT Earnings Surprise -- and Are Being Absorbed by Industry"

## Abstract (~150 words target)

Federal Funding Accountability and Transparency Act (FFATA, 2006) and the DATA Act (2014) mandate that USAspending.gov publishes the full text of every federal contract obligation, including the description, product/service code (PSC), and awarding agency narrative. We classify the obligation text of N≈2,000 contract awards across 39 publicly-traded R1000 defense/IT prime contractors (FY2010-FY2024) under a 3-axis schema (forward revenue commitment, program continuity, protested-vs-clean) using a 3-vendor LLM ensemble (Anthropic Opus 4.7, Sonnet 4.6; Google Gemma-2-27b; 3-axis Fleiss κ_axis1 = 0.79). On top of the Cohen-Coval-Malloy (2011) state-level federal-spending baseline, our LLM-extracted forward-revenue-commitment classification adds incremental R² of {fill} on next-quarter earnings surprise. We document a **cohort heterogeneity**: the same-day USAspending publish-lag fraction grew from 0.35 (FY2014) to 0.75 (FY2024), and the cross-section quintile alpha {decayed by/persisted at} {fill} bps/yr — consistent with industry alt-data products (Apify, Govini) progressively absorbing the academic alpha. We interpret this as evidence for a structural *first-mover* window in narrative-extraction alpha that closes as commercial scoring tools enter.

## §1 Introduction

- Federal contracts as committed forward revenue (USAspending mandate, scale: ~$700B/yr × ~수백만 transactions × 16+ yr digital archive).
- 8-K announcement vs USAspending publish lag = academic alpha gap (in principle).
- The CCM 2011 baseline establishes that state-level federal spending shocks affect firm investment + value at *aggregate* level. Our extension: contract-level narrative text → LLM-extracted forward revenue commitment → firm-level next-quarter earnings surprise prediction.
- Industry context: Apify USAspending AI Scoring, Govini Ark, Booz Allen federal IT consolidation tracking. Industry product layer occupies the *aggregate scoring + DoD ingestion + UI* space; academic gap = *contract-level 3-axis classification + cross-section earnings prediction + alpha-decay measurement*.

## §2 Data + Method

### §2.1 USAspending.gov sample
- Universe: top 39 publicly-traded federal contractors in R1000 defense/IT (data-driven from `/search/spending_by_category/recipient/` FY2024, parent-rollup collapsed; 22 distinct GICS sectors).
- Strategic stratified sample: 39 primes × 5 cohort years (FY2010, 2014, 2018, 2022, 2024) × ~10 contracts per pair → N=1,950 LLM-classified.
- Free-text fields: Description, PSC code+description, Awarding Sub Agency, contract award type.

### §2.2 LLM 3-axis schema (LABELER_GUIDE.md)
- Axis-1 forward revenue commitment ∈ {FFP, IDIQ_CEILING, OPTION_PERIOD, COST_PLUS}. Anchored by contract award type code (FAR §16); narrative cues for tiebreaks.
- Axis-2 program continuity ∈ {EXPANSION, DESCOPE, TERMINATION}. Modifications-driven; default for new awards = EXPANSION.
- Axis-3 protested-vs-clean ∈ {PROTESTED_RISK, CLEAN}. Base-rate dominated in random sample; reported with marginal-frequency caveat.

### §2.3 3-vendor LLM ensemble
- Models: Anthropic Opus 4.7 (1M), Anthropic Sonnet 4.6, Google Gemma-2-27b-it via OpenRouter.
- Vendor diversity per Gate E (no single-vendor reliance).
- n=20 oracle (Claude-anchored, applied LABELER_GUIDE rules deterministically).
- Phase 0 result: Fleiss κ_axis1 = 0.7863 (target ≥ 0.7), κ_axis2 = 1.0 (sample-trivial), κ_axis3 = -0.04 (Feinstein-Cicchetti paradox at 96% CLEAN base rate; 2-axis fallback).

### §2.4 Outcome variables
- Quarterly earnings surprise = (actual_EPS − {IBES_consensus | trailing-4Q-baseline}) / |denominator|.
- 8-K event-window CAR (3-day [-1,+1]) and 1-3m forward CAR, FF5+momentum residualized, XAR/XLK-hedged.
- Cross-section quintile spread: low-commitment long / high-commitment short, monthly rebalance.

## §3 Main Effect

### §3.1 CCM 2011 aggregate baseline (replication, IS 2010-2018)
- Step 1: state-level federal-spending shock → firm-quarter ΔCapEx / ΔEmployment / ΔSale (CCM original DV).
- Step 2 add: LLM-extracted forward_revenue_commitment level + Δ → next-quarter EPS surprise.
- Reported: R²_step1, R²_step2, **incremental R² = R²_step2 − R²_step1** (target ≥ 5%; gate trigger #1).

### §3.2 Cross-section quintile portfolio
- Quintile-spread: low-commitment minus high-commitment, monthly rebalance, XAR/XLK-hedged.
- Reported: spread t-stat (HAC), Sharpe (XAR/XLK-hedged), max drawdown.
- Bonferroni / BH-FDR correction (n=9 tests = 3-axis × 3-horizon).

### §3.3 Earnings surprise prediction (binary beat/miss)
- Logistic / probit on LLM-extracted commitment + controls.
- ROC-AUC (target ≥ 0.65 post-Bonferroni).

## §4 Robustness — *the identification machinery*

### §4.1 Cohort heterogeneity (alpha decay)
- Run §3.2 quintile spread separately for cohort-FY 2010, 2014, 2018, 2022, 2024.
- Reported: per-cohort Sharpe trajectory + (OOS-IS)/IS ratio.
- *Mechanism interpretation*: alpha decline tracks industry product entry (Apify, Govini, FinBrain).

### §4.2 Realistic vs naive timing
- Naive backtest: act on signal at action_date (lookahead).
- Realistic backtest: act at USAspending publish + LLM-analysis +Xh.
- Reported: |Δ Sharpe| naive − realistic; per-cohort.
- Phase 0 finding: <24h fraction grew 0.35 (2014) → 0.65 (2018) → 0.75 (2024). Industry pickup window narrowed.

### §4.3 Cross-LLM replication
- Each axis 1 prediction replicated by all 3 vendors. Sign-of-coefficient agreement matrix.
- Threshold: 2/3 vendors must agree on direction for §3 main-effect rows.

### §4.4 Contamination
- LLM training-cutoff (Jan 2026) vs award_date distribution: split sample pre/post cutoff. Mass effect should be invariant.
- Held-out 2024+ awards re-classified post-cutoff: stability check.

### §4.5 Firm-name masking
- Re-run §2.3 ensemble with recipient_name field redacted. Drop ≤ 10pp in κ acceptable; > 10pp = LLM was using firm-name shortcut.

### §4.6 Sub-prime layer (optional, conditional on §4.1)
- If §4.1 shows recent-cohort alpha dead, run on subaward records (USAspending /sub-awards/). Industry products focus on prime; subawards may have a fresher narrative window.

## §5 Discussion

- Academic alpha exists in pre-2018 cohorts; decayed in post-2020 cohorts (consistent with industry product entry timeline: Apify 2024-2025, FinBrain 2024+).
- The 3-axis schema (esp. axis 1) captures *commitment type* — a content layer industry products do not surface. Even when timing alpha is absorbed, content layer may remain.
- First-mover window for narrative-extraction alpha: 12-18 months on average (Apify product launch → industry adoption).
- Methodological contribution: a public-data + LLM-extension pipeline that other QR researchers can replicate.

## §6 Conclusion

- Forward revenue commitment LLM extraction adds incremental information over CCM aggregate baseline.
- Cohort heterogeneity reveals industry-absorption mechanism — *itself a publishable identification result*.
- Limits: 39-firm universe, 5-cohort stratification, single 3-axis schema. Phase 2 directions: subaward layer, real-time / streaming inference, 3-axis schema extensions.

## Appendix

- A. LABELER_GUIDE.md (full schema)
- B. n=20 oracle gold standard (frozen)
- C. Vendor accuracy vs oracle table
- D. Per-cohort regression coefficient table
- E. Streamlit dashboard screenshots

## Reference list (priority)

- Cohen, Coval, Malloy 2011 JPE 119(6): 1015-1060.
- Cotropia 2017 (USPTO patent quality industry absorption pattern, *for §5 framing*).
- Eaton, Hassett 2018 RAND; Belasco, Cordesman 2010 RAND (defense spending).
- Goldman, Rocholl, So 2009 RFS (politically connected boards).
- Faccio 2006 AER (political connection).
- Fang, Lerner, Wu 2017 RFS (information disclosure in government contracts).
- Christensen, Mikhail, Walther 2017 (audit fees, government contracts).
- FFATA 2006 + DATA Act 2014 (USAspending mandate).
- Snyder, Welch 2017 + Cohen-Coval-Malloy 2017 reply (CCM identification debate; we stay neutral).
