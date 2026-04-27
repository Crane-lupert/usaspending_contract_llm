# RESUMABLE.md — Project M1 (USAspending Federal Contract Narrative LLM)

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

## Phase 1 entry (Day 8) — what next session needs

1. **Strategic sampling expansion**: R1000 defense/IT × IS 2010-2020 + OOS 2021-2026 stratified → ~50K LLM target. Build via:
   - `usaspending_client.search_spending_by_award` w/ start_date/end_date overrides + recipient_search_text from universe.
   - Parallel asyncio.gather over 39 primes × cohort years.
   - Idempotent: dedup cache means re-runs cost $0.
2. **LLM 3-axis batch**: 50K × 3 vendors. Cost estimate at $0.004/call avg = ~$600. Way over budget. **Plan**: only 2 vendors for batch (Opus + Gemma — vendor-diversity preserved), or sample-down to 10K for IS + 10K for OOS = ~$80, or use only Sonnet 4.6 + Gemma. Need a cost / sample-size compromise — Day 8 kickoff decision.
3. **Cohen-Coval-Malloy 2011 baseline replication**: `analysis/ccm_baseline.py` (Day 12). Free-tier WRDS or Compustat substitute (Yahoo Finance R&D ratios + manually curated state-of-HQ for the 39 primes).
4. **Realistic execution audit core (Day 16)**: cohort-stratified naive-vs-realistic backtest + alpha-decay rolling Sharpe — this is the trigger #2 formal evaluator.

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
