"""xAI (Grok) official list prices — docs.x.ai/developers/pricing.

The vendor's own price page, used as the official baseline to measure relay
markups/discounts against (Atlas Cloud resells Grok; this is what it resells).
Like Atlas, docs.x.ai server-renders into a Next.js RSC stream. Prices are
encoded as protobuf-style strings: "$n12500" is an integer in units of 1e-10
USD, so $n12500 -> $1.25e-6 / token -> $1.25 / 1M tokens.

  LanguageModel       -> promptTextTokenPrice / completionTextTokenPrice / cachedPromptTokenPrice  (per token)
  ImageGenerationModel-> imagePrice                                                                (per image)
  VideoGenerationModel-> resolutionPricing[].pricePerSecond                                        (per second)
"""

from __future__ import annotations

from ._common import (
    FetchResult,
    PriceRecord,
    http_client,
    iter_objects_containing,
    next_f_blob,
)

PROVIDER_ID = "xai_official"
PROVIDER_NAME = "xAI (official)"
SOURCE_URL = "https://docs.x.ai/developers/pricing"

# RSC numbers are integers scaled by 1e-10 USD.
_N_SCALE = 1e-10

_TOKEN_FIELDS = (
    ("promptTextTokenPrice", "per_1m_input_tokens"),
    ("completionTextTokenPrice", "per_1m_output_tokens"),
    ("cachedPromptTokenPrice", "per_1m_input_cache_read_tokens"),
)


def fetch() -> FetchResult:
    with http_client() as c:
        r = c.get(SOURCE_URL)
        r.raise_for_status()
        blob = next_f_blob(r.text)

    records: list[PriceRecord] = []
    seen: set[str] = set()

    for d in iter_objects_containing(blob, '"$typeName":"auth_mgmt.LanguageModel"'):
        name = d.get("name")
        if not name or ("lang", name) in seen:
            continue
        seen.add(("lang", name))
        for field, unit in _TOKEN_FIELDS:
            usd_per_token = _n(d.get(field))
            if usd_per_token is None or usd_per_token <= 0:
                continue
            records.append(_rec(name, unit, usd_per_token * 1_000_000))

    for d in iter_objects_containing(blob, '"$typeName":"auth_mgmt.ImageGenerationModel"'):
        name = d.get("name")
        if not name or ("img", name) in seen:
            continue
        seen.add(("img", name))
        price = _n(d.get("imagePrice"))
        if price and price > 0:
            records.append(_rec(name, "per_image", price))

    for d in iter_objects_containing(blob, '"$typeName":"auth_mgmt.VideoGenerationModel"'):
        name = d.get("name")
        if not name or ("vid", name) in seen:
            continue
        seen.add(("vid", name))
        per_second = _cheapest_video_rate(d.get("resolutionPricing"))
        if per_second and per_second > 0:
            records.append(
                _rec(name, "per_second", per_second, note="cheapest resolution")
            )

    if not records:
        raise RuntimeError(
            "xAI pricing RSC parse produced 0 records — page markup likely changed."
        )

    return FetchResult(
        provider_id=PROVIDER_ID,
        records=records,
        raw_model_count=len(seen),
    )


def _cheapest_video_rate(resolution_pricing: object) -> float | None:
    if not isinstance(resolution_pricing, list):
        return None
    rates = [
        _n(r.get("pricePerSecond"))
        for r in resolution_pricing
        if isinstance(r, dict)
    ]
    rates = [x for x in rates if x and x > 0]
    return min(rates) if rates else None


def _n(raw: object) -> float | None:
    """Decode a "$n<int>" RSC price into USD."""
    if not isinstance(raw, str) or not raw.startswith("$n"):
        return None
    try:
        return float(raw[2:]) * _N_SCALE
    except ValueError:
        return None


def _rec(name: str, unit: str, price: float, note: str | None = None) -> PriceRecord:
    return PriceRecord(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        raw_model_name=name,
        channel_type="official-relay",
        unit=unit,  # type: ignore[arg-type]
        price_usd=price,
        source_url=SOURCE_URL,
        method="dom",
        notes=note,
    )
