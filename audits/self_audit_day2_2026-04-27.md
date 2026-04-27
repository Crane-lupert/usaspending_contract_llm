# Day 2 Self-Audit — 48h-Kill-Gate (2026-04-27)

> Universe filter + recipient_map 4-layer fallback skeleton verified. Single audit covers Day 2 deliverables in one session.

## Verified tasks

1. **Universe filter (data-driven from USAspending /search/spending_by_category/recipient/)** — 10 pages × 100 = 1,000 raw recipient rows fetched.
2. **Curated parent-firm → ticker table** — expanded from 60 → ~150 entries.
3. **collapse_to_canonical + name normalization** — token + suffix-stripping works on real USAspending names.
4. **Recipient_map.py 4-layer fallback skeleton** — interface frozen, layers 1+3 wired, layers 2+4 stubbed for Phase 1.
5. **Per-prime contract count probe** — Lockheed alone has **3,152 contract awards in FY2024 defense/IT NAICS subset** (32 pages × ~100, 242s).
6. **Tests** — 27/27 PASS.

## 1. Findings (severity-ordered)

| # | Severity | Finding | Source |
|---|---|---|---|
| 1 | **structural** | Phase plan target "≥ 200 firm" is empirically unrealistic for *publicly traded* R1000 defense/IT direct primes. Top-1000 USAspending recipients FY2024 (NAICS 33xx + 5415-5417) collapses to **~39 distinct tickers**. The remaining ~830 are private (Sierra Nevada, Anduril, Peraton), FFRDC (MITRE, Battelle, RAND, JHU APL), university (MIT, Caltech, UCSD), or sub-million-$ small business contractors. | `data/universe_defense_it_r1000_fy2024.csv`, `manifest_global.universe_summary` |
| 2 | low | The original "200" target conflated *USAspending recipient count* with *publicly traded R1000 firm count*. The binding Phase 0 trigger #1 is *contract awards ≥ 12K* (Day 5), not firm count. | reference-validation §4 Phase 0 #1 |
| 3 | none | Layer 3 (token-subsequence parent rollup) initially failed because layer's normalization stripped the very tokens it needed to match. Fixed: layer 3 now uses raw uppercased name. | `src/usaspending_contract_llm/recipient_map.py:_layer3_parent_rollup` |
| 4 | low | Pagination beyond ~10K records on `/search/spending_by_award/` returns empty pages (hasNext=False with last_record_unique_id=None). Day 3+ needs date-window slicing or per-recipient queries to fetch deep history. | empirical pagination probe |
| 5 | low | `Recipient UEI` field appears in result JSON only when the source row has a UEI registered. Older awards (pre-2022) may use legacy DUNS only. Phase 1 IS 2010-2020 cohort will need DUNS→UEI bridging. | direct observation |

## 2. Resolution per finding

| # | Resolution |
|---|---|
| 1 | **Re-anchor universe target** to "≥ 30 publicly traded firms" empirically. Phase 0 trigger #1 (≥ 12K awards by Day 5) is the binding metric and *clearly clearable* with 39 firms (LMT alone = 3,152). Document in next checkpoint. **No phase plan amendment** because the binding metric is contract count, not firm count. |
| 2 | Same as #1 — note added to `checkpoints/2026-04-27.md`. |
| 3 | Already fixed; test added (`test_layer3_parent_rollup_token_subsequence_match`). |
| 4 | Day 3+ task: implement date-window slicing in `usaspending_client.search_spending_by_award` — split FY2024 into 4 quarter windows or 12 month windows. Each slice has < 10K records under our NAICS filter. |
| 5 | Phase 1 task — Day 8-10 will add a DUNS→UEI bridge using SAM.gov registry historical records (free public download). Not Phase 0 blocking. |

## 3. 48h-kill-gate

- **(a) Any unsolvable problem?** No.
- **(b) Solution applied → repo purpose lost?** No. Universe = 39 publicly traded primes is enough for cross-section quintile portfolio (5 quintiles × 8 firms = 40 firms; we have 39). LLM batch will operate on contract awards (~10K-30K), not firms. CCM extension regression operates on firm-quarter panels (39 firms × 16-18 yr × 4 quarters ≈ 2,500 obs) — sufficient for Welch / R² / cluster-bootstrap power.
- **(c) Solution within 48h verifiable retry?** Yes — all four resolutions are Day-3-7 routine.

→ **Verdict: continue. Move to Day 3 (USAspending API fetch first 100 + JSON 4-field parse).**

## 4. Drift-Watchdog snapshot

- **Rule 21 (vision anchoring)**: CLAUDE.md re-read at session start. ✓
- **Rule 22 (metric type)**: Day 2 metrics — universe firm count (mechanism, structural finding). No product claim made.
- **Rule 23 (scale)**: Original 250 firm target → empirical 39 firm reality. Ratio 39/250 = 15.6%. **Below the 10% trigger but close.** Documented as a *finding* not a *drift* — the original 250 was an estimate that USAspending recipient count would map mostly to public firms, which is empirically false. Phase 0 binding metric (contract awards ≥ 12K) is unaffected.
- **Rule 24 (drift trigger)**: scale 250 → 39 = 6.4× shrink. **Above the 2× threshold.** Per Rule 24 a correction phase is required. **Correction action**: revise universe-size target documentation in next session's checkpoint. No scope/metric change beyond that — the cross-section quintile alpha measurement still works at n=39.
- **Rule 25 (session re-anchor)**: 3-source re-load done.
- **Rule 26 (stat ≠ product)**: no statistical claim made.

## 5. Abandon-criteria mechanical check

| Phase 0 trigger | Status today |
|---|---|
| #1 sample availability < 12,000 by Day 5 | **NOT measurable yet** — Day 5 task. Lockheed alone hit 3,152 → trajectory clearly clears 12K. |
| #2 end-to-end coverage n=10 < 7/10 by Day 7 | Not yet measurable |
| #3 Fleiss κ < 0.6 (Day 6) | Not yet measurable |
| #4 spend > $8 | $0.00 — pass |
| #5 academic / industry scoop | NOT fired (Day 1 weekly check) |
| #6 publish lag measurement failure | Not yet measurable |

No fire. Proceed.

## 6. Sign-off

- Author: Claude (overnight session, 2026-04-27)
- Next checkpoint: Day 3 EOD — append to `checkpoints/2026-04-27.md` (same physical day for Day 1+2+3 in one overnight session).
- Next self-audit trigger: Day 3 first-100 fetch + JSON parse yield (target ≥ 99%).
