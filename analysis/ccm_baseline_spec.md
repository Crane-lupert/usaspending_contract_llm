# Cohen-Coval-Malloy 2011 (JPE) Aggregate Baseline Spec — Project M1

> Day 1 deliverable. Defines the *aggregate baseline* on top of which Project M1's LLM-extracted forward revenue commitment features must show **incremental R² > 5%** (Phase 1 trigger #1) to clear the mechanism gate.
>
> Without this baseline written down before LLM batch launch, Phase 1 Day 13-14 incremental-R² claim is unfalsifiable. We measure what we said we would measure.

## 1. Source paper

- **Citation**: Cohen, L., J. Coval, C. Malloy. *"Do Powerful Politicians Cause Corporate Downsizing?"* Journal of Political Economy 119(6), Dec 2011, pp. 1015-1060.
- **NBER WP**: w15839 (2010 draft).
- **Google Scholar citations**: ~800+ as of 2026-04-27. Standard reference for political-spending → firm-value channel.
- **Key follow-up critique**: Snyder & Welch JPE 2017 — comments on identification strength. Cohen-Coval-Malloy reply (2017) defends the design. Both sides cited in M1's literature framing; M1 stays neutral on the IV debate and only uses CCM as a *baseline*, not an *identification claim*.

## 2. CCM identification strategy (the part we replicate)

- **Treatment**: A state's senator or representative becomes chair of a House/Senate committee that controls federal spending allocations.
- **Source of exogenous variation**: Committee chairmanship changes are largely driven by party control + seniority, plausibly orthogonal to a state's contemporaneous private-sector investment fundamentals.
- **Effect they document**: Federal spending → that state ↑ ~40-50% on average after chair gain. Firms HQ'd in that state respond by *cutting* CapEx, R&D, and employment.
- **Mechanism story**: Crowding-out (gov spending ↑ → private factor cost ↑ / private demand ↓). Reversed on chair loss.
- **Level of analysis**: firm-level dependent variable, state-level treatment.

## 3. CCM regression form (M1 will replicate exactly)

For firm i in state s, year t:

```
Y[i,s,t]  =  α  +  β · ChairChange[s,t]            (Step 1 — CCM baseline)
              +  γ · FedSpending[s,t]              (control)
              +  X[i,s,t]' · δ                     (firm controls: size, B/M, leverage, age, sector FE)
              +  μ[s] + τ[t]                       (state + year FE)
              +  ε[i,s,t]
```

