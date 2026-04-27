"""3-vendor LLM ensemble client for the M1 3-axis classification.

Wraps `shared_utils.openrouter_client.OpenRouterClient` with:
- 3 model selection (Anthropic + non-Anthropic vendor diversity per Gate E)
- request_id-based dedup cache (idempotent re-runs over the same prompt)
- atomic cache write (manifest_axis_classify.jsonl)
- response JSON-shape validation against LABELER_GUIDE schema

Per CLAUDE.md §Dependencies, project="usaspending" cap=$20.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from .manifest import DATA_DIR, append_jsonl, manifest_path

# ---------------------------------------------------------------------------
# Bootstrap: load the coord-side .env so OPENROUTER_API_KEY is available
# without the user having to set the env var manually for each session.
# ---------------------------------------------------------------------------
_COORD_ENV = Path("D:/vscode/portfolio-coordination/.env")
if _COORD_ENV.exists() and not os.environ.get("OPENROUTER_API_KEY"):
    for k, v in (dotenv_values(_COORD_ENV) or {}).items():
        if k and v and k not in os.environ:
            os.environ[k] = v

# Import after env is loaded so OpenRouterClient sees the key.
from shared_utils.openrouter_client import OpenRouterClient  # noqa: E402

# ---------------------------------------------------------------------------
# 3-vendor model picks. Vendor diversity satisfies Gate E (no single-vendor).
# ---------------------------------------------------------------------------
DEFAULT_VENDORS: tuple[str, ...] = (
    "anthropic/claude-opus-4.7",          # Anthropic top-tier
    "anthropic/claude-sonnet-4.6",        # Anthropic mid-tier (different model row)
    "google/gemma-2-27b-it",              # Non-Anthropic (Google) — vendor-diversity guarantor
)

CACHE_DIR = DATA_DIR / "cache" / "llm_responses"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PROJECT = "usaspending"  # CLAUDE.md §Dependencies. Cap = $20 per project.


# ---------------------------------------------------------------------------
# 3-axis classification prompt. Stays tight — the LABELER_GUIDE.md is the
# authoritative spec; the prompt embeds the rule subset that fits the input
# context window without sending the full guide every call.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_TEMPLATE = """You are classifying a US federal contract obligation under M1's 3-axis schema.

3-axis labels (output exactly these strings):

Axis 1 — Forward Revenue Commitment (4 classes):
  FFP            : firm fixed price; lump sum
  IDIQ_CEILING   : indefinite delivery / BPA / delivery-order against ceiling
  OPTION_PERIOD  : base + N option years; "exercise an option"
  COST_PLUS      : cost-plus / T&M / level-of-effort
  Tie-break priority (most uncertain wins): COST_PLUS > IDIQ_CEILING > OPTION_PERIOD > FFP.

Axis 2 — Program Continuity (3 classes):
  EXPANSION    : new award, option exercise, scope increase, funding-only-action with +obligation
  DESCOPE      : deobligation, partial termination, scope decrease, negative obligation
  TERMINATION  : termination for default/convenience (T4D / T4C), full cancellation
  Default for a new award (no modification context): EXPANSION.

Axis 3 — Protested-vs-Clean (2 classes):
  PROTESTED_RISK : amount > $50M sole-source, large DoD procurement with multi-incumbent history
  CLEAN          : small/routine, delivery-order, micro-purchase
  Default: CLEAN. Only mark PROTESTED_RISK if an explicit cue fires.

Return ONLY a JSON object with these keys (no markdown, no preamble):
{{
  "axis1_forward_revenue_commitment": "FFP" | "IDIQ_CEILING" | "OPTION_PERIOD" | "COST_PLUS",
  "axis2_program_continuity":         "EXPANSION" | "DESCOPE" | "TERMINATION",
  "axis3_protested_vs_clean":         "PROTESTED_RISK" | "CLEAN",
  "confidence":                        0.0 to 1.0,
  "reasoning":                         "<= 200 chars, one phrase per axis"
}}

Contract:
  Description:                {description}
  PSC code:                   {psc_code} ({psc_description})
  Awarding sub agency:        {awarding_sub_agency}
  Contract award type:        {contract_award_type}
  NAICS:                      {naics_code}
  Award amount (USD):         {award_amount}
