# RESUMABLE.md — Project M1 (USAspending Federal Contract Narrative LLM)

> Token-budget pause, not abandon. Next session resumes here.

## Status snapshot — 2026-04-27 EOD

- **Phase**: 0 (Day 3 of 7 done)
- **Day 7 single kill gate (6-AND)**: 4/6 passing-or-on-track, 2/6 not yet measurable
- **Phase 0 OpenRouter spend**: $0.00 / $8 cap
- **Total OpenRouter spend (this project)**: $0.00 / $35 cap
- **Gate F (daemon-free)**: ✓ (verified at runtime + import + static scan)
- **Tests**: 36 / 36 PASS
- **Commits**: 2 (Day 1 = `14ac8ef`, Day 2 = pending verify)
- **Mailbox sent**: 1 (`portfolio_coordination` re: OpenRouter key registration)

## Day 1+2+3 deliverables (done)

- **Skeleton + tooling**: `pyproject.toml`, `.gitignore`, dirs, settings.json, 4 .claude/skills/.
- **Modules**:
  - `manifest.py`         — atomic_io + FileLock + 11 manifest paths
  - `resume.py`           — entry point CLI (always run first)
  - `usaspending_client.py` — async httpx + tenacity backoff + Gate F deny-list guard
  - `universe.py`         — data-driven universe filter (39 publicly traded primes)
  - `recipient_map.py`    — 4-layer fallback chain (curated, filer_ontology, parent_rollup, ma_history)
  - `parse.py`            — JSON 4-field extract (100% yield / 100 sample)
  - `publish_lag.py`      — 5-bin distribution (v1 deprecated, v2 per-transaction)
  - `publish_lag_v2.py`   — per-transaction action_date measurement
  - `day3_smoke.py`       — Day-3 smoke driver
- **Tests** (36): manifest 5, resume 2, Gate F 6, universe 8, recipient_map 6, parse 4, publish_lag 5
- **Audits**: Day 1 / 2 / 3 self-audit logs + scoop search log
- **Specs**: `analysis/ccm_baseline_spec.md`
- **Data**: `data/universe_defense_it_r1000_fy2024.csv` (1,000 rows → 39 distinct tickers)

## Critical findings to carry forward

1. **Phase plan "≥ 200 firm" target was over-specified.** Empirical universe = ~39 publicly traded primes. Re-anchored to "≥ 30 firms". Binding metric remains **contract awards ≥ 12K (Day 5 trigger #1)** — Lockheed alone has 3,152 awards FY2024, so on track.

2. **Phase 1 trigger #2a preview-FIRES**: <24h publish-lag fraction = 75% on a 20-sample (biased toward currently-active records). Cohort-stratified re-sample at Day 16 will confirm. Most likely Phase 1 outcome: **writeup-only freeze**, negative-incremental publishable.

3. **`Last Modified Date` is a USAspending record-update timestamp**, not a per-transaction publish timestamp. v2 lag measurement uses POST /transactions/ to get per-transaction action_date — correct for currently-flowing mods, approximate for historical.

4. **Phase 0 trigger #6 satisfied early**: 5-bin distribution + <24h / <7d fractions all measurable. The Day 7 kill gate's hardest prerequisite is already met.

## Day 4 entry — what the next session needs

1. **Decide $ commitment for n=20 oracle** (~$0.20-1.00 estimate, well within $8 Phase 0 cap).
2. **Manual gold-label of n=20 random contract narratives** (3-axis: forward revenue commitment / program continuity / protested-vs-clean) — human judgment task, ~30-60 min.
3. **3-vendor LLM ensemble client setup** — Opus 4.7 / Sonnet 4.7 / Llama-3.3-70B (or Gemma-2-27B) via shared_utils.openrouter_client (project="usaspending_contract_llm" or "usaspending" — depends on coord reply).
4. **Cohort-stratified publish-lag re-sample** — 20 awards × 3 cohorts (2010-2014, 2015-2020, 2021-2026) = 60 transaction calls. Cheap.

## Resume command

Fresh session start:
```
python -m usaspending_contract_llm.resume
pytest tests/ -v
```

Then proceed with Day 4 prompt: `Day 4 시작` or `계속`.

## Open mailboxes / dependencies

- **Outbound**: `D:/vscode/portfolio-coordination/mailbox/portfolio_coordination/20260427T1604-usaspending_contract_llm-openrouter-project-registration.md` (correlation_id `20260427T1604-usaspending_contract_llm-001`). Non-blocking through Day 3-4.
- **Inbound**: none. Last broadcast `20260426T2340-portfolio_coordination-bcast-001` acknowledged in `.broadcast_seen`.

## Drift-watchdog standing items

- Re-anchor universe target documentation in next session's checkpoint header (Day 2 finding).
- Track Phase 1 trigger #2a / #2b through to Day 16 — if both fire, plan negative-incremental writeup framing.