where:
- `Y[i,s,t]` ∈ {CapEx/Assets, R&D/Assets, ΔEmployment, Investment Rate}
- `ChairChange[s,t]` = 1 if state s gains a relevant chair in year t (appropriations, ways/means, finance, etc.); -1 on loss; 0 else.
- `FedSpending[s,t]` = log(state-level federal obligation $ from USAspending, 2008+ — extending CCM's original 1967-2008 window with USAspending data 2008-2026).

**M1 sample expansion**: CCM used 1967-2008. We extend to **2008-2026 USAspending digital archive** (mandatory under FFATA 2006 / DATA Act 2014) — this is the modern slice where contract-level obligation *text* exists.

## 4. The M1 extension on top of CCM (Step 2 — what we add)

For *firm-quarter* (not firm-year — finer cross-section), q for firm i:

```
Surprise[i,q+1]  =  α  +  β1 · CCM_Aggregate[i,q]                     (Step-1 controls)
                       +  β2 · Forward_Revenue_Commitment[i,q]        (LLM-extracted, M1 NEW)
                       +  β3 · Program_Continuity[i,q]                (LLM-extracted, M1 NEW)
                       +  β4 · Protested_vs_Clean[i,q]                (LLM-extracted, M1 NEW)
                       +  X[i,q]' · δ                                 (firm controls)
                       +  μ[i] + τ[q]                                 (firm + quarter FE)
                       +  ε[i,q+1]
```

where:
- `Surprise[i,q+1]` = (Actual_EPS - IBES_Consensus_EPS) / |IBES_Consensus_EPS|, defense/IT R&D-intensive R1000 universe.
- `CCM_Aggregate[i,q]` = state-level federal spending change rolled up to firm i's HQ state (CCM-style aggregate).
- `Forward_Revenue_Commitment[i,q]` = Σ over firm i's FY2024-FY2026 contract awards: LLM 3-axis classification → committed-revenue $ (FFP × full ceiling + IDIQ × historical exercise rate × ceiling + option-period × Pr(exercise) × value + cost-plus × estimated burn).
- `Program_Continuity[i,q]` = Σ LLM tag of "expansion" (+1) / "descope" (-1) / "termination" (-2) on modifications in quarter q.
- `Protested_vs_Clean[i,q]` = Pr(post-award protest) for new awards in quarter q (LLM-classified).

## 5. Incremental R² gate (Phase 1 trigger #1 prerequisite — measure both)

- **R²_step1**: regression with CCM_Aggregate only.
- **R²_step2**: full regression including the three LLM-extracted variables.
- **Incremental R²** := R²_step2 − R²_step1.
- **Trigger threshold**: Incremental R² ≥ 5% → mechanism gate PASS. < 5% → negative writeup mode.
- **Equivalent F-test**: joint F on β2 = β3 = β4 = 0, threshold p < 0.001 (Bonferroni-3 within mechanism, separate from the 9-test universe).
- **Why 5%**: SEC-free brainstorm §4.3 + reference-validation §4 Phase 1 #1 sets the bar from prior CAM-style LLM extension benchmarks (Cohen-Malloy-Nguyen 2020 / Cohen-Lou-Malloy 2013 are similar-scale LLM/text adds with 3-7% incremental R² over numeric baselines).

## 5b. Commitment SURPRISE incremental R² (sub-trigger #1b — F1 frozen lesson F1-3 retroactive)

The level test above can fail simply because *expected* contract levels are already priced in. The SURPRISE form is the cleaner test:

```
Surprise[i,q+1]  =  α + β1 · CCM_Aggregate
                       + β5 · (FwdRevCommit[i,q] - E[FwdRevCommit[i,q] | IBES, options-implied, prior-runup])
                       + ...controls
```

- **Expectation prior**: stack of (IBES forward-revenue consensus, options-implied prob of revenue beat from near-the-money straddles, prior 60-day cumulative obligation Δ).
- **Threshold**: incremental R² over expectation prior ≥ 3% → SURPRISE channel exists.
- **Combinatorial verdict** (level #1 × surprise #1b):
  - PASS × PASS: standard mechanism alpha.
  - PASS × FAIL: level-based artifact (sell-the-news risk, F1 frozen-two-layer pattern).
  - FAIL × PASS: expectation-prior is the real alpha — paper headline candidate.
  - FAIL × FAIL: two-layer null; frozen-as-is.

## 6. Sample / data sources

| Element | Source | Window | Notes |
|---|---|---|---|
| State-level federal spending | USAspending.gov API `/search/spending_by_geography/` | 2008-2026 | Replaces CCM's CRSP-data-mart aggregate |
| Committee chairmanships | Charles Stewart's congressional committee dataset (public) | 2008-2026 | Used as control |
| Firm financials | Compustat (XRD/SALE for R&D filter, AT/CAPX/EMP for outcomes) | 2008-2026 | R1000 defense/IT |
| Earnings actuals + consensus | IBES / Compustat ACTQ + EPSPI | 2008-2026 | Quarterly |
| Stock returns | yfinance + CRSP | 2008-2026 | Daily; FF5+momentum residualized |
| Contract obligation text | USAspending API `/awards/<id>/` description + agency narrative | 2008-2026 | M1's LLM input |

## 7. Implementation milestones

| Phase 1 day | Task | Status |
|---|---|---|
| Day 12 | `analysis/ccm_baseline.py` — Step 1 replication, R²_step1 reported | pending |
| Day 13 | LLM 3-axis features merged into firm-quarter panel; Step 2 R²_step2 | pending |
| Day 14 | mid-checkpoint: trigger #1 evaluation | pending |
| Day 14b | trigger #1b SURPRISE gate evaluation | pending |

## 8. Falsification + robustness

- **Placebo state**: re-randomize state-of-HQ assignment within sector × year buckets — incremental R² should collapse to ~0%.
- **Pre-2008 hold-out** (CCM original window 1967-2008): run the same Step 1 regression on CCM's window — coefficient sign should match CCM's original β. If it doesn't, our CCM replication itself is bugged before we even add LLM features.
- **LLM cohort split**: 2008-2014 / 2015-2020 / 2021-2026 cohorts — incremental R² stability across cohorts is the §7 alpha-decay measurement. (OOS-IS)/IS < -0.5 → Phase 1 trigger #2 (writeup-only freeze).

## 9. References

- Cohen, Coval, Malloy 2011 JPE 119(6): 1015-1060.
- Cohen, Coval, Malloy 2017 reply to Snyder-Welch (laurenhcohen.com).
- Belasco, Cordesman 2010 RAND — defense-spending baseline.
- Eaton, Hassett 2018 RAND — defense-spending macro replication.
- Faccio 2006 AER, Goldman-Rocholl-So 2009 RFS — political-connection follow-ups.
- Reference-validation §1.3 + §10 — full citation table.

---

**Status**: spec frozen Day 1, 2026-04-27. Any deviation in Day 12-14 implementation requires a self-audit log (`audits/self_audit_ccm_baseline_<ISO>.md`) explaining the deviation.