"""

VALID_AXIS1 = {"FFP", "IDIQ_CEILING", "OPTION_PERIOD", "COST_PLUS"}
VALID_AXIS2 = {"EXPANSION", "DESCOPE", "TERMINATION"}
VALID_AXIS3 = {"PROTESTED_RISK", "CLEAN"}


@dataclass
class EnsembleLabel:
    request_id: str
    contract_id: str
    model: str
    axis1: str | None
    axis2: str | None
    axis3: str | None
    confidence: float | None
    reasoning: str | None
    raw_text: str
    cost_usd: float
    tokens_in: int
    tokens_out: int
    error: str | None = None

    def to_row(self) -> dict:
        return {
            "request_id":  self.request_id,
            "contract_id": self.contract_id,
            "model":       self.model,
            "axis1":       self.axis1,
            "axis2":       self.axis2,
            "axis3":       self.axis3,
            "confidence":  self.confidence,
            "reasoning":   self.reasoning,
            "cost_usd":    self.cost_usd,
            "tokens_in":   self.tokens_in,
            "tokens_out":  self.tokens_out,
            "error":       self.error,
        }


def _request_id(model: str, contract: dict) -> str:
    """Idempotent cache key — same (model, contract_id) -> same request_id."""
    payload = json.dumps({
        "model": model,
        "contract_id": contract.get("generated_internal_id"),
        "description": contract.get("description"),
        "psc_code": contract.get("psc_code"),
        "contract_award_type": contract.get("contract_award_type"),
    }, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _format_prompt(contract: dict) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        description=(contract.get("description") or "")[:1500],
        psc_code=contract.get("psc_code") or "",
        psc_description=contract.get("psc_description") or "",
        awarding_sub_agency=contract.get("awarding_sub_agency") or "",
        contract_award_type=contract.get("contract_award_type") or "",
        naics_code=contract.get("naics_code") or "",
        award_amount=contract.get("award_amount", 0.0),
    )


_JSON_BRACE_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _parse_json_response(raw: str) -> dict | None:
    """LLMs sometimes wrap JSON in markdown fences or add preamble. Be lenient."""
    if not raw:
        return None
    raw = raw.strip()
    # Strip ```json ... ``` fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```\s*$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract the first {...} block
        for m in _JSON_BRACE_RE.findall(raw):
            try:
                return json.loads(m)
            except json.JSONDecodeError:
                continue
    return None


def _validate_label(d: dict | None) -> tuple[str | None, str | None, str | None, float | None, str | None, str | None]:
    """Return (axis1, axis2, axis3, confidence, reasoning, error)."""
    if not isinstance(d, dict):
        return None, None, None, None, None, "no_json_object"
    a1 = d.get("axis1_forward_revenue_commitment")
    a2 = d.get("axis2_program_continuity")
    a3 = d.get("axis3_protested_vs_clean")
    conf = d.get("confidence")
    reasoning = d.get("reasoning")
    err_parts = []
    if a1 not in VALID_AXIS1:
        err_parts.append(f"axis1_invalid:{a1!r}")
        a1 = None
    if a2 not in VALID_AXIS2:
        err_parts.append(f"axis2_invalid:{a2!r}")
        a2 = None
    if a3 not in VALID_AXIS3:
        err_parts.append(f"axis3_invalid:{a3!r}")
        a3 = None
    try:
        conf = float(conf) if conf is not None else None
    except (TypeError, ValueError):
        conf = None
    return a1, a2, a3, conf, (str(reasoning) if reasoning else None), (";".join(err_parts) if err_parts else None)


def _cache_path(request_id: str) -> Path:
    return CACHE_DIR / f"{request_id}.json"


def classify_one(
    *,
    contract: dict,
    model: str,
    client: OpenRouterClient | None = None,
    use_cache: bool = True,
    log_to_manifest: bool = True,
    max_tokens: int = 512,
    temperature: float = 0.0,
) -> EnsembleLabel:
    """Sync classify a single contract under one model.

    Idempotent: re-running the same contract+model returns the cached
    response and incurs $0 (modulo the small filesystem read).
    """
    rid = _request_id(model, contract)
    cache_p = _cache_path(rid)

    if use_cache and cache_p.exists():
        cached = json.loads(cache_p.read_text(encoding="utf-8"))
        return EnsembleLabel(
            request_id=rid,
            contract_id=contract.get("generated_internal_id", ""),
            model=model,
            axis1=cached.get("axis1"),
            axis2=cached.get("axis2"),
            axis3=cached.get("axis3"),
            confidence=cached.get("confidence"),
            reasoning=cached.get("reasoning"),
            raw_text=cached.get("raw_text", ""),
            cost_usd=0.0,
            tokens_in=0,
            tokens_out=0,
            error=cached.get("error"),
        )

    if client is None:
        client = OpenRouterClient(project=PROJECT)

    prompt = _format_prompt(contract)
    try:
        resp = client.complete(model=model, prompt=prompt, max_tokens=max_tokens, temperature=temperature)
    except Exception as e:
        label = EnsembleLabel(
            request_id=rid, contract_id=contract.get("generated_internal_id", ""), model=model,
            axis1=None, axis2=None, axis3=None, confidence=None, reasoning=None,
            raw_text="", cost_usd=0.0, tokens_in=0, tokens_out=0, error=f"api_error:{type(e).__name__}:{e}",
        )
        if log_to_manifest:
            append_jsonl("axis_classify", label.to_row())
        return label

    raw_text = ""
    try:
        raw_text = resp["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raw_text = ""
    parsed = _parse_json_response(raw_text)
    a1, a2, a3, conf, reasoning, validation_err = _validate_label(parsed)
    usage = resp.get("usage") or {}

    label = EnsembleLabel(
        request_id=rid,
        contract_id=contract.get("generated_internal_id", ""),
        model=model,
        axis1=a1, axis2=a2, axis3=a3,
        confidence=conf,
        reasoning=reasoning,
        raw_text=raw_text,
        cost_usd=float(usage.get("cost", 0.0) or 0.0),
        tokens_in=int(usage.get("prompt_tokens", 0) or 0),
        tokens_out=int(usage.get("completion_tokens", 0) or 0),
        error=validation_err,
    )

    if use_cache:
        cache_p.write_text(json.dumps({
            "request_id": rid,
            "model": model,
            "contract_id": label.contract_id,
            "axis1": a1, "axis2": a2, "axis3": a3,
            "confidence": conf, "reasoning": reasoning,
            "raw_text": raw_text,
            "error": validation_err,
        }, indent=2), encoding="utf-8")

    if log_to_manifest:
        append_jsonl("axis_classify", label.to_row())

    return label


def classify_ensemble(
    *,
    contract: dict,
    vendors: tuple[str, ...] = DEFAULT_VENDORS,
    use_cache: bool = True,
) -> list[EnsembleLabel]:
    """Run all 3 vendors on the same contract. Returns list of 3 EnsembleLabel.

    Vendors run in parallel via ThreadPoolExecutor (OpenRouterClient.complete
    is sync; concurrency is bounded by the upstream semaphore in shared_utils).
    """
    client = OpenRouterClient(project=PROJECT)
    with ThreadPoolExecutor(max_workers=len(vendors)) as ex:
        futures = [
            ex.submit(classify_one, contract=contract, model=m, client=client, use_cache=use_cache)
            for m in vendors
        ]
        return [f.result() for f in futures]


def classify_batch(
    *,
    contracts: list[dict],
    vendors: tuple[str, ...] = DEFAULT_VENDORS,
    use_cache: bool = True,
    max_concurrent_contracts: int = 3,
) -> dict[str, list[EnsembleLabel]]:
    """Run ensemble over a batch. Outer concurrency = `max_concurrent_contracts`.

    Returns {contract_id: [label_per_vendor, ...]}.
    """
    out: dict[str, list[EnsembleLabel]] = {}
    with ThreadPoolExecutor(max_workers=max_concurrent_contracts) as ex:
        futures = {
            ex.submit(classify_ensemble, contract=c, vendors=vendors, use_cache=use_cache): c
            for c in contracts
        }
        for f, c in futures.items():
            try:
                out[c.get("generated_internal_id", "")] = f.result()
            except Exception as e:
                out[c.get("generated_internal_id", "")] = [
                    EnsembleLabel(
                        request_id="", contract_id=c.get("generated_internal_id", ""),
                        model=m, axis1=None, axis2=None, axis3=None,
                        confidence=None, reasoning=None, raw_text="",
                        cost_usd=0.0, tokens_in=0, tokens_out=0,
                        error=f"batch_error:{type(e).__name__}:{e}",
                    ) for m in vendors
                ]
    return out
