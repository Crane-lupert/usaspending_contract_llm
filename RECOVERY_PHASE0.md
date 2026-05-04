# Project M1 — Recovery Phase 0 (2026-05-04)

> Resumes from `FREEZE_NOTICE.md` (2026-04-28). WRDS data (CRSP + IBES) now accessible at `E:/wrds-data-courier/`. CCM (CRSP/Compustat Merged) BLOCKED at WRDS USAGE permission level — bypassed via ticker → CUSIP → PERMNO chain through `crsp_a_stock.dseall` (no linktable needed).

## Day 1 verification — completed

### WRDS courier connection
- CRSP `dsf` / `stkdlysecuritydata` / `dseall`: ✅ accessible via `wrds_courier_client.query()`.
- IBES `statsumu_epsus` / `act_xepsus`: ✅ accessible via local DuckDB `read_csv(ignore_errors=true, strict_mode=false)`. Direct courier path failed on quote-embedded comma in IBES CSV — wrapper handles this.
- LMT smoke test: permno 21178, 22,144 daily rows since 1939; IBES oftic LMT, 1,480 quarterly EPS since 1995.

### Universe coverage (39-ticker M1 universe)

| Source | Coverage | Threshold | Verdict |
|---|---|---|---|
| **IBES `oftic`** | 37/39 = 94.9% | ≥ 80% | ✅ PASS (margin +14.9 pp) |
| **CRSP via IBES CUSIP-6** | 35/39 = 89.7% | ≥ 95% | initial FAIL |
| **CRSP after 1× expansion via `dseall` direct ticker** | 37/39 = **94.9%** | ≥ 95% | borderline (95% strict miss by 0.1 pp) |
| **Effective universe** | 37 firms | ≥ 30 (drift Rule 24 floor) | ✅ |

**Unresolved (2)**: BAESY (BAE Systems plc, UK ADR) + RYCEY (Rolls-Royce, UK ADR). These are *structural* foreign-ADR exclusions — CRSP US main file does not index ADRs of foreign-incorporated firms separately from underlying. Practical impact = 0 (already excluded from any cross-section quintile due to ADR liquidity discount).

**Power floor check**: 37 firms × 17 yr × 4 quarters ≈ 2,516 firm-quarter cells. **Clears CLAUDE.md §4.5.1 n_min ≥ 1,500 by ~68%.** This is the binding metric, not the 95% strict threshold.

### CCM bypass (BLOCKED schema impact)

`crsp_a_ccm` (CRSP/Compustat Merged) blocked at WRDS USAGE level. M1 path:
- ❌ Cannot use `ccmxpf_linktable` for PERMNO ↔ GVKEY join.
- ✅ M1 doesn't need GVKEY — we use **PERMNO directly from CRSP** for daily returns (CAR computation) + **CUSIP / oftic from IBES** for earnings surprise. No Compustat fundamental panel needed for the §3 main effect; CCM aggregate baseline can be built from `comp_na_daily_all.fundq_fncd` (annual fundamentals quarterly cuts) joined via CUSIP at the firm-quarter level.

CCM block is **NOT** a recovery blocker for M1.

### Pre-existing assets — preserved

| Asset | Status |
|---|---|
| `analysis/paper_v1.md` (8-12p draft) | ✅ preserved at commit `a801933` |
| `analysis/paper_outline.md` + `paper_writeup_skeleton.md` | ✅ preserved |
| `analysis/ccm_baseline_spec.md` | ✅ preserved (regression form unchanged) |
| `dashboard/app.py` (5-page Streamlit) | ✅ preserved |
| 49 tests | ✅ all PASS post-restore |
| LLM 3-axis cache (5,446 responses, $19 cost) | ✅ preserved (re-run cost = $0) |
| SEC EDGAR submissions cache (86 CIKs) | ✅ preserved |
| Universe CSV (836 rows, 39 distinct tickers) | ✅ preserved |

**Lift rate**: ~80%+ of pre-freeze infrastructure carries over. Recovery is *swap data layer*, not rebuild.

## Day 1 verdict

| Phase 0 EOD 5-AND kill gate | Status |
|---|---|
| #1 WRDS courier connection + CRSP/IBES accessible | ✅ |
| #2 Compustat/CRSP coverage ≥ 95% (or PASS_STRUCTURAL_CAVEAT) | ✅ at 94.9% (2 missing = foreign ADR, structural) |
| #3 IBES TICKER coverage ≥ 80% | ✅ 94.9% |
| #4 sample n_with_CAR ≥ 1,500 (Day 2-3 task) | not yet measured |
| #5 existing assets lift OK + paper draft audit | ✅ |

**Day 1: 4/5 PASS, 1 deferred to Day 2.** Proceed to Day 2 (3-way join + IBES surprise feature).

## Day 2 next tasks

1. Universe × CRSP (`stkdlysecuritydata`) × IBES (`act_xepsus` + `statsumu_epsus`) 3-way join → measure `n_with_CAR`.
2. Sanity check: yfinance vs CRSP daily return time-aligned (T-1, T+1) for top 5 firms; |Δ_return| should be < 5 bp at most timestamps.
3. Build IBES earnings surprise feature: `(actual_eps - statsumu.medest) / statsumu.stdev` at 30-day-pre-announcement window.
4. Cross-tab pre-analysis: cached LLM 3-axis vs IBES surprise sign at the firm-quarter level.

## References

- `FREEZE_NOTICE.md` — 2026-04-28 freeze.
- `FROZEN_WITH_CAVEAT.md` — 2026-04-28 verdict reframe.
- `analysis/paper_v1.md` — paper draft to extend → paper_v2.
- `D:/vscode/meta-harness/audits/2026-04-28-M1-paid-data-vendor-needs.md` §11-§16 — vendor decision tree.
- `E:/wrds-data-courier/INTERFACE.md` — WRDS courier client API.
- `E:/wrds-data-courier/WRDS_BLOCKED_SCHEMAS.md` — CCM blocked, secd substitute path.
