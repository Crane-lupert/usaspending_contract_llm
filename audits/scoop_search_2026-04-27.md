# Day 1 — Academic + Industry Scoop Search Log

- **Date**: 2026-04-27 KST
- **Triggers in scope**: Phase 0 #5 (academic scoop), Phase 1 #2 (industry lead time risk)
- **Action on positive**: immediate ABANDONED.md (no rescue attempt)

## 1. Search queries run

| # | Query | Surface | Hit? |
|---|---|---|---|
| 1 | `"USAspending" LLM "forward revenue" OR "earnings surprise" cross-section defense contractor 2025 2026 academic` | Web | **No academic match** — only commercial coverage of LMT/defense spend |
| 2 | `"federal contract" "obligation text" NLP defense stock returns earnings surprise SSRN arxiv 2026` | Web | **No direct match** — adjacent: Anser Press 2024 study on "public contract winning announcements" in pharma (event study, not LLM/NLP), generic PEAD-text papers |
| 3 | `FinBrain Apify Govini "USAspending AI scoring" defense IT contractor academic publication 2025 2026` | Web | Industry products confirmed (Apify USAspending Federal Contracts + AI Scoring, Govini Ark, Govini 2025 National Security Scorecard) — **no academic publication from these vendors** |
| 4 | `Cohen Coval Malloy 2011 JPE "Do Powerful Politicians Cause Corporate Downsizing" earmark firm value abstract` | Web | Confirms anchor exists, ~800+ cites, JPE 119(6), pp.1015-1060. NBER w15839. Snyder-Welch 2017 critique + CCM 2017 reply found. |

## 2. Adjacent prior art (cite, do not match)

- **Anser Press 2024 — "Effect of Public Contract Winning Announcements on Share Prices: An Event-Based Study on the Pharmaceutical Industry"** — narrowly pharma, event-study methodology, no LLM, no cross-section earnings-surprise prediction, no defense/IT focus. Cite + contrast.
- **Cook-Kazinnik-Hansen-McAdam SSRN 4627143 — "Evaluating Local Language Models: An Application to Financial Earnings Calls"** — earnings calls (SEC-filed transcripts), not federal contract text. Methodology adjacent but data orthogonal.
- **PEAT-LLM4LCR (SSRN 5503414)** — Chinese legal contract review. Methodology adjacent, jurisdiction + topic orthogonal.
- **PEAD.txt (Indiana Econ)** — text-augmented PEAD on earnings calls. Adjacent, not federal-contract.

None of these match the M1 angle (`USAspending obligation text × multi-vendor LLM × 3-axis forward revenue commitment × cross-section quarterly earnings surprise`). Phase 0 trigger #5 NOT fired.

## 3. Industry products (Phase 1 trigger #2 lead-time anchor)

| Product | Status 2026-04-27 | Threat to academic angle |
|---|---|---|
| **Apify USAspending Federal Contracts + AI Scoring** | Active (`apify.com/benthepythondev/usaspending-contracts-intelligence`) — opportunity-scoring tool, not academic | Medium — same data source, but no published methodology / cross-section earnings prediction / alpha-decay measurement |
| **Govini Ark + 2025 National Security Scorecard** | Active (Defense Acquisition Software of the Year 2025) — supply chain + program intelligence | Medium — DoD-side ingestion + LLM augment, not firm-level earnings surprise prediction |
| **Sweetspot opportunity discovery** | Active — bid recommendation tool, not academic | Low |
| **Fed-Spend / readthegovcontract** | Active — UI/aggregator, not academic | Low |
| **FinBrain "USAspending AI Scoring"** | Surface mention only (no accessible product page) | Low — but worth re-checking next week |
| **Palantir DoD AI awards 2024-2025** | DoD-side ingestion, not commercial publication | Low (DoD-internal, not academic alpha) |
| **Booz Allen federal IT consolidation tracking** | Advisory layer, not publication | Low |

**Verdict**: Industry product layer occupies the *aggregate scoring + DoD ingestion + UI* space. M1's academic angle (LLM 3-axis + cross-section earnings-surprise prediction + alpha-decay measurement + publish-lag audit) remains uncontested at the publication layer. **Phase 1 #2 is a risk to monitor weekly, not a kill condition today.**

## 4. Day 1 verdict

- Phase 0 trigger #5 (academic scoop): **NOT fired** — proceed.
- Phase 1 trigger #2 (industry lead-time): **NOT yet measurable** — requires publish-lag distribution measurement (Day 5-7). Re-check weekly per Phase 0 prompt.
- CCM 2011 anchor confirmed; baseline spec written → `analysis/ccm_baseline_spec.md`.

## 5. Next monitoring cadence

- **Weekly during Phase 0** (Day 1, 7): re-run queries 1-3.
- **Weekly during Phase 1** (Day 8, 14, 21): same + add "USAspending Cohen Coval Malloy LLM" + "DoD contract narrative cross-section earnings prediction" specific.
- **Trigger of weekly check**: any new SSRN / arxiv-q-fin / JF / RFS / JPE paper with the same angle → immediate ABANDONED.md (no rescue).

## 6. Sources (web-search returns inline above)

- USAspending.gov primary: <https://www.usaspending.gov/>
- Cohen-Coval-Malloy 2011 NBER WP: <https://www.nber.org/papers/w15839>
- Cohen-Coval-Malloy 2011 JPE: <https://www.journals.uchicago.edu/doi/abs/10.1086/664820>
- Snyder-Welch 2017 comment: <https://jason1566.github.io/jpe2017.pdf>
- CCM 2017 reply: <https://www.laurenhcohen.com/s/reply_powerful_politicians.pdf>
- Anser Press 2024 pharma event study: <https://www.anserpress.org/journal/jea/3/1/43>
- Apify USAspending AI Scoring: <https://apify.com/benthepythondev/usaspending-contracts-intelligence/api>
- Govini 2025 National Security Scorecard: <https://www.govini.com/insights/2025-national-security-scorecard>
