"""Manifest atomic-IO wrappers for Project M1.

Wraps `shared_utils.atomic_io` (commit f4719d1, atomic_write_json + tmp+rename)
and adds JSONL append under FileLock — race-safe across the 3-vendor LLM
ensemble + asyncio.gather batches.

All manifest writes go through here. RAM-only state forbidden — every batch
flushes to disk so resume.py can pick up the next undone task.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from filelock import FileLock
from shared_utils import atomic_io  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

MANIFESTS = {
    "global":           DATA_DIR / "manifest_global.json",
    "fetch":            DATA_DIR / "manifest_usaspending_fetch.jsonl",
    "parse":            DATA_DIR / "manifest_parse.jsonl",
    "axis_classify":    DATA_DIR / "manifest_axis_classify.jsonl",
    "recipient_map":    DATA_DIR / "manifest_recipient_map.jsonl",
    "earnings_join":    DATA_DIR / "manifest_earnings_join.jsonl",
    "car_join":         DATA_DIR / "manifest_car_join.jsonl",
    "quintile":         DATA_DIR / "manifest_quintile_portfolio.jsonl",
    "ccm_incremental":  DATA_DIR / "manifest_ccm_incremental.jsonl",
    "publish_lag":      DATA_DIR / "manifest_publish_lag_audit.jsonl",
    "dryrun_n10":       DATA_DIR / "manifest_dryrun_n10.json",
}


def manifest_path(key: str) -> Path:
    if key not in MANIFESTS:
        raise KeyError(f"Unknown manifest key {key!r}; valid: {sorted(MANIFESTS)}")
    p = MANIFESTS[key]
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _lock_for(p: Path) -> FileLock:
    return FileLock(str(p) + ".lock", timeout=30)


def write_json(key: str, obj: Any) -> None:
    p = manifest_path(key)
    with _lock_for(p):
        atomic_io.atomic_write_json(p, obj)


def append_jsonl(key: str, row: dict) -> None:
    p = manifest_path(key)
    line = json.dumps(row, ensure_ascii=False, default=str) + "\n"
    with _lock_for(p):
        with p.open("a", encoding="utf-8") as fh:
            fh.write(line)


def read_json(key: str, default: Any = None) -> Any:
    p = manifest_path(key)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def read_jsonl(key: str) -> Iterator[dict]:
    p = manifest_path(key)
    if not p.exists():
        return iter(())
    def _gen() -> Iterator[dict]:
        with p.open("r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln:
                    yield json.loads(ln)
    return _gen()


def update_global(**fields: Any) -> dict:
    g = read_json("global", default={}) or {}
    g.update(fields)
    write_json("global", g)
    return g
