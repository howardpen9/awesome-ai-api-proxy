"""Atlas Cloud — pricing page RSC payload.

The public `/v1/models` JSON only lists ~120 text LLMs and exposes a single
(already-discounted) price. The marketing pricing page server-renders a richer
dataset into its Next.js RSC stream: 300+ models including image/video/3D
generation, each with `origin` (list) + `actual` (paid) prices and a `discount`
field. We parse that stream so the observatory captures the media models and the
per-model discount the JSON API hides.

Price encoding in the RSC:
  LLM   -> price.actual = {input_price, output_price, cache_price}  ($/1M tokens, already)
  media -> price.actual = {base_price}                              ($ per generation)
  discount = percent of list price you pay ("65" => pay 65% => -35%).
"""

from __future__ import annotations

from ._common import (
    FetchResult,
    PriceRecord,
    http_client,
    iter_objects_containing,
    next_f_blob,
)

PROVIDER_ID = "atlascloud"
PROVIDER_NAME = "Atlas Cloud"
SOURCE_URL = "https://www.atlascloud.ai/pricing/models"
DISPLAY_URL = "https://www.atlascloud.ai/pricing/models"

# Atlas category -> the unit its base_price is billed in. Image-producing tasks
# are per output image; everything else generative (video/3D/audio) is priced
# per generation call. We deliberately do NOT claim per-second for video here —
# the RSC carries no duration, so per_request is the honest unit.
_IMAGE_CATEGORIES = {"TEXT-TO-IMAGE", "IMAGE-TO-IMAGE"}

_TOKEN_UNITS = (
    ("input_price", "per_1m_input_tokens"),
    ("output_price", "per_1m_output_tokens"),
    ("cache_price", "per_1m_input_cache_read_tokens"),
)


def fetch() -> FetchResult:
    with http_client() as c:
        r = c.get(SOURCE_URL)
        r.raise_for_status()
        blob = next_f_blob(r.text)

    records: list[PriceRecord] = []
    seen: set[str] = set()
    for d in iter_objects_containing(blob, '"price":{"discount"'):
        model_id = d.get("model")
        price = d.get("price")
        if not model_id or model_id in seen or not isinstance(price, dict):
            continue
        actual = price.get("actual") or {}
        origin = price.get("origin") or {}
        if not isinstance(actual, dict):
            continue
        seen.add(model_id)

        categories = d.get("categories") or []
        discount_pct = _discount_pct(price.get("discount"))

        if "base_price" in actual:
            unit = "per_image" if _is_image(categories) else "per_request"
            records.extend(
                _media_records(model_id, actual, origin, unit, discount_pct, categories)
            )
        else:
            records.extend(_token_records(model_id, actual, origin, discount_pct))

    if not records:
        raise RuntimeError(
            "Atlas Cloud RSC parse produced 0 records — page markup likely changed."
        )

    return FetchResult(
        provider_id=PROVIDER_ID,
        records=records,
        raw_model_count=len(seen),
    )


def _is_image(categories: list[str]) -> bool:
    return any(c in _IMAGE_CATEGORIES for c in categories)


def _discount_pct(raw: object) -> float | None:
    """RSC `discount` is the percent of list price paid; convert to percent off."""
    try:
        paid = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    off = round(100.0 - paid, 2)
    return off if off > 0 else None


def _token_records(
    model_id: str, actual: dict, origin: dict, discount_pct: float | None
) -> list[PriceRecord]:
    out: list[PriceRecord] = []
    for src_key, unit in _TOKEN_UNITS:
        price = _f(actual.get(src_key))
        if price is None or price <= 0:
            continue
        out.append(_rec(model_id, unit, price, _f(origin.get(src_key)), discount_pct))
    return out


def _media_records(
    model_id: str,
    actual: dict,
    origin: dict,
    unit: str,
    discount_pct: float | None,
    categories: list[str],
) -> list[PriceRecord]:
    price = _f(actual.get("base_price"))
    if price is None or price <= 0:
        return []
    note = categories[0].lower() if categories else None
    return [_rec(model_id, unit, price, _f(origin.get("base_price")), discount_pct, note)]


def _f(v: object) -> float | None:
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _rec(
    model_id: str,
    unit: str,
    price: float,
    origin_price: float | None,
    discount_pct: float | None,
    note: str | None = None,
) -> PriceRecord:
    return PriceRecord(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        raw_model_name=model_id,
        channel_type="aggregator",
        unit=unit,  # type: ignore[arg-type]
        price_usd=price,
        origin_price_usd=origin_price if origin_price != price else None,
        discount_pct=discount_pct,
        source_url=DISPLAY_URL,
        method="dom",
        notes=note,
    )
