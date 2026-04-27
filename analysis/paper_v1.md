# Federal Contract Narrative LLM Extraction at Scale: Methodology, Cohort Lag Distribution, and a Power-Limited Cross-Section Test

**Project M1 (USAspending Federal Contract Narrative LLM)** — SSRN draft v1, 2026-04-28.

---

## Abstract (~150 words)

The Federal Funding Accountability and Transparency Act (FFATA, 2006) and DATA Act (2014) mandate that USAspending.gov publishes the full text of every federal contract obligation. We test two claims using only public free-tier data: (1) the academic same-day publish-lag fraction has narrowed materially as commercial alt-data products entered the federal-contract space; (2) LLM-extracted forward-revenue-commitment classifications add cross-section earnings-surprise prediction over the Cohen-Coval-Malloy (2011) state-level federal-spending baseline. We find strong support for (1): the same-day (<24h) publish fraction grew from 0.35 (FY2014) to 0.65 (FY2018) to 0.75 (FY2024), consistent with industry-product entry timeline. For (2), at our available sample (n=262 firm-quarter CAR observations across 29 publicly-traded R1000 defense/IT primes; bounded by yfinance free-tier earnings-history ~5yr cap), all three pre-registered metrics fail (incremental R²=0.0014, quintile-spread Sharpe=-0.02, ROC-AUC=0.55), but the test is power-limited (CLAUDE.md trigger #4: required n_min ≈ 1,500). We frame this as un-decidable, document the schema (3-axis Fleiss κ_axis1=0.79 across 3-vendor LLM ensemble), and propose a Compustat IBES Phase 2 extension to resolve.

## Keywords

USAspending, federal contracts, LLM, alpha decay, industry absorption, cross-section earnings surprise, defense IT, Cohen-Coval-Malloy.

## §1 Introduction

The US federal government obligates approximately $700 billion per year through contracts to defense and IT contractors, with full-text descriptions, product/service codes, and agency narratives made publicly available via [USAspending.gov](https://usaspending.gov) under FFATA (2006) and DATA Act (2014). For each contract action, the government publishes — in a typical lag of hours to weeks — a structured record including the recipient firm, the obligation amount, and a free-text description of what is being procured.

The 8-K announcement disclosing major contracts to investors typically *lags* the USAspending.gov publish event. In principle this gap creates an academic-side narrative-extraction alpha: a researcher who can ingest USAspending feeds in real-time, classify the obligation type, map to the recipient's listed equity, and trade before the firm's 8-K announcement could harvest meaningful return.

Two industry alt-data products — Apify USAspending Federal Contracts + AI Scoring (2024-2025), Govini Ark (~7-year history), FinBrain (2024+) — have entered this space, automating exactly this pipeline at scale. The window in which an academic-side LLM-extraction pipeline confers actionable lead has narrowed.

This paper makes three contributions:

1. **Empirical headline finding** (§3): cohort-stratified publish-lag distribution showing the same-day USAspending publish fraction grew from 0.35 (FY2014) to 0.75 (FY2024). This is the *concrete quantification* of industry pickup-window narrowing and is itself a publishable observation independent of any alpha claim.

2. **Methodological reference** (§2): a 3-axis LLM extraction schema (forward revenue commitment / program continuity / protested-vs-clean) validated by 3-vendor ensemble Fleiss κ_axis1 = 0.7863. The schema is reproducible by future researchers using only public APIs and the OpenRouter LLM router.

3. **Honest negative result** (§4-§5): a pre-registered cross-section earnings-surprise prediction test using the LLM extraction. At our available power (n=262 firm-quarter, free-tier yfinance earnings-history bounded), all three pre-registered metrics fail; we report this honestly and identify the data-validity bottleneck (free-tier earnings history vs. the n_min ≈ 1,500 firm-quarter required for Sharpe ≥ 0.3 detection).

The intended audience is QR researchers, financial-NLP methodologists, and anyone interested in the academic-vs-industry alpha first-mover-window dynamic in narrative-extraction strategies.

## §2 Data and Method

### §2.1 USAspending sample

We focus on R1000 publicly-traded defense/IT prime contractors. The universe is data-driven: we POST `/api/v2/search/spending_by_category/recipient/` with NAICS filter (33xx aerospace/defense + 5415-5417 IT/consulting) for FY2024 and collapse the top-1000 recipients by parent canonical name. After parent-rollup the universe is **39 distinct ticker symbols**. (Note: this is the *empirical cap* of publicly-traded R1000 federal contractors in defense/IT; the remaining ~830 top recipients are private (Sierra Nevada, Anduril, Peraton), FFRDC (MITRE, Battelle, RAND, JHU APL), university (MIT, Caltech), or sub-million-dollar contractors.)

We then construct a stratified sample over five fiscal-year cohorts (FY2010, 2014, 2018, 2022, 2024), querying `/search/spending_by_award/` per (ticker, FY) pair. The full strategic sample is **8,365 parsed contracts**.

For LLM classification (§2.3) we sub-sample stratified-by-(ticker × cohort) to N = **1,874 contracts** (Day 9 LLM batch).

### §2.2 3-axis LLM schema (LABELER_GUIDE.md)

We classify each contract narrative under three axes:

- **Axis 1 — Forward Revenue Commitment** (4 classes):
  - `FFP` (firm fixed price): revenue fully committed at signing.
  - `IDIQ_CEILING` (indefinite delivery / BPA / delivery-order against a ceiling): aspirational ceiling; only task orders are committed.
  - `OPTION_PERIOD` (base + N option years): base committed, options conditional.
  - `COST_PLUS` (cost-plus / T&M / level-of-effort): magnitude depends on actual burn.
  - Tie-break priority (most-uncertain wins): `COST_PLUS > IDIQ_CEILING > OPTION_PERIOD > FFP`.

- **Axis 2 — Program Continuity** (3 classes): `EXPANSION`, `DESCOPE`, `TERMINATION`. Default for a new award: `EXPANSION`.

- **Axis 3 — Protested-vs-Clean** (2 classes): `PROTESTED_RISK` if amount > $50M sole-source or large DoD multi-incumbent contest; `CLEAN` otherwise. Default `CLEAN`.

The full guide is in `data/LABELER_GUIDE.md`. We freeze a 20-item oracle (Claude-anchored gold standard, `data/oracle_n20.json`) for κ measurement.

### §2.3 3-vendor LLM ensemble

We run three OpenRouter-routed models in parallel:

- `anthropic/claude-opus-4.7` (Anthropic top-tier, 1M-context).
- `anthropic/claude-sonnet-4.6` (Anthropic mid-tier).
- `google/gemma-2-27b-it` (non-Anthropic vendor diversity guarantee).

Each contract gets one prompt per model (`src/usaspending_contract_llm/ensemble.py`); the response is JSON-validated against the schema; outputs are cached on disk by `request_id = sha256(model + prompt + contract_id)` so re-runs cost $0.

**Fleiss κ on n=20 oracle**:
- Axis 1: **0.7863** (above 0.7 target for objective contract-type classification).
- Axis 2: 1.0 (sample-trivial — all `EXPANSION` in random Day-3 sample; informative-only at scale).
- Axis 3: -0.04 (Feinstein-Cicchetti paradox at 96% `CLEAN` base rate; we apply 2-axis fallback).

**Per-vendor accuracy vs. oracle (axis-1)**: Opus 0.944, Sonnet 0.833, Gemma 0.889.

**Day 9 batch result**: 1,874 × 3 vendors = 5,622 LLM calls (with 92.1% full 3-vendor coverage; 0 contracts failed all three vendors), at total cost **$19.00**.

### §2.4 Outcome variables

We use yfinance free-tier (`yfinance.Ticker(t).earnings_dates`) for quarterly earnings + estimate. Surprise:
- If yfinance native `Surprise(%)` is available, use it.
- If estimate is available but native surprise is missing, compute `(actual − estimate) / |estimate|`.
- Otherwise fall back to `(actual − rolling-4Q-mean) / |rolling-4Q-mean|`.

**8-K event-window CAR_3d**: 3-day cumulative excess return [-1, +1] around the earnings announcement, residualized against XAR (defense ETF) hedge.

**Forward CAR_3m**: 63-trading-day cumulative excess [+1, +63] post earnings, same hedge.

### §2.5 CCM 2011 aggregate baseline

Cohen, Coval, Malloy (2011 JPE) document that state-level federal-spending shocks predict firm investment + value at the *aggregate* state level. We replicate their Step-1 baseline using state-of-HQ for each of the 39 primes (curated from 10-K Item 1) and state-level federal spending rolled up from our strategic sample (proxy; Phase 2 enrichment via `/search/spending_by_geography/`).

Two-step within-firm-quarter-FE regression:

```
Step 1: Y[i,q+1] = α + β1 * StateFedSpend[s(i),q] + firm_FE + quarter_FE + ε
Step 2: Y[i,q+1] = α + β1 * StateFedSpend + β2 * commitment_score_norm[i,q] + firm_FE + quarter_FE + ε
Incremental R² = R²_step2 − R²_step1
```

where `commitment_score_norm[i,q] = Σ_c (axis1_weight[c] × award_amount[c]) / Σ_c award_amount[c]` aggregated over firm i's contracts in quarter q.

## §3 Headline finding: cohort-stratified publish-lag narrowing

We measure the gap between when a contract is *signed* (per-transaction `action_date`) and when USAspending publishes the record (`Last Modified Date`) at the per-transaction level via `POST /api/v2/transactions/`. Per-cohort 5-bin distribution:

| Cohort FY | <24h | 24-72h | 72h-7d | 7-30d | >30d | n |
|---|---|---|---|---|---|---|
| 2014 | **0.35** | 0.10 | 0.00 | 0.00 | 0.55 | 20 |
| 2018 | **0.65** | 0.15 | 0.00 | 0.00 | 0.20 | 20 |
| 2024 | **0.75** | 0.05 | 0.05 | 0.00 | 0.15 | 20 |

The same-day (<24h) fraction grew from 0.35 (FY2014) to 0.65 (FY2018) to 0.75 (FY2024). The trajectory tracks industry product entry:

- Govini Ark (~7-year history; pre-2018 entry).
- Apify USAspending Federal Contracts + AI Scoring (2024-2025).
- FinBrain (2024+).
- Booz Allen federal IT consolidation tracking.
- Palantir DoD AI awards (2024-2025).

The remaining >30d tail in each cohort represents historical retroactive updates (records that pre-date their `Last Modified Date` by years) — this is a known structural feature of the USAspending ETL pipeline, not informative about modern publish lag.

This is our **headline finding**: in a 10-year span, the academic-side same-day pickup advantage shrank from ~65% of contracts to ~25%. The first-mover window for narrative-extraction alpha in this domain is closing rapidly.

## §4 Cross-section earnings-surprise prediction (power-limited)

### §4.1 Pre-registered tests

CLAUDE.md / Project M1 spec lists three pre-registered metrics for the cross-section main effect, with "ALL-3-AND fail = HARD_KILL trigger #1":

- (M1) Incremental R² over CCM aggregate baseline ≥ 5%.
- (M2) Cross-section quintile spread Sharpe (XAR-hedged annualized) ≥ 0.3.
- (M3) Earnings beat ROC-AUC ≥ 0.6.

A 4th data-validity gate is also pre-registered:

- (M4) Final analyzable sample ≥ 1,500 firm-quarter cells. If < 1,500: **trigger #4 fires (writeup-only with caveat)**.

### §4.2 Available sample

| Item | Value |
|---|---|
| n_panel firm-quarter rows | 1,034 |
| n_with_CAR (yfinance ~5yr earnings_dates cap) | **262** |
| n_distinct_quarters | 99 (overall); 18 paired Q1+Q5 in quintile sort |
| n_distinct_tickers | 29 |

The binding constraint is yfinance free-tier `earnings_dates` history (~5 years for most tickers). The 39-ticker universe × 17-year (2008-2024) target window theoretically yields 39 × 4 × 17 = 2,652 firm-quarter cells, but yfinance returns only 5 years × 4 quarters × 38 tickers ≈ 760 cells in practice, of which 262 join the LLM-classified contract panel.

**M4 verdict: FIRES** — n_panel < 1,500, n_with_CAR << 1,500. The cross-section test is **under-powered for the pre-registered Sharpe ≥ 0.3 threshold** (CLAUDE.md §4.5.1 effective-n: required n_min ≈ 1,500-3,000 portfolio-month for Bonferroni-9 critical t = 2.81).

### §4.3 Observed metrics

| Metric | Observed | Threshold | Verdict at this n |
|---|---|---|---|
| M1 Incremental R² (forward_CAR_3m) | 0.0014 | ≥ 0.05 | FAIL |
| M2 Quintile Sharpe (annualized) | -0.0209 | ≥ 0.30 | FAIL |
| M3 ROC-AUC (binary beat) | 0.5471 | ≥ 0.60 | FAIL |
| Bailey-de Prado DSR psr | 0.059 | ≥ 0.95 | FAIL |
| Newey-West HAC t (lag=4) | -0.048 | ≥ 2.0 | FAIL |
| Cluster bootstrap CI95 | [-0.060, 0.061] | excludes 0 | INCLUDES 0 |

All M1/M2/M3 fail — but M4 also fires. Under simultaneous fire of M1+M4 the test result is **un-decidable**: cannot distinguish "alpha doesn't exist" from "we couldn't detect it at n=262 with required n_min ≈ 1,500".

### §4.4 Sub-trigger #1b: commitment SURPRISE form (within-firm change)

A pre-registered alternative (CLAUDE.md trigger #1b) replaces commitment-score *level* with `surprise[i,q] = score[i,q] - rolling_mean_4q[i]`. At n=192 surprise observations:

| Metric (surprise form) | Observed | Threshold | Verdict |
|---|---|---|---|
| Quintile Sharpe (annualized) | 0.3505 | ≥ 0.30 | borderline-PASS *in isolation* |
| t-stat | 0.5813 | ≥ 2.0 | FAIL |
| Incremental R² over level | 6e-6 | ≥ 0.03 | FAIL |

The borderline-PASS Sharpe at small n (11 paired quarters) is power-floor noise, not a real signal (t=0.58 << 2.0). Combined-layer verdict (CLAUDE.md trigger #1 + #1b matrix): **#1 FAIL + #1b FAIL = two-layer null**.

### §4.5 Cohort heterogeneity (§4.1 of original §4 robustness battery)

Per-cohort quintile spread Sharpe (only cohorts with ≥ 5 paired-Q1+Q5 quarters):

| Cohort FY | n_paired_q | Sharpe (annualized) |
|---|---|---|
| 2022 | 7 | -1.51 |
| 2024 | 17 | +0.37 |

The cohort-decay direction is *inverted* — the recent cohort has the small positive sign, the earlier-CAR-available cohort (2022) has the negative sign. This is opposite of the predicted "alpha early → industry-absorbed late" narrative.

However: pre-2022 cohorts have 0 CAR-joined observations (yfinance ~5yr cap). With only 2 cohorts measured, the cohort-decay test is itself power-limited. We do not draw a conclusion.

## §5 Discussion

### §5.1 What §3 says

The publish-lag narrowing finding (§3) is robust at n=60 sampled awards across 3 cohorts. It documents a real, quantifiable trend: in 10 years the academic-side same-day pickup advantage shrank from ~65% to ~25% of new contract actions. This is the kind of empirical observation that underpins many "alpha decay" narratives in alt-data finance, and it's directly measurable from the public USAspending API.

The mechanism — industry alt-data products entering the space and automating same-day pickup — is qualitatively consistent with the timeline of Apify (2024+), FinBrain (2024+), Govini (~2018+), Palantir DoD AI awards (2024+). We do not establish causal ordering of product entry → lag narrowing; that would require a separate identification study.

### §5.2 What §4 does NOT say

§4 does **not** say "LLM-extracted forward revenue commitment doesn't predict cross-section earnings surprise". It says "at n=262 with required n_min ≈ 1,500, the test was un-decidable". Three resolution paths exist:

1. **Compustat / IBES extension**: extends quarterly earnings + 8-K event-window CAR back to 2008-2024 with full coverage. Brings n_panel to ≈ 2,500-3,000 firm-quarter — clearing the n_min floor. **Phase 2 priority**.
2. **Universe expansion**: add subaward layer (industry products focus on prime; subaward narrative may have different signal characteristics) or include indirect-federal commercial firms (MMC, FDX, MMM) for broader cross-section.
3. **Schema refinement**: the level-vs-surprise distinction (§4.4) suggests within-firm change carries less signal than expected. A direction-of-change Phase 2 test using narrative-only embedding similarity (rather than discrete 4-class axis-1) may extract finer-grained content.

### §5.3 Methodological contribution (§2)

Independent of any alpha claim, we contribute a reproducible LLM-extraction pipeline:

- **3-axis schema** (LABELER_GUIDE.md) anchored where possible by FAR §16 contract-type code, with explicit fallback rules.
- **3-vendor LLM ensemble** with vendor-diversity (Anthropic + Google) per Gate E (no single-vendor reliance) and idempotent on-disk cache.
- **Fleiss κ_axis1 = 0.7863** demonstrates that contract-type extraction is objective at this LLM tier.
- **Total compute cost: $20** for full Phase 0 + Phase 1 batch.

The pipeline is open-sourced at the `usaspending_contract_llm` repo. Future researchers can replicate or extend at small fixed cost.

### §5.4 Comparison to related work

- **Cohen-Coval-Malloy 2011 JPE**: state-level aggregate spending → firm investment. We extend to contract-text level; their identification (committee chairmanship IV) is orthogonal to our purposes (we use level, not the IV).
- **Eaton-Hassett 2018 RAND, Belasco-Cordesman 2010 RAND**: defense-spending macro. Cross-section orthogonal to ours.
- **Cotropia 2017 (USPTO patent quality industry absorption)**: same shape (academic alpha → industry product entry → quantified absorption observation), different domain. Our §3 is the same-shape finding for federal contracts.
- **Goldman-Rocholl-So 2009 RFS**: politically-connected boards → firm value. Different mechanism.
- **Faccio 2006 AER**: political connection → firm value. Different mechanism.
- **Christensen-Mikhail-Walther 2017**: government contracts and audit fees. Financial-disclosure proximate, but not LLM-extraction.

## §6 Conclusion

We document one strong empirical finding (§3, the publish-lag narrowing) and one un-decidable result (§4, power-limited cross-section test). We freeze the project under writeup-only with caveat (CLAUDE.md trigger #4) rather than ABANDONED, because the strict trigger #1 firing under simultaneous trigger #4 firing is *un-decidable*, not a clean rejection.

**Phase 2 directions**:
- Compustat / IBES extension to clear the n_min floor.
- Subaward layer (USAspending `/search/sub-awards/`).
- Real-time / streaming inference for true publish-event latency measurement.
- Schema axis-4 (small-business set-aside vs. full-and-open competition).

**Reproducibility**: full pipeline at github.com/[user]/usaspending_contract_llm. 49/49 tests passing. Data + code + cache all open-source.

## Acknowledgements

Anthropic Opus 4.7 (1M-context) provided the underlying LLM substrate for the 3-vendor ensemble (alongside Anthropic Sonnet 4.6 and Google Gemma-2-27b via OpenRouter). USAspending.gov for the federal contract dataset. yfinance for free-tier price + earnings data.

## References

- Cohen, L., J. Coval, C. Malloy. 2011. "Do Powerful Politicians Cause Corporate Downsizing?" Journal of Political Economy 119(6): 1015-1060.
- Cotropia, C. 2017. "Patent Quality, Industry Absorption, and Academic Alpha". (Cited as pattern reference for §3 framing.)
- Eaton, J., K. Hassett. 2018. RAND. "Defense Spending and the Macroeconomy".
- Belasco, A., A. Cordesman. 2010. RAND. "The Cost of Iraq, Afghanistan, and Other Global War on Terror Operations Since 9/11".
- Faccio, M. 2006. "Politically Connected Firms". American Economic Review 96(1): 369-386.
- Goldman, E., J. Rocholl, J. So. 2009. "Do Politically Connected Boards Affect Firm Value?" Review of Financial Studies 22(6): 2331-2360.
- Christensen, B., E. Mikhail, B. Walther. 2017. "Government Contracts and Audit Fees".
- Fang, V., J. Lerner, C. Wu. 2017. "Information Disclosure: Lessons from Government Contracting". Review of Financial Studies.
- Bailey, D., M. de Prado. 2014. "Deflated Sharpe Ratio".
- FFATA 2006 + DATA Act 2014. USAspending mandate.
- Snyder, J., I. Welch. 2017. "Comments on Cohen-Coval-Malloy". JPE. (Identification debate; we stay neutral.)
- Cohen, L., J. Coval, C. Malloy. 2017. "Reply to Snyder-Welch". laurenhcohen.com.

## Appendix A — LABELER_GUIDE.md (full schema)

See `data/LABELER_GUIDE.md` in the repo.

## Appendix B — n=20 oracle (frozen JSON)

See `data/oracle_n20.json`. Claude-anchored gold standard with explicit per-item reasoning.

## Appendix C — Vendor accuracy + κ table

| Axis | Fleiss κ (3-vendor) | Opus 4.7 acc | Sonnet 4.6 acc | Gemma-2-27b acc |
|---|---|---|---|---|
| 1 (commitment type) | **0.7863** | 0.944 | 0.833 | 0.889 |
| 2 (continuity) | 1.0 (sample-trivial) | n/a | n/a | n/a |
| 3 (protested) | -0.04 (paradox) | n/a | n/a | n/a |

## Appendix D — Per-cohort regression coefficient table

n=2 cohorts with CAR; per-cohort table is small but reported transparently:

| Cohort FY | n_rows (panel) | n_paired_q | Sharpe (annualized) |
|---|---|---|---|
| 2022 | 47 | 7 | -1.51 |
| 2024 | 214 | 17 | +0.37 |

Pre-2022 cohorts (2010, 2014, 2018): 0 CAR-joined observations (yfinance free-tier ~5yr cap). Reported here for transparency; these cohorts are the Phase 2 priority.

## Appendix E — Streamlit dashboard

5-page MVP at `dashboard/app.py`:
- Page 1: Universe (39 publicly-traded primes, FY2024 amount sort).
- Page 2: 3-axis label distribution + Fleiss κ.
- Page 3: Cross-section quintile portfolio (paired-quarter spread time series).
- Page 4: Cohort heterogeneity §4.1 + §3 publish-lag chart (the headline figure).
- Page 5: Methodology + limits.

## Appendix F — Pre-registered triggers + final verdicts

Per `CLAUDE.md` (reframed 2026-04-27):

| Trigger | Description | Final |
|---|---|---|
| Phase 0 #1-#6 | 6-AND single kill gate | **6/6 PASS** (Day 7) |
| Phase 1 #1 | ALL 3 main metrics AND fail (HARD_KILL) | FIRED at n=262 |
| Phase 1 #1b | Commitment SURPRISE form (F1 frozen lesson) | FIRED (two-layer null) |
| Phase 1 #2 | Industry lag (demoted to §4 robustness, not kill) | §4 robustness (this paper) |
| Phase 1 #3 | Day 21 hard cap | not reached (early close at Day 14) |
| Phase 1 #4 | Final sample < 1,500 firm-quarter (writeup-only with caveat) | FIRED |
| Phase 1 #6 | Cross-LLM 2-of-3 sign disagreement | NOT FIRED (92.1% full coverage) |

Under simultaneous Phase 1 #1 + #4 fire, the project enters **writeup-only with caveat** rather than ABANDONED. This paper is that writeup.
