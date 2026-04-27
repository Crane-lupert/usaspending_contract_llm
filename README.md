# Project M1 — USAspending Federal Contract Narrative LLM

USAspending.gov federal contract obligation text → 3-vendor LLM ensemble → 3-axis classification (forward revenue commitment / program continuity / protested-vs-clean) → defense/IT contractor cross-section next-quarter earnings surprise prediction.

**Status (2026-04-27)**: Phase 0 Day 1 — repo skeleton + USAspending API client + CCM baseline spec.
**Gate F (PURE daemon-free)**: ✓ — SEC EDGAR not touched.
**Gate G (discovery-form)**: ✓
**Position**: β2 frozen swap queue 1순위 fill.

## Quickstart

```bash
pip install -e .
pip install -e ../portfolio-coordination/shared-utils
python -m usaspending_contract_llm.resume          # phase / manifest summary
python -m usaspending_contract_llm.usaspending_client  # smoke test against api.usaspending.gov
pytest tests/ -v
```

## Project layout

```
src/usaspending_contract_llm/
    __init__.py
    manifest.py             # atomic_io + FileLock JSONL append (resumable)
    resume.py               # python -m usaspending_contract_llm.resume
    usaspending_client.py   # api.usaspending.gov client + Gate F guard

analysis/
    ccm_baseline_spec.md    # Cohen-Coval-Malloy 2011 baseline + LLM extension regression form

audits/
    scoop_search_2026-04-27.md     # weekly academic + industry scoop log
    self_audit_*.md                # 48h-kill-gate logs

data/
    manifest_*.jsonl        # resumable batch state (created on first run)
    cache/llm_responses/    # request_id-keyed dedup cache

tests/
    test_manifest.py        # atomic IO round-trip
    test_resume.py          # Day-1 cold-start invariant
    test_usaspending_gate_f.py  # Gate F deny-list guard

checkpoints/                # daily 08:00 / 20:00 KST
```

## Phase / day plan

See `CLAUDE.md` and `d:/vscode/meta-harness/audits/2026-04-27-project-usaspending-contract-phase0-plan.md`.

- **Phase 0 (Day 1-7)**: API skeleton, n=10 dry-run, n=20 oracle Fleiss κ, USAspending publish-lag distribution.
  - Day 7 EOD single kill gate: 6-AND (sample ≥ 20K + dry-run ≥ 7/10 + κ ≥ 0.6 + spend ≤ $8 + scoop-clear + publish-lag-OK).
- **Phase 1 (Day 8-21)**: full LLM batch + cross-section quintile + realistic execution audit + alpha decay.
  - Day 16 핵심 gate: lag-<24h sample ≥ 50% OR alpha decay > 50%/yr → writeup-only freeze (full kill 아님).

## Key invariants

- **Daemon-free (Gate F)**: SEC EDGAR never reached. `tests/test_usaspending_gate_f.py` enforces.
- **Resumable**: every batch flushes manifest. `python -m usaspending_contract_llm.resume` is the entry point on every fresh session.
- **Atomic writes**: all manifest writes go through `shared_utils.atomic_io` + FileLock.
- **Idempotent LLM calls**: request_id (hash of model + prompt + award_id) → on-disk dedup cache.

## License

MIT (skeleton). Final license decision pending public-portfolio publication.
