# Project M1 — USAspending Federal Contract Narrative LLM

USAspending.gov federal contract obligation text → 3-vendor LLM ensemble → 3-axis classification → defense/IT contractor cross-section next-quarter earnings surprise prediction.

**Methodology**: replication-grade pipeline using only USAspending API + yfinance free-tier + OpenRouter LLM ensemble at ~$25 total cost.

## Status (2026-04-28)

- **Phase 0**: 6/6 PASS at single 6-AND kill gate. Day 7 → Day 8 GO.
  - Sample availability: PASS_CAPACITY (LMT alone 3,152 contracts FY2024 → 39-firm extrapolation 19.5K-39K).
  - n=10 full-pipeline dry-run: PASS (10/10) on universe-filtered sample.
  - 3-vendor Fleiss κ_axis1 = **0.7863** (target ≥ 0.7 — 4-class FFP/IDIQ/OPTION/COST_PLUS).
  - Phase 0 OpenRouter spend: $0.334 / $8 cap.
  - No academic / industry-academic-grade scoop.
  - Publish-lag 5-bin distribution measured across 3 cohorts (2014/2018/2024).
- **Phase 1**: in progress. Day 9 LLM batch (~2K contracts × 3 vendors) running. Day 14 mid-checkpoint pending full batch.
- **Gate F (PURE daemon-free)** ✓ — SEC EDGAR never touched. Static + runtime guard verified.
- **Gate G (discovery-form)** ✓ — phenomenon-existence triggers.

## Critical Phase 0 finding (cohort-stratified publish lag)

The same-day USAspending publish fraction grew from **0.35 (FY2014)** to **0.65 (FY2018)** to **0.75 (FY2024)** — industry alt-data products (Apify USAspending AI Scoring, Govini Ark, FinBrain) progressively absorbed the same-day pickup window. This is itself a publishable observation about academic-vs-industry alpha first-mover-window dynamics (Cotropia 2017 USPTO patent quality pattern).

## Quickstart

```bash
# install
pip install -e .
pip install -e ../portfolio-coordination/shared-utils

# verify
python -m usaspending_contract_llm.resume                   # phase / manifest summary
python -m usaspending_contract_llm.usaspending_client       # smoke test against api.usaspending.gov
pytest tests/ -v                                             # 49 tests

# Phase 0 verification
python -m usaspending_contract_llm.phase0_kill_gate          # 6/6 PASS

# Phase 1 (after Day 9 LLM batch completes)
python -m usaspending_contract_llm.final_pipeline            # cross_section + ccm + cohort + rigor + timing + masking + day14

# dashboard
streamlit run dashboard/app.py
```

## Project layout

```
src/usaspending_contract_llm/
    manifest.py              # atomic_io + FileLock JSONL append (resumable)
    resume.py                # python -m usaspending_contract_llm.resume
    usaspending_client.py    # api.usaspending.gov client + Gate F guard
    universe.py              # data-driven universe (39 publicly traded primes)
    recipient_map.py         # 4-layer fallback (curated → filer_ontology → parent → M&A)
    parse.py                 # JSON 4-field extract
    publish_lag.py           # per-transaction publish-lag distribution
    publish_lag_v2.py        # cohort-stratified driver
    cohort_lag.py            # 3-cohort lag re-sample (2014/2018/2024)
    ensemble.py              # 3-vendor LLM client (Opus 4.7 + Sonnet 4.6 + Gemma-2-27b)
    oracle_run.py            # n=20 oracle + Fleiss κ
    universe_fetch.py        # universe-filtered fetch (per-prime)
    strategic_sample.py      # 30 primes × 5 cohorts → 8,365 contracts
    day9_batch.py            # stratified-by-(ticker, cohort) ensemble batch
    yfinance_join.py         # daily prices + EPS + 8-K CAR
    cross_section.py         # firm-quarter quintile spread (low-commit long / high-commit short)
    ccm_baseline.py          # CCM 2011 2-step regression (state-FE)
    cohort_heterogeneity.py  # §4.1 per-cohort Sharpe trajectory
    rigor.py                 # DSR + Newey-West + cluster bootstrap + BH-FDR
    timing_audit.py          # §4.2 naive vs realistic timing first-order proxy
    contamination_masking.py # §4.4 + §4.5 (LLM cutoff + firm-name redaction)
    commitment_surprise.py   # §3.5 sub-trigger #1b (within-firm change form)
    final_pipeline.py        # one-command runner for downstream
    phase0_kill_gate.py      # 6-AND evaluator
    day14_mid_checkpoint.py  # trigger #1 evaluator (reframed plan)
    dryrun_n10.py            # Day-5 end-to-end pipeline n=10

analysis/
    ccm_baseline_spec.md     # Cohen-Coval-Malloy 2011 baseline + 2-step regression form
    paper_outline.md         # 8-12p SSRN draft outline
    paper_writeup_skeleton.md # full draft skeleton with {placeholder} tokens

audits/
    scoop_search_2026-04-27.md
    self_audit_day*.md       # 5 logs, all 48h-kill-gate clear
    postmortem_template.md   # ready for HARD_KILL outcome

data/
    manifest_*.jsonl         # 11 resumable manifests
    cache/llm_responses/     # 5,850 LLM response cache (idempotent re-runs)
    universe_*.csv           # 39-firm universe
    oracle_n20.json          # Claude-anchored gold standard
    LABELER_GUIDE.md         # 3-axis schema spec

tests/                       # 49 tests, all PASS
checkpoints/                 # daily 08:00 / 20:00 KST
dashboard/app.py             # 5-page Streamlit MVP
```

## Phase / day plan (reframed 2026-04-27)

See `CLAUDE.md` and `analysis/paper_outline.md`.

- **Phase 0 (Day 1-7)**: ✓ DONE.
- **Phase 1 (Day 8-21)**: alpha-discovery + §4 robustness structure (Cotropia 2017 USPTO pattern).
  - Single hard kill = trigger #1: incremental R² < 5% AND quintile Sharpe < 0.3 AND ROC-AUC < 0.6 (ALL 3 AND fail).
  - Trigger #2 (industry lag) demoted from kill to §4 robustness *finding*.

## Key invariants

- **Daemon-free (Gate F)**: SEC EDGAR never reached. Runtime guard + static source scan + 6 dedicated tests.
- **Resumable**: every batch flushes atomic. Re-runs cost $0 via on-disk LLM cache.
- **Atomic writes**: all manifest writes go through `shared_utils.atomic_io` + FileLock.
- **Idempotent LLM calls**: request_id (hash of model + prompt + award_id) → on-disk dedup cache.
- **Vendor diversity**: 3-vendor (Anthropic Opus 4.7, Anthropic Sonnet 4.6, Google Gemma-2-27b) per Gate E.

## Reproducibility

- Total OpenRouter spend cap: $35 ($8 Phase 0 + $25 Phase 1 + $2 buffer).
- Total compute time: ~1 day (Phase 0) + ~1 day (Phase 1 batch) wall-clock.
- All data sources free-tier: USAspending.gov API, yfinance, OpenRouter pay-as-you-go (~$25).

## License

MIT.
