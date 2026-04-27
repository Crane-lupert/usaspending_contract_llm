"""Resume CLI -- manifest read -> undone-task summary -> next-action hint.

Run:
    python -m usaspending_contract_llm.resume

This is the entry point a fresh session calls before doing anything else.
It must never crash on missing files (Day 1 has nothing yet) -- empty manifests
are valid state.
"""
from __future__ import annotations

import io
import sys
from datetime import datetime, timezone

from . import manifest as M

# Windows console default cp949 cannot encode unicode separators / Korean.
# Force stdout to UTF-8 so resume.py never crashes mid-overnight on Korean
# content that we propagate from CLAUDE.md / phase plans.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PHASE_DAY_PLAN = [
    ("Day 1", "Repo init + manifest skeleton + USAspending API skeleton + CCM read + scoop search + daemon-free Gate F verify"),
    ("Day 2", "defense/IT R&D-intensive R1000 universe filter + FY2024 target list + uei->ticker mapping skeleton"),
    ("Day 3", "USAspending API fetch first 100 + JSON 4-field parse"),
    ("Day 4", "3-axis LLM prompt + n=20 oracle + 3-vendor ensemble client"),
    ("Day 5", "n=10 dry-run #1 + publish lag first measurement (M1 specific)"),
    ("Day 6", "n=10 dry-run #2 + n=20 oracle done + 3-vendor Fleiss kappa"),
    ("Day 7", "Phase 0 EOD 6-AND kill gate (sample>=20K + dry-run>=7/10 + kappa>=0.6 + spend<=$8 + scoop-clear + publish-lag-OK)"),
]


def _phase_summary() -> dict:
    g = M.read_json("global", default={}) or {}
    return {
        "phase":          g.get("phase", "Phase 0 — Day 1"),
        "current_task":   g.get("current_task", "bootstrap (manifest skeleton)"),
        "last_synced":    g.get("last_synced", "never"),
        "phase0_spend":   g.get("phase0_openrouter_spend_usd", 0.0),
        "abandoned":      g.get("abandoned", False),
        "abandoned_reason": g.get("abandoned_reason", None),
    }


def _manifest_counts() -> dict:
    out = {}
    for key, path in M.MANIFESTS.items():
        if not path.exists():
            out[key] = 0
            continue
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as fh:
                out[key] = sum(1 for ln in fh if ln.strip())
        else:
            out[key] = 1 if path.stat().st_size > 0 else 0
    return out


def _next_action(counts: dict, summary: dict) -> str:
    if summary["abandoned"]:
        return f"ABANDONED: {summary['abandoned_reason']}. No further automated action."
    if counts["fetch"] == 0:
        return "Day 1-2: define defense/IT R1000 universe + run first 100 USAspending fetch (smoke test)."
    if counts["parse"] < counts["fetch"]:
        return f"Continue parse: {counts['fetch'] - counts['parse']} fetched rows pending JSON 4-field extract."
    if counts["axis_classify"] < counts["parse"]:
        return f"Continue 3-axis LLM classify: {counts['parse'] - counts['axis_classify']} parsed rows pending."
    if counts["recipient_map"] < counts["axis_classify"]:
        return f"Continue uei→ticker mapping: {counts['axis_classify'] - counts['recipient_map']} pending."
    if counts["publish_lag"] == 0:
        return "Day 5-7 (M1 특수): publish lag distribution measurement is the trigger #6 prerequisite."
    return "All tracked stages caught up. Inspect manifest_global.json for next milestone."


def main(argv: list[str] | None = None) -> int:
    summary = _phase_summary()
    counts = _manifest_counts()
    print("=" * 72)
    print("Project M1 -- USAspending Federal Contract Narrative LLM -- resume.py")
    print(f"Now (UTC):       {datetime.now(timezone.utc).isoformat()}")
    print(f"Repo root:       {M.REPO_ROOT}")
    print("=" * 72)
    print()
    print("Phase / task state")
    print("-" * 72)
    for k, v in summary.items():
        print(f"  {k:24s} {v}")
    print()
    print("Manifest row counts")
    print("-" * 72)
    for k, v in counts.items():
        print(f"  {k:24s} {v}")
    print()
    print("Day-by-day plan (Phase 0)")
    print("-" * 72)
    for d, desc in PHASE_DAY_PLAN:
        print(f"  {d}: {desc}")
    print()
    print("Next action")
    print("-" * 72)
    print(f"  {_next_action(counts, summary)}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
