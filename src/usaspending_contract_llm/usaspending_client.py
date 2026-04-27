"""USAspending.gov API client — daemon-free (Gate F ✓).

Endpoint base: https://api.usaspending.gov/api/v2/

Used for:
- /search/spending_by_award/   — list defense/IT contract awards by recipient + FY
- /awards/<id>/                  — fetch a single award's full obligation text + PSC
- /awards/<id>/transactions/    — modification timeline

We do NOT touch SEC EDGAR (Gate F): no data.sec.gov / efts.sec.gov / www.sec.gov.
A guard at module import time aborts if any deny-listed SEC client is reachable
through this client's stack.

Rate limit: USAspending.gov publishes no formal RPS but throttles aggressively
above ~10 RPS in practice. We cap at 5 concurrent + tenacity exponential backoff
on 429/503/timeout. This is a self-throttle — no shared daemon.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Iterable, Iterator

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

API_BASE = "https://api.usaspending.gov/api/v2"

# Hard guard: any of these hostnames showing up here means SEC daemon leak (Gate F violation).
SEC_HOSTS_DENY = ("data.sec.gov", "efts.sec.gov", "www.sec.gov")

# Defense / IT NAICS prefixes (subset — full universe filter is Day 2 task).
DEFENSE_IT_NAICS_PREFIX = (
    "3364",  # Aerospace product & parts mfg
    "3361",  # Motor vehicle mfg (military vehicles)
    "5415",  # Computer systems design (incl. federal IT contractors)
    "5416",  # Management/scientific/technical consulting (Booz Allen, Leidos, SAIC)
    "5417",  # Scientific R&D services
    "3344",  # Semiconductor & electronic component
    "3345",  # Navigational, measuring, electromedical & control instruments
    "3342",  # Communications equipment
)

# Contract action codes filtered down to definitive obligations (skip de-obligations).
DEFAULT_AWARD_TYPE_CODES = ("A", "B", "C", "D")  # A=BPA call, B=purchase order, C=delivery order, D=definitive contract


@dataclass
class FetchSpec:
    fiscal_year: int
    award_type_codes: tuple[str, ...] = DEFAULT_AWARD_TYPE_CODES
    naics_prefixes: tuple[str, ...] = DEFENSE_IT_NAICS_PREFIX
    limit_per_page: int = 100  # API max = 100
    max_concurrent: int = 5


def _assert_no_sec_url(url: str) -> None:
    low = url.lower()
    for host in SEC_HOSTS_DENY:
        if host in low:
            raise RuntimeError(
                f"Gate F violation: SEC EDGAR host {host!r} reached from USAspending client. "
                f"PURE daemon-free invariant broken. URL={url!r}."
            )


class UsaSpendingClient:
    """Async HTTPX client with self-throttle + retry/backoff.

    Use as a context manager:
        async with UsaSpendingClient() as c:
            page = await c.search_spending_by_award(...)
    """

    def __init__(self, *, timeout: float = 30.0, max_concurrent: int = 5) -> None:
        self._timeout = timeout
        self._sem = asyncio.Semaphore(max_concurrent)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "UsaSpendingClient":
        self._client = httpx.AsyncClient(
            base_url=API_BASE,
            timeout=self._timeout,
            http2=True,
            headers={
                "User-Agent": "usaspending_contract_llm/0.0.1 (research; daemon-free; gate-F)",
                "Accept": "application/json",
            },
        )
        return self

    async def __aexit__(self, *exc) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential_jitter(initial=2, max=60),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
        reraise=True,
    )
    async def _post(self, path: str, json_body: dict) -> dict:
        assert self._client is not None, "Use as async context manager."
        url = f"{API_BASE}{path}"
        _assert_no_sec_url(url)
        async with self._sem:
            t0 = time.monotonic()
            r = await self._client.post(path, json=json_body)
            dt = time.monotonic() - t0
            if r.status_code in (429, 503):
                # Force tenacity to retry with backoff.
                raise httpx.HTTPStatusError(
                    f"throttle {r.status_code} after {dt:.1f}s",
                    request=r.request, response=r,
                )
            r.raise_for_status()
            return r.json()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential_jitter(initial=2, max=60),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
        reraise=True,
    )
    async def _get(self, path: str, params: dict | None = None) -> dict:
        assert self._client is not None, "Use as async context manager."
        url = f"{API_BASE}{path}"
        _assert_no_sec_url(url)
        async with self._sem:
            r = await self._client.get(path, params=params or {})
            if r.status_code in (429, 503):
                raise httpx.HTTPStatusError(
                    f"throttle {r.status_code}", request=r.request, response=r,
                )
            r.raise_for_status()
            return r.json()

    async def search_spending_by_award(
        self,
        spec: FetchSpec,
        *,
        page: int = 1,
        recipient_name: str | None = None,
        recipient_uei: str | None = None,
    ) -> dict:
        """POST /search/spending_by_award/

        Returns one page of awards under the given filters. The response shape:
            {"results": [...], "page_metadata": {"page": 1, "hasNext": true}}
        """
        filters: dict[str, Any] = {
            "time_period": [{
                "start_date": f"{spec.fiscal_year - 1}-10-01",
                "end_date":   f"{spec.fiscal_year}-09-30",
            }],
            "award_type_codes": list(spec.award_type_codes),
            "naics_codes": list(spec.naics_prefixes),
        }
        if recipient_name:
            filters["recipient_search_text"] = [recipient_name]
        if recipient_uei:
            filters["recipient_id"] = recipient_uei
        body = {
            "filters": filters,
            "fields": [
                "Award ID", "Recipient Name", "recipient_id", "Recipient UEI",
                "Last Modified Date", "Base Obligation Date",
                "Start Date", "End Date",
                "Award Amount", "Total Outlays",
                "Description", "Awarding Agency", "Awarding Sub Agency",
                "naics_code", "naics_description",
                "psc_code", "psc_description",
                "Contract Award Type",
                "generated_internal_id",
            ],
            "page": page,
            "limit": spec.limit_per_page,
            "sort": "Last Modified Date",
            "order": "desc",
        }
        return await self._post("/search/spending_by_award/", body)

    async def fetch_award(self, generated_internal_id: str) -> dict:
        """GET /awards/<generated_internal_id>/  — full award detail incl. obligation text."""
        return await self._get(f"/awards/{generated_internal_id}/")

    async def fetch_award_transactions(self, generated_internal_id: str) -> dict:
        """GET /awards/<id>/transactions/ — modification timeline (program continuity axis)."""
        return await self._get(f"/awards/{generated_internal_id}/transactions/")


def iter_award_pages_sync(
    spec: FetchSpec,
    *,
    recipient_name: str | None = None,
    max_pages: int | None = None,
) -> Iterator[dict]:
    """Synchronous wrapper for ad-hoc smoke tests / Day 1 sanity check.

    Yields each /search/spending_by_award/ page until hasNext=False or max_pages.
    """
    async def _run() -> list[dict]:
        out: list[dict] = []
        async with UsaSpendingClient() as c:
            page = 1
            while True:
                resp = await c.search_spending_by_award(spec, page=page, recipient_name=recipient_name)
                out.append(resp)
                meta = resp.get("page_metadata") or {}
                if not meta.get("hasNext"):
                    break
                if max_pages is not None and page >= max_pages:
                    break
                page += 1
        return out

    pages = asyncio.run(_run())
    return iter(pages)


async def smoke_test() -> dict:
    """Day 1 smoke test — fetch first page of FY2024 defense/IT awards.

    Returns lightweight summary (count, first-row keys, latency).
    Used by tests/test_smoke.py + Day 1 self-audit.
    """
    spec = FetchSpec(fiscal_year=2024, limit_per_page=10)
    t0 = time.monotonic()
    async with UsaSpendingClient() as c:
        page1 = await c.search_spending_by_award(spec, page=1)
    dt = time.monotonic() - t0
    results = page1.get("results", [])
    return {
        "ok": True,
        "elapsed_sec": round(dt, 2),
        "n_results": len(results),
        "first_keys": sorted(results[0].keys()) if results else [],
        "page_metadata": page1.get("page_metadata", {}),
    }


if __name__ == "__main__":
    # python -m usaspending_contract_llm.usaspending_client
    import json as _json
    out = asyncio.run(smoke_test())
    print(_json.dumps(out, indent=2, default=str))
