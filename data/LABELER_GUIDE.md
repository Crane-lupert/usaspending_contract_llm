# M1 3-Axis Labeling Guide — USAspending Federal Contract Narrative

> Schema for both the n=20 oracle (gold standard) and the 3-vendor LLM ensemble. Labels must be deterministic given the input fields. β2 / C2 객관적 schema axis 패턴 reuse — when the contract type code itself dictates the answer, the LLM job is *to read the code + narrative consistently*, not to make a judgment call.

## Inputs (4 fields, from `manifest_parse.jsonl`)

1. **Description** — free-text obligation narrative (the LLM input that carries the most signal).
2. **psc_code + psc_description** — Product/Service Code (controlled vocabulary, e.g. `1510 Aircraft, fixed wing`).
3. **Awarding Sub Agency** — contracting officer's organizational scope (signals which DoD / civil branch).
4. **contract_award_type** — one of: `DEFINITIVE CONTRACT`, `BPA CALL`, `PURCHASE ORDER`, `DELIVERY ORDER`. *Used as the primary anchor for Axis-1*.

Optional / contextual:
- `naics_code`, `award_amount`, `start_date`, `end_date`, `recipient_name`.

## Axis 1 — Forward Revenue Commitment (4 classes)

The most objective axis. Anchored by `contract_award_type` and narrative cues.

| Label | Cue patterns | When to use |
|---|---|---|
| `FFP` | "firm fixed price", "FFP", set unit price, lump sum | Revenue is fully committed at signing. Recipient bears cost overrun risk. |
| `IDIQ_CEILING` | "indefinite delivery indefinite quantity", "IDIQ", "task order", "ceiling value", "blanket purchase agreement", "BPA", "delivery order" against an IDIQ vehicle | Ceiling is *aspirational*; only task orders within it are committed. Default for `BPA CALL` / `DELIVERY ORDER` types unless the narrative explicitly says FFP. |
| `OPTION_PERIOD` | "base year + N option years", "option to extend", "base + option", "exercise an option" | Base period committed; option years are conditional (Pr(exercise) ≈ 0.7-0.9 in defense). Exercise an option transactions count here if the underlying contract has option periods. |
| `COST_PLUS` | "cost-plus-fixed-fee", "cost-plus-incentive", "CPFF", "CPIF", "T&M", "time and materials", "level of effort", "LOE" | Recipient gets reimbursed for cost; revenue magnitude depends on actual burn. Highest commitment uncertainty. |

**Tie-breaker rule**: If multiple cues fire, use this priority: `COST_PLUS > IDIQ_CEILING > OPTION_PERIOD > FFP` (most uncertain wins, since the trader cares about *commitment risk*).

**Fallback**: If the narrative is opaque (e.g. just a stock-keeping number `8510833257!ADAPTER,ELECTRICAL`) and `contract_award_type` is:
- `DEFINITIVE CONTRACT` → `FFP` (default for definitive purchase of goods).
- `PURCHASE ORDER` → `FFP`.
- `BPA CALL` / `DELIVERY ORDER` → `IDIQ_CEILING`.

## Axis 2 — Program Continuity (3 classes)

Reads modification narratives to classify what is happening to a running program.

| Label | Cue patterns | When to use |
|---|---|---|
| `EXPANSION` | "increase scope", "additional units", "exercise option year", "modification to add", "incremental funding", "FUNDING ONLY ACTION" with positive obligation | Program is growing / option exercised / additional CLINs added. |
| `DESCOPE` | "decrease scope", "deobligation", "partial termination", "remove CLIN", negative `federal_action_obligation` | Program is shrinking (de-obligation, partial cancellation). |
| `TERMINATION` | "termination for default", "terminated for convenience", "T4D", "T4C", "terminated", "cancellation" | Full program kill. |

**Default for new awards** (no modifications yet): `EXPANSION` (the contract itself is an expansion of the recipient's revenue).

**Default for routine recurring task orders**: `EXPANSION` (each task order against an IDIQ ceiling expands the realized portion).

## Axis 3 — Protested-vs-Clean (2 classes)

Predicts post-award protest probability based on narrative + amount + agency cues.

| Label | Cue patterns | When to use |
|---|---|---|
| `PROTESTED_RISK` | award amount > $50M and sole-source; "8(a) sole source"; "competitive bid" with multi-incumbent history; agency = DoD large procurement; narrative mentions "post-award protest", "GAO bid protest", "court of federal claims" | High likelihood the loser-bidder protests within 10 days, triggering a CICA stay. |
| `CLEAN` | small dollar (< $5M); routine recurring (delivery order against existing BPA); micro-purchase; sole-source under simplified acquisition threshold | Low protest risk — most common label. |

**Default**: `CLEAN`. Only mark `PROTESTED_RISK` when at least one explicit cue fires.

## Output schema (the LLM must emit exactly this JSON)

```json
{
  "axis1_forward_revenue_commitment": "FFP" | "IDIQ_CEILING" | "OPTION_PERIOD" | "COST_PLUS",
  "axis2_program_continuity": "EXPANSION" | "DESCOPE" | "TERMINATION",
  "axis3_protested_vs_clean": "PROTESTED_RISK" | "CLEAN",
  "confidence": 0.0 to 1.0,
  "reasoning": "one sentence per axis, e.g. 'A1: FFP because narrative says \"firm fixed price\".'"
}
```

## Fallback to 2-axis (Phase 0 trigger #3)

If 3-axis Fleiss κ < 0.6 across the 3-vendor ensemble, fallback collapses Axis 1+2+3 → a single binary axis:

- `COMMITTED` = `FFP` ∧ (`EXPANSION` ∨ no-mod) ∧ `CLEAN`
- `CONDITIONAL` = anything else

This is the `forward-revenue-binary` Step-1 fallback per CLAUDE.md §abandon-criteria.

## Notes for the human anchor labeler (oracle author)

- Read the full Description before assigning labels.
- If three axes disagree on what kind of contract this is (rare), default to FFP/EXPANSION/CLEAN.
- Use confidence ≤ 0.7 when narrative is opaque (e.g. stock-keeping numbers); use confidence ≥ 0.9 when an explicit FFP / IDIQ / option keyword fires.
- The oracle is the gold standard; 3-vendor ensemble gets compared to it via accuracy + kappa.
