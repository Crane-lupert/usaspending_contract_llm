"""Recipient UEI -> ticker mapping with 4-layer fallback (Day 2 skeleton).

Per reference-validation §4.5.3, this is the *known yield-loss point* of the
end-to-end pipeline (target 80%, compounded coverage 74%). The 4-layer chain:

  1. Curated PARENT_TICKER seed table  (universe.py)         — Day 2 done
  2. shared_utils.filer_ontology fuzzy name match            — Day 2-3
  3. Parent rollup (subsidiary -> ultimate parent equity)    — Day 3-5
  4. Corporate-action history (M&A ticker change handling)   — Day 5-7

Day 2 deliverable is the *interface* — calls return None for layers not yet
wired, but the dispatch order is locked in. resume.py reports unmatched UEIs
in `manifest_recipient_map.jsonl` so we can see the long tail concretely.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .manifest import append_jsonl
from .universe import lookup_ticker, normalize_name

try:
    from shared_utils import filer_ontology  # type: ignore
    _HAS_FILER_ONTOLOGY = True
except Exception:  # pragma: no cover
    _HAS_FILER_ONTOLOGY = False


@dataclass
class MapResult:
    uei: str
    name_raw: str
    canonical: str
    ticker: Optional[str]
    layer: str            # "curated" | "filer_ontology" | "parent_rollup" | "ma_history" | "unmapped"
    notes: str = ""

    def to_row(self) -> dict:
        return {
            "uei": self.uei,
            "name": self.name_raw,
            "canonical": self.canonical,
            "ticker": self.ticker,
            "layer": self.layer,
            "notes": self.notes,
        }


def _layer1_curated(name: str) -> Optional[str]:
    """Layer 1: curated PARENT_TICKER table (universe.PARENT_TICKER)."""
    return lookup_ticker(name)


def _layer2_filer_ontology(name: str) -> Optional[str]:
    """Layer 2: shared_utils.filer_ontology fuzzy match.

    filer_ontology was originally a SEC filer-name -> CIK map; for M1 we use
    its name-normalization + fuzzy-match scaffolding to handle the long tail
    of small contractors that have a public parent listing under a different
    name. Returns None until the filer_ontology side gets a contractor-name
    layer (coord ticket open).
    """
    if not _HAS_FILER_ONTOLOGY:
        return None
    # Hook for future filer_ontology contractor-name extension.
    # As of 2026-04-27 commit 0a2f269 the filer_ontology only ships SEC filer
    # name -> CIK lookup -- not contractor-side. We return None here and rely
    # on layers 3-4 plus future coord ticket for the contractor extension.
    return None


def _layer3_parent_rollup(name: str) -> Optional[str]:
    """Layer 3: token-subsequence parent rollup.

    Layer 1 only catches strict-prefix matches. Layer 3 catches names where
    the parent's tokens appear in order *anywhere* inside the candidate -- e.g.
    'INTEGRATED L3 TECHNOLOGIES SUBSIDIARY' should still rollup to LHX.

    We deliberately use the *raw uppercased* candidate (not the suffix-
    stripped canonical) because the parent-key list itself contains
    suffix-suffixed entries like 'L3 TECHNOLOGIES'. Stripping both sides
    drops the very tokens we are trying to match on.
    """
    from .universe import PARENT_TICKER
    raw_tokens = name.upper().replace(",", " ").replace(".", " ").split()
    if len(raw_tokens) < 2:
        return None
    for key, ticker in PARENT_TICKER.items():
        if not ticker:
            continue
        key_tokens = key.split()
        if len(key_tokens) < 2:
            continue
        i = 0
        matched = True
        for tk in key_tokens:
            while i < len(raw_tokens) and raw_tokens[i] != tk:
                i += 1
            if i >= len(raw_tokens):
                matched = False
                break
            i += 1
        if matched:
            return ticker
    return None


def _layer4_ma_history(name: str) -> Optional[str]:
    """Layer 4: corporate-action / M&A history (Phase 1 task).

    Hook for future module that walks SEC EDGAR 13D/G + Form 8-K Item 1.01 +
    press-release ticker-change archive. Returns None until Phase 1 Day 10.
    """
    return None


def map_recipient(uei: str, name: str, *, log_to_manifest: bool = True) -> MapResult:
    """Run all 4 fallback layers in order. First non-None wins."""
    canonical = normalize_name(name)

    for layer_name, fn in (
        ("curated",         _layer1_curated),
        ("filer_ontology",  _layer2_filer_ontology),
        ("parent_rollup",   _layer3_parent_rollup),
        ("ma_history",      _layer4_ma_history),
    ):
        ticker = fn(name)
        if ticker:
            res = MapResult(uei=uei, name_raw=name, canonical=canonical,
                            ticker=ticker, layer=layer_name)
            if log_to_manifest:
                append_jsonl("recipient_map", res.to_row())
            return res

    res = MapResult(uei=uei, name_raw=name, canonical=canonical, ticker=None, layer="unmapped")
    if log_to_manifest:
        append_jsonl("recipient_map", res.to_row())
    return res


def yield_summary(rows: list[dict]) -> dict:
    by_layer: dict[str, int] = {}
    for r in rows:
        by_layer[r["layer"]] = by_layer.get(r["layer"], 0) + 1
    n = len(rows)
    mapped = sum(c for k, c in by_layer.items() if k != "unmapped")
    return {
        "n_total": n,
        "n_mapped": mapped,
        "yield_pct": round(100 * mapped / n, 1) if n else 0.0,
        "by_layer": by_layer,
    }
