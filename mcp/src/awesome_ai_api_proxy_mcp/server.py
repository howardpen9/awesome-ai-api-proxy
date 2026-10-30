"""MCP server exposing the awesome-ai-api-proxy price observatory.

Six tools:
    list_providers()                 - all providers with status + pricing URL
    list_canonical_models()          - the 9 canonical models on the tier ladder
    get_price(model, provider?, unit?) - matching price records
    find_cheapest(model, unit?)       - cheapest record for a model+unit
    compare(model, unit?)             - all providers' prices, sorted ascending
    tier_overview(tier)               - all canonical models in a tier with prices

Data source: data/prices.latest.json from main branch (raw URL).
Cached in-memory for 5 minutes per process.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Override with AWESOME_AI_API_PROXY_REF=<branch_or_tag> for dev / staging.
# Defaults to `main` so production agents always see the latest merged data.
GIT_REF = os.environ.get("AWESOME_AI_API_PROXY_REF", "main")
RAW_BASE = f"https://raw.githubusercontent.com/howardpen9/awesome-ai-api-proxy/{GIT_REF}"

PRICES_URL = f"{RAW_BASE}/data/prices.latest.json"
PROVIDERS_URL = f"{RAW_BASE}/data/providers.yaml"
CANONICAL_URL = f"{RAW_BASE}/data/canonical-models.yaml"

CACHE_TTL_SECONDS = 300
_cache: dict[str, tuple[float, Any]] = {}


def _get_cached(key: str, fetch_fn) -> Any:
    now = time.time()
    cached = _cache.get(key)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]
    value = fetch_fn()
    _cache[key] = (now, value)
    return value


def _fetch_prices() -> dict:
    return _get_cached("prices", lambda: httpx.get(PRICES_URL, timeout=20).json())


def _fetch_providers() -> list[dict]:
    import yaml

    def go() -> list[dict]:
        raw = httpx.get(PROVIDERS_URL, timeout=20).text
        doc = yaml.safe_load(raw)
        out = []
        for section, entries in doc.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict):
                    out.append({"section": section, **entry})
        return out

    return _get_cached("providers", go)


def _fetch_canonical() -> list[dict]:
    import yaml

    def go() -> list[dict]:
        raw = httpx.get(CANONICAL_URL, timeout=20).text
        doc = yaml.safe_load(raw)
        return doc.get("canonical_models", [])

    return _get_cached("canonical", go)


mcp = FastMCP("awesome-ai-api-proxy")


@mcp.tool()
def list_providers() -> list[dict]:
    """List every relay station, gateway, and tool tracked in the registry.

    Returns each provider's name, URL, type (official / official-relay / mixed / reverse /
    aggregator / gateway-oss / observability / comparison / list), status, and
    pricing page when available.
    """
    out = []
    for p in _fetch_providers():
        out.append(
            {
                "provider_id": (p.get("pricing") or {}).get("fetcher"),
                "name": p.get("name"),
                "url": p.get("url"),
                "type": p.get("type"),
                "status": p.get("status"),
                "section": p.get("section"),
                "pricing_url": (p.get("pricing") or {}).get("pricing_url"),
                "has_fetcher": bool((p.get("pricing") or {}).get("fetcher")),
            }
        )
    return out


@mcp.tool()
def list_canonical_models() -> list[dict]:
    """List the canonical models picked to span the cost-tier ladder.

    Tier 1 = cheapest viable (routine work), Tier 2 = daily driver,
    Tier 3 = top frontier (hardest problems), Tier 4 = multimodal.
    The README's headline price table only compares these canonical models.
    """
    return [
        {
            "canonical": m["canonical"],
            "family": m.get("family"),
            "tier": m.get("tier"),
            "task": m.get("task"),
            "aliases": m.get("aliases", []),
        }
        for m in _fetch_canonical()
    ]


@mcp.tool()
def get_price(
    canonical_model: str,
    provider_id: str | None = None,
    unit: str | None = None,
) -> list[dict]:
    """Get price records for a canonical model.

    Args:
        canonical_model: e.g. "claude-sonnet-4.6", "grok-4.3", "deepseek-v3"
        provider_id: optional filter, e.g. "openrouter" / "atlascloud" / "relaydance"
        unit: optional filter, e.g. "per_1m_input_tokens" / "per_1m_output_tokens"

    Each record carries source_url + captured_at + method — the citation envelope.
    price_usd is quota USD after the public group ratio. effective_price_usd is
    cash USD when a checked top-up rate exists; the key is absent otherwise.
    Comparisons use price_usd so a relay with no rate is not ranked as if its
    cash price were zero. See docs/methodology.md.
    """
    doc = _fetch_prices()
    out = []
    for rec in doc.get("records", []):
        if rec.get("canonical_model") != canonical_model:
            continue
        if provider_id and rec.get("provider_id") != provider_id:
            continue
        if unit and rec.get("unit") != unit:
            continue
        out.append(rec)
    return out


@mcp.tool()
def find_cheapest(
    canonical_model: str,
    unit: str = "per_1m_input_tokens",
) -> dict | None:
    """Find the cheapest provider for a given canonical model and unit.

    Returns the single cheapest record with full provenance (source_url +
    captured_at) so the answer is citable. Returns None if no provider has the
    model at that unit.

    Note: "cheapest" doesn't mean "best" — see the ⚠ rule. If price is <50% of
    OpenRouter, the relay is likely reverse / mixed and may silently downgrade.
    Run docs/canary-prompts.md before trusting cheap relays.
    """
    matches = get_price(canonical_model, unit=unit)
    if not matches:
        return None
    return min(matches, key=lambda r: r["price_usd"])


@mcp.tool()
def compare(
    canonical_model: str,
    unit: str = "per_1m_input_tokens",
) -> list[dict]:
    """Compare all providers' prices for a canonical model, sorted cheapest first.

    Useful for cost-tier routing decisions: shows the spread at a glance.
    """
    matches = get_price(canonical_model, unit=unit)
    return sorted(matches, key=lambda r: r["price_usd"])


@mcp.tool()
def tier_overview(tier: int) -> dict[str, list[dict]]:
    """Show all canonical models in a tier with their compared prices.

    Args:
        tier: 1 (cheapest viable), 2 (daily driver), 3 (top frontier), 4 (multimodal)

    Returns {canonical_model: [sorted-cheapest-first records]}.
    """
    canon = [m for m in _fetch_canonical() if m.get("tier") == tier]
    out: dict[str, list[dict]] = {}
    for m in canon:
        out[m["canonical"]] = compare(m["canonical"])
    return out


@mcp.resource("data://prices/latest")
def prices_latest_resource() -> str:
    """The full latest prices.latest.json document as an MCP resource."""
    import json

    return json.dumps(_fetch_prices(), indent=2, ensure_ascii=False)


def main() -> None:
    """Entry point for `uvx awesome-ai-api-proxy-mcp` and `pip install -e .` console script."""
    mcp.run()


if __name__ == "__main__":
    main()
